"""
Main function to pack stones from Thangavelu et al. with 10 degree pose interval.
20 walls are generated for each noise level.
"""
import matplotlib
import os
import pathlib
import datetime
import cv2
from cv2 import repeat

import matplotlib.pyplot as plt

import math
import numpy as np
from Stonepacker2D import *
from skimage.measure import label
from skimage.measure import regionprops

def seed_everything(seed=20):
    """"
    Seed everything.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)


seed_everything()
# ____________________________________________________________________________parameters
# %%
_root_dir = pathlib.Path(__file__).resolve().parent
_root_dir = os.path.abspath(_root_dir)
_rescale = 0.5
#wall_width = 780#noise10
# wall_width = 770
# wall_height = 450
# set_world_size(int(wall_width*_rescale)+2,int(wall_height*_rescale)+3)
set_ksteps(0)
set_stabalize_method('rotation')
set_head_joint_state(True)
set_local_width(10)
set_dilation(20)
set_number_cpu(12)
set_mu(0.58)
set_placement_optimization("image_convolve")
set_record_detail({'RECORD_PLACEMENT_IMG':False,'RECORD_PLACEMENT_VALUE':False})
matplotlib.interactive(False)
time_stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#read annotated wall image
wall_image = _root_dir+'/data/stones_noise_10_labels.png'
wall_image = cv2.imread(wall_image, cv2.IMREAD_GRAYSCALE)

#label
wall_image = wall_image.astype(np.uint8)
wall_image = label(wall_image)
# read each region
regions = regionprops(wall_image)
# get average bounding box width and height of regions
average_region_width = 0
average_region_height = 0
nb_valid_regions = 0
for region in regions:
    if region.area < 50:
        continue
    # plt.imshow(region.image)
    # plt.title(str(region.area))
    # plt.show()
    # max_width = max(region.bbox[3]-region.bbox[1],region.axis_major_length)
    # max_height = max(region.bbox[2]-region.bbox[0],region.axis_minor_length)
    max_width = region.bbox[3]-region.bbox[1]
    max_height = region.bbox[2]-region.bbox[0]
    average_region_width += max_width
    average_region_height += max_height
    nb_valid_regions += 1
average_region_width /= nb_valid_regions
average_region_height /= nb_valid_regions
wall_width = average_region_width*5
wall_height = average_region_height*5
print("Wall size: ", wall_width, wall_height)
set_world_size(int(wall_width*_rescale)+2,int(wall_height*_rescale)+3)
# create stones
stones = []
initial_rotation_angles = dict()  # positive clockwise
for i, region in enumerate(regions):
    stone = Stone()
    region_label = region.label
    # skip small regions
    if region.area < 50:
        continue
    # plt.imshow(region.image)
    # plt.title(str(region_label))
    # plt.show()
    # #dilate
    # stone_image = region.matrix.astype(np.uint8)
    # kernel = np.ones((3,3),np.uint8)
    # wall_image = cv2.dilate(wall_image,kernel,iterations = 1)
    # #erode
    # kernel = np.ones((3,3),np.uint8)
    # wall_image = cv2.erode(wall_image,kernel,iterations = 1)
    if stone.from_matrix(region.image_filled.astype(np.uint8), _rescale):
        stone.id = region_label
        #rotation_result_1 = stone.rotate_axis_align()
        #stone = rotation_result_1['stone']
        #rot_aa = rotation_result_1['angle']
        rotation_result = stone.rotate_min_shape_factor()
        stone = rotation_result['stone']
        stone.cal_shape_factor()
        stones.append(stone)
        initial_rotation_angles[stone.id] = rotation_result['angle']
        for angle_i in range(10,90,10):
            new_stone = Stone()
            #move the original_pose_matrix to the center of the image
            new_stone = stone.transformed(
            [int(stone.matrix.shape[1]/2)-stone.center[0], int(stone.matrix.shape[0]/2)-stone.center[1]])
            original_pose_matrix = new_stone.matrix.copy()
            # plt.imshow(new_stone.matrix.astype(np.uint8))
            # plt.title(str(new_stone.id))
            # plt.show()
            #rotate the matrix
            rot_mat = cv2.getRotationMatrix2D(
            new_stone.center, angle_i, 1.0)
            img_rotated = cv2.warpAffine(
                original_pose_matrix, rot_mat, original_pose_matrix.shape[1::-1], flags=cv2.WARP_FILL_OUTLIERS)
            #format the new matrix
            true_stone = np.argwhere(img_rotated)
            top_left = true_stone.min(axis=0)
            bottom_right = true_stone.max(axis=0)
            cropped_matrix = img_rotated[top_left[0]:bottom_right[0]+1, top_left[1]:bottom_right[1]+1]
            new_stone.matrix = np.zeros((new_stone.matrix.shape))
            new_stone.matrix[:cropped_matrix.shape[0],
                            :cropped_matrix.shape[1]] = cropped_matrix

            new_stone.center = [new_stone.center[0] -
                                top_left[1], new_stone.center[1]-top_left[0]]
            # Step 4
            region_prop = regionprops(new_stone.matrix.astype(np.uint8))
            bbx_width = region_prop[0].bbox[3]-region_prop[0].bbox[1]
            bbx_hight = region_prop[0].bbox[2]-region_prop[0].bbox[0]
            new_stone.height = bbx_hight
            new_stone.width = bbx_width
            new_stone.id = stone.id+angle_i*100
            #new_stone.cluster = stone.cluster
            #new_stone.roundness = stone.roundness
            stones.append(new_stone)
            # plt.imshow(new_stone.matrix.astype(np.uint8))
            # plt.title(str(new_stone.id))
            # plt.show()
            initial_rotation_angles[new_stone.id] = rotation_result['angle']+angle_i



# ______________________________WEIGHTS
iw = 1
kw = 1
cw = 1
gw = 1
lw = 1
sw = {'interlocking': iw, 'kinematic': kw,
    'course_height': cw, 'global_density': gw, 'local_void': lw}
# ______________________________END WEIGHTS
set_selection_weights(sw)
matplotlib.interactive(False)

max_nb_runs = 5
for wall_i in range(max_nb_runs):
    set_dump(True, _root_dir+'/result_'+time_stamp+f'_wall{wall_i}'+'/')
    if not os.path.exists(_root_dir+'/result_'+time_stamp+f'_wall{wall_i}'+'/'):
        os.mkdir(_root_dir+'/result_'+time_stamp+f'_wall{wall_i}'+'/')
        os.mkdir(_root_dir+'/result_'+time_stamp+f'_wall{wall_i}'+'/img/')
        os.mkdir(_root_dir+'/result_'+time_stamp+f'_wall{wall_i}'+'/record/')
    else:
        os.system('rm -rf '+_root_dir+'/result_'+time_stamp+f'_wall{wall_i}'+'/*')
        os.mkdir(_root_dir+'/result_'+time_stamp+f'_wall{wall_i}'+'/img/')
        os.mkdir(_root_dir+'/result_'+time_stamp+f'_wall{wall_i}'+'/record/')
    with open(get_dir()+'img/selection.txt', 'w+') as f:
        f.write("iteration;stone id;width;x;y;score;course height;global density;interlocking;local_density;kinematic\n")
    save_transformation_dir = get_dir()
    with open(save_transformation_dir+'transformation.txt', 'w+') as f:
        f.write("id;d_x;d_y;angle\n")
    base = Base()
    ground = Brick(int(wall_width*_rescale)+2, 2)
    ground.id = get_base_id()
    base.add_stone(ground, [0, 0])
    #base.matrix[:, -15:-1] = 1
    base.matrix[:, -1] = get_ignore_pixel_value()
    base.matrix[:, 0] = get_ignore_pixel_value()
    base.matrix[-1, :] = get_ignore_pixel_value()
    vendor = Vendor(stones,False)
    nb_clusters = vendor.cluster_stones()
    final_base = build_wall_vendor(
        base, vendor, nb_clusters,vendor_type = 'variant')
    
    # Output transformation
    for placed_stone in final_base.placed_rocks:
        current_stone_matrix = np.where(final_base.id_matrix==placed_stone.id,1,0)
        stone_prop = regionprops(current_stone_matrix.astype(np.uint8))
        stone_center = stone_prop[0].centroid
        d_x = (stone_center[1])/_rescale
        d_y = (stone_center[0])/_rescale
        angle_d = placed_stone.rot_angle
        angle_i = placed_stone.rotate_from_ori
        stone_id = placed_stone.id
        print(
            f"stone {stone_id} is placed at ({d_x},{d_y}) with stable angle {angle_d} degree")
        with open(save_transformation_dir+'transformation.txt', 'a+') as f:
            f.write("{};{};{};{}\n".format(placed_stone.id, d_x, d_y,
                    initial_rotation_angles[placed_stone.id]+angle_i+angle_d))


    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    import matplotlib.cm as cm
    tab20_cm = cm.get_cmap('tab20')
    newcolors = np.concatenate([tab20_cm(np.linspace(0, 1, 20))] * 13, axis=0)
    white = np.array([255/256, 255/256, 255/256, 1])
    newcolors[:1, :] = white
    newcmp = ListedColormap(newcolors)

    plt.imshow(final_base.matrix, cmap=newcmp,interpolation='none')
    # plt.axis('off')
    text_kwargs = dict(ha='center', va='center',
                        fontsize=10, color='black')
    for i, stone_i in enumerate(final_base.placed_rocks):
        plt.text(final_base.rock_centers[i][0],
                    final_base.rock_centers[i][1], str(i+1), **text_kwargs)
    plt.gca().invert_yaxis()
    result_plt_name = _root_dir+'/result_'+time_stamp+f'_wall{wall_i}'+'/' + \
        'Base_' + \
        str(sw['interlocking'])+'_'+str(sw['kinematic'])+'_' + \
        str(sw['course_height'])+'_'+str(sw['global_density'])+'.png'
    plt.savefig(result_plt_name, dpi=300)

    evaluate_kine(final_base, save_failure=True, load='tilting_table')

