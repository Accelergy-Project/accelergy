from accelergy.plug_in_interface.interface import *
from accelergy.version import input_version_greater_or_equal
from accelergy.plug_in_interface.estimator_wrapper import (
    SupportedComponent,
    PrintableCall,
)


class DummyTable(AccelergyPlugIn):
    """
    A dummy estimation plug-in. Estimations from this plug-in are not
    meaningful and to be used for testing only.
    """

    # -------------------------------------------------------------------------------------
    # Interface functions, function name, input arguments, and output have to adhere
    # -------------------------------------------------------------------------------------
    def __init__(self):
        pass

    def primitive_action_supported(self, query: AccelergyQuery) -> AccuracyEstimation:
        class_name = query.class_name
        attributes = query.class_attrs
        action_name = query.action_name
        arguments = query.action_args
        if attributes.get("technology", None) == -1:
            return AccuracyEstimation(100)
        if not input_version_greater_or_equal(0.4):
            return AccuracyEstimation(1)
        self.logger.info(
            'Set attribute "technology" to -1 to use placeholder estimations (for testing).'
        )
        return AccuracyEstimation(0)

    def estimate_energy(self, query: AccelergyQuery) -> Estimation:
        class_name = query.class_name
        attributes = query.class_attrs
        action_name = query.action_name
        arguments = query.action_args

        energy_pj = 0 if action_name == "leak" else 1
        return Estimation(energy_pj, "p")  # Dummy returns 1 for all non-leak actions

    def primitive_area_supported(self, query: AccelergyQuery) -> AccuracyEstimation:
        class_name = query.class_name
        attributes = query.class_attrs
        action_name = query.action_name
        arguments = query.action_args
        if attributes.get("technology", None) == -1:
            return AccuracyEstimation(100)
        if not input_version_greater_or_equal(0.4):
            return AccuracyEstimation(1)
        self.logger.info(
            'Set attribute "technology" to -1 to use placeholder estimations (for testing).'
        )
        return AccuracyEstimation(0)

    def estimate_area(self, query: AccelergyQuery) -> Estimation:
        class_name = query.class_name
        attributes = query.class_attrs
        action_name = query.action_name
        arguments = query.action_args
        return Estimation(1, "u^2")  # Dummy returns 1 for all non-leak actions

    def get_name(self) -> str:
        return "dummy"

    def get_supported_components(self) -> List[SupportedComponent]:
        return [
            SupportedComponent(
                "_anything_",
                PrintableCall(
                    "",
                    [
                        "set 'technology=-1' to use placeholder estimations (for testing)."
                    ],
                ),
                [PrintableCall("_anything_")],
            )
        ]
