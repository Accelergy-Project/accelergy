from accelergy.plug_in_interface.estimator import Estimator, action2energy


class DummyObjectAreaEnergyOne(Estimator):
    name = 'dummy_object_area_energy_one'
    percent_accuracy_0_to_100 = 100

    def __init__(self):
        super().__init__()

    @action2energy
    def read(self):
        return 1e-12

    @action2energy
    def write(self):
        return 1e-12

    @action2energy
    def idle(self):
        return 1e-12

    def get_area(self):
        return 1e-12
