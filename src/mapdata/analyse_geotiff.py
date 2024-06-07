""" This file prepares the geotiff data."""
import math

### modules
#from osgeo import gdal, gdal_array, osr
import numpy as np
import matplotlib.pyplot as plt
import rasterio as rs
from rasterio.warp import transform, calculate_default_transform, Resampling
from pyproj import Proj, transform as pyproj_transform
from pyproj import CRS
import re


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