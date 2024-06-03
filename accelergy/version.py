from accelergy.utils.utils import *

__version__ = "0.4"

VERSION_COMPATIBILITIES = (
    {  # Key: Parser Version, Value: List of compatible input file versions
        "0.1": [],  # Parser version 0.1 deprecated
        "0.2": ["0.2"],
        "0.3": ["0.2", "0.3"],
        "0.4": ["0.2", "0.3", "0.4"],
    }
)


INPUT_VERSION = None
PARSER_VERSION = None
MAX_VERSION = list(VERSION_COMPATIBILITIES.keys())[-1]
INPUT_FILE_VERSIONS = set()
PATH_TO_VERSION = {}
SUPPRESS_VERSION_ERRORS = True

VERSION_OUTDATED_MSG = f"""
Input file version is newer than Accelergy version. Please install the latest
Accelergy version or use v{__version__} input files.
"""


def version_compare(version1, version2):
    if version1 is None:
        return -1
    if version2 is None:
        return 1
    v1 = str(version1).split(".")
    v2 = str(version2).split(".")
    for i in range(max(len(v1), len(v2))):
        if i >= len(v1):
            return -1
        elif i >= len(v2):
            return 1
        elif int(v1[i]) > int(v2[i]):
            return 1
        elif int(v1[i]) < int(v2[i]):
            return -1
    return 0


def input_version_greater_or_equal(version):
    v = __version__ if INPUT_VERSION is None else INPUT_VERSION
    return version_compare(v, version) >= 0


def parser_version_greater_or_equal(version):
    return version_compare(PARSER_VERSION, version) >= 0


def versions_compatible(parser_version, file_version):
    if parser_version is None or file_version is None:
        return True
    parser_version, file_version = str(parser_version), str(file_version)
    return file_version in VERSION_COMPATIBILITIES.get(parser_version, [])


def check_input_parser_version(input_parser_version, input_file_type, input_file_path):
    global PARSER_VERSION
    global INPUT_VERSION
    version_error_func = ERROR_CLEAN_EXIT if not SUPPRESS_VERSION_ERRORS else WARN

    # Accelergy v0.3 can parser input files of version 0.2 and 0.3 (except ERT)
    if input_file_type is not "ERT":
        if input_file_type != "config":
            INPUT_VERSION = input_parser_version
            INPUT_FILE_VERSIONS.add(input_parser_version)
    PARSER_VERSION = __version__

    # Warn for outdated parser version
    if input_file_type == "config" and PARSER_VERSION != MAX_VERSION:
        WARN(VERSION_OUTDATED_MSG)

    # Error for incompatible parser + input versions
    if not versions_compatible(PARSER_VERSION, INPUT_VERSION):
        version_error_func(
            f"Input file {input_file_path} version {input_parser_version} is "
            f"incompatible with parser version {PARSER_VERSION}."
            f"\n Parser version {PARSER_VERSION} can only parse input files of "
            f"version {VERSION_COMPATIBILITIES.get(PARSER_VERSION, [])}. "
        )

    # Error for input files of multiple versions
    PATH_TO_VERSION[input_file_path] = input_parser_version
    if len(INPUT_FILE_VERSIONS) > 1:
        lowest_version = min(INPUT_FILE_VERSIONS)
        highest_version = max(INPUT_FILE_VERSIONS)
        # If the highest version is leq 0.4, then we just use the highest version
        if version_compare(highest_version, "0.4") <= 0:
            INPUT_FILE_VERSIONS.clear()
            INPUT_FILE_VERSIONS.add(highest_version)

        else:
            lowest_version_paths = [
                path
                for path, version in PATH_TO_VERSION.items()
                if version == lowest_version
            ]
            version_error_func(
                f"Input files of multiple versions detected. Input file versions are {INPUT_FILE_VERSIONS}. "
                f"\n Please use input files of the same version. Files with version {lowest_version} are: "
                + "\n".join(lowest_version_paths)
            )

    # Warn for outdated input files
    if str(input_parser_version) != str(MAX_VERSION):
        WARN(
            f"File {input_file_path} is outdated. File version is {input_parser_version}, "
            f"while the latest version is {MAX_VERSION}. "
            f"\n Please update the file to the latest version."
        )
