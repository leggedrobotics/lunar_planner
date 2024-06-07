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

'''A file that includes several transformation functions'''

import numpy as np
import math


def from_pixel_to_globe(coordinates, setup):
    '''
    Transforms pixel coordinates into global coordinates using the provided setup.
        Parameters:
            coordinates (ndarray or list of tuples): Input coordinates in pixel format. Must be a NumPy array of shape (n, 2) or a list of tuples of length n.
            setup (Setup): Setup object containing map data and map size in pixels.
        Returns:
            transformed_coordinates (ndarray): 2D array of transformed coordinates with shape (n, 2).
    '''
    # Extract x and y coordinates from the input array or the tupel ist
    coordinates_sim = from_pixel_to_map(coordinates, setup)
    return from_map_to_globe(coordinates_sim, setup)


def from_pixel_to_map(coordinates, setup):
    '''
    Transforms pixel coordinates into map coordinates using the provided setup.
        Parameters:
            coordinates (ndarray or list of tuples): Input coordinates in pixel format. Must be a NumPy array of shape (n, 2) or a list of tuples of length n.
            setup (Setup): Setup object containing map data and map size in pixels.
        Returns:
            transformed_coordinates (ndarray): 2D array of transformed coordinates with shape (n, 2).
    '''
    # Extract x and y coordinates from the input array or the tuple list
    if isinstance(coordinates, np.ndarray):
        # If coordinates is a NumPy array
        output_type = np.ndarray
    elif isinstance(coordinates, list):
        # If coordinates is a list of tuples
        coordinates = tupellist_to_array(coordinates)
        output_type = list
    else:
        raise TypeError("Invalid type for 'coordinates'. Must be a NumPy array or a list of tuples.")
    
    row = coordinates[:, 0]
    col = setup.maps.n_px_height-1 - coordinates[:, 1]
    
    transformed_y = abs(setup.maps.pixel_size) * (col + 0.5)
    transformed_x = abs(setup.maps.pixel_size) * (row + 0.5)

    # Return the transformed coordinates based on the input type
    if output_type == np.ndarray:
        return np.column_stack((transformed_x, transformed_y))
    if output_type == list:
        return [tuple(row) for row in np.column_stack((transformed_x, transformed_y))]


def from_map_to_pixel(coordinates, setup):
    '''
    Transforms map coordinates into pixel coordinates using the provided setup.
        Parameters:
            coordinates (ndarray or list of tuples): Input coordinates in map format. Must be a NumPy array of shape (n, 2) or a list of tuples of length n.
            setup (Setup): Setup object containing map data and map size in pixels.
        Returns:
            transformed_coordinates (ndarray): 2D array of transformed coordinates with shape (n, 2).
    '''
    # Extract x and y coordinates from the input array or the tuple list
    if isinstance(coordinates, np.ndarray):
        # If coordinates is a NumPy array
        output_type = np.ndarray
    elif isinstance(coordinates, list):
        # If coordinates is a list of tuples
        coordinates = tupellist_to_array(coordinates)
        output_type = list
    else:
        raise TypeError("Invalid type for 'coordinates'. Must be a NumPy array or a list of tuples.")
    
    x = coordinates[:, 0]
    y = coordinates[:, 1]
    
    transformed_y = (setup.maps.n_px_height-1 - y//abs(setup.maps.pixel_size)).astype(int)
    transformed_x = (x//abs(setup.maps.pixel_size)).astype(int)

    # Return the transformed coordinates based on the input type
    if output_type == np.ndarray:
        return np.column_stack((transformed_x, transformed_y))
    if output_type == list:
        return [tuple(row) for row in np.column_stack((transformed_x, transformed_y))]


def tupellist_to_array(tuples_list):
    '''
    Converts a list of tuples into a NumPy array of shape (n, 2).
        Parameters:
            tuples_list (list of tuples): List of tuples where each tuple contains two integers.
        Returns:
            ndarray: 2D NumPy array of shape (n, 2).
    '''
    return np.array([list(t) for t in tuples_list])


def from_globe_to_map(coordinates, setup):
    '''
    Transforms coordinates from global (longitude, latitude) to simulation map coordinates.
        Parameters:
            coordinates (ndarray or list of tuples): Input coordinates in global format. Must be a NumPy array of shape (n, 2) or a list of tuples of length n.
            setup (Setup): Setup object containing map data and map size in pixels.
        Returns:
            transformed_coordinates (ndarray or list of tuples): Transformed coordinates in simulation map format.
    '''
    if isinstance(coordinates, np.ndarray):
        # If coordinates is a NumPy array
        output_type = np.ndarray
    elif isinstance(coordinates, list):
        # If coordinates is a list of tuples
        coordinates = tupellist_to_array(coordinates)
        output_type = list
    else:
        raise TypeError("Invalid type for 'coordinates'. Must be a NumPy array or a list of tuples.")

    reference_heading = math.pi/2

    cn = np.cos(reference_heading)
    sn = np.sin(reference_heading)
    kn = 180.0 / 1736000 / np.pi
    ke = 180.0 / 1738100 / np.pi
    lat_tmp = (coordinates[:, 1] - setup.maps.ymin) / kn
    lon_tmp = (coordinates[:, 0] - setup.maps.xmin) / ke

    x_transformed = cn * lat_tmp + sn * lon_tmp
    y_transformed = sn * lat_tmp - cn * lon_tmp

    # Return the transformed coordinates based on the input type
    if output_type == np.ndarray:
        return np.column_stack((x_transformed, y_transformed))
    if output_type == list:
        return [tuple(row) for row in np.column_stack((x_transformed, y_transformed))]


def from_map_to_globe(coordinates, setup):
    '''
    Transforms coordinates from simulation map format to global (longitude, latitude) coordinates.
        Parameters:
            coordinates (ndarray or list of tuples): Input coordinates in simulation map format. Must be a NumPy array of shape (n, 2) or a list of tuples of length n.
            setup (Setup): Setup object containing map data and map size in pixels.
        Returns:
            transformed_coordinates (ndarray or list of tuples): Transformed coordinates in global format.
    '''
    if isinstance(coordinates, np.ndarray):
        # If coordinates is a NumPy array
        output_type = np.ndarray
    elif isinstance(coordinates, list):
        # If coordinates is a list of tuples
        coordinates = tupellist_to_array(coordinates)
        output_type = list
    else:
        raise TypeError("Invalid type for 'coordinates'. Must be a NumPy array or a list of tuples.")

    reference_heading = math.pi/2

    cn = np.cos(reference_heading)
    sn = np.sin(reference_heading)
    kn = 180.0 / 1736000 / np.pi
    ke = 180.0 / 1738100 / np.pi

    lat_tmp = cn * coordinates[:, 0] + sn * coordinates[:, 1]
    lon_tmp = sn * coordinates[:, 0] - cn * coordinates[:, 1]

    y_transformed = lat_tmp * kn + setup.maps.ymin
    x_transformed = lon_tmp * ke + setup.maps.xmin

    # Return the transformed coordinates based on the input type
    if output_type == np.ndarray:
        return np.column_stack((x_transformed, y_transformed))
    if output_type == list:
        return [tuple(row) for row in np.column_stack((x_transformed, y_transformed))]


def calculate_distance_on_globe(lon1, lat1, lon2, lat2, globe_radius):
    '''
    Function to calculate distance between two points using the haversine formula
        Parameters:
            lon1 (Float): Longitude of point 1
            lat1 (Float): Latitude of point 1
            lon2 (Float): Longitude of point 2
            lat2 (Float): Latitude of point 2
        Returns:
            float: Distance between the two points
    '''
    lon1_rad = degrees_to_radians(lon1)
    lat1_rad = degrees_to_radians(lat1)
    lon2_rad = degrees_to_radians(lon2)
    lat2_rad = degrees_to_radians(lat2)

    delta_lon = lon2_rad - lon1_rad
    delta_lat = lat2_rad - lat1_rad

    a = np.sin(delta_lat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) \
        * np.sin(delta_lon / 2) ** 2
    c = 2 * np.arctan(np.sqrt(a), np.sqrt(1 - a))

    # Distance on the surface of the sphere (Moon)
    distance = globe_radius * c

    return distance


def degrees_to_radians(degrees):
    '''
    Function to convert degrees to radians
        Parameters:
            degrees (float): Angle in degrees
        Returns:
            float: Angle in radians
    '''
    return degrees * math.pi / 180
