import rasterio
from rasterio.plot import reshape_as_image
import numpy as np
from PIL import Image
import sys
import matplotlib.pyplot as plt

def create_grayscale_image_from_tif(tif_path, output_image_path, show_image=True, layer_keyword='wac'):
    with rasterio.open(tif_path) as src:
        # Find the index of the layer that contains the keyword
        layer_index = None
        for i in range(1, src.count + 1):
            if layer_keyword in src.descriptions[i-1].lower():
                layer_index = i
                break
        
        if layer_index is None:
            raise ValueError(f"No layer found with keyword '{layer_keyword}'")
        
        # Read the specific layer
        layer_data = src.read(layer_index)
        
        # Normalize the data to 0-255 for grayscale
        layer_data = (layer_data - layer_data.min()) / (layer_data.max() - layer_data.min()) * 255
        layer_data = layer_data.astype(np.uint8)
        
        # Convert to image and save
        image = Image.fromarray(layer_data, mode='L')
        image.save(output_image_path)

        if show_image:
            # Get extent from tif file
            width = src.bounds.right - src.bounds.left
            height = src.bounds.top - src.bounds.bottom
            crs_dict = src.crs.to_dict()
            lonref = crs_dict['lon_0']
            latref = crs_dict['lat_0']
            radius = crs_dict['R']

            # Get extent of geotiff file
            lonmin = lonref - width / 2 * 180 / np.pi / radius
            lonmax = lonref + width / 2 * 180 / np.pi / radius
            latmin = latref - height / 2 * 180 / np.pi / radius
            latmax = latref + height / 2 * 180 / np.pi / radius
            
            # Plot the image using matplotlib
            plt.imshow(layer_data, cmap='gray', extent=(lonmin, lonmax, latmin, latmax))
            plt.title("Grayscale Image from GeoTIFF Layer")
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")
            plt.show()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_grayscale_image.py <input_tif_path> <output_image_path>")
        sys.exit(1)

    input_tif_path = sys.argv[1]
    output_image_path = sys.argv[2]
    create_grayscale_image_from_tif(input_tif_path, output_image_path, show_image=True)
