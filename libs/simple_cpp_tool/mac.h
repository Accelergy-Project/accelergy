//
// Created by nelliewu on 5/27/19.
//

#ifndef SIM_MAC_H
#define SIM_MAC_H

#include "accelergyComponent.h"

class mac : public AccelergyComponent{

public:
    mac(const string& name, bool is_last_level, const map<string, string> &hw_attrs);
    int calc(int mult0, int mult1, int add);

};

#endif //SIM_MAC_H
