from setuptools import setup, find_packages
import os

def readme():
      with open('README.md') as f:
            return f.read()

setup(
    name='accelergy',
      version='0.3',
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
      packages=['accelergy'],
      install_requires = ['pyYAML >= 1.1', 'yamlordereddictloader >= 0.4', 'pyfiglet'],
      python_requires = '>=3.6',
      data_files=[('share/accelergy/primitive_component_libs/',
                    ['share/primitive_component_libs/primitive_component.lib.yaml',
                     'share/primitive_component_libs/pim_primitive_component.lib.yaml',
                     'share/primitive_component_libs/soc_primitives.lib.yaml']),
                  ('share/accelergy/estimation_plug_ins/dummy_tables',
                    ['share/estimation_plug_ins/dummy_tables/dummy.estimator.yaml',
                     'share/estimation_plug_ins/dummy_tables/dummy_table.py'])
                  ],
      include_package_data = True,
      entry_points = {
        'console_scripts': ['accelergy=accelergy.accelergy_console:main',
                            'accelergyDefineArch=accelergy.accelergy_define_arch_console:main'],
      },
      zip_safe = False,

    )
