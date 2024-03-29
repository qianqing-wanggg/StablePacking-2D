# Stone generation

`00_generate_fft_stones.py`

The stones are generated by prescribed Fourier descriptors that charatererize shape characteristics. The specific spectrum is chosen based on statistical data observed on real particles of the material. [The reference article](https://link.springer.com/article/10.1007/s10035-012-0356-x?utm_source=getftr&utm_medium=getftr&utm_campaign=getftr_pilot) for fft.

Four stone sets are generated:

- D2_0: This consists of stones of the same size (r = 30) and small elongation (D2=0).
- D2_0_uniformr: This consists of stones of uniformly distributed sizes from 10 to 50 pixels, with small elongation (D2=0).
- D2_02: This dataset is composed of stones with long elongation (D2=0.2) and radius of 30 pixels.
- D2_02_uniformr: This one also long elongation but uniformily distributed sizes from 10 to 50 pixels.

Other parameters are set as the following:

- D1=0
- D2 = 0.2
- D3 = 0.05
- D8= 0.015
- number of harmonics = 64
- number of points = 128
- image size = 150 pixels

The generated stones are stored in the data folder.

# Wall construction

`01_run.py`

Generate 5 packing layout for each stone set. The wall size is 420\*420 pixels.

# Visualizing

- 02_view_transformation_ori_reso.py: transform original stone images and visualize the layout in high resolution image.
- 03_evaluate_wall_metrics.py: evaluate the filling, stability and interlocking of all walls. It uses the functions of graph calculation in graph.py.
- 04_plot_filling_stability.py: plot filling and stability evaluations of all walls.
