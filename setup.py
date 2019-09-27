from setuptools import setup, find_packages
import os

def readme():
      with open('README.md') as f:
            return f.read()

setup(
    name='accelergy',
      version='0.2',
      description='Accelergy Estimation Framework',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
      ],
      keywords='accelerator hardware energy estimation',
      author='Yannan Wu',
      author_email='nelliewu@mit.edu',
      license='MIT',
      packages=['accelergy', 'accelergy.v01_functions', 'accelergy.v02_functions'],
      install_requires = ['pyYAML >= 1.1', 'yamlordereddictloader >= 0.4'],
      python_requires = '>=3.6',
      data_files=[('share/accelergy/primitive_component_libs/',
                    ['share/primitive_component_libs/primitive_component.lib.yaml']),
                  ('share/accelergy/estimation_plug_ins/dummy_tables',
                    ['share/estimation_plug_ins/dummy_tables/dummy.estimator.yaml',
                     'share/estimation_plug_ins/dummy_tables/dummy_table.py']),
                  ('share/accelergy/estimation_plug_ins/dummy_tables/data',
                    ['share/estimation_plug_ins/dummy_tables/data/counter.csv',
                     'share/estimation_plug_ins/dummy_tables/data/mac.csv',
                     'share/estimation_plug_ins/dummy_tables/data/SRAM.csv'])
                  ],
      include_package_data = True,
      entry_points = {
        'console_scripts': ['accelergy=accelergy.accelergy_console:main'],
      },
      zip_safe = False,

    )
