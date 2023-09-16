from accelergy.plug_in_interface.estimator import Estimator, actionDynamicEnergy


class LowAccuracyPlugIn(Estimator):
    name = 'component'
    percent_accuracy_0_to_100 = 90

    def __init__(self):
        super().__init__()

    @actionDynamicEnergy
    def action_a(self):
        return 1e-12

    @actionDynamicEnergy
    def action_b(self):
        return 1e-12

    def get_area(self):
        return 1e-12

    def leak(self, global_cycle_seconds):
        return 1e-12 * global_cycle_seconds


class MidAccuracyPlugIn(Estimator):
    name = 'component'
    percent_accuracy_0_to_100 = 95

    def __init__(self):
        super().__init__()

    @actionDynamicEnergy
    def action_a(self):
        return 2e-12

    @actionDynamicEnergy
    def action_b(self):
        raise Exception('Broken action')

    def get_area(self):
        return 2e-12

    def leak(self, global_cycle_seconds):
        return 1e-12 * global_cycle_seconds


class HighAccuracyPlugIn(Estimator):
    name = 'component'
    percent_accuracy_0_to_100 = 100

    def __init__(self, required_parameter, optional_parameter=2):
        super().__init__()
        self.required_parameter = required_parameter
        self.optional_parameter = optional_parameter
        assert required_parameter > 0, 'Required parameter is too low!'

    @actionDynamicEnergy
    def action_a(self):
        return self.required_parameter * 1e-12

    @actionDynamicEnergy
    def action_b(self, required_parameter):
        return self.required_parameter * required_parameter * 1e-12

    @actionDynamicEnergy
    def action_c(self, required_1, required_2, optional=3):
        return (required_1 + required_2 * 10 + optional * 100) * 1e-12

    def get_area(self):
        assert self.required_parameter < 5, 'Required parameter is too high!'
        return (self.required_parameter + self.optional_parameter * 10) * 1e-12

    def leak(self, global_cycle_seconds):
        return 1e-12 * global_cycle_seconds
