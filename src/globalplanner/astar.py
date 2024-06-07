'''This file includes all functions to run the A* algorithm.'''

import heapq
import numpy as np
import matplotlib.pyplot as plt


def astar(map_size, start, goal, setup, allow_diagonal, show_all_visited_nodes=False):
    '''
    Core A* function that calculates the optimal path and returns it as a list of tuples.

    Parameters:
        map_size (tuple): Dimensions of the map as (width, height).
        start (tuple): Starting pixel coordinates as (x, y).
        goal (tuple): Goal pixel coordinates as (x, y).
        setup (Setup): An instance of the Setup class containing configuration and utility functions.
        allow_diagonal (bool): If True, considers all 8 neighboring pixels; if False, considers only 4.
        show_all_visited_nodes (bool, optional): If True, visualizes all visited nodes. Default is False.
    
    Returns:
        list of tuple: The optimal path as a list of pixel coordinates (x, y).
    '''
    open_set = []
    heapq.heappush(open_set, (0, start))  # Priority queue ordered by cost
    came_from = {}
    costcomponents = 4 # defined in setup function
    g_score = {start: [0]*(costcomponents+1)}
    f_score = {start: setup.h_func(start, goal)}  # Estimated total cost from start to goal
    closed_set = set()

    if show_all_visited_nodes:
        visited_nodes = np.zeros(map_size)
        print(visited_nodes.shape)

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            if show_all_visited_nodes:
                plot_visited_nodes(visited_nodes, start, goal)
            return reconstruct_path(came_from, current, setup.g_func, setup.h_func, goal)

        closed_set.add(current)

        for neighbor in get_neighbors(current, map_size, allow_diagonal):
            if show_all_visited_nodes:
                visited_nodes[neighbor] = 1
            if neighbor in closed_set:
                continue

            new_g_score = [x + y for x, y in zip(g_score[current], setup.g_func(neighbor, current))]
            if setup.check_hard_constraints(new_g_score):
                new_g_score[costcomponents] = np.inf

            if new_g_score[costcomponents] < np.inf and (neighbor not in g_score or new_g_score[costcomponents] < g_score[neighbor][costcomponents]):
                g_score[neighbor] = new_g_score
                f_score[neighbor] = new_g_score[costcomponents] + setup.h_func(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
                came_from[neighbor] = current

    print('No path found. Check input parameters.')
    return [-1], [-1]  # No path found


def get_neighbors(node, map_size, allow_diagonal=False):
    '''
    Gets all neighbors of a node.

    Parameters:
        node (tuple): Pixel coordinates of the node as (x, y).
        map_size (tuple): Size of the map as (columns, rows).
        allow_diagonal (bool): If True, considers all 8 neighboring pixels; if False, considers only 4.

    Returns:
        list of tuple: List of pixel coordinates for all neighboring nodes.
    '''
    x, y = node
    cols, rows = map_size
    neighbors = []

    # Add adjacent cells as neighbors
    if x > 0:
        neighbors.append((x - 1, y))
    if x < cols - 1:
        neighbors.append((x + 1, y))
    if y > 0:
        neighbors.append((x, y - 1))
    if y < rows - 1:
        neighbors.append((x, y + 1))

    if allow_diagonal:
        # Add diagonal cells as neighbors
        if x > 0 and y > 0:
            neighbors.append((x - 1, y - 1))
        if x > 0 and y < rows - 1:
            neighbors.append((x - 1, y + 1))
        if x < cols - 1 and y > 0:
            neighbors.append((x + 1, y - 1))
        if x < cols - 1 and y < rows - 1:
            neighbors.append((x + 1, y + 1))

    return neighbors


def reconstruct_path(came_from, current, g_func, h_func, goal):
    '''
    Reconstructs the path from the goal node to the start node.

    Parameters:
        came_from (dict): A dictionary mapping each node to its predecessor.
        current (tuple): The current node (goal node) from which to start the reconstruction.
        g_func (function): A function that calculates the cost from one node to another.
        h_func (function): A heuristic function that estimates the cost from a node to the goal.
        goal (tuple): The goal node.

    Returns:
        np.ndarray: An array of nodes representing the path from start to goal.
        list: A list of costs associated with each step in the path.
    '''
    path = [current]
    cost = []
    while current in came_from:
        previous = came_from[current]
        path.append(previous)
        cost.append(g_func(current, previous)+(h_func(previous, goal),))
        #cost.append((g_func(current, previous),(h_func(previous, goal))))
        current = previous
    tupellist = list(reversed(path))
    stats = list(reversed(cost))
    return np.array([list(t) for t in tupellist]), stats


def plot_visited_nodes(visited_nodes, start, goal):
    """
    Plots the visited nodes on a grid, highlighting the start and goal nodes.

    Parameters:
        visited_nodes (np.ndarray): A 2D array representing the grid where each cell indicates if it was visited.
        start (tuple): The coordinates of the start node (x, y).
        goal (tuple): The coordinates of the goal node (x, y).
    """
    plt.figure()
    plt.imshow(visited_nodes.T, cmap='gray')
    plt.scatter(start[0], start[1], color='green', label='Start Node', marker='s')
    plt.scatter(goal[0], goal[1], color='red', label='Goal Node', marker='s')
    plt.legend()
    plt.title('Visited Nodes with Start and Goal')
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.show()
