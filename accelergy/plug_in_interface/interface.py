from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from math import floor, log10
from numbers import Number
from typing import Any, Dict, List, Union

from accelergy.utils.logging import ListLoggable
import accelergy.version as version

from accelergy.parsing_utils import (
    ruamel_str_to_normal_str,
    assert_required_keys_numeric,
)


class UnitOption(Enum):
    """Unit options for Estimation objects."""

    femto = (1e-15, "f")
    pico = (1e-12, "p")
    nano = (1e-9, "n")
    micro = (1e-6, "u")
    milli = (1e-3, "m")
    none = (1e0, "")
    kilo = (1e3, "k")
    mega = (1e6, "M")
    giga = (1e9, "G")
    tera = (1e12, "T")
    peta = (1e15, "P")
    percent = (1e-2, "%")
    kibi = (2**10, "Ki")
    mebi = (2**20, "Mi")
    gibi = (2**30, "Gi")
    tebi = (2**40, "Ti")
    pebi = (2**50, "Pi")
    femto_sq = (1e-30, "f^2")
    pico_sq = (1e-24, "p^2")
    nano_sq = (1e-18, "n^2")
    micro_sq = (1e-12, "u^2")
    milli_sq = (1e-6, "m^2")
    none_sq = (1, "")
    kilo_sq = (1e6, "k^2")
    mega_sq = (1e12, "M^2")
    giga_sq = (1e18, "G^2")
    tera_sq = (1e24, "T^2")
    peta_sq = (1e30, "P^2")
    percent_sq = (1e-4, "%^2")
    kibi_sq = (2**20, "Ki^2")
    mebi_sq = (2**40, "Mi^2")
    gibi_sq = (2**60, "Gi^2")
    tebi_sq = (2**80, "Ti^2")
    pebi_sq = (2**100, "Pi^2")

    @classmethod
    def from_str(cls, unit_str: str) -> "UnitOption":
        if not unit_str:
            return cls.none
        for unit_name in cls.__members__:
            if unit_str.lower() == getattr(cls, unit_name).name.lower():
                return getattr(cls, unit_name)
        for unit_name in cls.__members__:
            if unit_str == getattr(cls, unit_name).value[1]:
                return getattr(cls, unit_name)
        raise ValueError(
            f"Invalid unit string: {unit_str}. Valid unit strings are: "
            f'{", ".join([getattr(cls, unit_name).name for unit_name in cls.__members__])}'
        )

    def from_number(cls, unit_num: Number) -> "UnitOption":
        for unit_name in cls.__members__:
            if unit_num == getattr(cls, unit_name).value[0]:
                return getattr(cls, unit_name)
        raise ValueError(
            f"Invalid unit number: {unit_num}. Valid unit numbers are: "
            f'{", ".join([getattr(cls, unit_name).value[0] for unit_name in cls.__members__])}'
        )

    def __mul__(self, other):
        return self.value[0] * other

    def __rmul__(self, other):
        return self.value[0] * other

    def __str__(self):
        return self.value[1]


def unit2unitopt(value: Union[str, Number, UnitOption, None]) -> UnitOption:
    if isinstance(value, UnitOption):
        return value
    if isinstance(value, str):
        return UnitOption.from_str(value)
    if isinstance(value, Number):
        return UnitOption.from_number(value)
    return UnitOption.none


class Estimation:
    """Estimation object for storing estimation results."""

    def __init__(
        self,
        value: Number,
        unit: Union[str, Number, UnitOption, None] = None,
        success: bool = True,
    ):
        self.value = value
        if not isinstance(value, Number):
            raise TypeError(f"Estimation value must be a number, not {type(value)}")
        if not isinstance(unit, UnitOption):
            unit = unit2unitopt(unit)
        self.success = success
        self.messages = []
        self.estimator_name = None
        self.unit = unit

    def add_messages(self, messages: Union[List[str], str]):
        """
        Adds messages to the internal message list. The messages are reported by Accelergy depending
        on plug-in selections and verbosity level.
        """
        if isinstance(messages, str):
            self.add_messages([messages])
        else:
            self.messages += messages

    def __str__(self):
        return f"{self.value}{self.unit}"

    @classmethod
    def from_value(cls, value: Union[Number, "Estimation"]) -> "Estimation":
        if isinstance(value, Estimation):
            return value
        return Estimation(value=value)

    def fail(self, message: str):
        """Marks this estimation as failed and adds the message."""
        if not self.success:
            return
        self.success = False
        self.value = 0
        self.add_messages(message)

    def lastmessage(self) -> str:
        """Returns the last message in the message list. If no messages, returns a default."""
        if self.messages:
            return self.messages[-1]
        else:
            return f"No messages found."

    def round(self, precision: int):
        """Rounds to "precision" significant figures"""
        if self.value == 0:
            return self.value
        self.value = round(
            self.value, precision - int(floor(log10(abs(self.value)))) - 1
        )

    def get_value(self):
        return self.value * self.unit


class AccuracyEstimation(Estimation):
    """Estimation of percent accuracy returned from the primitive_XYZ_supported functions."""

    def __init__(self, value: float, success: bool = True):
        super().__init__(value=value, unit="percent", success=success)
        if not (0 <= value <= 100):
            raise ValueError(
                f"AccuracyEstimation value must be between 0 and 100, not {value}"
            )
        if value == 0:
            self.fail("Accuracy is 0%. Not supported.")

    def fail_if_accuracy_low(self, threshold: Number):
        """Marks this estimation as failed if the accuracy is below the threshold."""
        if self.value < threshold:
            self.fail(f"Accuracy {self.value} is below threshold {threshold}.")


@dataclass
class AccelergyQuery:
    """A query to an Accelergy plug-in."""

    class_name: str
    class_attrs: Dict[str, Any]
    action_name: str = None
    action_args: Dict[str, Any] = None
    input_file_version: float = None

    def __init__(
        self,
        class_name: str,
        class_attrs: Dict[str, Any],
        action_name: str = None,
        action_args: Dict[str, Any] = None,
    ):
        self.class_name = class_name
        self.action_name = action_name
        self.input_file_version = version.INPUT_VERSION
        # Attributes and arguments are only included if they are not None
        if action_args is None:
            action_args = {}
        else:
            self.action_args = {k: v for k, v in action_args.items() if v is not None}
        self.class_attrs = {k: v for k, v in class_attrs.items() if v is not None}

    def __str__(self):
        attrs_stringified = ", ".join([f"{k}={v}" for k, v in self.class_attrs.items()])
        s = f"{self.class_name}({attrs_stringified})"
        if self.action_name:
            args_stringified = ", ".join(
                [f"{k}={v}" for k, v in self.action_args.items()]
            )
            s += f".{self.action_name}({args_stringified})"
        return s

    def from_interface_dict(d: Dict[str, Any]) -> "AccelergyQuery":
        """
        Creates an AccelergyQuery from a dictionary. The dictionary is the same as the general
        internal representation in Accelergy, with "class_name", "attributes", "action_name", and
        "arguments" keys.
        """
        # In case plug-ins don't like that the provided strings are subclasses of str, we convert
        attributes = {
            k: ruamel_str_to_normal_str(v) for k, v in d["attributes"].items()
        }
        a = AccelergyQuery(class_name=d["class_name"], class_attrs=attributes)
        if ("action_name" in d) != ("arguments" in d):
            raise ValueError(
                f'Either both or neither of "action_name" and "action_args" must be '
                f"present in the interface dict."
            )
        if "action_name" in d:
            a.action_name = d["action_name"]
            a.action_args = d["arguments"] if d["arguments"] is not None else {}

        assert_required_keys_numeric(a.class_attrs or {}, f"{a.class_name} attributes")
        assert_required_keys_numeric(
            a.action_args or {}, f"{a.class_name} action arguments", True
        )
        return a

    def to_legacy_interface_dict(self) -> Dict[str, Any]:
        """Creates a dictionary in the legacy interface format."""
        d = {
            "class_name": self.class_name,
            "attributes": self.class_attrs,
        }
        if self.action_name:
            d["action_name"] = self.action_name
            d["arguments"] = self.action_args
            # Legacy plugins expect None instead of empty dict
            if not d["arguments"]:
                d["arguments"] = None
        return d


class AccelergyPlugIn(ListLoggable, ABC):
    def __AccelergyPlugIn__init__(self):  # Do not override this method
        """For internal use so users don't have to call super().__init__()"""
        super().__init__(name=self.get_name())
        self._accelergy_plug_in_initialized = True

    def __init__(self):
        self.__AccelergyPlugIn__init__()

    @abstractmethod
    def primitive_action_supported(self, query: AccelergyQuery) -> AccuracyEstimation:
        """
        Returns an AccuracyEstimation with the percent accuracy of the plug-in's ability to
        estimate the action represented by the query. Returns AccuracyEstimation(0) or raises an
        exception if the plug-in cannot estimate the action.
        """

    @abstractmethod
    def estimate_energy(self, query: AccelergyQuery) -> Estimation:
        """
        Returns an Estimation with the energy of the action represented by the query. Raises an
        exception if the plug-in cannot estimate the action.
        """

    @abstractmethod
    def primitive_area_supported(self, query: AccelergyQuery) -> AccuracyEstimation:
        """
        Returns an AccuracyEstimation with the percent accuracy of the plug-in's ability to
        estimate the area of the primitive represented by the query. Returns AccuracyEstimation(0)
        or raises an exception if the plug-in cannot estimate the area.
        """

    @abstractmethod
    def estimate_area(self, query: AccelergyQuery) -> Estimation:
        """
        Returns an Estimation with the area of the primitive represented by the query. Raises an
        exception if the plug-in cannot estimate the area.
        """

    @abstractmethod
    def get_name(self) -> str:
        """
        Returns the name of the plug-in.
        """
