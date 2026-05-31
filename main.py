'''
The project need following files:
1. create_gds.py: This python file creates the desired gds
2. q3d_simulate.py: This python file runs the simulation of ansys q3d and export the data to a csv file
3. main.py: This python file takes an initial set of parameters and automizes the iteration of the Q3D and find the desired parameters

algorithm:
    1. ask for input of the initial parameters and desired capacitance
    2. use the function scipy.minimize to automize the parameters
    3. output the target capacitance parameters

'''

import os
from scipy.optimize import minimize
import create_gds
import q3d_simulate

def loss_function(current_capacitance : list, target_capacitance : list) -> float: 
    result = (current_capacitance[0] - target_capacitance[0])**2 + (current_capacitance[1] - target_capacitance[1])**2 + (current_capacitance[2] - target_capacitance[2])**2
    return result


def one_procedure(IDC_parameters : list, cpw_parameters : list, target_capacitance: list, project_dir : list = "", project_name : str = "IDC.aedt", result_file_path : str = "all_results.gds") -> list | None:
    gds_file_path="IDC.gds"

    create_gds.generate_IDC(cpw_parameters[0], cpw_parameters[1], IDC_params=IDC_parameters)
    result_capacitance = q3d_simulate.q3d_simulate(project_dir=project_dir, project_name=project_name, gds_file_path=gds_file_path, gds_parameters=IDC_parameters, result_file_path=result_file_path)
    
    if result_capacitance == None:
        return None
    
    loss_function(result_capacitance, target_capacitance)
    return result_capacitance



def main():
    user_parameter = input("Please input parameters in the following order and seperate by space : cpwa cpwb N length width fgap ggap taper")
    parameters = user_parameter.split(" ")
    if not((len(parameters) == 6)):
        print("number of parameters does not match. ")
        return
    else:
        x0 = [float(x) for x in parameters]


    user_capacitance = input("Please input target capacitance in order of 1_2 1_GND 2_GND and seperated by space. ")
    target_capacitance = [float(x) for x in user_capacitance.split(" ")]
    if not len(target_capacitance) == 3:
        print("Number of capacitances are wrong, need three desired capacitance in order of 1_2 1_GND 2_GND. ")


    user_project_path = input("Please input project file path, press enter to use default path. ")
    user_project_name = input("Please input project name (need to end with .aedt), press enter to use default name. ")
    project_file_path = os.path.join(user_project_path, user_project_name)
    if os.path.exists(project_file_path):
        user_check = input("This file path exist, do you want to replace it? Yes, Y, or Enter to confirm; No, N to terminate. ")
        if user_check not in ["Yes", "yes", "Y", "y", ""]:
            if user_check in ["No", "no", "N", "n"]:
                print("user terminated the program. ")
                return
            else:
                print("Invalid input. ")
                return
        else:
            os.remove(project_file_path)
    os.makedirs(user_project_path)
        

    user_result_file_path = input("Please input result file path, press enter to use default file path. ")
    if not user_result_file_path == "" and not user_result_file_path.endswith(".csv"):
        print("Invalid result file path input, need to end with .csv. ")
        return


    user_cpw = input("Please input the two parameters of cpw and seperate them in space, press enter to use default (default: 13.5 8). ")
    cpw = user_cpw.split(" ")
    if len(cpw) == 2:
        cpw[0] = float(cpw[0])
        cpw[1] = float(cpw[1])
    else:
        print("cpw format unexpected.")
        return
    

    
    # automization
    args = [cpw, target_capacitance, user_project_path]
    if user_project_name == "":
        user_project_name = "IDC.aedt"
    args.append(user_project_name)

    if not user_result_file_path == "":
        args.append(user_result_file_path)

    minimize(one_procedure, x0=x0, args=args, bounds=[(0, None), (0, None), (0, None), (0, None), (0, None)])
    

    





if __name__ == "__main__":
    main()
