# ===============================================================
# useful helper functions that are commonly used in estimators
# ===============================================================
def oneD_linear_interpolation(desired_x, known):
    """
    utility function that performs 1D linear interpolation with a known energy value
    :param desired_x: integer value of the desired attribute/argument
    :param known: list of dictionary [{x: <value>, y: <energy>}]

    :return energy value with desired attribute/argument

    """
    ordered_list = []
    if known[1]['x'] < known[0]['x']:
        ordered_list[0] = known[1]['x']
    else:
        ordered_list = known

    slope = (known[1]['y'] - known[0]['y']) / (known[1]['x'] - known[0]['x'])
    desired_energy = slope * (desired_x - ordered_list[0]['x']) + ordered_list[0]['y']
    return desired_energy

def oneD_quadratic_interpolation(desired_x, known):
    """
    utility function that performs 1D linear interpolation with a known energy value
    :param desired_x: integer value of the desired attribute/argument
    :param known: list of dictionary [{x: <value>, y: <energy>}]

    :return energy value with desired attribute/argument

    """
    ordered_list = []
    if known[1]['x'] < known[0]['x']:
        ordered_list[0] = known[1]['x']
    else:
        ordered_list = known

    slope = (known[1]['y'] - known[0]['y']) / (known[1]['x'] - known[0]['x'])
    desired_energy = slope**2 * (desired_x - ordered_list[0]['x']) + ordered_list[0]['y']
    return desired_energy
