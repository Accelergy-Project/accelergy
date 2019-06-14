#include "accelergy.h"

Accelergy::Accelergy(string& design_name, const string& out_dir) {
    ac_design_name = design_name;
    ac_root = new AccelergyComponent(ac_design_name, false);
    checkOutputfiles(out_dir);
    architecture_description_path = out_dir + "architecture_description.yaml";
    action_counts_path = out_dir + "action_counts.yaml";
}


// remove the old results
void Accelergy::checkOutputfiles(const string& output_dir) {
    ifstream arch_check_file((output_dir + "architecture_description.yaml").c_str());
    ifstream counts_check_file((output_dir + "action_counts.yaml").c_str());
    if (arch_check_file.good()) {
        remove((output_dir + "architecture_description.yaml").c_str());
    }
    if (counts_check_file.good()) {
        remove((output_dir + "action_counts.yaml").c_str());
    }
}

void Accelergy::add_top_level_component(AccelergyComponent* child) {
     ac_root->insertChild(child);

}

void Accelergy::register_design_architecture(){
     YAML::Node design_architecture;
     design_architecture[ac_design_name] = register_component_definition(ac_root, design_architecture);
     ofstream fout;
     fout.open(architecture_description_path, std::fstream::app);  //assumes serial writes to the action_counts file
     fout << design_architecture << "\n";
     fout.close();

}

YAML::Node Accelergy::register_component_definition(AccelergyComponent* component, YAML::Node topLevel){
    for(list<AccelergyComponent>::iterator it = component->_ac_children.begin(); it != component->_ac_children.end(); ++it){
        topLevel[it->getName()] = it -> registerComponent();
        register_component_definition(&(*it), topLevel[it->getName()]);
    }
    return topLevel;
}

void Accelergy::register_design_action_counts(){
    YAML::Node design_action_counts;
    ofstream fout;
    design_action_counts[ac_design_name] = register_component_action_count(ac_root, design_action_counts);
    fout.open(action_counts_path, std::fstream::app);  //assumes serial writes to the action_counts file
    fout << design_action_counts << "\n";
    fout.close();
}

YAML::Node Accelergy::register_component_action_count(AccelergyComponent* component, YAML::Node topLevel){
    for(list<AccelergyComponent>::iterator it = component->_ac_children.begin(); it != component->_ac_children.end(); ++it){
        if (it->getCompType()){
            topLevel[it->getName()] = it -> registerActionCounts();
            register_component_action_count(&(*it), topLevel[it->getName()]);
        }else{
            register_component_action_count(&(*it), topLevel[it->getName()]);
        }
    }
    return topLevel;
}
