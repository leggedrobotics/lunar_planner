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

""" This file loads and analyses geotiff data.
It saves the different map layers into an array, which can be imported by the setup.py file """

### modules
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib import ticker
import globalplanner.transform as transform
import rasterio as rs
import math
from scipy.ndimage import convolve


class Maps:
    """
    A class to create and change the map.
    
    Attributes and Methods can be seen in the class diagram by running 'pyreverse -o png \
        path/to/src/globalplanner'
    """

    # DEFAULT_CMAP = colors.LinearSegmentedColormap.from_list\
    #     ("", ["darkslategray","mediumturquoise",'#c9a687','#a6611a'])
    DEFAULT_CMAP = 'viridis'
    
    def __init__(self, map_size, n_layers, init_filename, layer_description, plot_global=True, plot_pixel=False, add_filter_for_heightmap=False, layers_to_load=None):
        ''' 
        Initialize object map
            Parameters:
                map_size ((int, int)): n_pixel_width and n_pixel_height
                n_layers (int): final number of layers of the map
                init_filename (String): the first tif-file to initiate the map; following tif \
                    files have to be at the same location on the map
                layer_description (list[int]): List with Strings to describe the first added layers
                plot_global (Boolean): if plots are plotted in global (usually LON & LAT) or \
                    local coordinates (x=(0,width), y=(0,height))
                plot_pixel (Boolean): if plots are plotted in pixel coordinates
                add_filter_for_heightmap (Boolean): if a smooting filter should be added for the heightmap
                layers_to_load (list[int]): List of layers to load from the geotiff file
        '''
        self.n_px_width, self.n_px_height = map_size
        self.n_layers = n_layers

        # define extent of maps from one tif example
        self.xmin, self.ymin, self.xmax, self.ymax, self.width, self.height = \
            self.define_corners(init_filename)
        #print(self.xmin, self.ymin, self.xmax, self.ymax)
        self.pixel_size = self.width / self.n_px_width
        if plot_global:
            self.extent = (self.xmin, self.xmax, self.ymin, self.ymax)
            self.aspect_ratio = abs(self.xmax-self.xmin) / abs(self.ymax-self.ymin) * \
                                self.n_px_height / self.n_px_width
        else:
            self.extent = (0, self.width, 0, self.height)
            self.aspect_ratio = 'equal'

        # initalize a list of strings as a look-up which kind of data is saved in which layer of \
        # the array
        self.layer_names = []
        
        # initialize the maps array, where all map data is saves
        self.maps_array = np.zeros((self.n_px_width, self.n_px_height, self.n_layers))

        # append the first geotif to array
        self.extract_geotiff_and_add_to_array(init_filename, layer_description, add_filter_for_heightmap, layers_to_load)

        # Save clicked points as start or goal
        self.start = (0, 0)
        self.goal = (0, 0)


    def define_corners(self, init_filename):
        '''
        Creates an array with the first map layer and additionally saves the corners of the map \
        in globe-coordinates; should only be called once when initializing the object
            Parameters:
                init_finename (String): path to first geotif (can be any of the wanted)
            Returns:
                xmin (float)
                ymin (float)
                xmax (float)
                ymax (float)
                width (float)
                height (float)
        '''
        # open tif file
        dataset = rs.open(init_filename)

        # get width and height in m
        width = dataset.bounds.right - dataset.bounds.left
        height = dataset.bounds.top - dataset.bounds.bottom

        # Get reference lon & lat
        crs_dict = dataset.crs.to_dict()
        lonref = crs_dict['lon_0']
        latref = crs_dict['lat_0']
        radius = crs_dict['R']

        # Get extent of geotiff file
        lonmin = lonref - width / 2 * 180 / math.pi / radius
        lonmax = lonref + width / 2 * 180 / math.pi / radius
        latmin = latref - height / 2 * 180 / math.pi / radius
        latmax = latref + height / 2 * 180 / math.pi / radius

        return lonmin, latmin, lonmax, latmax, width, height


    def extract_geotiff_and_add_to_array(self, filename, description, add_filter_for_heightmap=False, layers_to_load=None, normalize_value=False):
        '''
        Extracts one or more geotiff layers from a file and adds them as one or more layers into the maps array.
        
        Parameters:
            filename (str): Path to the geotiff file.
            description (str): Description of the layer(s) being added.
            add_filter_for_heightmap (bool, optional): If True, applies a smoothing filter to heightmap layers. Default is False.
            layers_to_load (list of int, optional): Specific layers to load from the geotiff file. If None, all layers are loaded. Default is None.
            normalize_value (bool, optional): If True, normalizes the value before putting it into the array. Default is False.
        '''
        # load geotiff file
        dataset = rs.open(filename)

        # check how many layers are already in the array:
        n_layers_inscribed = len(self.layer_names)

        # extract the types from the geotif and save geotif data as an array
        for band in range(dataset.count):
            if layers_to_load and (band+1) not in layers_to_load:
                continue
            raster_band = dataset.read(band+1)
            self.layer_names.append(description)
            if add_filter_for_heightmap and ('eight' in description or 'DEM' in description or 'dem' in description):
                # Add kernel to average over heightmap and smooth out irregularities
                kernel = np.ones((9, 9), dtype=np.float32)
                kernel /= np.sum(kernel)
                smoothed_dem = convolve(np.array(raster_band), kernel, mode='nearest')
                if normalize_value:
                    smoothed_dem = np.interp(smoothed_dem, (np.min(smoothed_dem), np.max(smoothed_dem)), (0, 1))
                self.maps_array[:, :, len(self.layer_names)-1] = \
                    np.transpose(smoothed_dem)
            else:
                if normalize_value:
                    raster_band = np.interp(raster_band, (np.min(raster_band), np.max(raster_band)), (0, 1))
                self.maps_array[:, :, len(self.layer_names)-1] = \
                    np.transpose(np.array(raster_band))


    def load_npy_file_and_add_to_array(self, filename, description, normalize_value=False):
        '''
        Loads a npy file and saves it to the maps_array
            Parameters:
                filename (String): path to npy file
                description (String): will be added to the layer_names list and should describe \
                the new layer
                normalize_value (bool, optional): If True, normalizes the value before putting it into the array. Default is False.
        '''
        loaded_arr = np.load(filename)

        # check how many layers are already in the array:
        n_layers_inscribed = len(self.layer_names)
        # check if user tries to input too many layers
        if n_layers_inscribed+1 > self.n_layers:
            print("ERROR: The maps_array has "+str(self.n_layers)+" layers, where each of them is \
                  already filled.")
            sys.exit()
        if (loaded_arr.shape[0] != self.n_px_height) or (loaded_arr.shape[1] != self.n_px_width):
            print("ERROR: The raster size of the file "+filename+" ("+str(loaded_arr.shape[0])+","\
                  +str(loaded_arr.shape[1])+") does not fit the array size of the map ("\
                    +str(self.n_px_height)+","+str(self.n_px_width)+").")
            sys.exit()

        self.layer_names.append(description)
        if normalize_value:
            loaded_arr = np.interp(loaded_arr, (np.min(loaded_arr), np.max(loaded_arr)), (0, 1))
        self.maps_array[:, :, n_layers_inscribed] = np.transpose(loaded_arr)


    def add_empty_layer(self, empty_array, description):
        '''
        Adds an empty layer to the maps_array.
            Parameters:
                empty_array (ndarray): 2D array representing the empty layer to be added.
                description (String): Description of the new layer to be added to the layer_names list.
        '''
        n_layers_inscribed = len(self.layer_names)
        self.layer_names.append(description)
        self.maps_array[:, :, n_layers_inscribed] = np.transpose(empty_array)


    def get_slope_from_height(self, heightmap, get_min_slope=False):
        '''
        Calculates the slope map from a given heightmap.
        
        Parameters:
            heightmap (ndarray): A 2D array representing the heightmap.
            get_min_slope (bool): If True, returns the minimum slope; otherwise, returns the maximum slope.
        
        Returns:
            ndarray: A 2D array with the same size as the input heightmap, containing the slope values.
        '''
        slopemap = np.zeros(heightmap.shape)
        for i in range(heightmap.shape[0]):
            for j in range(heightmap.shape[1]):
                slopes = []
                for k, neighbor in enumerate(self.get_neighbors((i,j))):
                    if k<4:
                        slope = np.degrees(np.arctan((heightmap[neighbor]-heightmap[i,j])/(self.pixel_size)))
                    else:
                        slope = np.degrees(np.arctan((heightmap[neighbor]-heightmap[i,j])/(np.sqrt(2)*self.pixel_size)))
                    slopes.append(slope)
                if get_min_slope:
                    slopemap[i, j] = min(slopes, key=lambda x: abs(x))
                else:
                    slopemap[i, j] = max(slopes, key=lambda x: abs(x))
        return slopemap


    def get_neighbors(self, node):
        '''
        Retrieves all neighboring pixels of a given node.
        
        Parameters:
            node (tuple): A tuple (x, y) representing the coordinates of the node.
        
        Returns:
            list of tuple: A list of tuples where each tuple represents the coordinates of a neighboring pixel.
        '''
        x, y = node
        cols, rows = self.n_px_width, self.n_px_height
        neighbors = []

        # Add adjacent cells as neighbors
        if x > 0:
            neighbors.append((x - 1, y))
        if x < cols - 1:
            neighbors.append((x + 1, y))
        if y > 0:
            neighbors.append((x, y - 1))
        if y < rows - 1:
            neighbors.append((x, y + 1))

        # Add diagonal cells as neighbors
        if x > 0 and y > 0:
            neighbors.append((x - 1, y - 1))
        if x > 0 and y < rows - 1:
            neighbors.append((x - 1, y + 1))
        if x < cols - 1 and y > 0:
            neighbors.append((x + 1, y - 1))
        if x < cols - 1 and y < rows - 1:
            neighbors.append((x + 1, y + 1))

        return neighbors


    def define_image(self, filename):
        '''
        Define surface image
            Parameters:
                filename (String): Path to image file
        '''
        self.map_image = mpimg.imread(filename)


    def choose_start_and_goal_on_image(self):
        '''Displays the previously defined image and allows the user to select start and goal points.'''
        _, axs = plt.subplots()
        plt.imshow(self.map_image, extent=self.extent,
                aspect=self.aspect_ratio, cmap='gray')
        if self.extent[0]!=0:
            axs.set(xlabel='LON', ylabel='LAT')
            axs.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.3f}'))
            axs.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.3f}'))
        else:
            axs.set(xlabel='x(m)', ylabel='y(m)')

        # Connect the onclick function to the figure's button press event
        cid = plt.gcf().canvas.mpl_connect('button_press_event', self.onclick)
        plt.show()
        # Disconnect the event handler when done
        plt.gcf().canvas.mpl_disconnect(cid)

    def onclick(self, event):
        '''
        Handles mouse click events on the plot to set start and goal points.

        Parameters:
            event (MouseEvent): The mouse event containing information about the click.
        '''
        if event.inaxes:
            # Get the x and y coordinates of the click event
            x = event.xdata
            y = event.ydata
            if event.button == 1:
                self.start = (x, y)
                print(f"Start at x={x}, y={y}")
            elif event.button == 3:
                self.goal = (x, y)
                print(f"Goal at x={x}, y={y}")


    def plot_layers(self, layers, is_height_map, colormap='viridis'):
        '''
        Plots one or several layers of the map.

        Parameters:
            layers (list[int]): Indices of the layers to be plotted (from 0 to n_layers-1).
            is_height_map (list[bool]): A list of booleans indicating whether to activate height lines for each respective layer.
            colormap (str): The colormap to use for plotting the layers. Default is 'viridis'.
        '''
        for i in range(len(layers)):
            plot_map = self.maps_array[:,:,layers[i]]
            _, axs = plt.subplots()
            img = plt.imshow(plot_map.T, cmap=colormap,
                             extent=self.extent,
                             aspect = self.aspect_ratio)
            if is_height_map[i]:
                plt.contour(np.flip(plot_map.T, axis=0), levels=9, colors='#000000', linestyles='solid', \
                            linewidths=1, extent=self.extent)
            cbar = plt.colorbar(img)
            axs.set_xlabel('LON')
            axs.set_ylabel('LAT')
            #axs.set_xticklabels([f"{val:.{4}f}" for val in axs.get_xticks()])
            #axs.set_yticklabels([f"{val:.{4}f}" for val in axs.get_yticks()])
            cbar.ax.set_ylabel(self.layer_names[layers[i]])
        plt.show()


    def plot_four_layers_in_pixel(self, path):
        '''
        Plots four layers of the map in pixel coordinates and overlays a given path.

        Parameters:
            path (np.ndarray or list of tuples): The path to overlay on the map layers. Should be in pixel coordinates.
        '''
        plotting_array = self.maps_array

        # Plot layers of array
        cols = 4 #2 for rqt
        rows = 1 #3 for rqt
        fig, axs = plt.subplots(rows, cols)
        fig.tight_layout(h_pad=0.56, w_pad=0.2)
        fig.set_size_inches((20, 6))
        n = 0
        for i in range(rows):
            for j in range(cols):
                if n==2:
                    img = axs[j].imshow(plotting_array[:, :, n].T,
                                           extent=(0,self.n_px_width,0,self.n_px_height), aspect = 'equal',
                                           vmin=0.0, vmax=0.01)
                else:
                    img = axs[j].imshow(plotting_array[:, :, n].T,
                                           extent=(0,self.n_px_width,0,self.n_px_height), aspect = 'equal')
                if n==0:
                    axs[0].contour(np.flip(self.maps_array[:,:,0].T, axis=0), 
                                      levels=20, colors='#000000', linestyles='solid', linewidths=1,
                                      extent=(0,self.n_px_width,0,self.n_px_height))
                try:
                    axs[j].plot(path[:,0], path[:,1], 'r', linewidth=3)
                except:
                    pass 
                n=n+1

        # Add titles and axes
        axs[0].set_title('Height map', fontsize=26)
        axs[1].set_title('Slope', fontsize=26)
        axs[2].set_title('Traversability score', fontsize=26)
        axs[3].set_title('Scientific interest', fontsize=26)

        for ax in axs.flat:
            ax.set_xlabel('x [Pixel]', fontsize=26)
            ax.set_ylabel('y [Pixel]', fontsize=26)
            # ax.xaxis.set_major_locator(ticker.MaxNLocator(5))
            # ax.yaxis.set_major_locator(ticker.MaxNLocator(5))
            ax.tick_params(axis='both', which='major', labelsize=24)
        plt.show()


    def show_8plots_with_path(self, path, path_pixel, intermediate_goals=[]):
        '''
        Displays eight plots of the map layers with the given path and intermediate goals. Of these, four show the path 
        on the different layers of the satellite image while the other four show the course of the layer value along the path.

        Parameters:
            path (np.ndarray or list of tuples): The path to overlay on the map layers. Should be in global coordinates.
            path_pixel (np.ndarray or list of tuples): The path in pixel coordinates for plotting.
            intermediate_goals (np.ndarray or list of tuples, optional): Intermediate goals to overlay on the map layers. Defaults to an empty list.
        '''
        # Copy array to use in function
        plotting_array = self.maps_array

        # Plot layers of array
        cols = 2
        rows = 4
        fig, axs = plt.subplots(rows, cols)
        fig.tight_layout(h_pad=0.3, w_pad=0.2)
        cbar_label = ['[m]', '[deg]', '', '']
        plt.subplots_adjust(left=0.02, bottom=0.06, right=0.95, top=0.96, wspace=0.45, hspace=0.55)

        for i, ax in enumerate(axs.flat):
            if i%2==0:
                # Change colormap for traversability score
                if i==4:
                    img = ax.imshow(plotting_array[:, :, i//2].T, cmap='viridis',
                                    extent=self.extent, aspect=self.aspect_ratio,
                                    vmin=0.0, vmax=0.01)
                # Plot base for other layers
                else:
                    img = ax.imshow(plotting_array[:, :, i//2].T, cmap='viridis',
                                extent=self.extent, aspect=self.aspect_ratio)
                ax.set_xlabel("x [m]")
                ax.set_ylabel("y [m]")
                ax.tick_params(axis='both', which='major')
                cbar = plt.colorbar(img, ax=ax)
                cbar.ax.set_ylabel(cbar_label[i//2])
                # cbar.ax.tick_params()

                # Add contour for height map
                if i==0:
                    axs[0, 0].contour(np.flip(plotting_array[:,:,0].T, axis=0), levels=20, colors='#000000',
                                            linestyles='solid', linewidths=1, extent=self.extent)
                # Add path
                ax.plot(path[:,0], path[:,1], 'red', linewidth=3)
                if isinstance(intermediate_goals, list):
                    # If coordinates is a list of tuples
                    intermediate_goals = transform.tupellist_to_array(intermediate_goals)
                ax.plot(intermediate_goals[:,0], intermediate_goals[:,1], linestyle='none', marker='o', color='red', markersize=10)
            else:
                # Calculate and output length
                pairwise_distances = np.linalg.norm(path[1:] - path[:-1], axis=1)
                total_length = np.sum(pairwise_distances)

                # Prepare scaled x axis
                num_points = len(path)
                scaled_x = np.linspace(0, total_length, num_points)

                # Plot
                ax.plot(scaled_x, plotting_array[path_pixel[:,0], path_pixel[:,1], i//2], linewidth=3)
                ax.tick_params(axis='both', which='major')

        # Add titles and axes
        axs[0, 0].set_title('Height map')
        axs[0, 1].set_title('Height profile')
        axs[1, 0].set_title('Slope map')
        axs[1, 1].set_title('Slope profile')
        axs[2, 0].set_title('Traversability map')
        axs[2, 1].set_title('Traversability profile')
        axs[3, 0].set_title('Scientific interest map')
        axs[3, 1].set_title('Scientific interest profile')

        axs[0, 1].set_xlabel("Distance [m]")
        axs[0, 1].set_ylabel("Height [m]")
        axs[1, 1].set_xlabel("Distance [m]")
        axs[1, 1].set_ylabel("Slope [deg]")
        axs[2, 1].set_xlabel("Distance [m]")
        axs[2, 1].set_ylabel("Rock abundance")
        axs[3, 1].set_xlabel("Distance [m]")
        axs[3, 1].set_ylabel("Scientific value")

        plt.show()


    def show_image(self):
        '''Show previously defined image'''
        try:
            _, axs = plt.subplots()
            plt.imshow(self.map_image, extent=self.extent,
                       aspect=self.aspect_ratio, cmap='gray')
            if self.extent[0]!=0:
                axs.set(xlabel='LON', ylabel='LAT')
                axs.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.3f}'))
                axs.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.3f}'))
            else:
                axs.set(xlabel='x(m)', ylabel='y(m)')
            plt.show()
        except TypeError: 
            print("ERROR: This map does no have a surface image. Please define one using the\
                  function define_image(filename).")


    def show_image_with_path(self, path, plot_global=None, save_path=None):
        '''
        Show image of area plus calculated path
            Parameters:
                path (ndarray): 2D array of dimension (2,n) or rsp. length n (if tupellist)
                plot_global (bool): Defines if plot is showed in the local or global coordinate frame
                save_path (str): Path to save the figure. If None, the figure will be shown instead.
        '''
        if plot_global==None:
            extent = self.extent
            aspect_ratio = self.aspect_ratio
        elif plot_global:
            extent = (self.xmin, self.xmax, self.ymin, self.ymax)
            aspect_ratio = abs(self.xmax-self.xmin) / abs(self.ymax-self.ymin) * \
                                self.n_px_height / self.n_px_width
        else:
            extent = (0, self.width, 0, self.height)
            aspect_ratio = 'equal'

        if isinstance(path, np.ndarray):
            pass
        elif isinstance(path, list):
            path = transform.tupellist_to_array(path)
        else:
            raise TypeError("Invalid type for 'path'. Must be a NumPy array or a list of tuples.")

        try:
            _, axs = plt.subplots()
            plt.imshow(self.map_image, extent=extent, aspect = aspect_ratio, cmap='gray')
            if plot_global:
                axs.set_xlabel('LON [deg]')
                axs.set_ylabel('LAT [deg]')
                #axs.set_xticklabels([f"{val:.{4}f}" for val in axs.get_xticks()])
                #axs.set_yticklabels([f"{val:.{4}f}" for val in axs.get_yticks()])
            else:
                axs.set_xlabel('x [m]')
                axs.set_ylabel('y [m]')

            # Adjust tick frequency and rotation
            # axs.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
            plt.xticks(rotation=45)
            plt.yticks(rotation=45)

            # Add path
            plt.plot(path[:,0], path[:,1], 'r', linewidth=3)

            # Show or save pic
            if save_path:
                plt.tight_layout()
                plt.savefig(save_path)
                print(f'Figure saved to {save_path}')
            else:
                plt.show()
        except TypeError: 
            print("ERROR: This map does no have a surface image. Please define one using the \
                  function define_image(filename).")


    def get_maps_array(self):
        '''Returns the maps_array'''
        return self.maps_array
    

    def get_geo_xmin_ymin_xmax_ymax(self):
        '''Returns the four edges of the map in globe coordinates'''
        return self.xmin, self.ymin, self.xmax, self.ymax
    