### Examples Q&A:  
Q: How to run the examples?   
A: Please include all files in the input directory to generate both the ERT_generator and energy calculator.
```
cd examples/hierarchy_v0.2
accelergy *.yaml components/*.yaml -o ../output --enable_flattened_arch 1
```
 
Q: How do see the interactions between Accelergy and the plug-ins?  
A: Turn on the ```-v``` flag will allow the requests and returned energy to be printed

Q: How do interpret the data in ```*.reference```?  
A: All data in ```*.reference``` files are generated using the default dummy plug-in, which returns 1 for all non-idle actions
   and returns 0 for all idle actions, regardless of the component class and attributes.