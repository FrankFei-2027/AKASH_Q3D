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

import create_gds
import q3d_simulate

def main():
    print("Hello from akash-q3d!")


if __name__ == "__main__":
    main()
