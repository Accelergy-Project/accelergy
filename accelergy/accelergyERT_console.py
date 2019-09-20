from accelergy.ERT_generator import EnergyReferenceTableGenerator

import argparse

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('design_path', type=str, help = 'path to input file design.yaml')
    parser.add_argument('-o', '--outdir', type=str, default='./', help = 'optional path to output directory')
    parser.add_argument('-p', '--precision', type=int, default='3', help= 'number of decimal points for energy values' )
    parser.add_argument('--enable_flattened_arch', type=int, default='0', help= 'enable Accelergy to show the flattened architecture interpretation')

    args = parser.parse_args()
    design_path = args.design_path
    output_path = args.outdir
    precision = args.precision
    flatten_arch_flag = args.enable_flattened_arch

    generator = EnergyReferenceTableGenerator()
    generator.generate_ERTs(design_path, output_path, precision, flatten_arch_flag)



