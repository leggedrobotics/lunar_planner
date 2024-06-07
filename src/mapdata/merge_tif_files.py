import numpy as np
import rasterio as rs
from scipy.ndimage import convolve
import sys
import matplotlib.pyplot as plt


def extract_geotiff_science(filename):
    '''
    Extracts one or several geotiff layers from a file and returns the processed array.
        Parameters:
            filename (String): path to geotiff file
    '''
    # Load geotiff file
    dataset = rs.open(filename)

    # Initialise array
    maps_array = np.zeros((dataset.height, dataset.width, 1))

    # Add Clinopyroxene
    raster_band = dataset.read(1)
    science = np.interp(raster_band, (0, 50), (0, 1))

    # Add FeO
    raster_band = dataset.read(2)
    science = science + np.interp(raster_band, (0, 25), (0, 1))

    # Add TiO2
    raster_band = dataset.read(3)
    science = science + np.interp(raster_band, (2, 10), (0, 1))

    # Add Plagioclase
    raster_band = dataset.read(4)
    science = science + np.interp(raster_band, (50, 100), (0, 1))

    # Process the combined science value
    kernel = np.ones((4, 4), dtype=np.float32)
    kernel /= np.sum(kernel)
    science_smoothed = convolve(science, kernel, mode='nearest')
    science_scaled = np.interp(science_smoothed, (np.min(science_smoothed), np.max(science_smoothed)), (0, 1))
    science_scaled[science_scaled < 0.4] = 0
    maps_array[:, :, 0] = science_scaled#np.transpose(science_scaled)

    return maps_array


def plot_new_array(tif_filename, new_array):
    '''
    Creates an array with the first map layer and additionally saves the corners of the map \
    in globe-coordinates; should only be called once when initializing the object
        Parameters:
            tif_filename (String): path to geotif to get the lon-lat extent
            new_array (numpy array): array to be plotted
    '''
    # open tif file
    dataset = rs.open(tif_filename)

    # get width and height in m
    width = dataset.bounds.right - dataset.bounds.left
    height = dataset.bounds.top - dataset.bounds.bottom

    # Get reference lon & lat
    crs_dict = dataset.crs.to_dict()
    lonref = crs_dict['lon_0']
    latref = crs_dict['lat_0']
    radius = crs_dict['R']

    # Get extent of geotiff file
    lonmin = lonref - width / 2 * 180 / np.pi / radius
    lonmax = lonref + width / 2 * 180 / np.pi / radius
    latmin = latref - height / 2 * 180 / np.pi / radius
    latmax = latref + height / 2 * 180 / np.pi / radius

    # Calculate extent and aspect_ratio
    n_px_width, n_px_height, _ = new_array.shape
    extent = (lonmin, lonmax, latmin, latmax)
    aspect_ratio = abs(lonmax-lonmin) / abs(latmax-latmin) * \
                        n_px_width / n_px_height

    # Display the resulting array using matplotlib
    plt.imshow(new_array[:, :, 0], extent=extent, aspect=aspect_ratio)
    plt.colorbar()
    plt.title("Processed GeoTIFF Layer")
    plt.show()


def main(filename, output_path):
    # Call the function to process the GeoTIFF file
    maps_array = extract_geotiff_science(filename)

    # Save the resulting maps_array to a .npy file
    np.save(output_path, maps_array)
    print(f"Result saved to {output_path}")

    plot_new_array(filename, maps_array)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python merge_tif_files.py <input_geotiff> <output_npy>")
        sys.exit(1)

    input_geotiff = sys.argv[1]
    output_npy = sys.argv[2]
    main(input_geotiff, output_npy)