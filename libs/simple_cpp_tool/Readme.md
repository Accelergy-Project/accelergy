A very priliminary attempt to develop c++ code base for generating accelergy related input yaml files

cmake should work with cmake verison > 3.14

if cmake does not work, please use the following command for the current version of the code

```
g++ -o simple_sim accelergy.cpp accelergyComponent.cpp mac.cpp PE.cpp memory.cpp main.cpp -L libs -lyaml-cpp -I include -std=c++11
./simple_sim
```

to view the generated yaml files:

```cd output/```