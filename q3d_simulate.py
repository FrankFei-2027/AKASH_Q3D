'''
Docstring for q3d_simulate
2. q3d_simulate.py: This python file runs the simulation of ansys q3d and export the data to a csv file


algorithm: 
create_ansys_q3d: takes the ansys,
return the ansys project object or None
    try to create the ansys project using ansys.aedt.core
        if the project does not exist, create a new project and open the project desktop,
        else if the project exist but not opened, open the project desktop,
        else use the existing project desktop. 
        return the ansys project
    catch the error of opening failure and close the desktop
        return None

run_ansys_q3d: takes the ansys q3d project object, the path to gds file, the list of gds parameters, result csv file path, 
try running the simulation in the ansys project object, catch failure of the project, print the error message and return None,
add the simulation result to the csv file by running export_result, 
return the list in form [N, length, width, fgap, ggap, taper, 1_1, 1_2, 1_GND, 2_1, 2_2, 2_GND, GND_1, GND_2, GND_GND]

export_result: takes result csv file path, the result list in form [N, length, width, fgap, ggap, taper, 1_1, 1_2, 1_GND, 2_1, 2_2, 2_GND, GND_1, GND_2, GND_GND],
return a boolean success

q3d_simulate: takes the ansys project folder path, project name, gds file path, the list of parameters in form [N, length, width, fgap, ggap, taper],
create_ansys_q3d()

return run_ansys_q3d() 

'''

# Tell PyAEDT's core to strictly block console outputs
# ansys.aedt.core.settings.enable_screen_logs = False
# ansys.aedt.core.settings.enable_console_log = False
# ansys.aedt.core.settings.logger_level = "ERROR" # Block INFO/WARNING, allow only




import logging
# 1. Strip standard system logging bindings
logging.getLogger().handlers.clear() # not sure about this line

import os, sys
import ansys.aedt.core
import pandas as pd


def create_ansys_q3d(project_dir: str, project_name: str, NG_MODE: bool = True) -> ansys.aedt.core.Q3d | None:
    # AEDT_VERSION = "2024.2"
    # NG_MODE = True  # Run headless in background
    # project_dir = r"C:\Users\dixit\Documents\GitHub\Dual-Rail\Device Design\Q3D sim"
    # project_name = 'IDC_testing.aedt'
    project_path = os.path.join(project_dir, project_name)

    # Open/connect to the desktop session and project exactly ONCE globally.
    # This stays alive between simulate_IDC() function calls.
    q3d = ansys.aedt.core.Q3d(
        non_graphical=NG_MODE,
        new_desktop=False,
        project=project_path
    ) 
    '''
    can add fault tolerance of case where creation fails
    '''

    return q3d

def run_ansys_q3d(q3d: ansys.aedt.core.Q3d, gds_file_path: str, gds_parameter: list, result_csv_file_path: str) -> list:
    