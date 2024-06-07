# lunar_path_planner

This planner is developed by Julia Richter and part of the work "Multi-Objective Global Path Planning for Lunar Exploration with a Quadruped Robot".

Currently the path planning and analysis tool are only implemented for Aristarchus IMP and the ANYmal robot. Instructions on how to add further maps and other robots/ rovers will follow briefly.
Also the path export is currently under development. 

## Setup
* `git clone https://github.com/jurichterrsl/lunar_path_planner.git`
* `cd lunar_planner`
* create virtual environment named `venv` with method of choice (e.g. in terminal `python3.8 -m venv env`)
* `source env/bin/activate`
* `pip install -r requirements.txt` (Error from PyYAML can be ignored)
* `pip3 install -e .`

# Download map

* Open quickmap (https://quickmap.lroc.asu.edu)
* Choose Lunar Globe and navigate to region of interest
* Go to Layers and analyse which layers will be relevant
* Go to Draw & Query Tool and select bounding box. Set max pixels and click on `Download Cube`
* Choose layers (For sure use WAC global mosaic, TerrainHeight, TerrainSlope and Rock Abundance) and download the resulting .tif file
* Analyse downloaded tif file with `python src/mapdata/analyse_geotiff.py path/to/file.tif`. The important output are the 'Layer names' since they show in which order the layers are in the tif file. Analyse them and use this information to create the .yaml file as described in the next point.

# Run Scripts for map preparation (Obligatory)
If needed, I provide scripts to further preprocess or create more layers. 

* If several scientific layers are available, merge them into one tif file with `python src/mapdata/merge_tif_files.py /path/to/input_geotiff /path/to/output_npy` (please look at file to adapt the weights between the different map layers)
* If hand-labeled scientific interests are wished for, mark them on a map with `python src/mapdata/paint_map.py /path/to/input_geotiff /path/to/input_image_path /path/to/output_npy_path`. This needs a .png image of the area which can created from the downloaded .tif file with `python src/mapdata/create_map_image.py /path/to/input_geotiff /path/to/output_image_path`
* To create a gradient on this image, use `python src/mapdata/blur_map.py /path/to/input_npy_path /path/to/output_npy_path blur_radius minimal_value`

# Create .yaml file for config_map

In the config_map all layers which will be used are listed. Each layer needs the following parameters:

* type: 'tif', 'npy' or 'image'
* filename: Path to the file which is being loaded
* description: A string or a list of strings which describes the layers of the file. For .npy files, currently only one-dimensional inputs are supported.
* layers_to_load: A list of which layers need to be loaded. If param is left empty, all layers are loaded. The first layer is specified with number 1. (check aristarchus_cp.yaml)

Examples are given in the `user_data/config_map` folder.

Special remarks for type 'image':

* The image file can be either a .png of the same extent as the given geotiff file or a specified layer of a .tif file. In case of the latter, the parameter 'layers_to_load' should be set to the index of the layer which is to be used.

## Run GUI

* run `python src/user_interface/path_creator.py` to create database
* run `python src/user_interface/path_analysis.py` to analyse paths
* run `python src/user_interface/path_planning_widget.py` to create paths manually ???

## Leave venv
* `deactivate`
