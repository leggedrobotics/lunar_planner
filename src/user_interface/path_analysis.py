import sys
import os
from PyQt5 import QtWidgets, QtCore
from python_qt_binding import loadUi
from user_interface.map_widget import MapWidget
from user_interface.cluster_widget import ClusterWidget
from globalplanner import setup_file
import numpy as np
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
import pandas as pd
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import QSizePolicy
import yaml


class MyQtMainWindow(QtWidgets.QMainWindow):
    """
    MyQtMainWindow is the main window class for the application, inheriting from QMainWindow.

    Attributes:
        setup (Setup): Configuration setup for the map and user functions.
        mapwidget (MapWidget): Widget for displaying the map.
        clusterwidget (ClusterWidget): Widget for displaying cluster analysis.
        current_map (int): Index of the currently displayed map layer.
        pathplot (QWidget): Widget for displaying the path plot.

    Methods:
        change_to_next_map(): Changes the map to the next layer.
        change_to_previous_map(): Changes the map to the previous layer.
        define_path_folder(): Opens a dialog to define the path folder.
        show_path_analysis(): Displays the path analysis.
    """
    def __init__(self, ui_file):
        """
        Initializes the MyQtMainWindow class.

        Parameters:
            ui_file (str): Path to the .ui file used to load the UI layout.
        """
        super().__init__()

        # Load the UI file
        loadUi(ui_file, self)

        # Initialize cluster widget
        self.clusterwidget = ClusterWidget()
        QtWidgets.QVBoxLayout(self.analysisplot).addWidget(self.clusterwidget)
        # layout_clusterwidget = QtWidgets.QVBoxLayout(self.analysisplot)
        self.analysisplot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Prepare table
        self.analysistable.setRowCount(4)
        self.analysistable.setColumnCount(13)

        titles_tabel1 = ['','Weights','','','Relative energy','','Crash risk','','Scientific value','','Distance covered','# Paths in cluster','Custer var']
        titles_tabel2 = ['','alpha','beta','gamma','[k(Nm)^2]','cmp to base','%','cmp to base','% of path','cmp to base','km','','']
        
        for i, title in enumerate(titles_tabel1):
            self.analysistable.setItem(0, i, QtWidgets.QTableWidgetItem(title))
        for i, title in enumerate(titles_tabel2):
            self.analysistable.setItem(1, i, QtWidgets.QTableWidgetItem(title))
            self.analysistable.item(1, i).setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.analysistable.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.analysistable.resizeColumnsToContents()

        # Init other ui parts
        self.getpathfolder.clicked.connect(self.define_path_folder)
        self.recalculatebutton.clicked.connect(self.show_path_analysis)
        self.exportbutton.clicked.connect(self.export_path)

        # Disable buttons
        self.recalculatebutton.setEnabled(False)

        # Init some variables
        self.project_folder = ''
        self.paths_files = []
        self.stats_files = []
        self.current_paths = []
        self.colors = []


    def define_path_folder(self):
        """
        Opens a dialog for the user to select a project folder containing path and stats files.
        
        The selected folder must contain files ending with '_paths.csv' and '_stats.csv'.
        The number of '_paths.csv' and '_stats.csv' files must be equal and should follow the naming policy 
        'segmentX_paths.csv' and 'segmentX_stats.csv', where X are upcounting integers (1,2,...).
        """
        initial_directory = 'user_data/path_storage'
        self.selected_folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Project Folder", initial_directory)
        if self.selected_folder:
            paths_files = [file for file in os.listdir(self.selected_folder) if file.endswith("_paths.csv")]
            stats_files = [file for file in os.listdir(self.selected_folder) if file.endswith("_stats.csv")]
            yaml_file_path = os.path.join(self.selected_folder, "config_files.yaml")

            # Load config yaml file
            if os.path.exists(yaml_file_path):
                with open(yaml_file_path, 'r') as yaml_file:
                    config_data = yaml.safe_load(yaml_file)
            else:
                self.erroroutput.setStyleSheet("color: red;")
                self.erroroutput.setText("No 'config_files.yaml' found in the selected folder.")

            # Check that path and stats files are in Folder
            if not paths_files or not stats_files:
                self.erroroutput.setStyleSheet("color: red;")
                self.erroroutput.setText("Folder does not contain a file that ends with '_paths.csv' and '_stats.csv'.")
            elif len(paths_files)!=len(stats_files):
                self.erroroutput.setStyleSheet("color: red;")
                self.erroroutput.setText("The number of '_paths.csv' and '_stats.csv' files must be equal and should follow the naming policy 'segmentX_paths.csv' and 'segmentX_stats.csv', where X are upcounting integers (1,2,...).")
                self.erroroutput.setWordWrap(True)

            # Everything here so lets load map
            else:
                # Output infos
                self.erroroutput.setStyleSheet("color: black;")
                self.erroroutput.setText("Selected folder: "+self.selected_folder)

                self.project_folder = self.selected_folder+'/'
                self.paths_files = sorted(paths_files, key=self.extract_number)
                self.stats_files = sorted(stats_files, key=self.extract_number)

                entries = [f"Segment {i}" for i in range(1, len(self.paths_files) + 1)]
                self.pathsegmentchooser.addItems(entries)
                self.pathsegmentchooser.setEditable(True)

                self.recalculatebutton.setEnabled(True)

                # Load config and map information
                map_file = config_data.get('map_file', 'user_data/config_map/aristarchus_cp.yaml')
                robot_file = config_data.get('robot_file', 'user_data/config_robot/anymal.py')
                map_file = os.path.join(os.getcwd(), map_file)
                robot_file = os.path.join(os.getcwd(), robot_file)

                self.setup = setup_file.Setup(config_file=map_file,
                                            user_func_file=robot_file,
                                            plot_global=True)
                self.mapwidget = MapWidget(width=self.setup.maps.n_px_width,
                                        height=self.setup.maps.n_px_height,
                                        extent=self.setup.get_geo_xmin_ymin_xmax_ymax(),
                                        pixel_size=self.setup.maps.pixel_size,
                                        map_image=self.setup.maps.map_image,
                                        maps_array=self.setup.maps.maps_array,
                                        layer_names=self.setup.maps.layer_names,
                                        toolbar=True,
                                        plot_global=True)
                self.mapwidget.DEFAULT_CMAP = 'Greys'
                QtWidgets.QVBoxLayout(self.pathplot).addWidget(self.mapwidget)
                self.map_up.clicked.connect(self.change_to_next_map)
                self.map_down.clicked.connect(self.change_to_previous_map)
                self.map_down.setEnabled(False)
                self.current_map = -1
                self.mapwidget.plot_layer_global(self.current_map)
                self.pathplot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


    def extract_number(self, file_name):
        """
        Extracts the numeric part of a file name for sorting purposes.

        Parameters:
        file_name (str): The name of the file from which to extract the number.

        Returns:
        int: The extracted number from the file name.
        """
        return int(''.join(filter(str.isdigit, file_name)))


    def show_path_analysis(self):
        """
        Updates the plots based on the selected path segment and the number of clusters specified by the user.

        This function reads the number of clusters the user wants for the selected path segment and updates the plots accordingly.
        """
        self.current_segment = self.pathsegmentchooser.currentIndex()
        self.pathsaved_label.setText('')

        # Load stats from the file
        data = np.loadtxt(self.project_folder+self.stats_files[self.current_segment], skiprows=1)
        n_clusters = self.numberofclusters.value()

        # Add number of paths to combobox for user to choose path
        self.comboBox_pathchoice.clear()
        for i in range(n_clusters):
            self.comboBox_pathchoice.addItem(f'Path {i + 1}')

        # Adapt table
        self.analysistable.setRowCount(n_clusters+3)
        self.analysistable.setItem(2, 0, QtWidgets.QTableWidgetItem('Baseline'))
        for i in range(n_clusters):
            self.analysistable.setItem(i+3, 0, QtWidgets.QTableWidgetItem('Path '+str(i+1)))

        # Extract columns
        data_a = data[:, 1]
        data_b = data[:, 2]
        data_c = data[:, 3]
        data_E_P = data[:, 4]
        data_R_P = data[:, 5]
        data_I_P = data[:, 6]
        data_E_star = data[:, 7]
        data_C = data[:, 8]
        data_S = data[:, 9]
        path_length = data[:, 10]
        n_pixel = data[:, 11]

        # Calculate clusters
        kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=2**n_clusters).fit(np.column_stack((data_E_P, data_R_P, data_I_P)))
        labels = kmeans.labels_
        cluster_centers = kmeans.cluster_centers_
        self.clusterwidget.plot(data_E_P, data_R_P, data_I_P, color=labels)
        closest_paths = []
        all_points = data[:, 4:7]

        # Load path file
        max_pixel = int(np.max(n_pixel))
        df = pd.read_csv(self.project_folder+self.paths_files[self.current_segment], delimiter='\t', names=list(range(max_pixel+1)))
        num_rows = int(df.shape[0]/2)
        self.current_paths = []
        self.colors = []
        self.weights_of_paths = []
        self.specs_of_paths = []

        # Define path for comparison
        average_point_index = np.argmin(cdist(data[:,1:4], [[0.333333, 0.333333, 0.333333]]))

        # Load specs of baseline and add to table
        lon = df.loc[2*average_point_index]
        lat = df.loc[2*average_point_index+1]
        path_globe_baseline = np.array([(float(lon.iloc[i]), float(lat.iloc[i])) for i in range(1,lon.last_valid_index()+1)])
        self.current_paths.append(path_globe_baseline)
        self.colors.append('r')

        energy_base = data_E_star[average_point_index]/1000
        risk_base = data_C[average_point_index]
        science_base = data_S[average_point_index]

        self.analysistable.item(2,0).setBackground(QBrush(QColor(255, 0, 0, 80)))
        self.analysistable.setItem(2, 1, QtWidgets.QTableWidgetItem(str(round(data_a[average_point_index],4))))
        self.analysistable.setItem(2, 2, QtWidgets.QTableWidgetItem(str(round(data_b[average_point_index],4))))
        self.analysistable.setItem(2, 3, QtWidgets.QTableWidgetItem(str(round(data_c[average_point_index],4))))
        self.analysistable.setItem(2, 4, QtWidgets.QTableWidgetItem(str(round(energy_base,2))))
        self.analysistable.setItem(2, 6, QtWidgets.QTableWidgetItem(str(round(risk_base*100,2))))
        self.analysistable.setItem(2, 8, QtWidgets.QTableWidgetItem(str(round(science_base*100,2))))
        self.analysistable.setItem(2, 10, QtWidgets.QTableWidgetItem(str(round(path_length[average_point_index]/1000,3))))

        # Add weights for future reference
        self.weights_of_paths.append([data_a[average_point_index], data_b[average_point_index], data_c[average_point_index]])
        self.specs_of_paths.append([energy_base,risk_base,science_base])

        # Create data for comparison table
        for cluster_label, center in enumerate(cluster_centers):
            cluster_points = data[labels == cluster_label, 4:7]

            # Find the point closest to the centroid
            closest_point_index = np.argmin(cdist(all_points, [center]))
            closest_point = all_points[closest_point_index]
            closest_paths.append(closest_point_index)

            # Show cluster plot
            self.clusterwidget.plot_highlight(closest_point)

            # Calculate variance within the cluster
            cluster_variance = np.var(cluster_points, axis=0)

            # Plot path in mapwiget TOOOOODOOOOOO
            sc = self.clusterwidget.scatter_plot

            lon = df.loc[2*closest_point_index]
            lat = df.loc[2*closest_point_index+1]
            path_globe = np.array([(float(lon.iloc[i]), float(lat.iloc[i])) for i in range(1,lon.last_valid_index()+1)])
            path_globe_list = [tuple(row) for row in path_globe]
            # print('')
            # print("Path "+str(cluster_label+1)+" :",path_globe_list)
            color = sc.cmap(sc.norm(labels[closest_point_index]))
            self.current_paths.append(path_globe)
            self.colors.append(color)

            # Data for comparison table
            energy = data_E_star[closest_point_index]/1000
            risk = data_C[closest_point_index]
            science = data_S[closest_point_index]
            energysave = (energy-energy_base)/energy_base * 100
            if risk_base == 0:
                risksave = risk * 100
            else:
                risksave = (risk-risk_base)/risk_base * 100
            sciencegain = (science-science_base)/science_base * 100

            color = [int(i*255) for i in color]
            self.analysistable.item(cluster_label+3,0).setBackground(QBrush(QColor(*color[:3], 80)))
            self.analysistable.setItem(cluster_label+3, 1, QtWidgets.QTableWidgetItem(str(round(data_a[closest_point_index],4))))
            self.analysistable.setItem(cluster_label+3, 2, QtWidgets.QTableWidgetItem(str(round(data_b[closest_point_index],4))))
            self.analysistable.setItem(cluster_label+3, 3, QtWidgets.QTableWidgetItem(str(round(data_c[closest_point_index],4))))
            self.analysistable.setItem(cluster_label+3, 4, QtWidgets.QTableWidgetItem(str(round(energy,2))))
            self.analysistable.setItem(cluster_label+3, 5, QtWidgets.QTableWidgetItem(str(round(energysave,2))+'%'))
            self.analysistable.setItem(cluster_label+3, 6, QtWidgets.QTableWidgetItem(str(round(risk*100,2))))
            self.analysistable.setItem(cluster_label+3, 7, QtWidgets.QTableWidgetItem(str(round(risksave,2))+'%'))
            self.analysistable.setItem(cluster_label+3, 8, QtWidgets.QTableWidgetItem(str(round(science*100,2))))
            self.analysistable.setItem(cluster_label+3, 9, QtWidgets.QTableWidgetItem(str(round(sciencegain,2))+'%'))
            self.analysistable.setItem(cluster_label+3, 11, QtWidgets.QTableWidgetItem(str(len(cluster_points))))
            self.analysistable.setItem(cluster_label+3, 12, QtWidgets.QTableWidgetItem(str(round(np.average(cluster_variance),2))))
            self.analysistable.setItem(cluster_label+3, 10, QtWidgets.QTableWidgetItem(str(round(path_length[closest_point_index]/1000,3))))
            self.analysistable.resizeColumnsToContents()

            # Add weights for future reference
            self.weights_of_paths.append([data_a[closest_point_index], data_b[closest_point_index], data_c[closest_point_index]])
            self.specs_of_paths.append([energy,risk,science,path_length[closest_point_index]])

        # Plot all paths in map
        self.plot_layer_with_paths()


    def change_to_next_map(self):
        '''
        Changes the background of the map to the next map layer down.

        The following numbers define the maps:
        -1 = satellite picture
        0...n = layers of the Maps object
        '''
        # Save the last zoom state
        zoom = (self.mapwidget.axis.get_xlim(), self.mapwidget.axis.get_ylim())
        # Change map counter
        self.current_map = self.current_map + 1
        # Enable/ disable button function if on first/ last map\
        if self.current_map == self.setup.maps.maps_array.shape[2] - 1:
            self.map_up.setEnabled(False)
        elif self.current_map == 0:
            self.map_down.setEnabled(True)
        self.plot_layer_with_paths()
        # Set saved zoom
        self.mapwidget.axis.set_xlim(zoom[0])
        self.mapwidget.axis.set_ylim(zoom[1])
        self.mapwidget.canvas.draw()


    def change_to_previous_map(self):
        '''
        Changes the background of the map to the previous map layer up.

        This function decreases the current map layer index by one, updates the map display,
        and adjusts the enabled state of navigation buttons accordingly.
        '''
        # Save the last zoom state
        zoom = (self.mapwidget.axis.get_xlim(), self.mapwidget.axis.get_ylim())
        # Change map counter
        self.current_map = self.current_map - 1
        # Enable/ disable button function if on first/ last map
        if self.current_map == -1:
            self.map_down.setEnabled(False)
        elif self.current_map == self.setup.maps.maps_array.shape[2] - 2:
            self.map_up.setEnabled(True)
        self.plot_layer_with_paths()
        # Set saved zoom
        self.mapwidget.axis.set_xlim(zoom[0])
        self.mapwidget.axis.set_ylim(zoom[1])
        self.mapwidget.canvas.draw()


    def plot_layer_with_paths(self):
        '''
        Plots the current selected layer and paths.

        This function plots the current map layer specified by self.current_map.
        If there are paths to be plotted, it also plots them with predefined colors and linestyles.

        Parameters:
        None
        '''
        self.mapwidget.plot_layer_global(self.current_map)
        linestyles = [(0,(3,0)),(0,(3,1)),(0,(3,2)),(0,(2,2)),(0,(1,1)),
                      (0,(1,2)),(1,(1,2)),(0,(1,3)),(1,(1,3)),(2,(1,3)),
                      (0,(1,3))]

        for path, color, linestyle in zip(self.current_paths, self.colors, linestyles):
            self.mapwidget.plot_path_on_canvas(path, color, linestyle)
    

    def export_path(self, event):
        """
        Exports the current path's waypoints and weights to an Excel file and saves a satellite image with the path as a PDF.
        """
        self.exportbutton.setEnabled(False)
        QtWidgets.QApplication.processEvents()

        # Load calculated values from the current path
        chosen_path_index = self.comboBox_pathchoice.currentIndex()
        self.wp_global = self.current_paths[chosen_path_index+1] # first element is baseline

        # Save coordinates to an Excel file
        waypoints = []
        for i, global_coord in enumerate(self.wp_global):
            waypoints.append([i+1, global_coord[0], global_coord[1]])

        # Create panda data frame
        df_waypoints = pd.DataFrame(waypoints, columns=['Waypoint Nr.', 'LON [deg]', 'LAT [deg]'])

        # Prepare weights and specs data
        weights_and_specs = {
            'Specs': ['alpha', 'beta', 'gamma', 'Relative energy [k(Nm)^2]', 'Crash risk [%]', 'Scientific value [% of path]', 'Distance covered [m]'],
            'Values': self.weights_of_paths[chosen_path_index+1] + self.specs_of_paths[chosen_path_index+1] + [] # first element is baseline
        }
        df_weights_and_specs = pd.DataFrame(weights_and_specs)

        # Open file dialog to choose save location
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        initial_dir = self.selected_folder 
        # create identifier for current path
        identifier = f"segment{self.current_segment+1}_path{chosen_path_index+1}"
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 
                                                             "Save Path Coordinates", 
                                                             os.path.join(initial_dir, identifier+"_coordinates.xlsx"), 
                                                             "Excel Files (*.xlsx);;All Files (*)", 
                                                             options=options)
        if file_name:
            with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
                df_waypoints.to_excel(writer, sheet_name='Waypoints', index=False)
                df_weights_and_specs.to_excel(writer, sheet_name='Weights', index=False)
            print(f'Path coordinates saved to {file_name}')

        # Save satellite image with global path as PDF
        pdf_file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 
                                                                 "Save Satellite Image with Path", 
                                                                 os.path.join(initial_dir, identifier+"_image.pdf"), 
                                                                 "PDF Files (*.pdf);;All Files (*)", 
                                                                 options=options)
        if pdf_file_name:
            self.setup.maps.show_image_with_path(self.wp_global, plot_global=True, save_path=pdf_file_name)

        # Add output that elements are correctly saved in pathsaved_label 
        self.pathsaved_label.setText(f'Path {chosen_path_index+1} successfully exported.')
        self.pathsaved_label.setStyleSheet("color: green")

        # Change button enable as user feedback
        self.exportbutton.setEnabled(True)
        QtWidgets.QApplication.processEvents()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    # # Add image to application
    # image_path = "src/user_interface/ui/images/path_analysis.png"
    # app.setWindowIcon(QtGui.QIcon(image_path))

    my_main_window = MyQtMainWindow("src/user_interface/ui/PathAnalysis.ui")
    my_main_window.show()
    sys.exit(app.exec_())
