from accelergy.utils.utils import *
from accelergy.plug_in_interface.interface import AccelergyPlugIn

# Option to list all names and option to list all names and arguments
# tl accelergy list-components
# tl accelergy list-actions


class SystemState:
    def __init__(self):
        self.cc_classes = {}
        self.pc_classes = {}
        self.arch_spec = None
        self.hier_arch_spec = None
        self.ccs = {}
        self.pcs = {}
        self.action_counts = None
        self.plug_ins = []
        self.ERT = None
        self.ART = None
        self.parser_version = None
        self.flags = {}
        self.energy_estimations = None

    def set_flag_s(self, flag_name_val_dict):
        self.flags.update(flag_name_val_dict)

    def set_accelergy_version(self, version):
        self.parser_version = version

    def set_hier_arch_spec(self, arch_dict):
        ASSERT_MSG(self.hier_arch_spec is None, "interpreted input arch is set")
        self.hier_arch_spec = arch_dict

    def set_arch_spec(self, arch_spec):
        ASSERT_MSG(self.arch_spec is None, "architecture spec is already set")
        self.arch_spec = arch_spec

    def add_cc_class(self, cc_class):
        cc_class_name = cc_class.get_name()
        ASSERT_MSG(
            cc_class_name not in self.cc_classes,
            "%s compound class is already added" % (cc_class_name),
        )
        self.cc_classes[cc_class_name] = cc_class

    def add_pc_class(self, pc_class):
        pc_class_name = pc_class.get_name()
        ASSERT_MSG(
            pc_class_name not in self.pc_classes,
            "%s primitive class is already added" % (pc_class_name),
        )
        self.pc_classes[pc_class_name] = pc_class

    def add_cc(self, cc):
        cc_name = cc.get_name()
        ASSERT_MSG(
            cc_name not in self.ccs,
            "%s compound component is already added" % (cc_name),
        )
        self.ccs[cc_name] = cc

    def add_pc(self, pc):
        pc_name = pc.get_name()
        ASSERT_MSG(
            pc_name not in self.ccs,
            "%s compound component is already added" % (pc_name),
        )
        self.pcs[pc_name] = pc

    def add_plug_ins(self, plug_ins):
        ASSERT_MSG(
            isinstance(plug_ins, list), "plug in objects need to be passed in as a list"
        )
        self.plug_ins = []
        found_names = set()
        for plug_in in plug_ins:
            if plug_in.get_name() in found_names:
                WARN(f"Plug-in {plug_in.get_name()} is already added")
            else:
                self.plug_ins.append(plug_in)
                found_names.add(plug_in.get_name())

        for plug_in in self.plug_ins:
            if isinstance(plug_in, AccelergyPlugIn):
                if not getattr(plug_in, "_accelergy_plug_in_initialized", False):
                    plug_in.__AccelergyPlugIn__init__()
                if not getattr(plug_in, "_accelergy_plug_in_initialized", False):
                    raise RuntimeError(
                        f"Plug-in {plug_in.get_name()} is not initialized. Please "
                        f"call super().__init__() in the plug-in's __init__ method."
                    )

    def set_ERT(self, ERT):
        self.ERT = ERT

    def set_ART(self, ART):
        self.ART = ART

    def set_action_counts(self, action_counts):
        self.action_counts = action_counts

    def set_energy_estimations(self, energy_estimations):
        self.energy_estimations = energy_estimations
