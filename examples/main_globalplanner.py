from globalplanner import astar, transform, setup_file
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime


### Input settings ###
config_file = 'user_data/config_map/herodutus.yaml'
user_func_file = 'user_data/config_robot/anymal.py'
use_manual_input = False  # Set to True to use manual start and goal input
# Only needed if use_manual_input == True
start, goal = (-46.77546186, 25.03932639), (-46.75064526, 25.05898353) # IMP
start, goal = (-52.99632770016827, 27.425843848099724), (-52.85282349257713, 27.59859732093237) # Herodutus Mons

# Load setup file
setup = setup_file.Setup(config_file=config_file,
                         user_func_file=user_func_file,
                         plot_global=True)

### Uncomment the following lines to visualize the map layers ###
# setup.maps.plot_four_layers_in_pixel([])
# setup.maps.plot_layers([0,1,2,3,4],[True,False,False,False,False])
# setup.maps.show_image()

if use_manual_input:
    [start_sim, goal_sim] = transform.from_globe_to_map([start, goal], setup)
    # start_sim, goal_sim = (6000.0, 4000.0), (12000.0, 8000.0)
    [start_pixel, goal_pixel] = transform.from_map_to_pixel([start_sim, goal_sim], setup)
else:
    # Define start and goal through click on map
    print('Choose start & goal by clicking with the left & right mouse button (respectively) on the image.')
    setup.maps.choose_start_and_goal_on_image()
    [start_sim, goal_sim] = transform.from_globe_to_map([setup.maps.start, setup.maps.goal], setup)
    [start_pixel, goal_pixel] = transform.from_map_to_pixel([start_sim, goal_sim], setup)

# Run A* algorithm
path, stats = astar.astar(setup.map_size_in_pixel, start_pixel, goal_pixel, setup, allow_diagonal=True)
path_globe = transform.from_pixel_to_globe(path, setup)

if stats[0] != -1:
    # Save stats to file
    header = '\t\t'.join(('E_P', 'R_P', 'I_P', 'B_P', 'g_func', 'h_func'))
    stats_with_wp = np.vstack((stats, np.sum(stats, axis=0)))
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    np.savetxt(f'user_data/path_storage/temp/stats_{current_datetime}.dat', stats_with_wp, header=header, comments='', delimiter='\t', fmt='%-3f')
    
    # Print some stats
    results = np.sum(stats, axis=0)

    print('E, R, I:', results[0:3])
    E_star = results[0] * setup.Emax
    energy = E_star

    risk_list = np.array(stats)[:, 1]
    crash = 1
    for R_cost in risk_list:
        R_star = R_cost * setup.Rmax
        crash_single = 1 - (1 - R_star) ** (8 / setup.maps.pixel_size)
        crash = crash * (1 - crash_single)
    risk = 1 - crash

    science = 1 - abs(results[2]) / len(path)
    banned = results[3] / len(path)

    print('The complete energy consumption is ' + str(round(energy / 1000, 2)) + ' kNm^2.')
    print('The taken risk is ' + str(round(risk * 100, 6)) + ' %.')
    print('The scientific outcome is ' + str(round(science * 100, 2)) + ' % of what would have been possible on the same path length.')
    print('The length of the path is ' + str(len(path) * setup.maps.pixel_size) + ' m.')
    print('')

    # Save data in file in case more info is needed
    column_names = np.array(['# Longitute', 'Latitude'])
    wp_header = '\t'.join(['{:<10}'.format(name) for name in column_names])
    np.savetxt(f'user_data/path_storage/temp/waypoints_{current_datetime}.dat', path_globe, \
        header=header, comments='', delimiter='\t', fmt='%-3f')

    # Show the result
    ### Uncomment the following lines to visualize the map layers ###
    plt.close()
    # setup.maps.plot_layers_with_path([1],[False],path_globe)
    # setup.maps.show_8plots_with_path(path_globe, path, [path_globe[0], path_globe[len(path_globe) - 1]])
    setup.maps.show_image_with_path(path_globe)
