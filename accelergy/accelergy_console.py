# Copyright (c) 2019 Yannan Wu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import traceback
from accelergy.raw_inputs_2_dicts import RawInputs2Dicts
from accelergy.system_state import SystemState
from accelergy.component_class import ComponentClass
from accelergy.arch_dict_2_obj import arch_dict_2_obj
from accelergy.plug_in_path_to_obj import plug_in_path_to_obj
from accelergy.action_counts_dict_2_obj import action_counts_dict_2_obj
from accelergy.primitive_component import PrimitiveComponent
from accelergy.compound_component import CompoundComponent
from accelergy.ERT_generator import EnergyReferenceTableGenerator, ERT_dict_to_obj
from accelergy.ART_generator import AreaReferenceTableGenerator
from accelergy.energy_calculator import EnergyCalculator
from accelergy.input_output import parse_commandline_args, generate_output_files
from accelergy.utils.utils import *
import accelergy.version as version
import accelergy.parsing_utils


def run():
    accelergy_version = version.__version__

    # ----- Interpret Commandline Arguments
    args = parse_commandline_args()
    output_prefix = args.oprefix
    path_arglist = args.files
    precision = args.precision
    desired_output_files = args.output_files
    # args.scripts Script support disabled. PyTimeloop preprocessing should be used instead.
    scripts = []
    extra_plugins = args.extra_plugins
    version.SUPPRESS_VERSION_ERRORS = args.suppress_version_errors
    logging.getLogger().setLevel(logging.INFO if not args.verbose else logging.DEBUG)
    # interpret desired output files
    oflags = {
        "ERT": 0,
        "ERT_summary": 0,
        "ART": 0,
        "ART_summary": 0,
        "energy_estimation": 0,
        "flattened_arch": 0,
    }
    for key, val in oflags.items():
        if "all" in desired_output_files or key in desired_output_files:
            oflags[key] = 1

    INFO(
        "generating outputs according to the following specified output flags... \n "
        "Please use the -f flag to update the preference (default to all output files)"
    )
    INFO(oflags)

    oflags["output_prefix"] = output_prefix
    # interpret the types of processing that need to be performed
    flatten_architecture = 1 if oflags["flattened_arch"] else 0
    compute_ERT = (
        1
        if oflags["ERT"] or oflags["ERT_summary"] or oflags["energy_estimation"]
        else 0
    )
    compute_energy_estimate = 1 if oflags["energy_estimation"] else 0
    compute_ART = 1 if oflags["ART"] or oflags["ART_summary"] else 0

    # ----- Global Storage of System Info
    system_state = SystemState()
    system_state.set_accelergy_version(accelergy_version)
    # transport the input flag information to system state
    system_state.set_flag_s({"output_path": args.outdir, "verbose": args.verbose})
    system_state.set_flag_s(oflags)

    # ----- Load Raw Inputs to Parse into Dicts
    raw_input_info = {"path_arglist": path_arglist, "parser_version": accelergy_version}
    raw_dicts = RawInputs2Dicts(raw_input_info, args.update_config_version)

    # ----- Determine what operations should be performed
    available_inputs = raw_dicts.get_available_inputs()
    # accelergy.parsing_utils.set_script_paths()

    # ---- Detecting config only cases and gracefully exiting
    if len(available_inputs) == 0:
        INFO("no input is provided, exiting...")
        sys.exit(0)

    if (
        compute_ART
        or flatten_architecture
        or compute_ERT
        and "ERT" not in available_inputs
    ):
        # ----- Interpret the input architecture description using only the input information (w/o class definitions)
        system_state.set_hier_arch_spec(raw_dicts.get_hier_arch_spec_dict())

    if (
        flatten_architecture
        or (compute_ERT and "ERT" not in available_inputs)
        or compute_ART
    ):
        # architecture needs to be defined if
        #    (1) flattened architecture required output,
        #    (2) ERT needed but bot provided,
        #    (3) ART needed

        # ----- Add the Component Classes
        for pc_name, pc_info in raw_dicts.get_pc_classses().items():
            system_state.add_pc_class(ComponentClass(pc_info))
        for cc_name, cc_info in raw_dicts.get_cc_classses().items():
            system_state.add_cc_class(ComponentClass(cc_info))

        # ----- Set Architecture Spec (all attributes defined)
        arch_obj = arch_dict_2_obj(
            raw_dicts.get_flatten_arch_spec_dict(),
            system_state.cc_classes,
            system_state.pc_classes,
        )
        system_state.set_arch_spec(arch_obj)

    if (compute_ERT and "ERT" not in available_inputs) or compute_ART:
        # ERT/ERT_summary/energy estimates/ART/ART summary need to be generated without provided ERT
        #        ----> all components need to be defined
        # ----- Add the Fully Defined Components (all flattened out)

        for arch_component in system_state.arch_spec:
            if arch_component.get_class_name() in system_state.cc_classes:
                cc = CompoundComponent(
                    {
                        "component": arch_component,
                        "pc_classes": system_state.pc_classes,
                        "cc_classes": system_state.cc_classes,
                    }
                )
                system_state.add_cc(cc)
            else:
                class_name = arch_component.get_class_name()
                if class_name not in system_state.pc_classes:
                    system_state.pc_classes[class_name] = ComponentClass(
                        {"name": class_name, "attributes": {}, "actions": []}
                    )
                pc = PrimitiveComponent(
                    {
                        "component": arch_component,
                        "pc_class": system_state.pc_classes[class_name],
                    }
                )
                system_state.add_pc(pc)
        # ----- Add all available plug-ins
        system_state.add_plug_ins(
            plug_in_path_to_obj(
                raw_dicts.get_estimation_plug_in_paths(),
                raw_dicts.get_python_plug_in_paths() + extra_plugins,
                output_prefix,
            ),
        )

    if compute_ERT and "ERT" in available_inputs:
        # ERT/ ERT_summary/ energy estimates need to be generated with provided ERT
        #      ----> do not need to define components
        # ----- Get the ERT from raw inputs
        ert_dict = raw_dicts.get_ERT_dict()
        system_state.set_ERT(
            ERT_dict_to_obj(
                {
                    "ERT_dict": ert_dict,
                    "parser_version": accelergy_version,
                    "precision": precision,
                }
            )
        )

    if compute_ERT and "ERT" not in available_inputs:
        # ----- Generate Energy Reference Table
        ert_gen = EnergyReferenceTableGenerator(
            {
                "parser_version": accelergy_version,
                "pcs": system_state.pcs,
                "ccs": system_state.ccs,
                "plug_ins": system_state.plug_ins,
                "precision": precision,
            }
        )
        system_state.set_ERT(ert_gen.get_ERT())

    if compute_energy_estimate:  # if energy estimates need to be generated
        # ----- Generate Energy Estimates
        action_counts_obj = action_counts_dict_2_obj(raw_dicts.get_action_counts_dict())
        system_state.set_action_counts(action_counts_obj)
        energy_calc = EnergyCalculator(
            {
                "parser_version": accelergy_version,
                "action_counts": system_state.action_counts,
                "ERT": system_state.ERT,
            }
        )
        system_state.set_energy_estimations(energy_calc.energy_estimates)

    if compute_ART:  # if ART, ART_summary need to be generated
        # ----- Generate Area Reference Table
        art_gen = AreaReferenceTableGenerator(
            {
                "parser_version": accelergy_version,
                "pcs": system_state.pcs,
                "ccs": system_state.ccs,
                "plug_ins": system_state.plug_ins,
                "precision": precision,
            }
        )
        system_state.set_ART(art_gen.get_ART())

    # ----- Generate All Necessary Output Files
    generate_output_files(system_state)


def main():
    if False:
        run()
    else:
        try:
            run()
        except Exception as e:
            import traceback
            from traceback import linecache
            import re

            tb = sys.exc_info()[2]

            def ps(*args, **kwargs):
                print(*args, file=sys.stderr, **kwargs)

            ps("\n" * 5 + "=" * 60)
            ps(f"Accelergy has encountered an error and crashed. Error below: ")
            ps("=" * 60)
            ps("|| " + traceback.format_exc().strip().replace("\n", "\n|| "))
            ps("=" * 60)
            ps(f"Stack with local variables (most recent call last):")
            stack = []
            while tb:
                stack.append((tb.tb_frame, tb.tb_lineno))
                tb = tb.tb_next

            frameno = 4
            current_frame = frameno
            contextrange = 4
            for frame, lineno in stack[-frameno:]:
                current_frame -= 1
                context = []
                for i in range(lineno - contextrange, lineno + contextrange + 1):
                    try:
                        l = linecache.getline(
                            frame.f_code.co_filename, i, frame.f_globals
                        )
                        context.append((i, l))
                    except:
                        pass
                stripamount = min(len(c[1]) - len(c[1].lstrip()) for c in context)
                newcontext = []
                for c in context:
                    x = "         " if c[0] != lineno else "ERROR >> "
                    x += str(c[0]) + ": " + c[1][stripamount:]
                    if c[1][stripamount:] == "":
                        x += "\n"
                    newcontext.append(x)
                context = newcontext

                if current_frame != frameno:
                    ps("=" * 60)
                ps(f"Frame {current_frame}")
                ps("=" * 60)
                ps(f"| {frame.f_code.co_filename}:{lineno}")
                ps(f"| {type(e).__name__}: {e}")
                contextlines = "\n".join(context)
                for k, v in frame.f_locals.items():
                    if re.findall(r"\W" + k + r"\W", contextlines):
                        startline = f"Local var {k} ="
                        try:
                            strv = str(v)
                        except:
                            strv = "<Unable to print this variable]>"
                        ps(f"| {startline:<40} {strv}")
                for c in context:
                    ps("| " + c, end="")

            ps("=" * 60)
            ps("|| " + traceback.format_exc().strip().replace("\n", "\n|| "))
            ps("=" * 60)
            ps("Accelergy has encountered an error and crashed. Error above. ")
            ps("=" * 60 + "\n")

            exit(-1)
