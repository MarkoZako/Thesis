import subprocess
import os
import re
import sys
import matplotlib.pyplot as plt
import numpy as np
import math
from matplotlib.ticker import MaxNLocator
import itertools
from itertools import combinations
from itertools import product


def calculate_similarity(data):
    policies = list(data.keys())
    benchmarks = list(data[policies[0]].keys())
    num_policies = len(policies)
    num_benchmarks = len(benchmarks)

    # Initialize a similarity matrix
    similarity_matrix = np.zeros((num_benchmarks, num_benchmarks))

    # Calculate similarity scores
    for i, j in itertools.combinations(range(num_benchmarks), 2):
        benchmark1 = benchmarks[i]
        benchmark2 = benchmarks[j]
        measurements = np.zeros((num_policies, 2))
        for k, policy in enumerate(policies):
            measurements[k, 0] = data[policy][benchmark1]
            measurements[k, 1] = data[policy][benchmark2]
        similarity_matrix[i, j] = np.corrcoef(measurements.T)[0, 1]
        similarity_matrix[j, i] = similarity_matrix[i, j]

    # Define a similarity threshold (you can adjust this value)
    similarity_threshold = 0.8

    # Identify groups of benchmarks with similar behavior
    groups = []
    for i in range(num_benchmarks):
        group = [benchmarks[i]]
        for j in range(i + 1, num_benchmarks):
            if similarity_matrix[i, j] >= similarity_threshold:
                group.append(benchmarks[j])
        if len(group) > 1:
            groups.append(group)

    return groups

def create_options():
    posible_options = {"SPromClean" : 3, "SPromDirty": 3 , "DemClean": 5 , "DemDirty": 5, "Insert" : 4 } 
    order = ["DemClean", "DemDirty", "Insert", "SPromClean", "SPromDirty", "DemClean", "DemDirty", "Insert", "SPromClean", "SPromDirty", "DemClean", "DemDirty", "Insert", "SPromClean", "SPromDirty", "DemClean", "DemDirty", "Insert", "SPromClean", "SPromDirty"]
    options = []

    for i,option in enumerate(order):
        options.append({})
        for j in range(int(posible_options[option])):
            options[i][j] = 0
    
    return options

def count_options(strings, options):
    for string in strings:
        for index,character in enumerate(string):
            options[int(index)][int(character)] += 1

    print_percentage(options)


def print_percentage(options):
    j = 1
    for option in options:
        sum =0
        print("For the " + str(j) + " th character the percentage are :")
        for i in option:
            sum += option[i]
            print(str(i) + ": " + str(option[i] * 100 / 50))
        
        j+=1
        # Sanity Check
        if sum != 50:
            print("Sum is not 50 for " + option)
        
        

def check_randomnes_of_individuals(numIndividuals=50):
    
    strings = []

    for individual in range(1, numIndividuals+1, 1):
        strings.append(getSigniture(1,individual))

    options = create_options()

    count_options(strings,options)
    return

def calculate_standard_deviation(numbers):
    # Calculate the mean of the array
    mean = sum(numbers) / len(numbers)

    # Calculate the sum of the squared differences from the mean
    sum_squared_diff = sum((x - mean) ** 2 for x in numbers)

    # Calculate the sample variance
    variance = sum_squared_diff / (len(numbers) - 1)

    # Calculate the sample standard deviation
    standard_deviation = math.sqrt(variance)

    return standard_deviation


def getSigniture(generation, myID):

    # Get a list of all files in the directory
    file_list = os.listdir('./Results')

    # Filter only the filenames not directories
    file_list = [filename for filename in file_list if filename.endswith(".txt")]
    
    # Filter only the filename that corresponds to this individual
    file_list = [filename for filename in file_list if filename.startswith(str(generation) + "_" + str(myID) + "_")]

     # Sanity Check
    if len(file_list) != 1:
        print("I identified 2 files for individual " + str(myID) + " of generation " + str(generation))
    
    filename = file_list[0]

    signature = ""
    section_found = False
    try:
        with open('./Results/' + filename, 'r') as file:
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
                        signature += str(number)
    except:
        print("Couldn't open file \"" + filename + "\", ipc for this individual will be 0")
        return {"plist": "Error"}

    return signature




def getIPCs(myID, generation):
    
    # Get a list of all files in the directory
    folder_list = os.listdir('./SADRRIP/Results/')
    # Filter only the folder that corresponds to this individual
    folder_list = [folder for folder in folder_list if folder.endswith("-" + str(generation) + "-" + str(myID))]

    if len(folder_list) > 1:
        print("ERROR")

    folder = folder_list[0]

    values ={}
    # default filenames
    filenames = ["Blender", "Bwaves", "Cam4", "cactuBSSN", "Exchange", "Gcc", "Lbm", "Mcf", "Parest", "Povray", "Wrf", "Xalancbmk", "Fotonik3d", "Imagick", "Leela", "Omnetpp", "Perlbench", "Roms", "x264", "Xz"]
    
    for filename in filenames:

        full_filename = "./SADRRIP/Results/" + folder + "/" + filename + ".out"
        # check if file exists
        if not os.path.isfile(full_filename):
            #print("File " + full_filename + " does not exist")
            continue

        with open(full_filename, 'r') as f:
            for line in f:
                if "Finished CPU" in line and "IPC:" in line:
                    ipc_index = line.find("IPC:") + 5  # find index of IPC value
                    ipc_value = float(line[ipc_index:].split()[0])  # extract IPC value as float
                    values[filename] = ipc_value
                    break
    
    return values


def print_standard_deviation(value_dict):

    # default filenames
    filenames = ["Blender", "Bwaves", "Cam4", "cactuBSSN", "Exchange", "Gcc", "Lbm", "Mcf", "Parest", "Povray", "Wrf", "Xalancbmk", "Fotonik3d", "Imagick", "Leela", "Omnetpp", "Perlbench", "Roms", "x264", "Xz"]

    for benchmark in filenames:
        data = getPlotData(value_dict, benchmark)
        
        y = data[1]

        standard_deviation = calculate_standard_deviation(y)

        print("The standard deviation for benchmark " + benchmark + " is: " + str(standard_deviation))

def plot_ipc_trends(value_dict , benchmark):
    
    data = getPlotData(value_dict, benchmark)
     
    x = data[0]
    y = data[1]
    
    if len(x) == 0:
        return

    # Create a figure and axes
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot the x and y coordinates as a line plot
    ax.plot(x, y)

    # Set labels for x and y axes
    ax.set_xlabel('Individual')
    ax.set_ylabel('IPC Value')

    # Set a title for the graph
    ax.set_title('IPC Trend - ' + benchmark)
      
    # Set x-axis limits to ensure the plot finishes at the end of the last x-axis value
    ax.set_xlim(x[0], x[-1])
    
    increment = (max(y) - min(y)) / 3

    if increment < 0.005:
        increment = 0.005
    
    # Set y-axis limits and increment
    
    ax.set_ylim(min(y)-increment, max(y)+increment)
    
    plt.yticks(np.arange(min(y)-increment ,max(y)+increment, increment))
        

    # show all the tick labels on the y-axis
    ax = plt.gca()
    ax.yaxis.set_major_locator(MaxNLocator(prune='lower'))


    # # Calculate and plot the trend for the entire data set
    # trend = np.polyfit(x, y, 1)
    # ax.plot(x, np.polyval(trend, x), label="Overall Trend", color='black', linewidth=2)

       
    # # Set legend
    # ax.legend()

    # Save the graph as a PNG image
    plt.savefig("Ipc_Trend_"+benchmark+".png", dpi=600)

    # Close the plot
    plt.close()

def getPlotData(value_dict, benchmark):

    data_x = []
    data_y = []
    individuals_id = 1

    # For all individuals
    for key in value_dict.keys():
        if benchmark in value_dict[key].keys():
                data_x.append(individuals_id)
                data_y.append(value_dict[key][benchmark])
                individuals_id = individuals_id + 1
        else:
            continue

    return [data_x, data_y]

def create_plots(value_dict):
    # default filenames
    filenames = ["Blender", "Bwaves", "Cam4", "cactuBSSN", "Exchange", "Gcc", "Lbm", "Mcf", "Parest", "Povray", "Wrf", "Xalancbmk", "Fotonik3d", "Imagick", "Leela", "Omnetpp", "Perlbench", "Roms", "x264", "Xz"]

    for benchmark in filenames:
        plot_ipc_trends(value_dict,benchmark)

    subprocess.call("mkdir Graphs",shell=True)
    subprocess.call("mv Ipc_Trend_* ./Graphs", shell=True)

def print_average_ipc_validation(values):
    for unique_id in values.keys():
        myID = unique_id.split("_")[1]
        generation = unique_id.split("_")[0]
        print("IPC values for all benchmarks of individual " + str(myID) + " of generation " + str(generation))
        sum = 0.0
        for filename in values[unique_id].keys():
            print("IPC for " + filename + " is " + str(values[unique_id][filename]))
            sum = sum + float(values[unique_id][filename])

        average =sum/len(values[unique_id].keys())

        print("\nAverage IPC for this individual is " + "{:.3f}\n".format(average))



def average_ipc_validation(generations, numIndividuals):
     
    myID = 1
    generations = int(generations)
    numIndividuals = int(numIndividuals)

    values = {}
    for generation in range(1,generations+1,1):
        for i in range(1,numIndividuals+1, 1):
            unique_id = str(generation) + "_" + str(myID)
            values[unique_id] = getIPCs(myID, generation)
            myID += 1

    return values

def find_best_performance_combination(reference_values, data):
    benchmarks = reference_values.keys()
    combinations_list = list(product(*data.keys()))

    best_combination = None
    highest_total_performance = 0

    for combination in combinations_list:
        total_performance = 0

        for benchmark, ref_value in reference_values.items():
            max_performance = float('-inf')

            for id_ in combination:
                value = data[id_].get(benchmark, 0)
                performance = (value - ref_value) / ref_value * 100
                max_performance = max(max_performance, performance)

            total_performance += max_performance

        if total_performance > highest_total_performance:
            highest_total_performance = total_performance
            best_combination = combination

    return best_combination


def find_best_ids(data):
    benchmarks = list(data.values())[0].keys()

    for benchmark in benchmarks:
        best_id = max(data, key=lambda x: data[x].get(benchmark, 0))
        ipc = data[best_id].get(benchmark, 0)
        print(f"Benchmark: {benchmark}, Best ID: {best_id}, IPC: {ipc}")



#####################################################################################################
#                                               MAIN                                                #
#####################################################################################################


SRRIP = {
    "Blender": 0.663919,
    "Cam4": 0.727112,
    "cactuBSSN": 0.761397,
    "Gcc": 0.353657,
    "Lbm": 0.652197,
    "Mcf": 0.403874,
    "Parest": 0.960588,
    "Wrf": 0.828134,
    "Xalancbmk": 0.402336,
    "Fotonik3d": 0.615018,
    "Imagick": 2.19348,
    "Omnetpp": 0.246534,
    "Perlbench": 0.448236,
    "Roms": 1.07339,
    "x264": 1.37137,
    "Xz": 0.89735
}

generations = sys.argv[1]
numIndividuals = sys.argv[2]

#check_randomnes_of_individuals()

values = average_ipc_validation(generations, numIndividuals)

print_standard_deviation(values)
print_average_ipc_validation(values)
create_plots(values)

result = calculate_similarity(values)
print("Groups of benchmarks with similar behavior:")
for group in result:
    print(group)

print(find_best_performance_combination(SRRIP, values))

find_best_ids(values)
