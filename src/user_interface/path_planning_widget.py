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
from python_qt_binding import loadUi, QtWidgets
from globalplanner import astar, transform, setup_file
from user_interface.map_widget import MapWidget
import os
import pandas as pd


class PathPlanningWidget(QtWidgets.QWidget):
    '''
    PathPlanningWidget is a QWidget that provides an interface for path planning.

    Attributes: 
        setup (Setup): Configuration and setup details for the widget.
        wp_pixel (list): Waypoints in pixel coordinates.
        wp_global (list): Waypoints in global coordinates.
        wp_sim (list): Waypoints in local coordinates.
        start (tuple): Starting point coordinates.
        goal (tuple): Goal point coordinates.
        mapwidget (MapWidget): Widget to display maps and paths.

    Methods:
        calc_and_plot_path: Calculate and plot the path on the widget.
        slider_value_change: Handle changes in slider values.
        change_to_next_map: Change to the next map layer.
        change_to_previous_map: Change to the previous map layer.
    '''
    PLOT_GLOBE = False

    def __init__(self):
        '''Initializes the PathPlanningWidget with the given setup configuration.'''
        super().__init__()

        # Create QWidget and load ui file
        ui_file = ui_file = 'src/user_interface/ui/PathPlanningWidget.ui'
        loadUi(ui_file, self)

        # Load the setup file and init path variables
        self.wp_pixel = None
        self.wp_global = None
        self.wp_sim = None
        self.start = None
        self.goal = None

        # Init widget functions for adjusting path
        self.plan_button.clicked.connect(self.calc_and_plot_path)
        self.alpha_slider.valueChanged.connect(self.slider_value_change)
        self.beta_slider.valueChanged.connect(self.slider_value_change)
        self.gamma_slider.valueChanged.connect(self.slider_value_change)
        self.map_up.clicked.connect(self.change_to_next_map)
        self.map_down.clicked.connect(self.change_to_previous_map)
        self.map_down.setEnabled(False)

        # Init widget functions to compare different paths
        self.four_wp_pixel = [[],[],[],[]]
        self.four_wp_global = [[],[],[],[]]
        self.four_wp_sim = [[],[],[],[]]
        self.four_goals = [[],[],[],[]]

        self.load_coordinates.clicked.connect(self.load_and_plot_coordinates)

        self.save_path0.clicked.connect(self.add_path0)
        self.save_path1.clicked.connect(self.add_path1)
        self.save_path2.clicked.connect(self.add_path2)
        self.save_path3.clicked.connect(self.add_path3)
        self.save_path0.setEnabled(False)
        self.save_path1.setEnabled(False)
        self.save_path2.setEnabled(False)
        self.save_path3.setEnabled(False)

        self.execute0.clicked.connect(self.execute_path0)
        self.execute1.clicked.connect(self.execute_path1)
        self.execute2.clicked.connect(self.execute_path2)
        self.execute3.clicked.connect(self.execute_path3)
        self.execute_buttons = [self.execute0, self.execute1, self.execute2, self.execute3]
        for button in self.execute_buttons:
            button.setEnabled(False)

        # Prepare table to compare paths
        self.tablewidget = QtWidgets.QTableWidget()
        self.tablewidget.setRowCount(5)
        self.tablewidget.setColumnCount(6)
        QtWidgets.QVBoxLayout(self.results_table).addWidget(self.tablewidget)

        headers = ['Spec', '', 'Path 1', 'Path 2', 'Path 3', 'Path 4']
        metrics = ['Relative energy', 'Crash risk', 'Scientific value', 'Distance covered']
        units = ['[k(Nm)^2]', '[%]', '[% of path]', '[km]']
        for col, header in enumerate(headers):
            self.tablewidget.setItem(0, col, QtWidgets.QTableWidgetItem(header))
        for row in range(1,5):
            self.tablewidget.setItem(row, 0, QtWidgets.QTableWidgetItem(metrics[row-1]))
            self.tablewidget.setItem(row, 1, QtWidgets.QTableWidgetItem(units[row-1]))
        self.tablewidget.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.tablewidget.resizeColumnsToContents()

        self.loadconfigbutton.clicked.connect(self.load_config)
        self.loadconfigbutton.setEnabled(False)
        self.openmapconfigbutton.clicked.connect(self.choose_map_file)
        self.openrobotconfigbutton.clicked.connect(self.choose_robot_file)
        self.stackedWidget.setCurrentIndex(1)

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
        # Disable button
        self.loadconfigbutton.setEnabled(False)
        QtWidgets.QApplication.processEvents()

        # Init map frame
        self.setup = setup_file.Setup(config_file=self.map_file,
                            user_func_file=self.robot_file,
                            plot_global=True)
        self.mapwidget = MapWidget(width=self.setup.maps.n_px_width, 
                                   height=self.setup.maps.n_px_height, 
                                   extent=self.setup.get_geo_xmin_ymin_xmax_ymax(),
                                   pixel_size=self.setup.maps.pixel_size,
                                   map_image=self.setup.maps.map_image, 
                                   maps_array=self.setup.maps.maps_array, 
                                   layer_names=self.setup.maps.layer_names,
                                   toolbar=True,
                                   plot_global=False)
        QtWidgets.QVBoxLayout(self.mapwidget_adjust).addWidget(self.mapwidget)
        self.mapwidget.canvas.mpl_connect('button_press_event', self.click_on_map_sets_new_goal)
        self.current_map = -1
        self.mapwidget.plot_layer_local(self.current_map)

        # Load map comparison frame
        self.mapwidget_4images = MapWidget(width=self.setup.maps.n_px_width, 
                                           height=self.setup.maps.n_px_height, 
                                           extent=self.setup.get_geo_xmin_ymin_xmax_ymax(),
                                           pixel_size=self.setup.maps.pixel_size,
                                           map_image=self.setup.maps.map_image, 
                                           maps_array=self.setup.maps.maps_array, 
                                           layer_names=self.setup.maps.layer_names,
                                           toolbar=True,
                                           plot_global=False)
        self.mapwidget_4images.prepare_four_sat_pics()
        QtWidgets.QVBoxLayout(self.img_paths).addWidget(self.mapwidget_4images)

        self.stackedWidget.setCurrentIndex(0)

        # Enable button
        self.loadconfigbutton.setEnabled(True)
        QtWidgets.QApplication.processEvents()


    def load_and_plot_coordinates(self):
        """Loads the start and goal coordinates from the UI elements and plots them on the map."""
        self.start = (self.startx.value(), self.starty.value())
        self.goal = (self.goalx.value(), self.goaly.value())
        self.plot_layer_with_start_goal_and_path()


    def plot_layer_with_start_goal_and_path(self):
        '''Plots the current selected layer and, if applicable, the start point, goal point, and path.'''
        self.mapwidget.plot_layer_local(self.current_map)
        self.mapwidget.plot_path_on_canvas(self.wp_sim,'red')
        if self.start:
            self.mapwidget.plot_point_on_canvas(self.start, 'ro')
        if self.goal:
            self.mapwidget.plot_point_on_canvas(self.goal, 'r*')


    def calc_and_plot_path(self):
        '''Plots the current selected layer and, if applicable, the start point, goal point, and path'''
        # Change button enable as user feedback
        self.plan_button.setEnabled(False)
        QtWidgets.QApplication.processEvents()

        # Load values for alpha, beta and gamma
        self.setup.ALPHA = self.alpha_slider.value()/20
        self.setup.BETA = self.beta_slider.value()/20
        self.setup.GAMMA = self.gamma_slider.value()/20

        # Plan path
        print("Calculation of global path started.")
        self.calc_path()
        print("Global path successfully calculated.")
        self.plot_layer_with_start_goal_and_path()

        # Now that path is calculated it can also be saved
        self.save_path0.setEnabled(True)
        self.save_path1.setEnabled(True)
        self.save_path2.setEnabled(True)
        self.save_path3.setEnabled(True)

        # Change button enable as user feedback
        self.plan_button.setEnabled(True)
        QtWidgets.QApplication.processEvents()


    def click_on_map_sets_new_goal(self, event):
        '''Plots the current selected layer and, if applicable, the start point, goal point, and path'''
        try:
            input_point = (event.xdata, event.ydata)
            [(index_x, index_y)] = transform.from_map_to_pixel([input_point], self.setup)
            if self.setup.maps.maps_array[index_x, index_y, 4] != 1:
                if event.button == 1:
                    self.start = input_point
                    self.plot_layer_with_start_goal_and_path()
                elif event.button == 3:
                    self.goal = input_point
                    self.plot_layer_with_start_goal_and_path()
            else:
                print("A point in a banned area was chosen. Please choose a new goal by klicking with the right mouse button on the map.")

        except Exception as e:
            print(f"A goal outside map chosen. Choose a next goal while klicking with the right mouse button on the map. Errormsg: {e}")
       

    def calc_path(self):
        '''Calculates the path from the current defined start and goal coordinates.'''
        self.pathshows_label.setText(f"")
        # Run A* algorithm
        if self.start and self.goal:
            [start_pixel, goal_pixel] = transform.from_map_to_pixel([self.start, self.goal], self.setup)
            self.setup.hmin = self.setup.ALPHA * self.setup.Emin + self.setup.BETA * self.setup.Rmin
            self.wp_pixel, self.stats = astar.astar(self.setup.map_size_in_pixel, start_pixel, goal_pixel, \
                                                    self.setup, allow_diagonal=True)
            if self.wp_pixel.any() == -1:
                print("No valid path found! Please check input parameters.")

            # Transform in different coordinate systems in save in one .dat file
            self.wp_global = transform.from_pixel_to_globe(self.wp_pixel, self.setup)
            self.wp_sim = transform.from_pixel_to_map(self.wp_pixel, self.setup)

            # Get total length
            path = np.array(self.wp_sim)
            pairwise_distances = np.linalg.norm(path[1:] - path[:-1], axis=1)
            total_length = np.sum(pairwise_distances)
            total_pixel = len(path)
          
            # # Get absolute values from cost components
            # results = np.sum(self.stats, axis=0)
            # energy = results[0] * self.setup.Emax
            # risk_list = np.array(self.stats)[:, 1]
            # crash = 1
            # for R_cost in risk_list:
            #     R_star = R_cost * self.setup.Rmax
            #     crash_single = 1 - (1 - R_star) ** (8 / self.setup.maps.pixel_size)
            #     crash = crash * (1 - crash_single)
            # risk = 1 - crash

            # Transform the cost components into physical values
            energy_costs = np.array(self.stats)[:, 0]
            risk_costs = np.array(self.stats)[:, 1]
            energy, risk = self.setup.get_physical_values_from_cost(energy_costs,
                                                                 risk_costs,
                                                                 self.setup.Emax,
                                                                 self.setup.Rmax,
                                                                 self.setup.maps.pixel_size)
            science = 1 - abs(sum(np.array(self.stats)[:, 2])) / len(path)
            self.comparative_values = [energy/1000, risk, science, total_length]

            # Save data in file in case more info is needed
            wp_all = np.concatenate((self.wp_global, self.wp_sim, self.wp_pixel), axis=1)
            column_names = np.array(['# Longitute', 'Latitude', 'x in sim', 'y in sim', \
                                    'Row in arr', 'Col in arr'])
            wp_header = '\t'.join(['{:<10}'.format(name) for name in column_names])
            np.savetxt('src/globalplanner/data/waypoints.dat', wp_all, \
                    header=wp_header, comments='', delimiter='\t', fmt='%-3f')
            
            # Save the statistics into one .dat file
            path_coordinates = transform.from_pixel_to_globe(self.wp_pixel, self.setup)
            stats_header = '\t\t'.join(('LON', 'LAT', 'E_P', 'R_P', 'I_P', 'B_P', 'g_func', 'h_func'))
            stats_with_wp = np.hstack((path_coordinates[1:], np.array(self.stats)))
            stats_with_wp = np.vstack((stats_with_wp, np.sum(stats_with_wp, axis=0, where=[0,0,1,1,1,1,1,1])))
            np.savetxt('src/globalplanner/data/stats.dat', stats_with_wp, \
                    header=stats_header, comments='', delimiter='\t', fmt='%-3f')
        elif self.start:
            print("Please choose a goal by clicking on the map (right mouse button).")
        elif self.goal:
            print("Please choose a start by clicking on the map (left mouse button).")


    def slider_value_change(self):
        '''Updates the label that shows the value of each slider'''
        self.value_alpha.setText(str(self.alpha_slider.value()/20))
        self.value_beta.setText(str(self.beta_slider.value()/20))
        self.value_gamma.setText(str(self.gamma_slider.value()/20))


    def change_to_next_map(self):
        '''
        Changes the background of the map by moving one or more map layers down.
        
        The following numbers define the maps: -1 = satellite picture; 0...n = layers of Maps object
        '''
        self.current_map = self.current_map + 1
        # Enable/ disable button function if on first/ last map
        if self.current_map == self.setup.maps.maps_array.shape[2]-1:
            self.map_up.setEnabled(False)
        elif self.current_map == 0:
            self.map_down.setEnabled(True)
        
        self.plot_layer_with_start_goal_and_path()


    def change_to_previous_map(self):
        '''
        Changes the background of the map by moving one or more map layers up.
        
        The following numbers define the maps: -1 = satellite picture; 0...n = layers of Maps object
        '''
        self.current_map = self.current_map - 1
        # Enable/ disable button function if on first/ last map
        if self.current_map == -1:
            self.map_down.setEnabled(False)
        elif self.current_map == self.setup.maps.maps_array.shape[2]-2:
            self.map_up.setEnabled(True)

        self.plot_layer_with_start_goal_and_path()


    def add_path0(self):
        '''Plots path 0 in the mapwidget cmp'''
        self.add_pathx(0)
        print("Saved as path 1.")

    def add_path1(self):
        '''Plots path 1 in the mapwidget cmp'''
        self.add_pathx(1)
        print("Saved as path 2.")

    def add_path2(self):
        '''Plots path 2 in the mapwidget cmp'''
        self.add_pathx(2)
        print("Saved as path 3.")

    def add_path3(self):
        '''Plots path 3 in the mapwidget cmp'''
        self.add_pathx(3)
        print("Saved as path 4.")

    def add_pathx(self, x):
        '''Adds selected path'''
        # Save calculated values to list
        self.four_wp_pixel[x] = self.wp_pixel
        self.four_wp_global[x] = self.wp_global
        self.four_wp_sim[x] = self.wp_sim
        self.four_goals[x] = self.goal
        # Calculate full distance of path
        path = np.array(self.wp_sim)
        pairwise_distances = np.linalg.norm(path[1:] - path[:-1], axis=1)
        total_length = np.sum(pairwise_distances)
        # Change satellite view
        self.mapwidget_4images.clear_one_of_four_sat_pics(x)
        self.mapwidget_4images.plot_path_on_one_of_four_sat_pic(self.wp_global, x)
        # Change table data
        self.tablewidget.setItem(1, x+2, QtWidgets.QTableWidgetItem(str(round(self.comparative_values[0],4))))
        self.tablewidget.setItem(2, x+2, QtWidgets.QTableWidgetItem(str(round(self.comparative_values[1],4))))
        self.tablewidget.setItem(3, x+2, QtWidgets.QTableWidgetItem(str(round(self.comparative_values[2],4))))
        self.tablewidget.setItem(4, x+2, QtWidgets.QTableWidgetItem(str(round(self.comparative_values[3]/1000,4))))
        self.tablewidget.resizeColumnsToContents()
        # Change state of execution button
        self.execute_buttons[x].setEnabled(True)

        self.pathshows_label.setText(f"Path {x+1} saved successfully.\n"
                                     "Please check 'Compare several paths'-tab.")


    def reset_path0(self):
        '''Deletes path 0'''
        self.reset_pathx(0)

    def reset_path1(self):
        '''Deletes path 1'''
        self.reset_pathx(1)

    def reset_path2(self):
        '''Deletes path 2'''
        self.reset_pathx(2)

    def reset_path3(self):
        '''Deletes path 3'''
        self.reset_pathx(3)

    def reset_pathx(self, x):
        '''Deletes chosen path'''
        # Clears both plots
        self.mapwidget_4images.clear_one_of_four_sat_pics(x)
        # Disenables execution button
        self.execute_buttons[x].setEnabled(False)


    def execute_path0(self):
        '''Chooses path 0 to execute'''
        self.execute_pathx(0)

    def execute_path1(self):
        '''Chooses path 1 to execute'''
        self.execute_pathx(1)

    def execute_path2(self):
        '''Chooses path 2 to execute'''
        self.execute_pathx(2)

    def execute_path3(self):
        '''Chooses path 3 to execute'''
        self.execute_pathx(3)

    def execute_pathx(self, x):
        '''Loads data from path again to be executed by the path following widget'''
        # Change button enable as user feedback
        self.execute_buttons[x].setEnabled(False)
        QtWidgets.QApplication.processEvents()

        # Load calculated values from list
        self.wp_pixel = self.four_wp_pixel[x]
        self.wp_global = self.four_wp_global[x]
        self.wp_sim = self.four_wp_sim[x]
        self.goal = self.four_goals[x]

        # Save coordinates to an Excel file
        waypoints = []
        for i, (global_coord, sim_coord) in enumerate(zip(self.wp_global, self.wp_sim)):
            waypoints.append([i+1, global_coord[0], global_coord[1], sim_coord[0], sim_coord[1]])

        # Create panda data frame
        df_waypoints = pd.DataFrame(waypoints, columns=['Waypoint Nr.', 'LON [deg]', 'LAT [deg]', 'x [m]', 'y [m]'])

        # Prepare weights and specs data
        weights_and_specs = {
            'Specs': ['alpha', 'beta', 'gamma', 'Relative energy [k(Nm)^2]', 'Crash risk [%]', 'Scientific value [% of path]', 'Distance covered [m]'],
            'Values': [self.setup.ALPHA, self.setup.BETA, self.setup.GAMMA] + self.comparative_values 
        }
        df_weights_and_specs = pd.DataFrame(weights_and_specs)

        # Open file dialog to choose save location
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        initial_dir = os.path.join(os.getcwd(), 'user_data/path_storage')
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 
                                                             "Save Path Coordinates", 
                                                             os.path.join(initial_dir, f"path_{x+1}_coordinates.xlsx"), 
                                                             "Excel Files (*.xlsx);;All Files (*)", 
                                                             options=options)
        if file_name:
            with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
                df_waypoints.to_excel(writer, sheet_name='Waypoints', index=False)
                df_weights_and_specs.to_excel(writer, sheet_name='Weights', index=False)
            print(f'Path {x+1} coordinates saved to {file_name}')

        # Save satellite image with global path as PDF
        pdf_file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 
                                                                 "Save Satellite Image with Path", 
                                                                 os.path.join(initial_dir, f"path_{x+1}_image.pdf"), 
                                                                 "PDF Files (*.pdf);;All Files (*)", 
                                                                 options=options)
        if pdf_file_name:
            self.setup.maps.show_image_with_path(self.wp_global, plot_global=True, save_path=pdf_file_name)

        # Add output that elements are correctly saved in pathsaved_label
        self.pathsaved_label.setText(f'Path {x+1} successfully exported.')
        self.pathsaved_label.setStyleSheet("color: green")

        # Change button enable as user feedback
        self.execute_buttons[x].setEnabled(True)
        QtWidgets.QApplication.processEvents()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    path_planning_widget = PathPlanningWidget()
    path_planning_widget.show()
    sys.exit(app.exec_())