# -*- coding: utf-8 -*-

from yaml import load

filename = 'estimation.yaml'
result = load(open(filename))['energy_estimation']['components']

#
num_entries = 4
curr_entry  = 0
idx = 0
skip = 0
PE_energy = [0*168 for i in range(168)]
for item in result:

    trans = item.split('.')[1].replace('[', '').replace(']', '')
    PE_idx = int(trans[2:])
    PE_energy[PE_idx] += result[item]
    curr_entry += 1
    if curr_entry == num_entries:
        idx += 1
        curr_entry = 0
        if idx == 168:
            break


# PE_energy.sort(reverse=1)
s = 0
for entry in PE_energy:
    print(entry)
    s += entry
print('Active PEs Total Energy is:', s)

##############################################################################
# num_entries = 1
# curr_entry  = 0
# idx = 0
# PE_energy = [0*168 for i in range(168)]
# for item in result:
#    if 'weights_sp' in item:
#        trans = item.split('.')[1].replace('[', '').replace(']', '')
#        PE_idx = int(trans[2:])
#
#        PE_energy[PE_idx] += result[item]
#        curr_entry += 1
#
#        if curr_entry == num_entries:
# #            print(item, PE_energy[idx])
#            idx += 1
#            curr_entry = 0
#            if idx == 168:
#                break
# for entry in PE_energy:
#    print(entry)
#
#
#num_entries = 2
#curr_entry  = 0
#idx = 0
#PE_energy = [0*168 for i in range(168)]
#for item in result:
#    if 'ifmap_sp' in item or 'zero_sp' in item:
#
#        trans = item.split('.')[1][2:].replace('[', '')
#        trans = trans.replace(']', ',')
#        PE_idx = int(trans.split(',')[0]) * 14 + int(trans.split(',')[1])
#
#        PE_energy[PE_idx] += result[item]
#        curr_entry += 1
#
#        if curr_entry == num_entries:
##            print(item, PE_energy[idx])
#            idx += 1
#            curr_entry = 0
#            if idx == 168:
#                break
#for entry in PE_energy:
#    print(entry)
#


    
    
    
    
    
    
