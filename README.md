# Accelergy infrastructure (version 0.3)

An infrastructure for architecture-level energy/area estimations of accelerator designs. Project website: http://accelergy.mit.edu


[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg)](code_of_conduct.md)
[![Open Source Love png1](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](https://github.com/ellerbrock/open-source-badges/)
## Major updates from V0.2
- Addition of area reference table generation
- Updated command line flags
- The **ERT** and **energy_estimation** output format has been updated.
## Get started 
- Infrastructure tested on RedHat Linux, Ubuntu, MacOS
- Required packages
  - Python >= 3.6
  - PyYAML >= 1.1 (dependency automatically handled at installation)
  - yamlordereddictloader >= 0.4 (dependency automatically handled at installation)

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
      version: 0.3              # required version number
      subtree:                  # required architecture tree root
        ...
    ```
  - compound component class description (can be composed of multiple files)
    ```yaml
    compound_components: # required top-key
      version: 0.3       # required version number
      classes:           # required list identifier
        - name: ...      # various compound component classes specified as a list
        ...
    ```
  - action counts (can be composed of multiple files)
    ```yaml
    compound_components: # required top-key
      version: 0.3       # required version number
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
- Users need to specify the root directory in config file in the format below. Accelergy does a recursive search to locate the estimator 
plug-ins according to the provided root directories
```
estimator_plug_ins:
  - root0
  - root1
```
  
- *.estimator.yaml* file needs to be specified for Accelergy to locate the estimator, and the file should have the following format
```yaml
  version: <version_number> 
  estimator_plug_in_name:
    module:  <wrapper file name>
    class:   <class to be imported>
    parameter: <initialization values>  #optional, only specified if the estimator plug-in needs input for __init__()
    
```

- A python module is required to be present in the same folder as the *.estimator.yaml* file
    - The python file should contain a class as specified in *.estimator.yaml*
    - There are two required class functions, i.e., the interface function calls. Accelergy specifically calls
    these two functions to check if the estimator plug-in can be used for a specific primitive component
        - ``` primitive_action_supported(self, interface) ```
            - parameters: ```interface``` is a dictionary that contains the following four keys:
                - class_name, type string
                - attributes, type dictionary {attribute_name: attribute_value}
                - action_name, type string
                - arguments, type dictionary {argument_name: argument_value} 
                    - ```None``` if the action does not need arguments
            - return: integer accuracy if supported (0 is not supported)
                
        - ```estimate_energy(self, interface) ```
            - parameters: same interface
            - return: the energy/action value
    - Accelergy is unaware of the other functions that are implemented in this module
    