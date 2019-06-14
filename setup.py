from setuptools import setup

def readme():
      with open('README.md') as f:
            return f.read()

setup(
    name='accelergy',
      version='1.0',
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
      include_package_data = True,
      entry_points = {
        'console_scripts': ['accelergy=accelergy.accelergy_console:main',
                            'accelergyERT=accelergy.accelergyERT_console:main',
                            'accelergyCALC=accelergy.accelergyCALC_console:main'],
      },
      zip_safe = False,

    )
