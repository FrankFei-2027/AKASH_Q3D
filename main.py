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

def one_procedure(cpw_parameters, IDC_parameters, project_dir="", project_name="IDC.aedt", result_file_path="all_results.gds"):
    gds_file_path="IDC.gds"

    create_gds.generate_IDC(cpw_parameters[0], cpw_parameters[1], IDC_params=IDC_parameters)
    result_capacitance = q3d_simulate.q3d_simulate(project_dir=project_dir, project_name=project_name, gds_file_path=gds_file_path, gds_parameters=IDC_parameters, result_file_path=result_file_path)

    return result_capacitance



def main():
    user_in = input("Please input parameters in the following order and seperate by space : cpwa cpwb N length width fgap ggap taper")
    user_project_path = input("Please input project file path, press enter to use default path. ")
    user_project_name = input("Please input project name, press enter to use default name. ")

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
    if not user_result_file_path.endswith(".csv"):
        print("Invalid result file path input, need to end with .csv. ")
        return

    parameters = user_in.split(" ")
    if not((len(parameters) == 6)):
        print("number of parameters does not match. ")
        return
    
        
    # automization
    x0 = 
    minimize(one_procedure, x0=x0, args=[cpw], bounds=, constraints=, )
    

    





if __name__ == "__main__":
    main()
