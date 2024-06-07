# MIT License

# Copyright (c) 2024 Robotic Systems Lab - Legged Robotics at ETH Zürich

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

""" This file sets the energy function as well as the map-layers up. """

import yaml
from globalplanner import maps
import math
import numpy as np
import matplotlib.image as mpimg
import rasterio as rs
from mapdata import create_map_image
import os
import importlib.util

class Setup:
    """
    A class to create and change the map.

    This class is responsible for setting up the map layers and energy functions
    required for the global planner. It loads configuration files, initializes
    map parameters, and provides methods to load user-defined functions and create
    map layers. The class also defines constants for optimization weights and 
    plotting options.
    """
    ALPHA = 0.5 # weights optimisation between low energy (alpha=1)
    BETA = 0.5 # low risk (beta=1)
    GAMMA = 0 # and high scientific value (gamma=1); alpha+beta+gamma=1
    PLOT_GLOBAL = True

    def __init__(self, config_file, user_func_file, plot_global=True):
        """
        Initialize the Setup object.

        Parameters:
            config_file (str): Path to the configuration file for map layers.
            user_func_file (str): Path to the user-defined functions file.
            plot_global (bool, optional): Flag to enable or disable global plotting. Default is True.
        """
        self.PLOT_GLOBAL = plot_global
        self.energyreserve = math.inf
        self.map_size_in_pixel = [0,0]
        
        # load configs
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        self.load_user_function(user_func_file)

        self.n_layers = 5
        
        self.create_map(config.get('map_layers', []))
        self.define_constants()


    def load_user_function(self, user_func_file):
        """
        Load user-defined functions from the specified file.

        Parameters:
            user_func_file (str): Path to the user-defined functions file.

        This method dynamically loads the user-defined functions for energy calculation,
        risk assessment, robot limits, and constraint checking from the provided file.
        """
        spec = importlib.util.spec_from_file_location("robot_config", user_func_file)
        robot_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(robot_config)
        self.E_star = robot_config.E_star
        self.R_star = robot_config.R_star
        self.robot_limits = robot_config.robot_limits
        self.check_hard_constraints = robot_config.check_hard_constraints
        self.get_physical_values_from_cost = robot_config.get_physical_values_from_cost


    def create_map(self, config):
        """
        Loads the map data from the provided configuration.

        Parameters:
            config (dict): Configuration dictionary (defined as a yaml file) containing map layer details.
        """
        config_layers = {
            'Height': config.get('height', []),
            'Slope': config.get('slope', []),
            'Rock Abundance': config.get('rock_abundance', []),
            'Science': config.get('science', []),
            'Banned': config.get('banned', []),
            'Image': config.get('image', [])
        }

        # Get size of map from the height layer's file
        with rs.open(config_layers['Height'][0]['filename']) as dataset:
            self.map_size_in_pixel = (dataset.width, dataset.height)

        # Create Maps object with the height layer's filename and other parameters
        self.maps = maps.Maps(self.map_size_in_pixel, self.n_layers,
                              config_layers['Height'][0]['filename'],
                              "Height",
                              plot_global=self.PLOT_GLOBAL,
                              add_filter_for_heightmap=False,
                              layers_to_load=[config_layers['Height'][0]['layer']])

        # Iterate through each layer configuration
        for layer_name, layer_config in config_layers.items():
            if layer_name == 'Height':
                continue  # Skip height as it is already processed

            filename = layer_config[0].get('filename', '')

            if layer_name == 'Image':
                if filename.endswith('.png'):
                    self.maps.map_image = mpimg.imread(filename)
                elif filename.endswith('.tif'):
                    tif_input = filename
                    pic_output = os.path.join(os.path.dirname(tif_input), 'pic.png')
                    create_map_image.create_grayscale_image_from_tif(tif_input, pic_output, show_image=False)
                    self.maps.map_image = mpimg.imread(pic_output)
                continue # Load image not as map layer

            if filename:
                # Process GeoTIFF files
                if filename.endswith('.tif'):
                    if layer_name == 'Science':
                        self.maps.extract_geotiff_and_add_to_array(filename, layer_name,
                                                                   layers_to_load=[layer_config[0].get('layer')], normalize_value=True)
                    else:
                        self.maps.extract_geotiff_and_add_to_array(filename, layer_name,
                                                                   layers_to_load=[layer_config[0].get('layer')])
                elif filename.endswith('.npy'):
                    if layer_name == 'Science':
                        self.maps.load_npy_file_and_add_to_array(filename, layer_name, normalize_value=True)
                    else:
                        self.maps.load_npy_file_and_add_to_array(filename, layer_name)
            else:
                # Handle any layer if no filename is provided or filename is empty
                if not filename or filename.strip() == '':
                    empty_array = np.zeros((self.maps.n_px_height, self.maps.n_px_width))
                    self.maps.add_empty_layer(empty_array, layer_name)
                    continue

        # Add steep and rocky areas to banned areas
        slope = self.maps.maps_array[:,:,1]
        rockabundance = self.maps.maps_array[:,:,2]
        # Load banned areas or set to zero
        banned = self.maps.maps_array[:,:,4]
        for i in range(slope.shape[0]):
            for j in range(slope.shape[1]):
                if not self.is_within_robots_capabilities(slope[i, j], rockabundance[i, j]):
                    banned[i, j] = 1
        self.maps.maps_array[:,:,4] = banned
        self.maps.layer_names.append("Banned")


    def define_constants(self):
        ''' 
        Define constants for heuristic (h) and cost (g) functions.
        
        This method calculates and sets the maximum and minimum values for slope, 
        rock abundance, energy consumption, and risk based on the robot's capabilities 
        and the map data. These constants are used to normalize the heuristic and cost 
        functions in the path planning algorithm.
        '''
        # Get map of maximal slope
        max_slope_map = self.maps.get_slope_from_height(self.maps.maps_array[:,:,0])
        max_slope_map[max_slope_map>self.robot_limits()['smax']]=self.robot_limits()['smax']
        max_slope_map[max_slope_map<self.robot_limits()['smin']]=self.robot_limits()['smin']
        
        # Get map of maximal rock abundance
        max_rockabundance_map = self.maps.maps_array[:,:,2]
        max_rockabundance_map[max_rockabundance_map>self.robot_limits()['rmax']]=self.robot_limits()['rmax']
        max_rockabundance_map[max_rockabundance_map<self.robot_limits()['rmin']]=self.robot_limits()['rmin']
        
        # Get map of maximal energy consumption
        distance_max = math.sqrt(2) * abs(self.maps.pixel_size)
        E_map_max = self.E_star(max_slope_map, max_rockabundance_map, distance_max)
        # Get map of maximal risk (manually bc R function with if statement does not support array)
        R_map_max = np.zeros(max_slope_map.shape)
        for i in range(max_slope_map.shape[0]):
            for j in range(max_slope_map.shape[1]):
                R_map_max[i,j] = self.R_star(max_slope_map[i,j], max_rockabundance_map[i,j], distance_max)
        # Get maximal values
        self.Emax = np.nanmax(E_map_max)
        self.Rmax = np.nanmax(R_map_max)

        # Get map of minimal slope
        min_slope_map = self.maps.get_slope_from_height(self.maps.maps_array[:,:,0], get_min_slope=True)
        min_slope_map[min_slope_map>self.robot_limits()['smax']]=self.robot_limits()['smax']
        min_slope_map[min_slope_map<self.robot_limits()['smin']]=self.robot_limits()['smin']
        
        # Get map of minimal rock abundance
        min_rockabundance_map = self.maps.maps_array[:,:,2]
        min_rockabundance_map[min_rockabundance_map>self.robot_limits()['rmax']]=self.robot_limits()['rmax']
        min_rockabundance_map[min_rockabundance_map<self.robot_limits()['rmin']]=self.robot_limits()['rmin']
        
        # Get map of minimal energy consumption
        distance_min = abs(self.maps.pixel_size)
        E_map_min = self.E_star(min_slope_map, min_rockabundance_map, distance_min)
        # Get map of minimal risk (manually bc R function with if statement does not support array)
        R_map_min = np.zeros(min_slope_map.shape)
        for i in range(min_slope_map.shape[0]):
            for j in range(min_slope_map.shape[1]):
                R_map_min[i,j] = self.R_star(min_slope_map[i,j], min_rockabundance_map[i,j], distance_min)
        # Get minimal values
        self.Emin = np.nanmin(E_map_min)/self.Emax
        self.Rmin = np.nanmin(R_map_min)/self.Rmax
        # Get minimal cost for heuristic
        self.hmin = self.ALPHA * self.Emin + self.BETA * self.Rmin

        # print("Emin, Rmin: ", Emin, Rmin)
        # print("hmin: ", self.hmin)
        # print("Emax, Rmax: ", self.Emax, self.Rmax)


    def h_func(self, current_node, goal_node):
        '''
        Define the heuristic function h(x, y)
            Parameters:
                current_node ((int, int)): Tuple (x, y) in pixels defining the current node for which \
                    the heuristic is calculated
                goal_node ((int, int)): Tuple (x, y) in pixels defining the goal node
            Returns:
                float: Heuristic value
        '''
        x1, y1 = current_node
        x2, y2 = goal_node
        return self.hmin * math.sqrt((x2-x1)**2 + (y2-y1)**2)


    def g_func(self, current, previous):
        '''
        Define the cost function g(x, y) that calculates the cost from the previous node to the current node.
            Parameters:
                current ((int, int)): Node (x, y) in pixels defining the current node.
                previous ((int, int)): Node (x, y) in pixels defining the previous node.
            Returns:
                float: Total cost from the previous node to the current node.
        '''
        # get slope and rock abundance of node
        maps = self.maps.get_maps_array()
        x, y = current
        x0, y0 = previous
        distance = self.getdistance(current, previous)
        s = math.degrees(math.atan((maps[x,y,0]-maps[x0,y0,0]) / distance))
        t = maps[x,y,2]

        if self.is_within_robots_capabilities(s, t):
            E = self.E_star(s,t,distance)/self.Emax
            R = self.R_star(s,t,distance)/self.Rmax
        else:
            E = math.inf
            R = math.inf
        I = 1-maps[x,y,3]
        if maps[x,y,4]==1:
            B = math.inf
        else:
            B = 0

        total = self.ALPHA * E + self.BETA * R + self.GAMMA * I
        return E, R, I, B, total


    def getdistance(self, node1, node2):
        '''
        Calculates the Euclidean distance between two nodes.
        
        Parameters:
            node1 ((int, int)): Tuple (x, y) in pixels defining the first node.
            node2 ((int, int)): Tuple (x, y) in pixels defining the second node.
        
        Returns:
            float: Distance scaled on the map.
        '''
        x1, y1 = node1
        x2, y2 = node2
        return math.sqrt((x2-x1)**2 + (y2-y1)**2) * abs(self.maps.pixel_size)


    def is_within_robots_capabilities(self, s, r):
        '''Check if the slope and rock abundance values of this field exceed the defined limits

        Parameters:
            s (float): Slope value to check.
            r (float): Rock abundance value to check.

        Returns:
            bool: True if the values are within the limits, False otherwise.
        '''
        limits = self.robot_limits()
        if limits['smin'] <= s <= limits['smax'] and limits['rmin'] <= r <= limits['rmax']:
            return True
        return False


    def get_geo_xmin_ymin_xmax_ymax(self):
        return self.maps.get_geo_xmin_ymin_xmax_ymax()
