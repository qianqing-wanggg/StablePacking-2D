"""
Compute the metrics of the original wall.
"""

from matplotlib.colors import ListedColormap
import pickle
import json
import os
import math
import cv2
from cv2 import repeat
import matplotlib.pyplot as plt
import pathlib
import math
from matplotlib import cm
import numpy as np
from Stonepacker2D import *
from skimage.measure import regionprops
from graph import build_graph
import networkx as nx
np.random.seed(2804)
def compute_FAV(G,wall_eroded_stones):
    start_FAV = []
    end_FAV = []
    nb_points= 10
    interval = int(wall_eroded_stones.shape[1]//nb_points)
    for column in range(10,wall_eroded_stones.shape[1]-10,interval):
        start_FAV.append((0,column))
        end_FAV.append((wall_eroded_stones.shape[0]-1,column))
    paths = []
    distances = []
    for i in range(len(start_FAV)):
        paths.append(nx.dijkstra_path(
            G, start_FAV[i], end_FAV[i], weight='weight'))
        distances.append(nx.dijkstra_path_length(
            G, start_FAV[i], end_FAV[i], weight='weight'))

    FAVs = []
    for i, path in enumerate(paths):
        true_distance = 0
        for node_i in range(len(path)-1):
            true_distance += np.linalg.norm(np.asarray(path[node_i]) -
                                            np.asarray(path[node_i+1]))
        FAVs.append(
            (true_distance-abs(start_FAV[i][0]-end_FAV[i][0]))/abs(start_FAV[i][0]-end_FAV[i][0]))
    # take the minimum 5 FAVs
    FAVs = np.sort(FAVs)[:5]
    FAV_100 = 100*np.average(np.asarray(FAVs))
    return FAV_100
def compute_FAH(G,wall_eroded_stones):
    start_FAH = []
    end_FAH = []
    nb_points= 10
    interval = int(wall_eroded_stones.shape[0]//nb_points)
    for row in range(10,wall_eroded_stones.shape[0]-10,interval):
        if wall_eroded_stones[row,0] == 0:
            start_FAH.append((row,0))
            end_FAH.append((row,wall_eroded_stones.shape[1]-1))

    paths_hori = []
    for i in range(len(start_FAH)):
        paths_hori.append(nx.dijkstra_path(
            G, start_FAH[i], end_FAH[i], weight='weight'))

    FAHs = []
    for i, path in enumerate(paths_hori):
        true_distance = 0
        for node_i in range(len(path)-1):
            true_distance += np.linalg.norm(np.asarray(path[node_i]) -
                                            np.asarray(path[node_i+1]))
        FAHs.append(
            (true_distance-abs(start_FAH[i][1]-end_FAH[i][1]))/abs(start_FAH[i][1]-end_FAH[i][1]))
    # take the minimum 5 FAHs
    FAHs = np.sort(FAHs)[:5]
    FAHs_100 = 100*np.average(np.asarray(FAHs))
    return FAHs_100
# ____________________________________________________________________________parameters

# read wall image
_root_dir = pathlib.Path(__file__).resolve().parent
_root_dir = os.path.abspath(_root_dir)
data_dir_prefix = "./data"
result_dir = "./data/"
#write metrics
with open(result_dir+'metrics.txt', 'a+') as f:
    f.write('wall_id;wall_stone_ratio;FAV;FAH\n')


metrics = np.zeros((4,))
metrics[0] = 0
wall_image = cv2.imread(data_dir_prefix+f'/stone_wall_freepik_mask_cut.png', cv2.IMREAD_GRAYSCALE)
wall_area = wall_image.shape[0]*wall_image.shape[1]
stone_area = len(np.argwhere(wall_image!=0))
metrics[1] = stone_area/wall_area

# horiontality and interlocking
wall_eroded_stones = np.zeros_like(wall_image)
regions = regionprops(wall_image)
for region in regions:
    stones_matrix = np.zeros_like(wall_image)
    stones_matrix[region.bbox[0]:region.bbox[2],region.bbox[1]:region.bbox[3]] = region.image
    stones_matrix = stones_matrix.astype(np.uint8)
    kernel = np.ones((3,3),np.uint8)
    stones_matrix = cv2.erode(stones_matrix,kernel,iterations = 1)
    wall_eroded_stones += stones_matrix
wall_eroded_stones = np.where(wall_eroded_stones!=0,255,0)
#padding zero rows to the top and bottom
wall_eroded_stones = np.concatenate((np.zeros((1,wall_eroded_stones.shape[1])),wall_eroded_stones,np.zeros((2,wall_eroded_stones.shape[1]))),axis=0)
#padding zero columns to the left and right
wall_eroded_stones = np.concatenate((np.zeros((wall_eroded_stones.shape[0],1)),wall_eroded_stones,np.zeros((wall_eroded_stones.shape[0],2))),axis=1)

G = build_graph(wall_eroded_stones, erosion=False)
for u, v, e in G.edges(data=True):
    e['weight'] = np.linalg.norm(np.asarray(u)-np.asarray(v))

if metrics[1]>0.6:
    metrics[2] = compute_FAV(G,wall_eroded_stones)
    metrics[3] = compute_FAH(G,wall_eroded_stones)
#write metrics
with open(result_dir+'metrics.txt', 'a+') as f:
    for metric in metrics:
        f.write(str(metric)+';')
    f.write('\n')



