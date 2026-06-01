'''
Docstring for create_gds
1. create_gds.py: This python file creates the desired gds


'''

import gdsfactory as gf
import gdstk
import numpy as np
# import pendulum
import tomllib

from gdsfactory.cross_section import ComponentAlongPath
from gdsfactory.components import rectangle

from qfab.components import (
    airbridge, 
    bond_pad,
    border,
    branding,
    coupling_pad,
    dipole_qubit,
    id_box,
    interdigitated_capacitor,
    probe_alignment,
    junction_lead,
    junction_lead_v2,
    manhattan_junction,
    dolan_junction,
    raith_alignment
)
from qfab.device import (
    flux_trap_layout,
    standard_device_layout,
    subtract_cutouts,
    # positive_mask,    # not being used anyways
)
from qfab.pdk import CPW, CPW_open
from qfab.pdk import default_pdk as pdk
from qfab.utils import meander, junction_cd_bias

pdk.activate()

from gdsfactory.components import bend_euler
pdk.register_cells(bend_euler=bend_euler)


def generate_IDC(cpw, IDC_params):
    
    # print(cpw_xs.sections[0].width)
    # print(cpw_xs.sections[1].width)

    device = gf.Component()
    cpw_xs = CPW(cpw[0], cpw[1])
    cpw_o = CPW_open(width=cpw_xs.sections[0].width, gap=0.5*(cpw_xs.sections[1].width-cpw_xs.sections[0].width))
    rect1 = device<<  gf.path.extrude(
            gf.path.straight(25), cross_section=cpw_o
        )
    rect2 = device<<  gf.path.extrude(
            gf.path.straight(25), cross_section=cpw_o
        )
    
    cpw_path = gf.path.straight(100)
    cpw_len1 = device << gf.path.extrude(cpw_path, cross_section=cpw_xs)

    cpw_len2 = device << gf.path.extrude(cpw_path, cross_section=cpw_xs)
    
    print(f'from create_gds {IDC_params}') # debug
    IDC_coupler = interdigitated_capacitor(**IDC_params, xsection=cpw_xs)
    IDC_coupler = device << IDC_coupler

    for item in [cpw_len1, cpw_len2, IDC_coupler, rect1, rect2]:
        for port in item.ports:
            if port.port_type == "ground":
                port.port_type = "electrical"
    
    cpw_len1.connect("i", IDC_coupler.ports["i"], allow_width_mismatch=True, allow_type_mismatch=True, allow_layer_mismatch=True)
    cpw_len2.connect("i", IDC_coupler.ports["o"], allow_width_mismatch=True, allow_type_mismatch=True, allow_layer_mismatch=True)
    
    rect1.connect("ci", cpw_len1.ports["o"], allow_width_mismatch=True, allow_type_mismatch=True, allow_layer_mismatch=True)
    rect2.connect("ci", cpw_len2.ports["o"], allow_width_mismatch=True, allow_type_mismatch=True, allow_layer_mismatch=True)
    
    # device.plot(show_labels=False)
    device.write_gds("IDC.gds", with_metadata=False)