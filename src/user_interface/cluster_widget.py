from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT


class ClusterWidget(QWidget):
    def __init__(self):
        super().__init__()
        plt.switch_backend('Qt5Agg')

        # Create a Matplotlib Figure and Axes3D
        self.figure_3d = plt.figure()
        # self.figure_3d.tight_layout()
        self.axes_3d = self.figure_3d.add_subplot(111, projection='3d')

        self.axes_3d.set_title("Cost distribution")
        self.axes_3d.set_xlabel('E(s,r,d)')
        self.axes_3d.set_ylabel('R(s,r,d)')
        self.axes_3d.set_zlabel('I(s,r,d)')

        # Embed the Matplotlib plot into the widget
        self.mpl_canvas = FigureCanvasQTAgg(self.figure_3d)

        # Set up the layout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.mpl_canvas)

        # Initialize rotation angle
        self.angle = 0

        # Set up a timer to rotate the plot
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_plot)
        self.timer.start(100)  # Rotate every 100 ms


    def plot(self, x, y, z, color):
        # Clear the current 3D plot
        self.axes_3d.cla()
        self.scatter_plot = self.axes_3d.scatter(x, y, z, c=color, cmap='viridis', marker='o')
        self.mpl_canvas.draw()


    def plot_highlight(self, closest_point):
        # Plot highlighted graphs
        self.axes_3d.scatter(closest_point[0], closest_point[1], closest_point[2], c='red', marker='o', s=100, label='Closest Point')
        self.axes_3d.set_title("Cost distribution")
        self.axes_3d.set_xlabel('E(s,r,d)')
        self.axes_3d.set_ylabel('R(s,r,d)')
        self.axes_3d.set_zlabel('I(s,r,d)')
        self.mpl_canvas.draw()


    def rotate_plot(self):
        self.angle += 1
        self.axes_3d.view_init(azim=self.angle)
        self.mpl_canvas.draw()
