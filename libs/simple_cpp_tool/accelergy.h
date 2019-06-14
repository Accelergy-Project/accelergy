#ifndef __ACCELERGY_H__
#define __ACCELERGY_H__ 

using namespace std;

#include "accelergyComponent.h" 

class Accelergy {

public:
    string ac_design_name;
    AccelergyComponent* ac_root;
    string architecture_description_path;
    string action_counts_path;

    explicit Accelergy(string& design_name, const string& out_dir = "output/");

    void checkOutputfiles(const string& output_dir);
    void add_top_level_component(AccelergyComponent* child);

    void register_design_architecture();
    YAML::Node register_component_definition(AccelergyComponent* component, YAML::Node topLevel);
    void register_design_action_counts();
    YAML::Node register_component_action_count(AccelergyComponent* component, YAML::Node topLevel);
};

#endif /* __ACCELERGY_H__ */















