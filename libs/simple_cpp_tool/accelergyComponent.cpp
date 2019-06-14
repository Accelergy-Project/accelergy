#include "accelergyComponent.h"
#include "accelergy.h"

static bool output_dir_setup = 0; //flag to show whether the old results have been cleaned up

// constructor
AccelergyComponent::AccelergyComponent(const string &ac_name,
                                       const bool ac_is_last_level,
                                       const map<string, string> &ac_hwAttrs,
                                       const vector<int> &ac_nArgs,
                                       const string &ac_className,
                                       const vector<string> &ac_actions,
                                       const vector<int *> &ac_argRanges) :

                                       _ac_name(ac_name),
                                       _ac_is_last_level(ac_is_last_level),
                                       _ac_className(ac_className),
                                       _ac_actions(ac_actions),
                                       _ac_nArgs(ac_nArgs),
                                       _ac_argRanges(ac_argRanges),
                                       _ac_hwAttrs(ac_hwAttrs){

    // initialize the parent and child as empty on instantiation
    _ac_children = list<AccelergyComponent>{};

    // only if this component is a last level component, does it have actions
    if (_ac_is_last_level) {

        int actionIdx = 0;
        int actionNumArgs = 0;
        int argRange = 0;

        for (vector<string>::const_iterator it = _ac_actions.begin(); it != _ac_actions.end(); it++) {
            _ac_actionMap[*it] = actionIdx;
            actionNumArgs = _ac_nArgs[actionIdx];

            if (actionNumArgs == 0) {
                _ac_actionCounts[actionIdx] = new int[1];
            } else {
                int total_entries = 0;
                for (int argIdx = 0; argIdx < actionNumArgs; argIdx++) {
                    argRange = ac_argRanges[actionIdx][argIdx];
                    total_entries += argRange;
                }
                _ac_actionCounts[actionIdx] = new int[total_entries];
            }
            actionIdx++;
        }


    }
}


// write the component definition to the artchitecture description file
YAML::Node AccelergyComponent::registerComponent() {
    YAML::Node component_definition;
    component_definition = {};
    if(_ac_is_last_level){
        component_definition["class"] = _ac_className;
        component_definition["hardware_attributes"] = _ac_hwAttrs;
    }

    return component_definition;
}


map<int, int *> AccelergyComponent::getActionCounts() { return _ac_actionCounts; }

vector<int *> & AccelergyComponent::getArgRanges() { return _ac_argRanges; }

string AccelergyComponent::getName() {return _ac_name;}

bool AccelergyComponent::getCompType() {return _ac_is_last_level;}

void AccelergyComponent::insertChild(AccelergyComponent *child){_ac_children.push_back(*child);}



void AccelergyComponent::ac_count(string action_name, const vector<int>& argValues , int delta) {
    assert(_ac_is_last_level);
    int action_idx = _ac_actionMap[action_name], N = _ac_nArgs[action_idx];
    int *actionCount = _ac_actionCounts[action_idx];
    // if there is no argument, increment the first entry
    if (N == 0) {
        actionCount[0] += delta;
    }
        // if there is at least one argument,
        //     find the location in the table that needs to be incremented
    else {
        long int idx = 0, offset = 1;
        int *argRanges = getArgRanges()[action_idx];
        for (int i = 0; i < N; i++) {
            int argValue = argValues[i];
            idx += argValue * offset;
            offset *= argRanges[i];
        }
        actionCount[idx] += delta;
    }
}

// write the action counts to the action count yaml file
YAML::Node AccelergyComponent::registerActionCounts() {
    YAML::Node component_action_counts;
    for (map<int, int *>::iterator it = _ac_actionCounts.begin(); it != _ac_actionCounts.end(); ++it) {
        int action_idx = it->first;
        string action_name = _ac_actions[action_idx];
        int action_args = _ac_nArgs[action_idx];
        if (action_args == 0) { component_action_counts[action_name]["count"] = it->second[0]; }
        else {
            long int length;
            length = sizeof(_ac_actionCounts[action_idx]) / sizeof(_ac_actionCounts[action_idx][0]);
            for (long int entry_idx = 0; entry_idx < length; entry_idx++) {
                if (_ac_actionCounts[action_idx][entry_idx] != 0) {
                    long int offset = 1;
                    list<int> arg_lst;
                    for (int arg_idx = 0; arg_idx < _ac_nArgs[action_idx] - 1; arg_idx++) {
                        offset *= _ac_argRanges[action_idx][arg_idx];
                        arg_lst.push_back(entry_idx % offset);
                    }
                    arg_lst.push_back(entry_idx / offset);
                    component_action_counts[action_name]["count"] = _ac_actionCounts[action_idx][entry_idx];
                    component_action_counts[action_name]["arguments"] = arg_lst;
                }
            }
        }
        //cout << action_name << ':' << component_action_counts[_ac_name][action_name]["count"]  << "\n";
    }
    return component_action_counts;
}

