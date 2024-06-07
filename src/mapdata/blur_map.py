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

import numpy as np
import cv2
import matplotlib.pyplot as plt

class BlurMap:
    def __init__(self, path):
        self.path = path

    def blur_binary_mask(self, input_path, output_path, minimal_value, blur_size):
        '''
        Modifies binary mask and sets a gradient to the binary values
            Parameters:
                path (String): path to work folder
                name_image (String): name of the mask-data in the workfolder (data must be
                    .npy file, name must be without '.npy' ending)
                minimal_value (float): cuts of blurring at this value
                blur_size (float): defines area of blur (fitting examples (mapsize:sigma_kernel):
                (256,256):7, (762,1110):30)
                name_subtract (String): blur will naturally enhance the marked areas ->
                    this mask can be used to delete blur in certain areas 
        '''
        # Load np image
        binary_image = np.load(input_path)

        # Find the coordinates of 1s in the binary image
        rows, cols = binary_image.shape
        larger_rows = int(rows + 2 * blur_size)
        larger_cols = int(cols + 2 * blur_size)
        larger_array = np.zeros((larger_rows, larger_cols))
        start_x = (larger_rows - rows) // 2
        start_y = (larger_cols - cols) // 2
        larger_array[start_x:start_x + rows, start_y:start_y + cols] = binary_image

        coordinates = np.argwhere(larger_array == 1)
        washed_out_image_large = np.zeros((larger_rows, larger_cols), dtype=np.float32)
        
        kernel_size = int(2*blur_size+1)
        img=np.zeros((kernel_size,kernel_size))
        img[kernel_size//2,kernel_size//2]=1
        kernel = cv2.GaussianBlur(img, (kernel_size, kernel_size), blur_size/4)
        kernel = kernel/np.max(kernel)
        print(kernel[:, kernel.shape[0]//2+1])

        # Apply the gradient to the new image around each (x, y) coordinate
        for (x, y) in coordinates:
            x_min = x-blur_size
            x_max = x+blur_size+1
            y_min = y-blur_size
            y_max = y+blur_size+1

            washed_out_image_large[int(x_min):int(x_max), int(y_min):int(y_max)] = \
                np.maximum(washed_out_image_large[int(x_min):int(x_max), int(y_min):int(y_max)], kernel)
        washed_out_image = washed_out_image_large[start_x:start_x + rows, start_y:start_y + cols]
        #washed_out_image = washed_out_image/np.max(washed_out_image)

        # Add original mask on top of image
        washed_out_image[binary_image==1] = 1
        # Set a minimal value threshold
        washed_out_image[washed_out_image < minimal_value] = 0

        # Save to workfolder
        np.save(output_path, washed_out_image)
        print("Image saved as '"+output_path+"'.")

        # Show final image
        fig = plt.figure()
        plt.imshow(washed_out_image)
        plt.colorbar()
        plt.xlabel('x_pixel')
        plt.ylabel('y-pixel')

        plt.show()


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        print("Usage: python blur_map.py <input_path> <output_path> <blur_radius> <minimal_value>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    blur_radius = float(sys.argv[3])
    minimal_value = float(sys.argv[4])

    blur_map = BlurMap('')

    blur_map.blur_binary_mask(input_path, output_path, minimal_value, blur_radius)
