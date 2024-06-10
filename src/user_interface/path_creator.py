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

import sys
import numpy as np
import os
from python_qt_binding import loadUi
from PyQt5 import QtWidgets
from globalplanner import transform, astar, setup_file
from user_interface.map_widget import MapWidget
from itertools import product
import csv
import time
import yaml


class PathCreatorPlugin(QtWidgets.QWidget):
    '''
    PathCreatorPlugin is a QWidget-based plugin for creating and managing paths.

    Attributes:
        PLOT_GLOBAL (bool): Flag to determine if the map is plotted in global coordinates.
        canvas (FigureCanvasQTAgg): Canvas to display the map.
        clusterwidget (ClusterWidget): Widget for displaying cluster analysis.
        mapframe (MapWidget): Widget to display and interact with the map.
        setup (Setup): Configuration setup for the map and user functions.
        waypoints (list): List to store waypoints for the path.
    Methods:
        change_map_frame_to_global(event): Switches the map frame to global coordinates.
        change_map_frame_to_local(event): Switches the map frame to local coordinates.
        click_on_map_sets_new_goal(event): Sets a new goal when the map is clicked.
        load_path(): Loads a path from a file.
        delete_path(): Deletes the currently selected path.
        delete_last_point(): Deletes the last point from the current path.
        calculate_path(): Calculates a path based on the current waypoints.
    '''
    PLOT_GLOBAL = False

    def __init__(self, ui_file):
        '''
        Initializes the PathCreatorPlugin with the specified UI file.

        Parameters:
            ui_file (str): Path to the UI file to load for the plugin.
        '''
        super().__init__()
        loadUi(ui_file, self)
       
        # Connect buttons
        self.globalcoordbutton.clicked.connect(self.change_map_frame_to_global)
        self.localcoordbutton.clicked.connect(self.change_map_frame_to_local)
        self.loadpathbutton.clicked.connect(self.load_path)
        self.deletepathbutton.clicked.connect(self.delete_path)
        self.deletepointbutton.clicked.connect(self.delete_last_point)
        self.calculatebutton.clicked.connect(self.calculate_path)
        self.loadconfigbutton.clicked.connect(self.load_config)
        self.loadconfigbutton.setEnabled(False)
        self.openmapconfigbutton.clicked.connect(self.choose_map_file)
        self.openrobotconfigbutton.clicked.connect(self.choose_robot_file)
        self.calculatebutton.setEnabled(False)
        self.stackedWidget.setCurrentIndex(0)
        
        # Init variables
        self.waypoints = []
        self.map_file = None
        self.robot_file = None


    def choose_map_file(self, event):
        """
        Opens a file dialog to choose a .yaml file from the config_map directory.

        Parameters:
            event (QEvent): The event that triggers this method, typically a button press.
        """
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 
                                                             "Choose Map Config File", 
                                                             "user_data/config_map", 
                                                             "YAML Files (*.yaml);;All Files (*)", 
                                                             options=options)
        if file_name:
            self.map_file = file_name
            self.mapload_label.setText(f"Map Config File: {os.path.basename(file_name)}")
            if self.robot_file:
                self.loadconfigbutton.setEnabled(True)


    def choose_robot_file(self, event):
        """
        Opens a file dialog to choose a .py file from the config_robot directory and updates the robotload_label.

        Parameters:
            event (QEvent): The event that triggers this method, typically a button press.
        """
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 
                                                             "Choose Robot Config File", 
                                                             "user_data/config_robot",
                                                             "Python Files (*.py);;All Files (*)", 
                                                             options=options)
        if file_name:
            self.robot_file = file_name
            self.robotload_label.setText(f"Robot Config File: {os.path.basename(file_name)}")
            if self.map_file:
                self.loadconfigbutton.setEnabled(True)


    def load_config(self, event):
        """
        Loads the configuration for the map and robot, initializes the map frame, and sets up the UI.

        Parameters:
            event (QEvent): The event that triggers this method, typically a button press.
        """
        # Init map frame
        self.setup = setup_file.Setup(config_file=self.map_file,
                            user_func_file=self.robot_file,
                            plot_global=True)
        self.mapframe = MapWidget(width=self.setup.maps.n_px_width, 
                                   height=self.setup.maps.n_px_height, 
                                   extent=self.setup.get_geo_xmin_ymin_xmax_ymax(),
                                   pixel_size=self.setup.maps.pixel_size,
                                   map_image=self.setup.maps.map_image, 
                                   maps_array=self.setup.maps.maps_array, 
                                   layer_names=self.setup.maps.layer_names,
                                   toolbar=True,
                                   plot_global=self.PLOT_GLOBAL)
        QtWidgets.QVBoxLayout(self.mapwidget).addWidget(self.mapframe)
        self.mapframe.canvas.mpl_connect('button_press_event', self.click_on_map_sets_new_goal)
        self.mapframe.plot_layer_local(-1)

        self.stackedWidget.setCurrentIndex(1)


    def change_map_frame_to_global(self, event):
        '''
        Switches the map frame to global coordinates.

        This method changes the map frame to display global coordinates (GPS). 
        If the map is currently in local coordinates, it will transform the waypoints 
        to global coordinates and replot them on the map.

        Parameters:
            event (QEvent): The event that triggers this method, typically a button press.
        '''
        if not self.PLOT_GLOBAL:
            self.PLOT_GLOBAL = True
            self.mapframe.plot_layer_global(-1)
            if len(self.waypoints)>0:
                self.waypoints = transform.from_map_to_globe(self.waypoints, self.setup)
            self.mapframe.plot_path_on_canvas(self.waypoints, 'red')
            for point in self.waypoints:
                self.mapframe.plot_point_on_canvas(point, 'ro')


    def change_map_frame_to_local(self, event):
        """
        Switches the map frame to local coordinates.

        This method changes the map frame to display local coordinates. 
        If the map is currently in global coordinates, it will transform the waypoints 
        to local coordinates and replot them on the map.

        Parameters:
            event (QEvent): The event that triggers this method, typically a button press.
        """
        if self.PLOT_GLOBAL:
            self.PLOT_GLOBAL = False
            self.mapframe.plot_layer_local(-1)
            if len(self.waypoints)>0:
                self.waypoints = transform.from_globe_to_map(self.waypoints, self.setup)
            self.mapframe.plot_path_on_canvas(self.waypoints, 'red')
            for point in self.waypoints:
                self.mapframe.plot_point_on_canvas(point, 'ro')

    
    def load_path(self, event):
        """
        Loads a path from the input text field and plots it on the map.

        This method reads the path coordinates from the input text field, 
        parses them, and plots the path on the map. If the path is valid, 
        it enables the calculate button.

        Parameters:
            event (QEvent): The event that triggers this method, typically a button press.
        """
        input_str = self.pathinput.text()
        if len(input_str)>0:
            pairs = input_str.replace('(', '').replace(')', '').split(',')
            self.delete_path(0)

            try:
                self.waypoints = [(float(pairs[i]), float(pairs[i + 1])) for i in range(0, len(pairs), 2)]
                if len(self.waypoints)>1:
                    # Show path
                    self.mapframe.plot_path_on_canvas(self.waypoints, 'red')
                    for point in self.waypoints:
                        self.mapframe.plot_point_on_canvas(point, 'ro')
                    self.calculatebutton.setEnabled(True)
            except:
                pass


    def delete_path(self, event):
        """
        Deletes all waypoints from the current path.

        This method clears the list of waypoints, effectively deleting the current path 
        from the map. It also triggers a replot of the map to reflect the changes.

        Parameters:
            event (QEvent): The event that triggers this method, typically a button press.
        """
        self.waypoints = []
        self.replot_map()
        self.calculatebutton.setEnabled(False)


    def delete_last_point(self, event):
        """
        Deletes the last waypoint from the current path.

        This method removes the last waypoint from the list of waypoints, 
        effectively updating the current path on the map.

        Parameters:
            event (QEvent): The event that triggers this method, typically a button press.
        """
        self.waypoints.pop()
        self.replot_map()


    def replot_map(self):
        """
        Replots the map with the current waypoints.

        This method clears the current map and replots it based on the global or local
        plotting mode. It also plots the current waypoints on the map.

        Parameters:
            None
        """
        if self.PLOT_GLOBAL:
            self.mapframe.plot_layer_global(-1)
        else:
            self.mapframe.plot_layer_local(-1)
        if len(self.waypoints)>0:
            self.mapframe.plot_path_on_canvas(self.waypoints, 'red')
            for point in self.waypoints:
                self.mapframe.plot_point_on_canvas(point, 'ro')


    def click_on_map_sets_new_goal(self, event):
        """
        Handles the event of clicking on the map to set a new goal.

        This method captures the coordinates of the click event and, if the left mouse button
        is used, adds the new point to the list of waypoints. It also updates the map by plotting
        the new point and, if applicable, the path from the previous waypoint to the new one.

        Parameters:
            event (QEvent): The event that triggers this method, typically a mouse click.
        """
        input_point = (event.xdata, event.ydata)
        if event.button == 1:
            if input_point[0] is not None and input_point[1] is not None:
                self.waypoints.append(input_point)
                self.mapframe.plot_point_on_canvas(input_point, 'ro')
                if len(self.waypoints)>=2:
                    self.mapframe.plot_path_on_canvas([self.waypoints[len(self.waypoints)-2], input_point], 'red')
                    self.calculatebutton.setEnabled(True)


    def calculate_path(self, event):
        """
        Calculates and stores the path based on the current waypoints.

        This method creates a folder for storing the calculated paths, checks for folder name conflicts,
        and if no conflicts are found, it proceeds to calculate the paths between waypoints. The progress
        is displayed on a progress bar, and the paths are saved in the specified folder.

        Parameters:
            event (QEvent): The event that triggers this method, typically a button press.
        """
        # Create folder for storage
        string_input = self.outputfolder.text()
        project_name = string_input.replace(" ", "")
        output_folder = 'user_data/path_storage/'+project_name
        print("The chosen waypoints are: ", self.waypoints)
        if os.path.exists(output_folder):
            self.erroroutput.setStyleSheet("color: red;")
            self.erroroutput.setText("Foldername already exists in path '/user_data/path_storage'. Please choose different name.")
            self.erroroutput.setWordWrap(True)
        else:
            # Show screen with progress bar
            self.stackedWidget.setCurrentIndex(2)
            QtWidgets.QApplication.processEvents()

            # Create paths 
            os.makedirs(output_folder)
            if not self.PLOT_GLOBAL:
                self.waypoints = transform.from_map_to_globe(self.waypoints, self.setup)

            num_segments = len(self.waypoints)-1
            segment = 0

            start_time = time.time()
            for coord1, coord2 in zip(self.waypoints[:-1], self.waypoints[1:]):
                segment = segment+1
                self.create_paths(10, coord1, coord2, output_folder, segment, num_segments) # TODO change scale to 10
            end_time = time.time()
            elapsed_time = end_time - start_time
            print('The calculation of all paths took: '+str(elapsed_time/60)+' Minutes.')

            self.successmsg.setText("Paths successfully calculated and saved in folder '"+output_folder+"'. You can now close this window.")
            self.successmsg.setWordWrap(True)


    def create_paths(self, scale, start_global, goal_global, folder_name, segmentindex, num_segments):
        """
        Generates multiple paths between the start and goal points using different optimization weights.

        This function creates a distribution of the three path optimization weights (a, b, and c) and 
        calculates paths for each combination. The progress is updated on a progress bar.

        Parameters:
            scale (int): The number of divisions for the optimization weights.
            start_global (tuple): The starting point in global coordinates.
            goal_global (tuple): The goal point in global coordinates.
            folder_name (str): The name of the folder to save the path data.
            segmentindex (int): The index of the current path segment.
            num_segments (int): The total number of path segments.
        """
        # Read scale as current entry of scale_box
        scale_entries = [10,9,8,7,6,5]
        scale = scale_entries[self.scale_box.currentIndex()]

        # Iterate over different combinations of a, b, and c
        a_values = np.logspace(0, 1, scale)
        b_values = np.logspace(0, 1, scale)
        c_values = np.logspace(0, 1, scale)
        n = len(list(product(a_values, b_values, c_values)))

        # print(scale, n)
        
        # Define start and goal
        [start_sim, goal_sim] = transform.from_globe_to_map([start_global, goal_global], self.setup)
        [start_pixel, goal_pixel] = transform.from_map_to_pixel([start_sim, goal_sim], self.setup)
        
        done_weights = []
        i = 0
        path_found = False

        # Save which config files were used to create paths
        config_data = {
            'map_file': self.map_file.split('lunar_planner/', 1)[-1],
            'robot_file': self.robot_file.split('lunar_planner/', 1)[-1]
        }
        config_file_path = os.path.join(folder_name, 'config_files.yaml')
        with open(config_file_path, 'w') as config_file:
            yaml.dump(config_data, config_file)

        for a, b, c in product(a_values, b_values, c_values):
            if a + b + c != 0:
                # Status
                i += 1
                self.progressBar.setValue(int(((segmentindex - 1) / num_segments + i / (n * num_segments)) * 100))
                QtWidgets.QApplication.processEvents()
                [a, b, c] = [a, b, c] / (a + b + c)

                if [a, b, c] not in done_weights:
                    done_weights.append([a, b, c])
                    self.setup.ALPHA = a
                    self.setup.BETA = b
                    self.setup.GAMMA = c
                    self.setup.hmin = a * self.setup.Emin + b * self.setup.Rmin

                    # Run A* algorithm
                    path, stats = astar.astar(self.setup.map_size_in_pixel, start_pixel, goal_pixel, self.setup, allow_diagonal=True)
                    if path.any() == -1:
                        continue
                    path_found = True
                    path_globe = transform.from_pixel_to_globe(path, self.setup)
                    path_sim = transform.from_pixel_to_map(path, self.setup)

                    # Get total length
                    path = np.array(path_sim)
                    pairwise_distances = np.linalg.norm(path[1:] - path[:-1], axis=1)
                    total_length = np.sum(pairwise_distances)
                    total_pixel = len(path)

                    # Prepare file to save stats
                    if i == 1:
                        with open(folder_name + '/segment' + str(segmentindex) + '_stats.csv', 'w', newline='') as file:
                            stats_header = ['Path no.', 'a', 'b', 'c', 'E_P', 'R_P', 'I_P', 'E', 'crash', 'S', 'Length', 'No. pixel']
                            writer = csv.writer(file, delimiter='\t')
                            writer.writerow(stats_header)

                    # Transform the cost components into physical values
                    energy_costs = np.array(stats)[:, 0]
                    risk_costs = np.array(stats)[:, 1]
                    energy, risk = self.setup.get_physical_values_from_cost(energy_costs,
                                                        risk_costs,
                                                        self.setup.Emax,
                                                        self.setup.Rmax,
                                                        self.setup.maps.pixel_size)

                    science = 1 - abs(sum(np.array(stats)[:, 2])) / len(path)
                    comparative_values = [energy, risk, science]
                    stats_sum = np.sum(stats, axis=0, where=[1, 1, 1, 1, 1, 1])

                    # Save stats
                    with open(folder_name + '/segment' + str(segmentindex) + '_stats.csv', 'a', newline='') as file:
                        stats_with_weights = np.hstack([i, a, b, c, stats_sum[0:3], comparative_values, total_length, total_pixel])
                        writer = csv.writer(file, delimiter='\t')
                        writer.writerow(stats_with_weights)

                    # Save path coordinates
                    with open(folder_name + '/segment' + str(segmentindex) + '_paths.csv', 'a', newline='') as csvfile:
                        writer = csv.writer(csvfile, delimiter='\t')
                        for coord_type in ["LON", "LAT"]:
                            header = [f'Path {i} {coord_type}']
                            coordinates = [str(coord[0 if coord_type == "LON" else 1]) for coord in path_globe]
                            writer.writerow(header + coordinates)

        if not path_found:
            self.successmsg.setStyleSheet("color: red;")
            self.successmsg.setText("No path could be found, please check input parameters.")
            self.successmsg.setWordWrap(True)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    my_widget = PathCreatorPlugin("src/user_interface/ui/PathCreator.ui")
    my_widget.show()
    sys.exit(app.exec_())

