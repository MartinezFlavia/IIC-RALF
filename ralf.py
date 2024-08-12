#!/usr/bin/env python3

# ========================================================================
#
#  Top level wrapper for RALF program
# ========================================================================

import argparse
import main_RL_placement
import main_RP_placement
import main_place_circuit
import main_routing

#PDK setup
#PDKPATH = '/path'
#os.environ['PDKPATH'] = PDKPATH

# Define the argument parser
parser = argparse.ArgumentParser(description='Circuit placement program')
parser.add_argument('placement_type', choices=['rl', 'rps'], help='Type of placement (rl for reinforcement learning, rps for simulated annealing)')
parser.add_argument('circuit_name', help='Name of the circuit')

# Parse the arguments
args = parser.parse_args()

# Call the appropriate placement function
if args.placement_type == 'rl':
    main_RL_placement.main(args.circuit_name)
elif args.placement_type == 'rps':
    main_RP_placement.main(args.circuit_name)
else:
    print("Error: Invalid placement type. Must be 'rl' or 'rps'")
    exit(1)  # Exit the script with an error code

print("-------------------placement completed----------------")

# additional functions
main_place_circuit.main(args.circuit_name)


