'''This file includes several functions to create and edit binary maps.'''

import tkinter as tk
from PIL import ImageTk, Image
import cv2
import numpy as np
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import rasterio as rs
import os


plt.rcParams['font.size'] = 20

class Paint():
    """
    A class to paint binary images and save them.
    
    Attributes and Methods can be seen in the class diagram by running 'pyreverse -o png \
        path/to/src/globalplanner'
    """

    def __init__(self, map_size):
        '''
        Initialize object Paint
            Parameters:
                map_size (int-tupel): size of map in pixel
                path (String): path to data folder
        '''
        self.pixel_height, self.pixel_width = map_size
        self.root = None
        self.bg_image = None
        self.canvas = None
        self.scale = None
        self.output_path = None


    def draw_mask_and_save_to_file(self, input_path_pic, output_path, zoom):
        '''
        Allows user create a binary mask in the size of the map
            Parameters:
                name (String): Name which is used to save the mask to a file
                map_picture (String): path to satellite image
                zoom (int): Zooming factor to make the picture bigger on the screen for small files
        '''
        self.output_path = output_path
        self.root = tk.Tk()
        zoom = zoom
        self.bg_image = mpimg.imread(input_path_pic)
        self.bg_image = cv2.cvtColor(self.bg_image, cv2.COLOR_BGR2GRAY)

        # Resize the image to match the canvas size and make Tkinter compatible
        self.bg_image = cv2.resize(self.bg_image, (self.pixel_height*zoom, self.pixel_width*zoom))
        self.bg_image = ImageTk.PhotoImage(image=Image.fromarray((self.bg_image * 255).astype(np.uint8)))
        # Create canvas and add image
        self.canvas = tk.Canvas(self.root, width=self.pixel_height*zoom,
                                height=self.pixel_width*zoom)
        self.canvas.create_image(0, 0, image=self.bg_image, anchor=tk.NW)
        self.canvas.grid(row=0, column=0, columnspan=3)

        # Add several controls and buttons
        scale_label = tk.Label(self.root, text='Pencil Size')
        scale_label.grid(row=1, column=0)
        self.scale = tk.Scale(self.root, from_=zoom, to=20*zoom, orient=tk.HORIZONTAL, length = 500)
        self.scale.grid(row=2, column=0)
        save_button = tk.Button(self.root, text='Paint', command=self.__changecolorpaint)
        save_button.grid(row=2, column=1)
        save_button = tk.Button(self.root, text='Erase', command=self.__changecolorerase)
        save_button.grid(row=2, column=2)
        save_button = tk.Button(self.root, text='Reset', command=self.__erase_mask)
        save_button.grid(row=3, column=1)
        save_button = tk.Button(self.root, text='Save', command=self.__save_mask)
        save_button.grid(row=3, column=2)

        self.canvas.bind('<B1-Motion>', self.__paint)
        self.color = 'red'

        self.root.mainloop()

    def __paint(self, event):
        '''Function gets called when the user clicks/ "paints" on the Canvas'''
        x = event.x
        y = event.y
        size = self.scale.get()
        self.canvas.create_oval(x-size, y-size, x+size, y+size, fill=self.color, outline='')
    
    def __save_mask(self):
        '''Save the file as a numpy array'''
        # Save the file, open via PIL and convert to a numpy array
        self.canvas.postscript(file='temp_image_save.eps', colormode='color')
        image = Image.open('temp_image_save.eps')
        os.remove('temp_image_save.eps')

        # save_sizes = [(2048, 2048), (1024, 1024), (512, 512), (256, 256), (128, 128), (64, 64)]
        # sizes_string = ['2048', '1024', '512', '256', '128', '64']
        save_sizes = [(self.pixel_height, self.pixel_width)]
        sizes_string = ['']
        for i in range(len(save_sizes)):
            array = np.array(image.resize(save_sizes[i]))
            binary_mask = np.all(array == [255, 0, 0], axis=2).astype(np.uint8)
            np.save(self.output_path, binary_mask)

        print("The mask was successfully saved as " + self.output_path)

        # Cleanly close Tkinter
        self.bg_image = None
        self.canvas = None
        self.scale = None
        self.root.destroy()
    
    def __erase_mask(self):
        '''Resets the canvas'''
        self.canvas.create_image(0, 0, image=self.bg_image, anchor=tk.NW)

    def __changecolorpaint(self):
        '''Resets the canvas'''
        self.color = 'red'

    def __changecolorerase(self):
        '''Resets the canvas'''
        self.color = 'black'


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python paint_map.py <input_tif_path> <input_image_path> <output_npy_path>")
        sys.exit(1)

    input_tif_path = sys.argv[1]
    input_image_path = sys.argv[2]
    output_npy_path = sys.argv[3]

    # Load the tif file to get the size
    dataset = rs.open(input_tif_path)
    map_size = (dataset.width, dataset.height)

    painter = Paint(map_size)
    painter.draw_mask_and_save_to_file(input_image_path, output_npy_path, 7)
