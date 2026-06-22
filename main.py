"""
Entry point for IDC optimization.

File responsibilities:
1. main.py starts the script and controls the optimization loop.
2. create_gds.py contains GDS generation functions.
3. q3d_simulate.py contains Ansys Q3D simulation functions.

Algorithm:
    1. Ask for the initial parameters and target capacitances.
    2. Use scipy.minimize to optimize the geometry parameters.
    3. Output the optimized IDC parameters.
"""

import os
from scipy.optimize import minimize
import create_gds
import q3d_simulate

def loss_function(current_capacitance: list, target_capacitance: list) -> float:
    if len(current_capacitance) != len(target_capacitance):
        raise ValueError("current_capacitance and target_capacitance must have the same length.")
    if any(target == 0 for target in target_capacitance):
        raise ValueError("target capacitances must be non-zero for normalized loss.")

    return sum(
        ((current - target) / target) ** 2
        for current, target in zip(current_capacitance, target_capacitance)
    )

def idc_list_to_dict(x):
    return {
        "N": int(round(x[0])),
        "length": x[1],
        "width": x[2],
        "fgap": x[3],
        "ggap": x[4],
        "taper": x[5],
    }

def one_procedure(IDC_parameters : list, N : float, cpw_parameters : list, target_capacitance: list, project_dir : list = "", project_name : str = "IDC.aedt", result_file_path : str = "all_results.csv") -> float | None:
    gds_file_path="IDC_nonpdk.gds"

    IDC_parameters = [N] + list(IDC_parameters)
    print(f'from main: {IDC_parameters}') # debug

    IDC_parameters_dict = idc_list_to_dict(IDC_parameters)
    # print(f'IDC_parameters_dict: {IDC_parameters_dict}') # debug
    #  {'N': 2, 'length': np.float64(100.0), 'width': np.float64(10.0), 'fgap': np.float64(10.0), 'ggap': np.float64(75.0), 'taper': np.float64(50.0)}
    # exit()
    create_gds.generate_IDC(cpw_parameters, IDC_params=IDC_parameters_dict)
    result_capacitance = q3d_simulate.q3d_simulate(project_dir=project_dir, project_name=project_name, gds_file_path=gds_file_path, gds_parameters=IDC_parameters, result_file_path=result_file_path)
    
    if result_capacitance == None:
        return 1e99
    
    loss = loss_function(result_capacitance, target_capacitance)
    return loss



def main():
    # cpw input
    user_cpw = input("Please input the two parameters of cpw and seperate them in space, press enter to use default (default: 13.5 8). \n")
    if user_cpw == "": 
        cpw = [13.5, 8]
    else: 
        cpw = user_cpw.strip().split(" ")
        if len(cpw) == 2:
            cpw[0] = float(cpw[0])
            cpw[1] = float(cpw[1])
        else:
            print("cpw format unexpected. \n")
            return

    # IDC parameters input, also seperate N since N is discrete variable
    user_parameter = input("Please input parameters in the following order and seperate by space : N length width fgap ggap taper: \n")
    parameters = user_parameter.strip().split(" ")
    if not((len(parameters) == 6)):
        print("number of parameters does not match. \n")
        return
    else:
        x0 = [float(x) for x in parameters]
        N = x0.pop(0)

    user_bounds = input('''Please input the bounds of the parameters in form (min, max) in the following order and seperate by space : length width fgap ggap taper: \n
                        Enter to use default bounds: (0, 1000) (0, 1000) (0, 1000) (0, 1000) (0, 1000) \n''')
    if user_bounds == "":
        bounds = [(0, 1000)] * 5
    elif not len(user_bounds.strip().split(" ")) == 5:
        print("number of bounds does not match. \n")
        return
    else:
        bounds = []
        for b in user_bounds.strip().split(" "):
            min_val, max_val = map(float, b.strip("()").split(","))
            bounds.append((min_val, max_val))

    user_capacitance = input("Please input target capacitance in order of 1_2 1_GND 2_GND in unit femtofarads (fF=1e-15F) and seperated by space. \n")
    target_capacitance = [float(x) * 1e-15 for x in user_capacitance.strip().split(" ")]# target_capacitance in unit F
    if not len(target_capacitance) == 3:
        print("Number of capacitances are wrong, need three desired capacitance in order of 1_2 1_GND 2_GND. \n")
        return


    user_project_path = input("Please input project file path, press enter to use default path. \n")
    user_project_name = input("Please input project name (need to end with .aedt), press enter to use default name. \n")
    
    if user_project_name == "":
        user_project_name = "IDC.aedt"
    project_file_path = os.path.join(user_project_path, user_project_name)
    if os.path.exists(project_file_path):
        user_check = input("This file path exist, do you want to replace it? Yes, Y, or Enter to confirm; No, N to terminate. \n")
        if user_check not in ["Yes", "yes", "Y", "y", ""]:
            if user_check in ["No", "no", "N", "n"]:
                print("user terminated the program. ")
                return
            else:
                print("Invalid input. ")
                return
        else:
            os.remove(project_file_path)
    if user_project_path != "":
        os.makedirs(user_project_path, exist_ok=True)
        

    user_result_file_path = input("Please input result file path, press enter to use default file path. \n")
    if not user_result_file_path == "" and not user_result_file_path.endswith(".csv"):
        print("Invalid result file path input, need to end with .csv. \n")
        return    

    
    # automization
    fixed = [cpw, target_capacitance, user_project_path]
    if user_project_name == "":
        user_project_name = "IDC.aedt"
    fixed.append(user_project_name)

    if not user_result_file_path == "":
        fixed.append(user_result_file_path)

    # loop through possible N 
    N0 = int(round(N))
    N_values = range(max(2, N0 - 6), N0 + 7)

    final_result = []
    loss_value = float('inf')
    for current_N in N_values:
        args = (current_N, *fixed)
        result = minimize(one_procedure, x0=x0, args=args, bounds=bounds)
        if result.fun < loss_value:
            final_result = [current_N, result]
            loss_value = result.fun

    if final_result == []:
        print("No optimized result found. \n")
        return 
    
    final_parameters = [final_result[0]] + final_result[1].x.tolist()
    print(f'''final_parameters={final_parameters}, loss={final_result[1].fun}, success={final_result[1].success}, message={final_result[1].message}. \n 
          final_parameters in order are N length width fgap ggap taper. \n''')
    return final_parameters
    
        

    # 6 100 10 10 75 50
    # 2.73 29.3 27.8



if __name__ == "__main__":
    main()
