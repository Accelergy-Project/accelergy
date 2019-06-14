//
// Created by nelliewu on 5/27/19.
//

#include "mac.h"

mac::mac(const string& name, const bool is_last_level, const map<string, string> &hw_attrs)
: AccelergyComponent(name, is_last_level, hw_attrs,
                     vector<int>{0,0}, "MAC", vector<string>{"mac_random", "mac_gated"}){}

int mac::calc(int mult0, int mult1, int add) {
    int result;
    if (mult0 != 0 && mult1 !=0){
        result = mult0 * mult1 + add;
        ac_count("mac_random");
    }else{
        result = add;
        cout << "mac gated detected\n";
        ac_count("mac_gated");
    }
    return result;
}

