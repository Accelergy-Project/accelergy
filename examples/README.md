### Examples Q&A:  
Q: How to run the examples?   
A: Please include all files in the input directory to generate both the ERT_generator and energy calculator.
```
cd examples/hierarchy
accelergy input/*.yaml input/components/*.yaml -o ../output -v 1
```

Q: How to specify what outputs I want to generate?  
A: use the flag ```-f ``` to list the output files you want to generate 
(options: ERT, ART, ERT_summary, ART_summary, energy_estimation, flattened_arch)


Q: How do see the detailed primitive energy/area estimations from the plug-ins?  
A: Turn on the ```-v``` flag will allow the detailes estimations to be summarized in the ERT/ART_summary_verbose files

Q: How do interpret the data in ```reference```?  
A: All data in ```reference``` files are generated using the default dummy plug-in, which returns 1 for all non-idle actions
   and returns 0 for all idle actions, regardless of the component class and attributes.