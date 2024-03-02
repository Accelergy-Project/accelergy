from setuptools import setup, find_packages
import os


def readme():
    with open("README.md") as f:
        return f.read()


setup(
    name="accelergy",
    version="0.4",
    description="Accelergy Estimation Framework",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
    keywords="accelerator hardware energy estimation",
    author="Yannan Wu",
    author_email="nelliewu@mit.edu",
    license="MIT",
    packages=["accelergy"],
    install_requires=[
        "pyYAML >= 1.1",
        "pyfiglet",
        "ruamel.yaml >= 0.17.20",
        "deepdiff >= 6.2.3",
        "Jinja2 >= 3.1.3",
    ],
    python_requires=">=3.8",
    data_files=[
        ("share/accelergy/primitive_component_libs", []),
        (
            "share/accelergy/estimation_plug_ins/dummy_tables",
            [
                "share/estimation_plug_ins/dummy_tables/dummy.estimator.yaml",
                "share/estimation_plug_ins/dummy_tables/dummy_table.py",
            ],
        ),
    ],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "accelergy=accelergy.accelergy_console:main",
            "accelergyDefineArch=accelergy.accelergy_define_arch_console:main",
        ],
    },
    zip_safe=False,
)
