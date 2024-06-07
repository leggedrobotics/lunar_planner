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

""" This file prepares the geotiff data."""
import math
import numpy as np
import matplotlib.pyplot as plt
import rasterio as rs


def analyse_geotiff(path_to_tif):
    '''Quick script to analyse satellite data'''
    dataset = rs.open(path_to_tif)

    print(f"Number of layers: {dataset.count}")
    
    layer_names = []
    for i in range(1, dataset.count + 1):
        layer_names.append(dataset.descriptions[i-1] if dataset.descriptions[i-1] else f"Layer {i}")
    
    print("Layer names:", layer_names)
    
    print("Size in pixel: {} x {} (width x height)".format(dataset.width,
                                                                  dataset.height))
    width = dataset.bounds.right-dataset.bounds.left
    height = dataset.bounds.top-dataset.bounds.bottom
    print("Size in m: {} x {} (width x height)".format(width, height))

    # print("Projection: ", dataset.crs)

    # Get reference lon & lat
    crs_dict = dataset.crs.to_dict()
    lonref = crs_dict['lon_0']
    latref = crs_dict['lat_0']
    radius = crs_dict['R']

    # Get extent of geotiff file
    lonmin = lonref - width/2 * 180/math.pi /radius
    lonmax = lonref + width/2 * 180/math.pi /radius
    latmin = latref - height/2 * 180/math.pi /radius
    latmax = latref + height/2 * 180/math.pi /radius

    print("Extent Lon - min: {}, max: {} ".format(360+lonmin, 360+lonmax))
    print("Extent Lat - min: {}, max: {} ".format(latmin, latmax))

    for i in range(1, dataset.count + 1):
        band = dataset.read(i)
        min_val = np.nanmin(band)
        max_val = np.nanmax(band)
        
        plt.figure()
        plt.imshow(band, extent=(lonmin, lonmax, latmin, latmax))
        plt.colorbar(label=f"Min={min_val:.3f}, Max={max_val:.3f}")
        plt.title(layer_names[i-1])
        plt.xlabel("LON")
        plt.ylabel("LAT")
    plt.show()


def analyse_geotiff_pic(path_to_tif):
    '''Another quick script to analyse satellite data - this time for a RGB picture aka a 3-band tif file'''
    dataset = rs.open(path_to_tif)
    print("Size is {} x {} x {}".format(dataset.width,
                                        dataset.height,
                                        dataset.count))
    print("Extent Lon - left: {}, right: {} ".format(dataset.bounds.left,
                                           dataset.bounds.right))
    print("Extent Lat - bottom: {}, top: {} ".format(dataset.bounds.bottom,
                                           dataset.bounds.top))
    print("Projection: ", dataset.crs)

    red = dataset.read(1)
    green = dataset.read(2)
    blue = dataset.read(3)
    array = np.dstack((red, green, blue))

    plt.imshow(array)
    plt.show()


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python src/mapdata/analyse_geotiff.py path/to/file.tif")
        sys.exit(1)

    path_to_tif = sys.argv[1]
    analyse_geotiff(path_to_tif)