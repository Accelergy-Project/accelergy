from setuptools import setup
from setuptools.command.install_scripts import install_scripts
import subprocess
import os

class InstallCommand(install_scripts):
    """A custom install_scripts setup to install accelergy plug-ins too."""
    """This happens at the later stage after plug-in dir is created."""
    def run(self):
        print("Installing extra plugins.")
        try:
            tmp = subprocess.call([
                "bash",
                "install_plug-in.sh",
                "/".join(self.install_dir.split("/")[:-1])]) # take out the /bin part
        except:
            print("Extra plugin installation failed.")
        install_scripts.run(self)

def readme():
      with open('README.md') as f:
            return f.read()

setup(cmdclass={'install_scripts' : InstallCommand},
      name='accelergy',
      version='0.1',
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
      install_requires = ['pyYAML'],
      python_requires = '>=3.6',
      data_files=[('share/accelergy/primitive_component_libs/',
                    ['share/primitive_component_libs/primitive_component.lib.yaml']),
                  ('share/accelergy/estimation_plug_ins/dummy_tables',
                    ['share/estimation_plug_ins/dummy_tables/dummy.estimator.yaml',
                     'share/estimation_plug_ins/dummy_tables/dummy_table.py']),
                  ('share/accelergy/estimation_plug_ins/dummy_tables/data',
                    ['share/estimation_plug_ins/dummy_tables/data/counter.csv',
                     'share/estimation_plug_ins/dummy_tables/data/mac.csv',
                     'share/estimation_plug_ins/dummy_tables/data/SRAM.csv']),
                  ('share/accelergy/estimation_plug_ins/dummy_tables_w_interpolation',
                    ['share/estimation_plug_ins/dummy_tables_w_interpolation/dummy_interpolate.estimator.yaml',
                     'share/estimation_plug_ins/dummy_tables_w_interpolation/dummy_table_w_interpolation.py']),
                  ('share/accelergy/estimation_plug_ins/dummy_tables_w_interpolation/data',
                    ['share/estimation_plug_ins/dummy_tables_w_interpolation/data/counter.csv',
                     'share/estimation_plug_ins/dummy_tables_w_interpolation/data/mac.csv',
                     'share/estimation_plug_ins/dummy_tables_w_interpolation/data/SRAM.csv'])
                  ],
      include_package_data = True,
      entry_points = {
        'console_scripts': ['accelergy=accelergy.accelergy_console:main',
                            'accelergyERT=accelergy.accelergyERT_console:main',
                            'accelergyCALC=accelergy.accelergyCALC_console:main'],
      },
      zip_safe = False,

    )
