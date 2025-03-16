import os
import re
import sys

# default Benchmarks
Benchmarks = ["Blender", "Bwaves", "Cam4", "cactuBSSN", "Exchange", "Gcc", "Lbm", "Mcf", "Parest", "Povray", "Wrf", "Xalancbmk", "Fotonik3d", "Imagick", "Leela", "Omnetpp", "Perlbench", "Roms", "x264", "Xz"]
ipc_values = []



generation = sys.argv[1]
myID = sys.argv[2]

# Get a list of all files in the directory
folder_list = os.listdir('./Results')

# Get the folder that has the unique id generation-myID at the end of the name
folder_list = [folder for folder in folder_list if folder.endswith("-" + generation + "-" + myID)]

# SANITY CHECK
if len(folder_list) > 1:
    print("0")
    exit()

# Extract the folder name from the list
folder = folder_list[0]

for benchmark in Benchmarks:

    full_filename = "Results/" + folder + "/" + benchmark + ".out"
    
    # Check if file exists
    if not os.path.isfile(full_filename):
        continue
    
    # Open the file and search fo the comulative IPC at the Finished CPU 
    with open(full_filename, 'r') as f:
        for line in f:
            if "Finished CPU" in line and "IPC:" in line:
                ipc_index = line.find("IPC:") + 5  # find index of IPC value
                ipc_value = float(line[ipc_index:].split()[0])  # extract IPC value as float
                ipc_values.append(ipc_value)  # add ipc value to list
                break


if ipc_values:
    avg_ipc = sum(ipc_values) / len(ipc_values)
    print("{:.3f}".format(avg_ipc))
else:
    print("0")
