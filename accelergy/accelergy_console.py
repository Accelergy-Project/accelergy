from accelergy.ERT_generator import EnergyReferenceTableGenerator
from accelergy.energy_calculator import EnergyCalculator

import argparse

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('design_path', type=str, help = 'path to input file design.yaml')
    parser.add_argument('action_counts_path', type=str, help = 'path to input file action_counts.yaml')
    parser.add_argument('-o', '--outdir', type=str, default='./', help = 'optional path to output directory')
    parser.add_argument('-p', '--precision', type=int, default='3', help= 'number of decimal points for energy values' )

    args = parser.parse_args()
    design_path = args.design_path
    action_counts_path = args.action_counts_path
    output_path = args.outdir
    precision = args.precision



    generator = EnergyReferenceTableGenerator()
    generator.generate_ERTs(design_path, output_path, precision)

    ert_path = output_path + '/' + 'ERT.yaml'
    estimator = EnergyCalculator()
    estimator.generate_estimations(action_counts_path, ert_path, output_path, precision)





