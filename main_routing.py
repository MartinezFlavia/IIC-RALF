# ========================================================================
#
# Script to route a already placed circuit.
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

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from SchematicCapture.Circuit import Circuit
    from Magic.MagicDie import MagicDie 

import faulthandler
faulthandler.enable()

import pickle
from Routing_v2.Obstacles import DieObstacles
from Routing_v2.utils import route

import time
import matplotlib.pyplot as plt

from PDK.PDK import global_pdk

#########################################################################

DEFAULT_CIRCUIT_NAME = "DiffAmp"            #Name of the circuit

DEFAULT_PLAN_WIRES = True                   #If True, before detail-routing, wire-planning (global-routing) will be performed
DEFAULT_N_PLANNING_ITERATIONS = 15          #Number of wire-planning iterations
DEFAULT_GCELL_LENGTH = 150                  #Length of a wire-planning cell (in units of lambda)
DEFAULT_LAYERS = ['m1','m2','m3','m4']      #Layers which will be used for wire-planning

SHOW_STATS = True                    #If True, statistics of the routing will be printed
DESTINATION_PATH = 'Magic/Routing/'  #Destination path of the routing file
PLOT_RESULT = False                  #If True, the result will be plotted
LOG_WIREPLAN = False                 #If True, the stats of the wire-planning iterations will be logged to a csv file

#########################################################################
def main(CIRCUIT_NAME, PLAN_WIRES, N_PLANNING_ITERATIONS, GCELL_LENGTH, LAYERS):

    I
    #load the placed circuit 
    if CIRCUIT_NAME == None:    
        file = open(f"PlacementCircuits/{DEFAULT_CIRCUIT_NAME}_placement.pkl", 'rb')
    else:
        file = open(f"PlacementCircuits/{CIRCUIT_NAME}_placement.pkl", 'rb')

    die : MagicDie
    die = pickle.load(file)
    file.close()

    #setup obstacles from the die
    die_obstacles = DieObstacles(die)

    #get the placed circuit
    circuit = die.circuit

    #setup a axis for plotting
    if PLOT_RESULT:
        fig, ax = plt.subplots(1)
        ax.set_aspect('equal')
        ax.plot()
        cm = plt.get_cmap('Set1')
        for layer in global_pdk.metal_layers.values():
            color = cm(hash(layer)%9)
            ax.plot([], color=color, label=str(layer), linewidth=10, alpha=0.5)
        fig.legend(loc='right')
    else:
        ax = None

    start = time.time()
    #route the circuit

    if PLAN_WIRES == None and CIRCUIT_NAME== None and GCELL_LENGTH ==None and LAYERS == None:
        route(circuit=circuit, routing_name=DEFAULT_CIRCUIT_NAME, plan_wires=DEFAULT_PLAN_WIRES, 
            planning_iterations=N_PLANNING_ITERATIONS, gcell_length=DEFAULT_GCELL_LENGTH, use_layers=DEFAULT_LAYERS,
            destination_path=DESTINATION_PATH, show_stats=SHOW_STATS, ax=ax, log_wireplan=LOG_WIREPLAN)
    else:
        route(circuit=circuit, routing_name=CIRCUIT_NAME, plan_wires=PLAN_WIRES, 
            planning_iterations=N_PLANNING_ITERATIONS, gcell_length=GCELL_LENGTH, use_layers=LAYERS,
            destination_path=DESTINATION_PATH, show_stats=SHOW_STATS, ax=ax, log_wireplan=LOG_WIREPLAN)
        
    print(f"Took {round((time.time()-start)*1e3,2)}ms")

    if PLOT_RESULT:
        plt.show()

if __name__ == '__main__':
    main(None, None, None, None, None)