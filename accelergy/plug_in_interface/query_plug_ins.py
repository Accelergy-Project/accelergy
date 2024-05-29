import logging
import copy
from typing import Any, Callable, Dict, List, Tuple, Union
from accelergy.plug_in_interface.interface import *
from accelergy.utils.utils import ERROR_CLEAN_EXIT, indent_list_text_block, WARN
from accelergy.utils.logging import (
    get_logger,
    pop_all_messages,
    print_messages,
    log_all_lines,
)

RAISED_WARNINGS_FOR_CLASSES = []


def warn_depreciation(plug_in: Any):
    plug_in_name = plug_in.estimator_name
    if plug_in_name in RAISED_WARNINGS_FOR_CLASSES:
        return
    WARN(
        f"Plug-in {plug_in_name} is using a deprecated interface. Please update to new interface."
    )
    RAISED_WARNINGS_FOR_CLASSES.append(plug_in_name)


def plugin2name(plug_in: Any) -> str:
    if isinstance(plug_in, AccelergyPlugIn):
        return plug_in.get_name()
    warn_depreciation(plug_in)
    return plug_in.estimator_name


def call_plug_in(
    plug_in: Any,
    query: AccelergyQuery,
    target_func: Callable,
    estimation_type: Union[Estimation, AccuracyEstimation],
) -> Estimation:
    logger = get_logger(plugin2name(plug_in))
    try:
        # New interface
        if isinstance(plug_in, AccelergyPlugIn):
            estimation = target_func(query)
            logger = plug_in.logger
        # Deprecated interface
        else:
            warn_depreciation(plug_in)
            estimation = estimation_type(target_func(query.to_legacy_interface_dict()))
            if estimation.success and not isinstance(estimation, AccuracyEstimation):
                estimation.unit = UnitOption.from_str("p")
    except Exception as e:
        # Error
        # if isinstance(e, TypeError):
        #     raise e
        estimation = estimation_type(0, success=False)
        logger.error(f"{type(e).__name__}: {e}")

    if not isinstance(estimation, estimation_type):
        raise TypeError(
            f"Plug-in {plugin2name(plug_in)} returned {type(estimation)} instead of "
            f"{estimation_type}. "
            f'{indent_list_text_block("Messages:", pop_all_messages(plugin2name(plug_in)))}'
        )

    # Add message logs
    estimation.add_messages(pop_all_messages(logger))
    estimation.estimator_name = plugin2name(plug_in)

    # See if this estimation matches user requested plug-in and min accuracy
    attrs = query.class_attrs
    if (
        attrs.get("plug_in", None) is not None
        and attrs["plug_in"] != estimation.estimator_name
    ):
        estimation.fail(
            f"Plug-in {estimation.estimator_name} was not selected for query."
        )
    if isinstance(estimation, AccuracyEstimation):
        estimation.fail_if_accuracy_low(attrs.get("minimum_accuracy", 0))
        estimation.fail_if_accuracy_low(attrs.get("min_accuracy", 0))
    return estimation


def primitive_energy_supported(
    plug_in: Any, query: AccelergyQuery
) -> AccuracyEstimation:
    return call_plug_in(
        plug_in, query, plug_in.primitive_action_supported, AccuracyEstimation
    )


def get_energy_estimation(plug_in: Any, query: AccelergyQuery) -> Estimation:
    e = call_plug_in(plug_in, query, plug_in.estimate_energy, Estimation)
    if e and e.success and query.action_name == "leak":
        n_instances = query.class_attrs.get("n_instances", 1)
        e.add_messages(f"Multiplying by n_instances {n_instances}")
        e.value *= n_instances
    return e


def primitive_area_supported(plug_in: Any, query: AccelergyQuery) -> AccuracyEstimation:
    return call_plug_in(
        plug_in, query, plug_in.primitive_area_supported, AccuracyEstimation
    )


def get_area_estimation(plug_in: Any, query: AccelergyQuery) -> AccuracyEstimation:
    e = call_plug_in(plug_in, query, plug_in.estimate_area, Estimation)
    if e and e.success:
        n_instances = query.class_attrs.get("n_instances", 1)
        e.add_messages(f"Multiplying by n_instances {n_instances}")
        e.value *= n_instances
    return e


def get_best_estimate(
    plug_ins: List[Union[AccelergyPlugIn, Any]],
    query: Dict[str, Any],
    is_energy_estimation: bool,
) -> Estimation:
    acc_func = (
        primitive_energy_supported if is_energy_estimation else primitive_area_supported
    )
    est_func = get_energy_estimation if is_energy_estimation else get_area_estimation
    query = AccelergyQuery.from_interface_dict(query)
    target = "ENERGY" if is_energy_estimation else "AREA"
    if logging.getLogger("").isEnabledFor(logging.INFO):
        logging.getLogger("").info("")
    logging.getLogger("").info(f"{target} ESTIMATION for {query}")

    accuracies = [(plug_in, acc_func(plug_in, query)) for plug_in in plug_ins]
    estimations = []
    accuracies = sorted(accuracies, key=lambda x: x[1].value, reverse=True)
    estimation = None
    for plug_in, accuracy in accuracies:
        if not accuracy.success or accuracy.value == 0:
            continue
        estimation = est_func(plug_in, copy.deepcopy(query))
        logger = get_logger(plugin2name(plug_in))
        if not estimation.success:
            estimation.add_messages(pop_all_messages(logger))
            estimations.append((accuracy, estimation))
        else:
            log_all_lines(
                f"Accelergy",
                "info",
                f"{estimation.estimator_name} estimated "
                f"{estimation} with accuracy {accuracy}. "
                + indent_list_text_block("Messages:", estimation.messages),
            )
            break

    full_logs_acc = [
        indent_list_text_block(
            f"{e.estimator_name} with accuracy {e} estimating accuracy:", e.messages
        )
        for _, e in accuracies
    ]
    full_logs_estimations = [
        indent_list_text_block(
            f"{e.estimator_name} with accuracy {a} estimating value: ", e.messages
        )
        for a, e in estimations
    ]
    full_logs = (full_logs_acc if full_logs_acc[0] else []) + full_logs_estimations
    fail_reasons_accuracy = [
        f"{e.estimator_name} with accuracy {e} estimating accuracy: {e.lastmessage()}"
        for _, e in accuracies
    ]
    fail_reasons_estimations = [
        f"{e.estimator_name} with accuracy {a} estimating value: " f"{e.lastmessage()}"
        for a, e in estimations
    ]
    fail_reasons = fail_reasons_accuracy + fail_reasons_estimations

    if full_logs:
        log_all_lines(
            "Accelergy", "debug", indent_list_text_block("Estimator logs:", full_logs)
        )
    if fail_reasons:
        log_all_lines(
            "Accelergy",
            "debug",
            indent_list_text_block("Why plug-ins did not estimate:", fail_reasons),
        )
    if fail_reasons_estimations:
        log_all_lines(
            "Accelergy",
            "info",
            indent_list_text_block(
                "Plug-ins provided accuracy, but failed to estimate:",
                fail_reasons_estimations,
            ),
        )

    if estimation and estimation.success:
        return estimation

    estimation_target = "energy" if is_energy_estimation else "area"
    ERROR_CLEAN_EXIT(
        *(
            f"Can not find an {estimation_target} estimator for {query}\n"
            f'{indent_list_text_block("Logs for plug-ins that could estimate query:", full_logs)}\n'
            f'{indent_list_text_block("Why plug-ins did not estimate:", fail_reasons)}\n'
            f'\n.\n.\nTo see a list of available component models, run "<command you used> -h" and '
            f"find the option to list Accelergy components. Alternatively, run accelergy verbose and "
            f"check the log file."
        ).splitlines()
    )
