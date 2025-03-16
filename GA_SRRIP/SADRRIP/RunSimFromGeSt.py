import re
import subprocess
import sys
import os
from time import sleep
from datetime import datetime

GenerationRun = False

if len(sys.argv) == 2:
    generation = sys.argv[1]
    GenerationRun = True
elif len(sys.argv) == 3:
    generation = sys.argv[1]
    myID = sys.argv[2]


error = open("error.out", 'a')


# Get a list of all files in the directory
file_list = os.listdir('./Individuals')

# Check if we are running a generation Run or an individual Run
if GenerationRun:
    # Filter the list to include only files that start with "1_"
    file_list = [filename for filename in file_list if filename.startswith(generation + "_")]
    
    # Sort the filenames based on the number after "_"
    file_list.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))

    # Create a bash file
    sbatch = open("Gen_" + str(generation) + ".sh", 'w')
else:
    # Filter the list to include only files that start with "1_"
    file_list = [filename for filename in file_list if filename.startswith(generation + "_" + myID + "_")]
    sbatch = open("individual_" + str(generation) + "_" + str(myID) + ".sh", 'w')



for individual , filename in enumerate(file_list):
    values = {}
    section_found = False

    # Open the individual file
    with open("./Individuals/" + filename, 'r') as file:
        for line in file:
            # Section of interest started
            if '.L2:' in line:
                section_found = True

            # Section of interest ended
            if 'OPromPrefetch' in line:
                break

            # Get the number from each line
            if section_found:
                if line.startswith('\t'):
                    # extract number at the end of the line
                    text = line.strip().split()[-1]
                    key = line.split()[0]
                    number = re.search(r"\d+", text).group()
                    values[key] = number

    # Using the dictionary create the plist
    plist_keys = ["W_SPromClean", "W_Insert", "P_SPromClean", "P_Insert", "R_SPromClean", "R_Insert", "L_SPromClean", "L_Insert"]
    plist = ""

    for key in plist_keys:
        if key in values.keys():
            plist += values.get(key)
        else:
            plist += "0"
            error.write("A value for " + key + " was not found and the default 0 was used instead")


    # Using the dictionary create the dirty_plist
    dirty_plist_keys = ["W_SPromDirty", "W_Insert", "P_SPromDirty", "P_Insert", "R_SPromDirty", "R_Insert", "L_SPromDirty", "L_Insert"]
    dirty_plist = ""

    for key in dirty_plist_keys:
        if key in values.keys():
            dirty_plist += values.get(key)
        else:
            dirty_plist += "0"
            error.write("A value for " + key + " was not found and the default 0 was used instead")


    # Using the dictionary create the demmask
    demmask_keys = ["W_DemDirty", "W_DemClean", "P_DemDirty", "P_DemClean", "R_DemDirty", "R_DemClean", "L_DemDirty", "L_DemClean"]
    demmask = ""

    for key in demmask_keys:
        if key in values.keys():
            demmask += values.get(key)
        else:
            demmask += "0"
            error.write("A value for " + key + " was not found and the default 0 was used instead")



    
    batch_script = "RRIP_BATCH_RUN"
    switch_script = "RRIP_RUN"
    # Get the ID that GeST gave to the individual
    myID = filename.split("_")[1].split(".")[0]
    # Command that allows us to run the simulations on the cluster
    batch_command = "sbatch --export=ALL,script=" + switch_script + ",plist=" + plist+plist + ",dplist=" + dirty_plist+dirty_plist + ",demmask=" + demmask+demmask + ",id='" + str(generation) + "-" + str(myID) + "' " + batch_script + "\n"
    # Write the command to the batch file we created 
    sbatch.write(batch_command)

# Close the batch file
sbatch.close()

# Write in the error.out file the time the simumation/s have started, make the batch file executable and then run it
if GenerationRun:
    error.write("Simulations for generation " + str(generation) + " started at " + datetime.now().strftime("%H:%M:%S") + "\n")
    subprocess.call("chmod u+x " + "Gen_" + str(generation) + ".sh", shell=True)
    subprocess.call("./Gen_" + str(generation) + ".sh", shell=True)
else:
    error.write("Simulations for individual " + str(myID) + " from generation " + str(generation) + " started at " + datetime.now().strftime("%H:%M:%S") + "\n")
    subprocess.call("chmod u+x " + "individual_" + str(generation) + "_" + str(myID) + ".sh", shell=True)
    subprocess.call("./individual_" + str(generation) + "_" + (myID) + ".sh", shell=True)

# Close the error file
error.close()
