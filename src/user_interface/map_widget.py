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

from matplotlib import ticker
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.figure import Figure
import numpy as np


class MapWidget(QtWidgets.QWidget):
    '''
        Child class of the Qt QWidget. Integrates a matplotlib plot of the satellite map into Qt.

        Attributes: 
            figure (matplotlib Figure): Holder for the plots
            axis (matplotlib Axis): To actually plot functions or images
            canvas (FigureCanvasQTAgg): Canvas to show Figure in Qt environment
            mainwindow (QtWidgets): Connection to main plugin to load relevant map setups

        Methods:
            plot_picture
            plot_layer
            add_path_to_four_layer_view_on_canvas   
    '''
    DEFAULT_CMAP = 'viridis'
    FONTSIZE = 11

    def __init__(self, width, height, extent, pixel_size, map_image, maps_array, \
                 layer_names, toolbar, plot_global):
        '''
        Init function for the class
            Parameters:
                width (int): Number of columns in maps array
                height (int): Number of rows in maps array
                extent (xmin (float), ymin (float), xmax (float), ymax (float)): Corners of map in
                    global coordinates
                pixel_size (float): Size of one pixel
                map_image (String): Path to satellite image from area
                maps_array (ndarray): 3D array with (x,y,layer)
                layer_names (String[]): List with names of layers as identifier
                toolbar (Boolean): Decides wether a toolbar should be added to the plot
                plot_global (Boolean): Sets flag if map is plotted in global coordinates (GPS) or 
                    local coordinates ((0,0) to (width,height)m)
        '''
        super().__init__()

        layout = QtWidgets.QVBoxLayout(self)

        self.figure = Figure()
        self.axis = self.figure.add_subplot(111)
        self.cbar = None
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)

        # self.figure.subplots_adjust(left=0.05, right=0.90, bottom=0.15, top=0.9)

        if toolbar:
            self.toolbar = NavigationToolbar(self.canvas, self)
            layout.addWidget(self.toolbar)

        self.xlabel_global = 'LON [deg]'
        self.ylabel_global = 'LAT [deg]'
        self.axis.set_title("Calculated paths")
        self.axis.set_xlabel(self.xlabel_global, fontsize=self.FONTSIZE)
        self.axis.set_ylabel(self.ylabel_global, fontsize=self.FONTSIZE)
        self.axis.tick_params(axis='both', which='major', labelsize=self.FONTSIZE)
        self.xmin, self.ymin, self.xmax, self.ymax = extent
        self.extent_global = (self.xmin, self.xmax, self.ymin, self.ymax)
        self.aspect_ratio_global = abs(self.xmax-self.xmin) / abs(self.ymax-self.ymin) * \
                                height / width

        self.xlabel_local = 'x [m]'
        self.ylabel_local = 'y [m]'
        self.axis.set_xlabel(self.xlabel_local, fontsize=self.FONTSIZE)
        self.axis.set_ylabel(self.ylabel_local, fontsize=self.FONTSIZE)
        self.axis.tick_params(axis='both', which='major', labelsize=self.FONTSIZE)
        self.extent_local = (0, width*pixel_size, 0, height*pixel_size)
        self.aspect_ratio_local = 'equal'

        self.axis.tick_params(axis='both', which='major', labelsize=self.FONTSIZE)
        
        self.map_img = map_image
        self.maps_array = maps_array
        self.layer_names = layer_names
        

    def plot_layer_global(self, layer):
        '''
        Plots one or several layers of the maps plus the calculated path
            Parameters:
                layers (int): which layer is to be plotted (from 0 to n_array-1); -1 stands for satellite image
                is_height_map (boolean): setting this to true for the respective layer activates \
                height lines
        '''
        # Clear previous content of figure including colorbar
        self.axis.cla()
        if self.cbar != None:
            self.cbar.remove()
            self.cbar = None
        
        if layer == -1:
            self.axis.imshow(self.map_img, extent=self.extent_global, aspect=self.aspect_ratio_global, cmap='gray', alpha=0.7)
        else:
            plot_map = self.maps_array[:,:,layer]
            self.img = self.axis.imshow(plot_map.T, cmap=self.DEFAULT_CMAP,\
                                extent=self.extent_global, aspect = self.aspect_ratio_global)
            if layer==0:
                self.axis.contour(np.flip(plot_map.T, axis=0), levels=20, colors='#333333', linestyles='solid', \
                            linewidths=1, extent=self.extent_global)
            self.cbar = self.figure.colorbar(self.img)
            self.cbar.ax.set_ylabel(self.layer_names[layer])

        self.axis.set_xlabel(self.xlabel_global, fontsize=self.FONTSIZE)
        self.axis.set_ylabel(self.ylabel_global, fontsize=self.FONTSIZE)
        # self.axis.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.4f}'))
        # self.axis.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.4f}'))
        self.axis.xaxis.set_major_locator(ticker.MaxNLocator(4))
        self.axis.yaxis.set_major_locator(ticker.MaxNLocator(5))
        self.axis.tick_params(axis='both', which='major', labelsize=self.FONTSIZE)

        # self.figure.tight_layout()
        self.canvas.draw()


    def plot_layer_local(self, layer):
        '''
        Plots one or several layers of the maps plus the calculated path
            Parameters:
                layers (int): which layer is to be plotted (from 0 to n_array-1); -1 stands for satellite image
                is_height_map (boolean): setting this to true for the respective layer activates \
                height lines
        '''
        # Clear previous content of figure including colorbar
        self.axis.cla()
        if self.cbar != None:
            self.cbar.remove()
            self.cbar = None
        
        if layer == -1:
            self.axis.imshow(self.map_img, extent=self.extent_local, aspect = self.aspect_ratio_local, cmap='gray', alpha=0.7)
        else:
            plot_map = self.maps_array[:,:,layer]
            self.img = self.axis.imshow(plot_map.T, cmap=self.DEFAULT_CMAP,\
                                extent=self.extent_local, aspect = self.aspect_ratio_local)
            if layer==0:
                self.axis.contour(np.flip(plot_map.T, axis=0), levels=20, colors='#333333', linestyles='solid', \
                            linewidths=1, extent=self.extent_local)
            self.cbar = self.figure.colorbar(self.img)
            self.cbar.ax.set_ylabel(self.layer_names[layer])

        self.axis.set(xlabel=self.xlabel_local, ylabel=self.ylabel_local)
        self.figure.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        self.canvas.draw()
        

    def plot_path_on_canvas(self, path, color, linestyle='solid'):
        '''
        Plots path on whichever picture was shown before
            Parameters:
                path (ndarray): 2D array with coordinates and size (n, 2)
                type (String): Defines style of line ('planned_path'/'tracked_path')
        '''
        if isinstance(path, list):
            path = np.array(path)
        if path is not None and len(path) > 0:
            self.axis.plot(path[:,0], path[:,1], color=color, linewidth=3, linestyle=linestyle)
        self.canvas.draw()


    def plot_point_on_canvas(self, coordinate, color='r*'):
        '''
        Plots one point on whichever picture was shown before
            Parameters:
                coordinate (float[]): list with len (2) defining the coordinates (x, y)
                type (String): Defines style of marker (e.g. 'r*' or 'ro')
        '''
        self.axis.plot(coordinate[0], coordinate[1], color)
        self.canvas.draw()


    def prepare_four_sat_pics(self):
        '''
        Clears the current figure and plots the satellite image four times for path comparison.

        This method is useful for visualizing and comparing different paths on the same satellite image.
        '''
        self.figure.clf()

        # Plot layers of array
        self.axis = self.figure.subplots(1, 4)
        self.figure.tight_layout()

        for i, ax in enumerate(self.axis.flat):
            ax.imshow(self.map_img, extent=self.extent_global, aspect=self.aspect_ratio_global, cmap='gray', alpha=0.7)
            ax.set_xlabel('LON [deg]', fontsize=self.FONTSIZE)
            ax.set_ylabel('LAT [deg]', fontsize=self.FONTSIZE)
            #ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.3f}'))
            #ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.3f}'))
            ax.set_title('Path segment '+str(i+1), fontsize = self.FONTSIZE)
            ax.tick_params(axis='both', which='major', labelsize=self.FONTSIZE)
                
        self.canvas.draw()


    def clear_one_of_four_sat_pics(self, i):
        '''
        Clears the canvas and puts satellite image up again.
        
        Parameters:
            i (int): Index of the subplot to clear and redraw (0 to 3).
        '''
        self.axis.flat[i].cla()
        self.axis.flat[i].imshow(self.map_img, extent=self.extent_global, aspect = self.aspect_ratio_global, cmap='gray', alpha=0.7)
        self.axis.flat[i].set(xlabel='LON [deg]', ylabel='LAT [deg]')
        #self.axis.flat[i].xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.3f}'))
        #self.axis.flat[i].yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.3f}'))
        self.axis.flat[i].set_title('Path segment '+str(i+1), fontsize = self.FONTSIZE)
        self.axis.flat[i].tick_params(axis='both', which='major', labelsize = self.FONTSIZE)
        self.canvas.draw()


    def plot_path_on_one_of_four_sat_pic(self, path, i):
        '''
        Plots a path on one of the four satellite images.
        
        Parameters:
            path (ndarray): A 2D array of shape (n, 2) containing the coordinates (x, y) of the path.
            i (int): Index of the subplot (0 to 3) on which the path is to be plotted.
        '''
        self.axis.flat[i].plot(path[:,0], path[:,1], 'r', linewidth=3)
        self.canvas.draw()