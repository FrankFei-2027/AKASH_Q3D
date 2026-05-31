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


'''
run_ansys_q3d: takes the ansys q3d project object, the path to gds file, the list of gds parameters, result csv file path, 
try running the simulation in the ansys project object, catch failure of the project, print the error message and return None,
return the list in form [N, length, width, fgap, ggap, taper, 1_1, 1_2, 1_GND, 2_1, 2_2, 2_GND, GND_1, GND_2, GND_GND]
'''
def run_ansys_q3d(q3d: ansys.aedt.core.Q3d, gds_file_path: str, 
                  mapping_layer: dict = {1: (0, 0), 2: (0, 0)}, chip_x: float = 5000, chip_y: float = 5000, chip_z: float = 675, pec_thickness: float = 0.2) -> bool:
    # Set units on the brand new design
    if not os.path.exists(gds_file_path):
        print(f'gds path not exist: {gds_file_path}')
        return None
    

    q3d.modeler.model_units = "um"
    
    # 3. GEOMETRY GENERATION
    chip = q3d.modeler.create_box(origin=[-chip_x/2, -chip_y/2, -chip_z],
                                  sizes=[chip_x, chip_y, chip_z], 
                                  name="chip", 
                                  material="silicon")
    
    pec = q3d.modeler.create_rectangle(origin=[-chip_x/2, -chip_y/2, 0],
                                       orientation="XY",
                                       sizes=[chip_x, chip_y],
                                       name="PEC_sheet")
    
    # import gds
    q3d.import_gds_3d(gds_file_path, mapping_layer)
    
    pads = []
    tool_lst = []
    for obj_name in q3d.modeler.object_names:
        if 'signal1' in obj_name.lower():
            pads.append(obj_name)
        if 'signal2' in obj_name.lower():
            tool_lst.append(obj_name)
    
    q3d.modeler.subtract("PEC_sheet", tool_lst, keep_originals=False)
    
    # assign thin conductor to pec parts
    object_list = pads + ['PEC_sheet']
    q3d.assign_thin_conductor(object_list, material="pec", thickness=pec_thickness)
    
    # assign net
    q3d.assign_net(['Signal1_3', 'Signal1_7'], "1")
    q3d.assign_net(['Signal1_5', 'Signal1_8'], "2")
    q3d.assign_net(pec, "GND")
    
    # Setup
    setup_name = "Setup1"
    cur_setup = q3d.create_setup(setup_name=setup_name, AdaptiveFreq=5e9, Cap__PerRefine=0.05)
    cur_setup.capacitance_enabled = True   
    cur_setup.dc_enabled = False           
    cur_setup.ac_rl_enabled = False        
    
    # Analyze
    validate = q3d.validate_simple()
    if validate:
        # print(f"[{design_run_name}] Validation passed. Starting simulation...")
        q3d.analyze(cur_setup.name)
        print('Simulation complete.')
        q3d.save_project()
        return True
    else:
        print('Validation failed. Please check the model.')
        q3d.save_project()
        return False
    



def export_q3d_result(q3d: ansys.aedt.core.Q3d, simulation_parameters: list, result_file_path: str) -> list:
    return_lst = [False]
    file_exists = os.path.exists(result_file_path)

    if file_exists: 
        with open(result_file_path, 'r') as file:
            first_line = file.readline().split(",")
            if first_line[:6] != ["N", "length", "width", "fgap", "ggap", "taper"]:
                print(f"label of {result_file_path} is not desired. ")
                return return_lst
        
    export_file_name = 'current_simulation_result.csv'
    success = q3d.export_matrix_data(
        file_name=export_file_name,          
        problem_type="C",                            
        sweep="LastAdaptive",           
        reduce_matrix="Original",       
        freq="5",                       
        freq_unit="GHz",                
        matrix_type="Spice",
        c_unit="fF"
    )

    if not success:
        print("export_matrix_data failed.")
        return return_lst


    matrix_labels = ["1", "2", "GND"]
    flat_matrix_headers = [f"{r}_{c}" for r in matrix_labels for c in matrix_labels]

    cap_data = 1e-15 * pd.read_csv(
        export_file_name,
        header=6,
        nrows=3,
        sep="\t",
        index_col=0,
        usecols=[0, 1, 2, 3]
    )

    flat_values = cap_data.to_numpy().flatten()
    matrix_data_dict = dict(zip(flat_matrix_headers, flat_values))

    param_headers = ["N", "length", "width", "fgap", "ggap", "taper"]
    param_data_dict = dict(zip(param_headers, simulation_parameters))
    capacitance = [matrix_data_dict["1_2"], matrix_data_dict["1_GND"], matrix_data_dict["2_GND"]]
    

    row_dict = {
        **param_data_dict,
        **matrix_data_dict
    }

    sweep_df = pd.DataFrame([row_dict])

    sweep_df.to_csv(
        result_file_path,
        mode="a",
        header=not file_exists,
        index=False
    )

    return_lst.append(capacitance)

    return return_lst


'''
q3d_simulate: takes the ansys project folder path, project name, gds file path, the list of parameters in form [N, length, width, fgap, ggap, taper],
create_ansys_q3d()

return run_ansys_q3d() 

'''

def q3d_simulate(project_dir, project_name, gds_file_path, gds_parameters, result_file_path, 
                 NG_MODE: bool = True, 
                 mapping_layer: dict = {1: (0, 0), 2: (0, 0)}, chip_x: float = 5000, chip_y: float = 5000, chip_z: float = 675, pec_thickness: float = 0.2) -> list | None:
    q3d = create_ansys_q3d(project_dir=project_dir, project_name=project_name, NG_MODE=NG_MODE)
    if q3d == None:
        print("simulation creation failed")
        return None
    
    run_simulation_success = run_ansys_q3d(q3d=q3d, gds_file_path=gds_file_path, mapping_layer=mapping_layer, chip_x=chip_x, chip_y=chip_y, chip_z=chip_z, pec_thickness=pec_thickness)
    if not run_simulation_success:
        q3d.close_desktop()
        return None

    export_success = export_q3d_result(q3d, simulation_parameters=gds_parameters, result_file_path=result_file_path)
    if not export_success[0]:
        q3d.close_desktop()
        return None
    return export_success[1]