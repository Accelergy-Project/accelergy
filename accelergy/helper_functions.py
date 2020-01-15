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
    # assume E = ax + c where x is a hardware attribute
    ordered_list = []
    if known[1]['x'] < known[0]['x']:
        ordered_list.append(known[1])
        ordered_list.append(known[0])
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
    # assume E = ax^2 + c where x is a hardware attribute
    ordered_list = []
    if known[1]['x'] < known[0]['x']:
        ordered_list.append(known[1])
        ordered_list.append(known[0])
    else:
        ordered_list = known

    slope = (known[1]['y'] - known[0]['y']) / (known[1]['x']**2 - known[0]['x']**2)
    desired_energy = slope * (desired_x**2 - ordered_list[0]['x']**2) + ordered_list[0]['y']
    return desired_energy