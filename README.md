# Accelergy infrastructure (version 0.2)

An infrastructure for architecture-level energy estimations of accelerator designs. Project website: http://accelergy.mit.edu

## Get started 
- Infrastructure tested on RedHat Linux6, Ubuntu
- python 3.6
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

```accelergy``` generates the appropriate outputs according to the available input files. 
``` 
# To run both ERT generator and energy calculator
cd examples/simple_v0.2/input
accelergy -o ../output/ *.yaml 

# To run just the ERT generator
accelergy -o ../otuput/ design.yaml

# To run just the energy calculator
accelergy -o ../output ../output/ERT.yaml action_counts.yaml
```

### Input files

  There are three types of input files:
  - architecture description (unique)
    ```yaml
    artchitecture_description:  # required top-key
      version: 0.2              # required version number
      subtree:                  # required architecture tree root
        ...
    ```
  - compound component class description (can be composed of multiple files)
    ```yaml
    compound_components: # required top-key
      version: 0.2       # required version number
      classes:           # required list identifier
        - name: ...      # various compound component classes specified as a list
        ...
    ```
  - action counts (can be composed of multiple files)
    ```yaml
    compound_components: # required top-key
      version: 0.2       # required version number
      subtree:           # required architecture tree root
        - name: ...      # various action counts specified as a list
        ...
    ```
  Accelergy parses the input files and decide what operations to perform:
  - Providing **all three types of inputs** will allow Accelergy to generate the ERTs for the components in the design, 
  and perform energy estimations using the workload-generated action counts.
  
  - Providing just the **architecture description** and **compound component class description** allows Accelergy to generate 
  the ERTs for the components in the design.
  
  - Providing the **generated ERTs** and the **action counts** allows Accelergy to directly generate energy estimations 
  if the components in the design.
  
  ### Input flags
   Accelergy accepts several optional flags:
   - ```-o``` : specifies the output directory. Default is current directory
   - ```-p``` : specified the precision of the caclulated ERTs and estimations. Default is 3.
   - ```--enable_flattened_arch ```: once set to 1, it allows Accelergy to output an architecture summary in the output 
   directory and check the validity of component names in the action counts file. 
   The flattened architecture includes all the interpreted attribute values and classes for all the components
   in the design. Default is 0.
   

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
    