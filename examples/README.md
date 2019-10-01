### Examples Q&A:  
Q: How to run the simple example?
A: Everything is baked in to the design.yaml and action_counts.yaml using ```!include  or !includedir``` flags,
   so including those two files will be sufficient.
```
cd examples/simple_v0.2
accelergy *.yaml -o ../output --enable_flattened_arch 1
```

Q: How to run the hierarchy and eyeriss_like example?   
A: Note that there is no "!include" statements in the design file, so everything is scattered. Please include all files
```
cd examples/hierarchy_v0.2
accelergy *.yaml components/*.yaml -o ../output --enable_flattened_arch 1
```
 
Q: How do see the interactions between Accelergy and the plug-ins?
A: Turn on the ```-v``` flag will allow the requests and returned energy to be printed

Q: How do interpret the data in ```*.reference```?  
A: All data in ```*.reference``` files are generated using the default dummy plug-in, which returns 1 for all non-idle actions
   and returns 0 for all idle actions, regardless of the component class and attributes.