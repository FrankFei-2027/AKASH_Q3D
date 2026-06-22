"""
GDS generation functions for IDC layouts.

main.py starts the optimization script, and q3d_simulate.py owns the
Ansys Q3D simulation flow.
"""

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


"""
def CPW_NONE_pdk(
    width: float,
    gap: float,
    mlayer: tuple,
    slayer: tuple,
    chip: int = 1,
    vias=[],
):
    # mlayer = getattr(LAYER, f"SC{chip}")
    # slayer = getattr(LAYER, f"SC{chip}_E")

    xsection = gf.CrossSection(
        sections=[
            gf.Section(
                width=width,
                layer=mlayer,
                port_names=("i", "o"),
                port_types=("electrical", "electrical"),
            ),
            gf.Section(
                width=width + 2 * gap,
                layer=slayer,
                port_names=("ci", "co"),
                port_types=("electrical", "electrical"),
            ),
        ],
        components_along_path=vias,
    )

    return xsection


def CPW_open_NONE_pdk(width: float, gap: float, layer: tuple, chip: int = 1):
    xsection = gf.CrossSection(
        sections=[
            gf.Section(
                width=width + 2 * gap,
                layer=layer,
                port_names=("ci", "co"),
                port_types=("electrical", "electrical"),
            )
        ]
    )

    return xsection

def interdigitated_capacitor_NONE_pdk(N, length, width, fgap, ggap, taper, xsection):
    offsets = (width + fgap) * (np.arange(N) - (N - 1) / 2)
    total_finger_width = N * (width + fgap) - fgap
    xs1 = gf.CrossSection(
        sections=[
            gf.Section(width=width, layer="SC1", offset=ofst) for ofst in offsets[::2]
        ]
    )

    xs2 = gf.CrossSection(
        sections=[
            gf.Section(width=width, layer="SC1", offset=ofst) for ofst in offsets[1::2]
        ]
    )

    xsc = gf.CrossSection(
        sections=[
            gf.Section(
                width=total_finger_width + 2 * ggap,
                layer="SC1_E",
                port_names=("ci", "co"),
            )
        ]
    )

    p1 = gf.path.straight(length - fgap)
    p1.movex(-length / 2)

    p2 = gf.path.straight(length - fgap)
    p2.movex(-length / 2 + fgap)

    pc = gf.path.straight(length)
    pc.movex(-length / 2)

    c = gf.Component()
    finger1 = c << gf.path.extrude(p1, cross_section=xs1)
    finger2 = c << gf.path.extrude(p2, cross_section=xs2)
    cutout = c << gf.path.extrude(pc, cross_section=xsc)

    taper_xs = CPW(width=total_finger_width, gap=ggap)
    p_taper = gf.path.extrude_transition(
        gf.path.straight(taper), gf.path.transition(xsection, taper_xs)
    )

    t1 = c << p_taper
    t2 = c << p_taper
    t1.connect("co", cutout.ports["ci"])
    t2.connect("co", cutout.ports["co"])

    sc = gf.boolean(c.extract(layers=["SC1"]), [], "or", layer="SC1")
    sc_e = gf.boolean(c.extract(layers=["SC1_E"]), [], "or", layer="SC1_E")

    c = gf.Component()
    c << sc
    c << sc_e
    c.add_port("i", port=t1.ports["i"])
    c.add_port("ci", port=t1.ports["ci"])
    c.add_port("o", port=t2.ports["i"])
    c.add_port("co", port=t2.ports["ci"])

    return c


    

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

"""




# Explicit GDS layers for the non-PDK version
# GDSFactory layer format is (layer_number, datatype)
NONPDK_ETCH_LAYER = (0, 0)
NONPDK_PAD1_LAYER = (1, 0)
NONPDK_PAD2_LAYER = (2, 0)


def CPW_NONE_pdk(
    width: float,
    gap: float,
    mlayer: tuple,
    slayer: tuple,
    chip: int = 1,
    vias=None,
):
    """
    Non-PDK CPW cross-section.

    mlayer: metal layer
    slayer: etch/opening layer
    """

    if vias is None:
        vias = []

    xsection = gf.CrossSection(
        sections=[
            gf.Section(
                name="metal",
                width=width,
                layer=mlayer,
                port_names=("i", "o"),
                port_types=("electrical", "electrical"),
            ),
            gf.Section(
                name="etch",
                width=width + 2 * gap,
                layer=slayer,
                port_names=("ci", "co"),
                port_types=("electrical", "electrical"),
            ),
        ],
        components_along_path=vias,
    )

    return xsection


def CPW_open_NONE_pdk(
    width: float,
    gap: float,
    layer: tuple = NONPDK_ETCH_LAYER,
    chip: int = 1,
):
    """
    Non-PDK CPW opening / etch-only cross-section.
    """

    xsection = gf.CrossSection(
        sections=[
            gf.Section(
                width=width + 2 * gap,
                layer=layer,
                port_names=("ci", "co"),
                port_types=("electrical", "electrical"),
            )
        ]
    )

    return xsection


def interdigitated_capacitor_NONE_pdk(
    N,
    length,
    width,
    fgap,
    ggap,
    taper,
    xsection1,
    xsection2,
    pad1_layer: tuple = NONPDK_PAD1_LAYER,
    pad2_layer: tuple = NONPDK_PAD2_LAYER,
    etch_layer: tuple = NONPDK_ETCH_LAYER,
):
    """
    Non-PDK IDC.

    pad1_layer: first capacitor electrode layer, default GDS layer (1, 0)
    pad2_layer: second capacitor electrode layer, default GDS layer (2, 0)
    etch_layer: etch/opening layer, default GDS layer (0, 0)
    """

    offsets = (width + fgap) * (np.arange(N) - (N - 1) / 2)
    total_finger_width = N * (width + fgap) - fgap

    # First capacitor electrode: layer 1
    xs1 = gf.CrossSection(
        sections=[
            gf.Section(
                width=width,
                layer=pad1_layer,
                offset=ofst,
            )
            for ofst in offsets[::2]
        ]
    )

    # Second capacitor electrode: layer 2
    xs2 = gf.CrossSection(
        sections=[
            gf.Section(
                width=width,
                layer=pad2_layer,
                offset=ofst,
            )
            for ofst in offsets[1::2]
        ]
    )

    # Etch/opening region: layer 0
    xsc = gf.CrossSection(
        sections=[
            gf.Section(
                width=total_finger_width + 2 * ggap,
                layer=etch_layer,
                port_names=("ci", "co"),
                port_types=("electrical", "electrical"),
            )
        ]
    )

    p1 = gf.path.straight(length - fgap)
    p1.movex(-length / 2)

    p2 = gf.path.straight(length - fgap)
    p2.movex(-length / 2 + fgap)

    pc = gf.path.straight(length)
    pc.movex(-length / 2)

    c = gf.Component()

    finger1 = c << gf.path.extrude(p1, cross_section=xs1)
    finger2 = c << gf.path.extrude(p2, cross_section=xs2)
    cutout = c << gf.path.extrude(pc, cross_section=xsc)

    # Left taper connects to capacitor electrode 1 on layer 1
    taper_xs1 = CPW_NONE_pdk(
        width=total_finger_width,
        gap=ggap,
        mlayer=pad1_layer,
        slayer=etch_layer,
    )

    # Right taper connects to capacitor electrode 2 on layer 2
    taper_xs2 = CPW_NONE_pdk(
        width=total_finger_width,
        gap=ggap,
        mlayer=pad2_layer,
        slayer=etch_layer,
    )

    p_taper1 = gf.path.extrude_transition(
        gf.path.straight(taper),
        gf.path.transition(xsection1, taper_xs1),
    )

    p_taper2 = gf.path.extrude_transition(
        gf.path.straight(taper),
        gf.path.transition(xsection2, taper_xs2),
    )

    t1 = c << p_taper1
    t2 = c << p_taper2

    t1.connect(
        "co",
        cutout.ports["ci"],
        allow_width_mismatch=True,
        allow_layer_mismatch=True,
        allow_type_mismatch=True,
    )

    t2.connect(
        "co",
        cutout.ports["co"],
        allow_width_mismatch=True,
        allow_layer_mismatch=True,
        allow_type_mismatch=True,
    )

    # Boolean OR each layer separately so the final component has clean geometry
    c_final = c.extract(
    layers=[
        pad1_layer,
        pad2_layer,
        etch_layer,
    ]
)
    # External ports
    c_final.add_port("i", port=t1.ports["i"])
    c_final.add_port("ci", port=t1.ports["ci"])
    c_final.add_port("o", port=t2.ports["i"])
    c_final.add_port("co", port=t2.ports["ci"])

    return c_final


def generate_IDC_nonpdk(
    cpw,
    IDC_params,
    output_gds: str = "IDC_nonpdk.gds",
):
    """
    Generates the non-PDK IDC GDS.

    Layer mapping:
    Etch/opening layer       -> (0, 0)
    First capacitor electrode -> (1, 0)
    Second capacitor electrode -> (2, 0)
    """

    device = gf.Component("IDC_nonpdk")

    center_width = cpw[0]
    gap = cpw[1]

    cpw_xs1 = CPW_NONE_pdk(
        width=center_width,
        gap=gap,
        mlayer=NONPDK_PAD1_LAYER,
        slayer=NONPDK_ETCH_LAYER,
    )

    cpw_xs2 = CPW_NONE_pdk(
        width=center_width,
        gap=gap,
        mlayer=NONPDK_PAD2_LAYER,
        slayer=NONPDK_ETCH_LAYER,
    )

    cpw_o = CPW_open_NONE_pdk(
        width=center_width,
        gap=gap,
        layer=NONPDK_ETCH_LAYER,
    )

    rect1 = device << gf.path.extrude(
        gf.path.straight(25),
        cross_section=cpw_o,
    )

    rect2 = device << gf.path.extrude(
        gf.path.straight(25),
        cross_section=cpw_o,
    )

    cpw_path = gf.path.straight(100)

    cpw_len1 = device << gf.path.extrude(
        cpw_path,
        cross_section=cpw_xs1,
    )

    cpw_len2 = device << gf.path.extrude(
        cpw_path,
        cross_section=cpw_xs2,
    )

    IDC_coupler = interdigitated_capacitor_NONE_pdk(
        **IDC_params,
        xsection1=cpw_xs1,
        xsection2=cpw_xs2,
    )

    IDC_coupler = device << IDC_coupler

    for item in [cpw_len1, cpw_len2, IDC_coupler, rect1, rect2]:
        for port in item.ports:
            if port.port_type == "ground":
                port.port_type = "electrical"

    cpw_len1.connect(
        "i",
        IDC_coupler.ports["i"],
        allow_width_mismatch=True,
        allow_type_mismatch=True,
        allow_layer_mismatch=True,
    )

    cpw_len2.connect(
        "i",
        IDC_coupler.ports["o"],
        allow_width_mismatch=True,
        allow_type_mismatch=True,
        allow_layer_mismatch=True,
    )

    # Connect etch-only rectangles to the etch ports of the CPWs
    rect1.connect(
        "ci",
        cpw_len1.ports["co"],
        allow_width_mismatch=True,
        allow_type_mismatch=True,
        allow_layer_mismatch=True,
    )

    rect2.connect(
        "ci",
        cpw_len2.ports["co"],
        allow_width_mismatch=True,
        allow_type_mismatch=True,
        allow_layer_mismatch=True,
    )

    device.write_gds(output_gds, with_metadata=False)
    return device


def generate_IDC_pdk(
    cpw,
    IDC_params,
    output_gds: str = "IDC_pdk.gds",
):
    """
    Generates the original PDK-based IDC GDS.
    This uses qfab.pdk.CPW, qfab.pdk.CPW_open, and qfab.components.interdigitated_capacitor.
    """

    device = gf.Component("IDC_pdk")

    cpw_xs = CPW(cpw[0], cpw[1])

    cpw_o = CPW_open(
        width=cpw_xs.sections[0].width,
        gap=0.5 * (cpw_xs.sections[1].width - cpw_xs.sections[0].width),
    )

    rect1 = device << gf.path.extrude(
        gf.path.straight(25),
        cross_section=cpw_o,
    )

    rect2 = device << gf.path.extrude(
        gf.path.straight(25),
        cross_section=cpw_o,
    )

    cpw_path = gf.path.straight(100)

    cpw_len1 = device << gf.path.extrude(
        cpw_path,
        cross_section=cpw_xs,
    )

    cpw_len2 = device << gf.path.extrude(
        cpw_path,
        cross_section=cpw_xs,
    )

    IDC_coupler = interdigitated_capacitor(
        **IDC_params,
        xsection=cpw_xs,
    )

    IDC_coupler = device << IDC_coupler

    for item in [cpw_len1, cpw_len2, IDC_coupler, rect1, rect2]:
        for port in item.ports:
            if port.port_type == "ground":
                port.port_type = "electrical"

    cpw_len1.connect(
        "i",
        IDC_coupler.ports["i"],
        allow_width_mismatch=True,
        allow_type_mismatch=True,
        allow_layer_mismatch=True,
    )

    cpw_len2.connect(
        "i",
        IDC_coupler.ports["o"],
        allow_width_mismatch=True,
        allow_type_mismatch=True,
        allow_layer_mismatch=True,
    )

    rect1.connect(
        "ci",
        cpw_len1.ports["co"],
        allow_width_mismatch=True,
        allow_type_mismatch=True,
        allow_layer_mismatch=True,
    )

    rect2.connect(
        "ci",
        cpw_len2.ports["co"],
        allow_width_mismatch=True,
        allow_type_mismatch=True,
        allow_layer_mismatch=True,
    )

    device.write_gds(output_gds, with_metadata=False)
    return device


def generate_IDC(cpw, IDC_params):
    """
    Generates both versions:

    1. IDC_nonpdk.gds
       - Etch/opening layer: (0, 0)
       - First capacitor electrode: (1, 0)
       - Second capacitor electrode: (2, 0)

    2. IDC_pdk.gds
       - Uses the active qfab PDK layer definitions.
    """

    nonpdk_device = generate_IDC_nonpdk(
        cpw=cpw,
        IDC_params=IDC_params,
        output_gds="IDC_nonpdk.gds",
    )

    pdk_device = generate_IDC_pdk(
        cpw=cpw,
        IDC_params=IDC_params,
        output_gds="IDC_pdk.gds",
    )

    return nonpdk_device, pdk_device
