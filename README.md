# Accelergy infrastructure (version 0.2)

An infrastructure for architecture-level energy estimations of accelerator designs. Project website: http://accelergy.mit.edu

## Get started 
- Infrastructure tested on RedHat Linux6, WLS
- python 3.6
- PyYAML package 

## Install the package
```
   <pip_exec> install .
   # note:<pip_exec> is different for different python versions, e.g., pip3      
```
- Please make sure your python bin, e.g.,```~/.local/bin ```, is appropriately added to $PATH 
- Three new commands: ```accelergy, accelergyERT, accelergyCALC ```  should be available in your python bin 
- ```accelergy -h```, ```accelergyERT -h```, ```accelergyCALC -h``` show the help message for the commands

## Run an example evaluation

```accelergy``` runs both energy reference table (ERT) generator and energy calculator. Assuming at repo root directory:
``` 
cd examples/simple/input
accelergy -o ../output/ design.yaml action_counts.yaml 
```

```accelergyERT```  runs ERT generator only. Assuming at repo root directory:

```
cd examples/simple/input
accelergyERT -o ../output/ design.yaml
``` 

```accelergyCALC```  runs energy calculator only. Assuming at repo root directory:

```
cd examples/simple/input
accelergyCALC -o ../output/ ERT.yaml action_counts.yaml 
``` 


## File Structure
- accelergy : package source
- share: contains directories for default primitive component libraries and dummy estimation pug-ins
- examples: example designs and action counts for Accelergy to evaluate

## Documentation

### accelergy_config.yaml
   accelergy-config.yaml is the required config file for Accelergy to:
   - locate its estimator plug-ins
   - locate its primitive components
   
At the beginning of ```accelergy``` or ```accelergyERT``` run, Accelergy will automatically search for ```accelergy_config.yaml``` first at ```./``` and then at ```$HOME/.config/accelergy/``` the file will be loaded if found, otherwise, Accelergy will create a default 
   ```accelergy_config.yaml``` at ```$HOME/.config/accelergy/```, which points to the default estimator plug-in directory and primitive component library directory.

Users can create their own  ```accelergy_config.yaml``` at ```$HOME/.config/accelergy/``` or ```./```, or modify the default 
```accelergy_config.yaml``` created by Accelergy to specify their own root directories for estimator plug-ins
 and primitive component library. Accelergy does a recursive search from the specified root directories to locate 
 the estimation plug-ins and primitive component lib files.

Primitive component library files need be end with ```.lib.yaml``` for Accelergy to locate it. 
Estimation plug-in's API is described in *API for Estimation Plug-ins* section below. 

### Input files
Two input files are required for a complete run of Accelergy evaluation, 
detailed syntax examples are located in ```examples/```

- ```design.yaml```
- ```action_counts.yaml```

#### design.yaml
  There are two top-level keys in design.yaml, *architecture description* and *compound components*
- *architecture description*: hierarchically describes the design in terms of components. 
The architecture is represented as a tree structure, with internal nodes and leaf nodes.
Internal nodes are merely an internal level of representation,
not physical hardware instantiations. Leaf nodes are physical hardware instantiations, 
and therefore are components in the design. The component can either belong to a primitive component class or 
a compound component class. Architecture description should be generated using yaml format. 
Nodes at the same level are represented in a list format, each item in the list is dictionary format. 

- *compound components*: provides all the compound component classes that are needed by the design. A compound component class
provides the attributes, the subcomponents, the compound actions and corresponding arguments (if there are any).
Compound component classes are always two-level, top-level compound component and the lower-level sub-components,
which can primitive components (specified in Accelergy primitive library or user-defined primitive library) or compound component,
which needs to be specified in this file as another compound component class. 

#### action_counts.yaml
Action counts hierarchically record the run time behavior of the design running a specific workload. 
For each component in the design, the number of times each action has happened is recorded.
The component names in this file has to match the component names in architecture.yaml for Accelergy to find correspondence. 

### API for Estimation Plug-ins
- Users need to specify the root directory in config file in the format below. Accelergy does a recursive search to locate the estimator 
plug-ins according to the provided root directories
```
estimator_plug_ins:
  - root0
  - root1
```
  
- *.estimator.yaml* file needs to be specified for Accelergy to locate the estimator, and the file should have the following format
```
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
    