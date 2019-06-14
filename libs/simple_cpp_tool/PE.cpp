//
// Created by nelliewu on 5/27/19.
//

#include "PE.h"

PE::PE(const string& name, const int &width, const int &mac_n_pipe_stage, const int &mem_depth, const int& nbanks)
    :AccelergyComponent(name, false),
     _width(width),
    _mac_n_pipe_stage(mac_n_pipe_stage),
    _mem_depth(mem_depth),
    _mem_nbakns(nbanks){

    map<string, string> mac_attrs = {{"bit_width", to_string(_width)},
                                     {"n_pipe_stage", to_string(_mac_n_pipe_stage)}};

    PE_mac = new mac("PE_mac", true, mac_attrs);
    this->insertChild(PE_mac);

    map<string, string> spad_attrs = {{"width", to_string(_width)},
                                      {"depth", to_string(_mem_depth)},
                                      {"nbanks", to_string(_mem_nbakns)}   };
    PE_spad = new memory("PE_spad", true, spad_attrs);
    this->insertChild(PE_spad);



}

void PE::process_job(int op0_addr, int op1_addr, int offset) {
    cout << "--> PE start processing job\n";
    int op0 = PE_spad->read(op0_addr);  //mem read
    int op1 = PE_spad->read(op1_addr);  //mem read
    int result = PE_mac->calc(op0,op1,offset);  //mac1
    cout << "step 1 result: " << result << "\n";
    result = PE_mac->calc(op0, 0, offset );  //mac2
    cout << "step 2 result: " << result << "\n";
    PE_spad->write(op1_addr, result);
}