# ========================================================================
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
    

from Magic.Magic import Magic
from Magic.MagicParser import MagicParser
from Magic.Cell import Cell

from SchematicCapture.Circuit import Circuit, SubCircuit
from SchematicCapture.utils import get_top_down_topology, get_bottom_up_topology
from SchematicCapture.Devices import SubDevice

import copy
import os
import shutil
import sys
import logging

logger = logging.getLogger(__name__)

def instantiate_circuit(Circuit : Circuit, mag : Magic, path='Magic/Devices'):
    """Instantiate the devices of the given circuit, and all its possible
     sub-circuits in magic.

    Args:
        Circuit (Circuit): Circuit whose cell-view shall be generated.
        path (str, optional): Path where the resulting files, will be saved. Defaults to 'Magic/Devices'.
                            The files will be stored under:
                                <working_dir>/<path>
    """
    logger.info(f"Instantiating {Circuit} in magic.")

    #get the topology of the circuit
    topology = get_top_down_topology(Circuit)
    topology.sort(key=lambda x: x[0])

    logger.debug(f"Instantiation topology: {topology}")

    #make the Devices folder if it doesn't exist
    if not os.path.exists(path):
        os.makedirs(path)

    # Find the absolute path to "path" and move to it in the layout editor
    # Then remove any existing layout files in that directory.

    cwdpath = os.getcwd()
    abspath = os.path.join(cwdpath, path)
    if mag:
        mag.magic_command('cd ' + abspath)
        mag.magic_command('foreach fname [glob *.mag] {file delete $fname}')

    #for each circuit instantiate the devices
    for (t, c) in topology:
        print('Diagnostic:  instantiating devices.')
        instantiate_devices(c, mag, path, del_path=False)
        logger.debug(f"Instantiated devices of {c} at topological layer {t}.")

def instantiate_devices(Circuit : Circuit, mag : Magic, path = 'Magic/Devices', del_path = True):
    """Instantiate the devices of a circuit. (Without the devices of possible sub-circuits.)

    Args:
        Circuit (Circuit): Circuit which shall be instantiated in magic.
        mag (Magic): Process for sending and receiving magic commands and responses
        path (str, optional): Path where the resulting files, will be saved. Defaults to 'Magic/Devices'.
                            The files will be stored under:
                                <working_dir>/<path>
        del_path (bool, optional): If the content at <path> shall be deleted, before the instantiation. Defaults to True.
    """
    logger.info(f"Instantiating devices of {Circuit} in magic. Devices-path: {path}")
    
    #get the device generation commands
    lines = mag.gen_devices()

    #if devices folder exists delete it
    # NOTE:  This is *highly* dangerous;  try setting path to your home directory. . .
    # Instead, just remove .mag files from the path.
    if os.path.exists(path) and del_path:
        shutil.rmtree(path)

    #make the devices folder
    if not os.path.exists(path):
        os.makedirs(path)

    # Test:  Apply commands directly to the running magic process

    # #write a tcl script to generate the devices
    # file = open(path+'/init_devs.tcl', 'w')
    # for l in lines:
    #     file.write(l+'\n')
    # file.close()

    mag.magic_command(lines)

    # #let magic generate the devices
    # # check if the variable PDKPATH is set
    # if "PDKPATH" in os.environ:
    #     #save the actual directory
    #     act_dir = os.getcwd()
    #     os.chdir(path)
    #     os.system('magic -dnull -noconsole -rcfile ${PDKPATH}/libs.tech/magic/sky130A.magicrc "init_devs.tcl" > /dev/null')
    #     os.chdir(act_dir)
    # elif "PDK_ROOT" in os.environ and "PDK" in os.environ:
    #     act_dir = os.getcwd()
    #     os.chdir(path)
    #     os.system('magic -dnull -noconsole -rcfile ${PDK_ROOT}/${PDK}/libs.tech/magic/${PDK}.magicrc "init_devs.tcl" > /dev/null')
    #     os.chdir(act_dir)
    # else:
    #     raise KeyError(f"[ERROR] Variable PDKPATH not set!")
    
    #if the circuit has already a cell view, update the paths
    for device in Circuit.devices.values():
        if not (device.cell is None):
            if type(device.cell)==Cell:
                device.cell.add_path(os.path.realpath(f'{path}'))

def generate_cell(name : str, path='Magic/Devices') -> Cell:
    """Generate a Cell-view.

    Args:
        name (str): Name of the cell/device for which the cell-view shall be generated.
        path (str, optional): Path to the magic-view of the cell. Defaults to 'Magic/Devices'.

    Raises:
        FileNotFoundError: If the magic-view can't be found.

    Returns:
        Cell: Generated cell-view.
    """
    logger.debug(f"Generating cell: {name}")

    if not os.path.exists(f'{path}/{name}.mag'):
        raise FileNotFoundError(f"Magic-view of cell {name} not found in {path}/!")
    
    #parse the magic-file
    parser = MagicParser(f'{path}/{name}.mag')

    #get the layers of the device
    layers = copy.copy(parser.layers)

    #generate the cell
    cell = Cell(name, layers)
    
    #add the path to the cell
    cell.add_path(os.path.realpath(f'{path}'))
    #cell.add_path(f'..{path[5:]}/')

    logger.debug(f"Generated cell {cell}.")

    return cell 

def add_cells(circ : Circuit, mag : Magic, path='Magic/Devices'):
    """Add a cell-view to the circuit.

    Args:
        circ (Circuit): Circuit whose cell-view shall be generated.
        mag (Magic): Process for communicating with magic
        path (str, optional): Path to the magic-view of the devices. Defaults to 'Magic/Devices'.
    """

    try:
        topology = get_top_down_topology(circ)
        topology.sort(key=lambda x: x[0])

        for (t, c) in topology:
            for (d_name, d) in c.devices.items():
                if type(d) is not SubDevice:
                    cell_path = path
                    cell = generate_cell(d_name, cell_path)
                    d.set_cell(cell)
    except FileNotFoundError:
        print(f"Magic-view can't be found!")
        print(f"Generating new view under '{path}'!")
        # NOTE: instantiate_circuit MUST generate the layout or else the recursive call to add_cells
        # will be an infinite loop.
        instantiate_circuit(circ, mag, path)
        add_cells(circ=circ, mag=mag, path=path)
    except:
        print(f"Adding cells to {circ} failed!")
        sys.exit(1)
                

def place_circuit(name : str, Circuit : Circuit, mag : Magic, path = 'Magic/Placement', debug=False, clean_path=True):
    """Place the devices of circuit <Circuit> in magic.

    Args:
        name (str): Name of the top-cell.
        Circuit (Circuit): Circuit which shall be placed.
        mag (Magic): Magic process for sending commands and receiving responses
        path (str, optional): Path to the resulting top-cell. Defaults to 'Magic/Placement'.
        debug (bool, optional): If True, only the tcl script will be generated, but not executed. Defaults to False.
        clean_path (bool, optional): If True, the content at <path> will be deleted, before stating the placement. Defaults to True.
    """

    #generate the commands to place the circuit
    lines = mag.place_circuit(name, path="")

    #make the Placement folder
    if not os.path.exists(path):
        os.makedirs(path)

    # Find the absolute path to "path" and move to it in the layout editor
    # Then remove any existing layout files in that directory.

    cwdpath = os.getcwd()
    abspath = os.path.join(cwdpath, path)
    if mag:
        mag.magic_command('cd ' + abspath)
        mag.magic_command('foreach fname [glob *.mag] {file delete $fname}')

    #write the tcl script to generate the Placement
    # file = open(path+'/place_devs.tcl', 'w')
    # for l in lines:
    #     file.write(l+'\n')
    # file.close()

    # if not debug:
    #     # check if the variable PDKPATH is set
    #     if "PDKPATH" in os.environ:
    #         #let magic generate the devices
    #         act_dir = os.getcwd()
    #         os.chdir(path)
    #         os.system('magic -dnull -noconsole -rcfile ${PDKPATH}/libs.tech/magic/sky130A.magicrc "place_devs.tcl" > /dev/null')
    #         #delete the tcl script
    #         os.remove("place_devs.tcl")
    #         os.chdir(act_dir)
    #     else:
    #         raise KeyError(f"[ERROR] Variable PDKPATH not set!")

    mag.magic_command(lines)
        
    
def place_circuit_hierachical(name : str, circuit : Circuit, mag : Magic, path = "Magic/Placement", clean_path = True):
    """Do the placement of a circuit hierarchical.

        WARNING: Hierarchical placement can lead to errors, since 
                 Magic scales cells "spontaneously".
    Args:
        name (str): Name of the top-cell.
        circuit (Circuit): Circuit which shall be placed.
        path (str, optional): Path of the placement. Defaults to "Magic/Placement".
        clean_path (bool, optional): True, if the path should be cleaned before placing the devices. Defaults to True.
    """
    
    #if Placement folder exists delete it
    if os.path.exists(path) and clean_path:
        shutil.rmtree(path)

    #make the Placement folder
    if not os.path.exists(path):
        os.makedirs(path)

    topology = get_bottom_up_topology(circuit)

    #sort the topology in descent order (starting with the lowest)
    topology.sort(key=lambda x : x[0], reverse=True)

    for (topology_layer, circ) in topology:
        if type(circ) == SubCircuit:
            #get the subdevice
            circ_c = copy.deepcopy(circ)
            sub_device = circ_c.sub_device
            macro_cell = sub_device.cell
            #center the macro-cell
            macro_cell.move_center((0,0))
            macro_cell.rotate_center(-macro_cell.rotation)
            macro_cell._move_cells_to_bound()
            #place the subcircuit
            place_circuit(sub_device.name, circ_c, mag, path=path, clean_path=False)

            circ.sub_device.cell.add_path(os.path.realpath(f'{path}'))
        else:
            place_circuit(name, circ, mag, path=path, clean_path=False)

