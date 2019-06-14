//
// Created by nelliewu on 5/28/19.
//

#ifndef SIM_MEMORY_H
#define SIM_MEMORY_H

#include "accelergyComponent.h"

class memory  : public AccelergyComponent{
public:
    memory(const string& name, bool is_last_level, const map<string, string> &hw_attrs);
    int read(int address);
    void write(int address, int data);
};


#endif //SIM_MEMORY_H
