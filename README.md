# Accelergy (v4: CiMLoop)
An infrastructure for architecture-level energy/area estimations of accelerator designs. Project website: http://accelergy.mit.edu

Examples: [https://github.com/Accelergy-Project/timeloop-accelergy-exercises](https://github.com/Accelergy-Project/timeloop-accelergy-exercises)

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg)](code_of_conduct.md)
[![Open Source Love png1](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](https://github.com/ellerbrock/open-source-badges/)
## Update v0.4 (CiMLoop)
- New plug-in interface
- New arithmetic parsing system
- New logging system
- Tests
- Bug fixes

## Update v0.3
- Addition of area reference table generation
- Updated command line flags
- The **ERT** and **energy_estimation** output format has been updated.
## Get started 
- Infrastructure tested on RedHat Linux, Ubuntu, MacOS

## Install the package
```
   <pip_exec> install .
   # note:<pip_exec> is different for different python versions, e.g., pip3      
```
- Please make sure your python bin, e.g.,```~/.local/bin ```, is appropriately added to $PATH 
- A new command: ```accelergy ```  should be available in your python bin 
- ```accelergy -h``` shows the help message for the command

## Run an example evaluation

#### Area and Energy Estimations
Accelergy is capable of generating energy and area estimations of various accelerator designs. The following example
command generates the energy and area estimation of the design and saves the outputs in the ```../output``` folder.
```
cd examples/hierarchy/input
accelergy -o ../output/ *.yaml components/*.yaml -v 1
```
 ### Input flags
   Accelergy accepts several optional flags:
   - ```-o or --output``` : specifies the output directory. Default is current directory
   - ```-p  or --precision``` : specifies the precision of the calculated ERTs and estimations. Default is 3.
   - ```-f or --output_files```: specifies a list of desired output files. Default is ```['all']```.
   Options include: flattened_arch, ERT, ERT_summary, ART, ART_summary, energy_estimation.
   - ```-v or --verbose```: once set to 1, it allows Accelergy to output the more detailed descriptions of the desired outputs.

### Input files

  There are three types of input files:
  - architecture description (unique)
    ```yaml
    artchitecture_description:  # required top-key
      version: 0.4              # required version number
      subtree:                  # required architecture tree root
        ...
    ```
  - compound component class description (can be composed of multiple files)
    ```yaml
    compound_components: # required top-key
      version: 0.4       # required version number
      classes:           # required list identifier
        - name: ...      # various compound component classes specified as a list
        ...
    ```
  - action counts (can be composed of multiple files)
    ```yaml
    compound_components: # required top-key
      version: 0.4       # required version number
      subtree:           # required architecture tree root
        - name: ...      # various action counts specified as a list
        ...
    ```
  Accelergy parses the input files and decide what operations to perform:
  - Providing **all three types of inputs** will allow Accelergy to generate the ERTs/ARTs for the components in the design, 
  and perform energy estimations using the workload-generated action counts.
  
  - Providing just the **architecture description** and **compound component class description** allows Accelergy to generate 
  the ERTs/ARTs for the components in the design.
  
  - Providing the **generated ERTs** and the **action counts** allows Accelergy to directly generate energy estimations 
  if the components in the design.
  
 
  
## File Structure
- accelergy : package source
- share: contains directories for default primitive component libraries and dummy estimation pug-ins
- examples: example designs and action counts for Accelergy to evaluate
- test: tests

## Documentation

### accelergy_config.yaml
   accelergy-config.yaml is the required config file for Accelergy to:
   - locate its estimator plug-ins
   - locate its primitive components
   
At the beginning of ```accelergy``` run, Accelergy will automatically search for ```accelergy_config.yaml``` first at ```./``` and then at ```$HOME/.config/accelergy/``` the file will be loaded if found, otherwise, Accelergy will create a default 
   ```accelergy_config.yaml``` at ```$HOME/.config/accelergy/```, which points to the root directories of the default estimator plug-in directory and primitive component library directory.
   
Primitive component library files need be end with ```.lib.yaml``` for Accelergy to locate it. 
find correspondence. 

### API for Estimation Plug-ins
See the creating-plug-ins tutorial in the [exercises repository](https://github.com/Accelergy-Project/timeloop-accelergy-exercises/tree/master).


## Citation
Please cite the following:

- Y. N. Wu, J. S. Emer, and V. Sze, “Accelergy: An architecture-level energy estimation methodology for accelerator designs,” in 2019 IEEE/ACM International Conference on Computer-Aided Design (ICCAD), 2019, pp. 1–8.
- T. Andrulis, J. S. Emer, and V. Sze, “CiMLoop: A flexible, accurate, and fast compute-in-memory modeling tool,” in 2024 IEEE International Symposium on Performance Analysis of Systems and Software (ISPASS), 2024.

Or use the following BibTeX:

```BibTeX
@inproceedings{accelergy,
  author      = {Wu, Yannan Nellie and Emer, Joel S and Sze, Vivienne},
  booktitle   = {2019 IEEE/ACM International Conference on Computer-Aided Design (ICCAD)},
  title       = {Accelergy: An architecture-level energy estimation methodology for accelerator designs},
  year        = {2019},
}
@inproceedings{cimloop,
  author      = {Andrulis, Tanner and Emer, Joel S. and Sze, Vivienne},
  booktitle   = {2024 IEEE International Symposium on Performance Analysis of Systems and Software (ISPASS)}, 
  title       = {{CiMLoop}: A Flexible, Accurate, and Fast Compute-In-Memory Modeling Tool}, 
  year        = {2024},
}
```
