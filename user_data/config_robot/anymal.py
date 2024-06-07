''' This file defines the energy and risk cost functions that are used for optimizing the path.
These functions are specific to the used robot. '''

import numpy as np

def E_star(s, r, distance_walked):
    '''Approximated energy (e.g. through torque squared) for one edge. Equals equation 4 from paper.

    Parameters:
        s (float): Slope between last and current node.
        r (float): Rockabundance at current node.
        distance_walked (float): Distance for which the energy cost is calculated.

    Returns:
        float: Energy cost.
    '''
    # Calculate the energy cost based on the given coefficients and inputs
    return (803.3 + 10.54*s + 70.25*r + 0.7386*s**2 + -1.420*s*r + 1773*r**2) * distance_walked/8


def R_star(s, r, distance_walked):
    '''Crash risk for traversing one edge. Equals equation 7 from paper.

    Parameters:
        s (float): Slope between last and current node.
        r (float): Rockabundance at current node.
        distance_walked (float): Distance for which the risk cost is calculated.

    Returns:
        float: Risk cost.
    '''
    # Calculate the crash risk based on the given coefficients and inputs
    crash = -0.0288 + 0.0005310*s + 0.3194*r + 0.0003137*s**2 + -0.02298*s*r + 10.8*r**2
    # Ensure the crash risk is not less than a very small positive value
    if crash <= 0.00001:
        crash = 0.00001
    # Ensure the crash risk does not exceed 1
    if crash > 1:
        crash = 1
    # Calculate the overall risk cost over the distance walked    
    return 1 - (1 - crash)**(distance_walked/8)


def get_physical_values_from_cost(energy_costs, risk_costs, E_star_max, R_star_max, distance):
    '''Calculates the physical values from the energy and risk in cost space. Equals equations 13-15 from paper.

    Parameters:
        energy_costs (list): A list of energy costs for each visited node of the path.
        risk_costs (list): A list of risk costs for each visited node of the path.
        E_star_max (float): The maximum energy for this map; calculated based on E_star with smax and rmax.
        R_star_max (float): The maximum risk for this map; calculated based on R_star with smax and rmax.
        distance (float): The length of the path in m.

    Returns:
        tuple: A tuple containing the total energy and risk.
    '''
    # Equation 13
    energy = np.sum(energy_costs) * E_star_max
    # Equation 14
    crash = 1
    for R_cost in risk_costs:
        R_star = R_cost * R_star_max
        crash_single = 1 - (1 - R_star) ** (8 / distance)
        crash = crash * (1 - crash_single)
    # Equation 15
    risk = 1 - crash
    return energy, risk


def robot_limits():
    '''Sets the slope and rock abundance limits

    Parameters:
        s (float): Slope value to check.
        r (float): Rock abundance value to check.

    Returns:
        list: A list containing [smin, smax, rmin, rmax].
    '''
    limits = {
        'smin': -30,
        'smax': 30,
        'rmin': 0,
        'rmax': 0.3
    }
    return limits


def check_hard_constraints(g_score):
    '''Function to check the hard constraints

    This function discards a path if the cost exceeds a certain threshold.
    The different cost components can be read as
        - g_score[0]: Energy cost
        - g_score[1]: Risk cost
    If the energy cost (g_score[0]) is greater than or equal to the available energy reserve
    divided by a specific factor, the function returns True, indicating that the path should be discarded.

    Parameters:
        g_score (list): A list where the first element represents the energy cost and the second the risk cost.

    Returns:
        bool: True if the path should be discarded, False otherwise.
    '''
    # Check if the energy cost exceeds the threshold
    if g_score[0] >= np.inf:
        return True
