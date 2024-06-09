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

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from mpl_toolkits.mplot3d import Axes3D


class ClusterWidget(QWidget):
    FONTSIZE = 11

    def __init__(self):
        super().__init__()
        plt.switch_backend('Qt5Agg')

        # Create a Matplotlib Figure and Axes3D
        self.figure_3d = plt.figure()
        # self.figure_3d.tight_layout()
        self.axes_3d = self.figure_3d.add_subplot(111, projection='3d')

        self.axes_3d.set_title("Cost distribution", fontsize=self.FONTSIZE)
        self.axes_3d.set_xlabel('E(s,r,d)', fontsize=self.FONTSIZE, labelpad=self.FONTSIZE)
        self.axes_3d.set_ylabel('R(s,r,d)', fontsize=self.FONTSIZE, labelpad=self.FONTSIZE)
        self.axes_3d.set_zlabel('I(s,r,d)', fontsize=self.FONTSIZE, labelpad=self.FONTSIZE)
        self.axes_3d.tick_params(axis='both', which='major', labelsize=self.FONTSIZE)

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
        self.axes_3d.set_title("Cost distribution", fontsize=self.FONTSIZE)
        self.axes_3d.set_xlabel('E(s,r,d)', fontsize=self.FONTSIZE)
        self.axes_3d.set_ylabel('R(s,r,d)', fontsize=self.FONTSIZE)
        self.axes_3d.set_zlabel('I(s,r,d)', fontsize=self.FONTSIZE)
        self.axes_3d.tick_params(axis='both', which='major', labelsize=self.FONTSIZE)
        self.mpl_canvas.draw()


    def rotate_plot(self):
        self.angle += 1
        self.axes_3d.view_init(azim=self.angle)
        self.mpl_canvas.draw()
