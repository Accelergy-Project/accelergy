//
// Created by nelliewu on 5/28/19.
//

#include "memory.h"
#include "accelergyComponent.h"

memory::memory(const string& name, const bool is_last_level, const map<string, string> &hw_attrs)
        : AccelergyComponent(name, is_last_level, hw_attrs,
                             vector<int>{0,0}, "SRAM", vector<string>{"read_random", "write_random"}){}


int memory::read(int address) {
      ac_count("read_random");
      cout<< _ac_name << " reading address: " << address << "\n";
      return random()%10;
}

void memory::write(int address, int data) {
    ac_count("write_random");
    cout<< _ac_name << " writing to address: " << address << "\n";
}