
#ifndef __ACCELERGYCOMPONENT_H__
#define __ACCELERGYCOMPONENT_H__

#include <fstream>
#include <iostream>
#include <stdio.h>
#include <list>
#include <vector>
#include <iterator>
#include <map>
#include <string>
#include <assert.h>
#include "yaml-cpp/yaml.h"

using namespace std;

class AccelergyComponent {
    // class members
protected:
    string _ac_name;         // name of the component
    bool _ac_is_last_level;  // if the component is the last level component
    string _ac_className; // class name of the component
    vector<string> _ac_actions; // list of action names related to the component
    vector<int> _ac_nArgs;
    vector<int *> _ac_argRanges;
    map<string, string> _ac_hwAttrs;  // map of hardware attributes related to the component
    map<string, int> _ac_actionMap;   // map of action name and action id, for the ease of using templates

    // a collection of tables that store the counter(s) for each action id
    // each table's number of entries depend on # of arguments and # of possible values for each argument
    map<int, int *> _ac_actionCounts;

    string _architecture_description_path;
    string _action_counts_path;

public:
    list<AccelergyComponent> _ac_children;


public:
    // constructor
    AccelergyComponent(const string &ac_name,
                       bool ac_is_last_level,
                       const map<string, string> &ac_hwAttrs = {},
                       const vector<int> &ac_nArgs = vector<int>{},
                       const string &ac_className = "",
                       const vector<string> &ac_actions = {},
                       const vector<int *> &ac_argRanges = {}) ;

    // getter functions
    map<int, int *> getActionCounts();
    vector<int *> &getArgRanges();
    string getName();
    bool getCompType();

    // insert a new child
    void insertChild(AccelergyComponent *child);
    YAML::Node registerComponent();   // write component description into architecture description
    YAML::Node registerActionCounts(); // write component action counts into action counts yaml
    void ac_count(string action_name, const vector<int>& argValues = {}, int delta = 1);

    // template function for incrementing correct action counts
    template<int actionIdx, int N>
    void accelergyInc(vector<int> &argValues, int delta) {
        // find the table that is related to the action idx
        int *actionCount = getActionCounts()[actionIdx];
        // if there is no argument, increment the first entry
        if (N == 0) {
            actionCount[0] += delta;
        }
            // if there is at least one argument,
            //     find the location in the table that needs to be incremented
        else {
            long int idx = 0;
            long int offset = 1;
            int *argRanges = getArgRanges()[actionIdx];
            for (int i = 0; i < N; i++) {
                int argValue = argValues[i];
                idx += argValue * offset;
                offset *= argRanges[i];
            }
            actionCount[idx] += delta;
        }
    }
};

// template function to increment action counts for each action for the component



#endif /*__ACCELERGYCOMPONENT_H__*/