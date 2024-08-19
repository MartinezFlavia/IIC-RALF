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
parser.add_argument('circuit_name', help='Name of the circuit')
parser.add_argument('-p', '--placement_type', choices=['rl', 'rps'], help='Type of placement (rl for reinforcement learning, rps for simulated annealing)', default = 'rl')

parser.add_argument('-w', '--PLAN_WIRES',  type=bool, help='activates the planner', default = main_routing.DEFAULT_PLAN_WIRES)
parser.add_argument('-n','--N_PLANNING_ITERATIONS', type=int,help='defines the number of planning iterations', default = main_routing.DEFAULT_N_PLANNING_ITERATIONS)
parser.add_argument('-g','--GCELL_LENGTH', help=' defines the width and height of a grid cell (150 is recommended)', default = main_routing.DEFAULT_GCELL_LENGTH)
parser.add_argument('-l','--LAYERS', help='for defining the usable layers', default = main_routing.DEFAULT_LAYERS)

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

print("-------------------Placement completed----------------")

# additional functions

print("------------------Opening Magic--------------")
main_place_circuit.main(args.circuit_name)
#add info about opening magic

#ROUTING
print("------------------Routing:-----------------")


main_routing.main(args.circuit_name, args.PLAN_WIRES, args.N_PLANNING_ITERATIONS, args.GCELL_LENGTH, args.LAYERS)

