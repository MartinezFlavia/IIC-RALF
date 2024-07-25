#!/usr/bin/env python3
# ========================================================================
#
#   Script to generate the placement of a circuit, by using reinforcement learning.
#
# SPDX-FileCopyrightText: 2023 Jakob Ratschenberger
# Johannes Kepler University, Institute for Integrated Circuits
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# SPDX-License-Identifier: Apache-2.0
# ========================================================================

import sys
import faulthandler
faulthandler.enable()

from SchematicCapture.utils import setup_circuit, include_primitives_hierarchical
from Magic.utils import instantiate_circuit, add_cells
from Environment.utils import do_bottom_up_placement
from SchematicCapture.RString import include_RStrings_hierarchical
from Magic.MagicDie import MagicDie
from Magic.Magic import Magic
import pickle

import logging
from logging.handlers import RotatingFileHandler

#########################################################################

# Default values for global variables
DEFAULT_CIRCUIT_NAME = "DiffAmp"                                # Name of the top-circuit
DEFAULT_CIRCUIT_FILE = f"Circuits/Examples/{DEFAULT_CIRCUIT_NAME}.spice"        # Input spice-netlist
DEFAULT_NET_RULES_FILE = f"NetRules/net_rules_{DEFAULT_CIRCUIT_NAME}.json"      # Net-rules definition file
N_PLACEMENTS = 1000                                             # Number of trial placements per circuit/subcircuit

USE_LOGGER = False                  # If True, debug information will be logged under "Logs/{CIRCUIT_NAME}_placement.log".
INSTANTIATE_CELLS_IN_MAGIC = True   # If True, the devices cell-view will be instantiated in Magic
N_PLACEMENTS_PER_ROLLOUT = 100      # Number of trial placements per RL - rollout
DEF_FILE = None                     # Def file of the circuit
SHOW_STATS = True                   # Show statistics of the placement

#########################################################################

def main():

    print("Reinforcement learning based placement:")

    if USE_LOGGER:
        # Setup a logger
        logHandler = RotatingFileHandler(filename=f"Logs/{DEFAULT_CIRCUIT_NAME}_placement.log", mode='w', maxBytes=100e3, backupCount=1, encoding='utf-8')
        logHandler.setLevel(logging.DEBUG)
        logging.basicConfig(handlers=[logHandler], level=logging.DEBUG, format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s")
    
    # Get user input or use default values
    if len(sys.argv) <= 1:
        circuit_file_name = input(f"Enter the circuit file name (default: {DEFAULT_CIRCUIT_NAME}): ") or DEFAULT_CIRCUIT_NAME
    else:
        circuit_file_name = sys.argv[1]
    circuit_file = f"Circuits/Examples/{circuit_file_name}.spice"
    circuit_name = input(f"Enter the circuit name (default: {DEFAULT_CIRCUIT_NAME}): ") or DEFAULT_CIRCUIT_NAME
    net_rules_file_name = input(f"Enter the net rules file name (default: net_rules_{DEFAULT_CIRCUIT_NAME}): ") or f"net_rules_{DEFAULT_CIRCUIT_NAME}"
    net_rules_file = f"NetRules/{net_rules_file_name}.json"

    print("Setting up the circuit...")
    # Set up the process to communicate with magic
    M = Magic(None)
    # Set up the circuit
    C = setup_circuit(circuit_file, M, circuit_name, [], net_rules_file=net_rules_file)
    print(f"Circuit setup completed: {C}")
    M.set_circuit(C)

    print("Including primitive compositions into the circuit...")
    # Include primitive compositions into the circuit
    include_primitives_hierarchical(C)
    include_RStrings_hierarchical(C)
    print("Primitive compositions included.")

    # Instantiate the circuit cells in magic
    if INSTANTIATE_CELLS_IN_MAGIC:
        print("Instantiating the circuit cells in Magic...")
        instantiate_circuit(C, M, "Magic/Devices")
        print("Circuit cells instantiated in Magic.")

    print("Adding cells to the devices...")
    # Add the cells to the devices
    add_cells(C, M, "Magic/Devices")
    print("Cells added to the devices.")

    print("Defining a die for the circuit...")
    # Define a die for the circuit
    die = MagicDie(circuit=C, def_file=DEF_FILE)
    print("Die defined.")

    print("Starting the placement by training a RL-agent...")
    # Do the placement by training a RL-agent
    do_bottom_up_placement(C, N_PLACEMENTS, N_PLACEMENTS_PER_ROLLOUT, use_weights=False, show_stats=SHOW_STATS)
    print("Placement completed.")

    print("Saving the placed circuit...")
    # Save the placed circuit
    file = open(f"PlacementCircuits/{circuit_name}_placement.pkl", 'wb')
    pickle.dump(die, file)
    file.close()
    print("Placed circuit saved.")
    

if __name__ == '__main__':
    main()
