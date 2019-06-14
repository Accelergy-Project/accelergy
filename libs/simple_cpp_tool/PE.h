//
// Created by nelliewu on 5/27/19.
//

#ifndef SIM_PE_H
#define SIM_PE_H

#include "mac.h"
#include "memory.h"
#include "accelergyComponent.h"

class PE : public AccelergyComponent {
private:
    int _width;
    int _mac_n_pipe_stage;
    int _mem_depth;
    int _mem_nbakns;

    mac *PE_mac;
    memory *PE_spad;

public:
    PE(const string& name, const int &bit_width, const int &mac_n_pipe_stage, const int &mem_depth, const int& n_banks = 1);

    void process_job(int op0_addr, int op1_addr, int offset);
};


#endif //SIM_PE_H
