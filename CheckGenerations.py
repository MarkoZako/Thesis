import subprocess
import os
import re
import sys
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

def checkforDuplicates(generations):
    
    print("Checking generations to find duplicate individuals")
    print("--------------------------------------------------")
    Generation_Data = {}

    individuals = 0

    for generation in range(1,generations+1, 1):
        # Get a list of all files in the directory
        file_list = os.listdir('./Results')
        # Filter the list to include only files that start with "1_"
        file_list = [filename for filename in file_list if filename.startswith(str(generation)+ "_")]
        Generation_Data[generation] = {}
        individuals = 0
        for individual , filename in enumerate(file_list):
            section_found = False
            individuals += 1
            values = {}
            Generation_Data[generation][individual] = {}
            # Read the individual file and create a dictionary containing all key value pairs
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
                            values[key] = number

            # Using the dictionary create the plist
            plist_keys = ["W_SPromClean", "W_Insert", "P_SPromClean", "P_Insert", "R_SPromClean", "R_Insert", "L_SPromClean", "L_Insert"]
            plist = ""
            for key in plist_keys:
                plist += values.get(key)

            # Using the dictionary create the dirty_plist
            dirty_plist_keys = ["W_SPromDirty", "W_Insert", "P_SPromDirty", "P_Insert", "R_SPromDirty", "R_Insert", "L_SPromDirty", "L_Insert"]
            dirty_plist = ""
            for key in dirty_plist_keys:
                dirty_plist += values.get(key)

            # Using the dictionary create the demmask
            demmask_keys = ["W_DemDirty", "W_DemClean", "P_DemDirty", "P_DemClean", "R_DemDirty", "R_DemClean", "L_DemDirty", "L_DemClean"]
            demmask = ""
            for key in demmask_keys:
                demmask += values.get(key)

            Generation_Data[generation][individual]["plist"] = plist
            Generation_Data[generation][individual]["dirty_plist"] = dirty_plist
            Generation_Data[generation][individual]["demmask"] = demmask

            # print(Generation_Data[generation][individual]["plist"] + "\t" + Generation_Data[generation][individual]["dirty_plist"] + "\t" + Generation_Data[generation][individual]["demmask"])
        Generation_Data[generation]["individuals"] = individuals
        
    counts = {}
    for generation in range(1, generations+1, 1):
        counts[generation] = {}
        duplicates = 0 
        for individual in range(0, Generation_Data[generation]['individuals'], 1):
            
            signature = Generation_Data[generation][individual]["plist"] + Generation_Data[generation][individual]["dirty_plist"] + Generation_Data[generation][individual]["demmask"]
            if signature in counts[generation].keys():
                counts[generation][signature] = counts[generation][signature] + 1
            else:
                counts[generation][signature] = 1


        for key, value in counts[generation].items():
            if value > 1:
                duplicates += value

        print("Found " + str(duplicates) + " duplicate individuals in generation " + str(generation))
        dupliactes = 0
        
    
    print("\nEnd of search\n\n")

def getNumIndividuals():

    file_list = os.listdir('./Results')
    # Filter the list to include only files that start with "1_"
    file_list = [filename for filename in file_list if filename.startswith("1_")]

    return len(file_list)


def printPlotData(generation_dict , numgenerations):
    
    data = getPlotData_line(generation_dict)
    
    vertical_lines = []
    numindividuals = getNumIndividuals()
    for num in range(numindividuals, numgenerations*numindividuals, numindividuals):
        vertical_lines.append(num)

    x = data[0]
    y = data[1]
    
    file = open("plot_data.txt", 'w')

    for i in range(len(x)):
        file.write(str(x[i]) + " " + str(y[i])) 
   

def getPlotData(generation_dict):

    data_x = []
    data_y = []
    individuals_id = 1

    # For all generations
    for generation in generation_dict:
        # For each individual in this generation
        for individual in generation_dict[generation]:
            if individual['ID'] == individuals_id:
                data_x.append(individuals_id)
                data_y.append(individual['Value'])
                individuals_id = individuals_id + 1             

    return [data_x, data_y]


def getMutations(indv_signiture, parent1_signiture, parent2_signature):

    # Sanity Check
    if len(indv_signiture) != len(parent1_signiture) or len(indv_signiture) != len(parent2_signature) or len(parent1_signiture) != len(parent2_signature):
        return 0

    mutations = 0 
    for i in range(len(indv_signiture)):
        # Should be equal to parent 1
        if i < len(indv_signiture)/2:
            if indv_signiture[i] != parent1_signiture[i]:
                mutations = mutations + 1
        else:
            if indv_signiture[i] != parent2_signature[i]:
                mutations = mutations + 1


    return mutations


def get_Parents(generation_dict):
    parents_dict = {}

    file_dict = parseParentsFromFile()

    # For each generation
    for generation in generation_dict.keys():
        
        # Get the individuals of that generation
        individuals = generation_dict[generation]
        if generation != "generation 1":
            parents_dict[generation] = {}
            
            # parent_gen = generation_dict.get("generation " + str(int(generation.split(" ")[-1]) - 1), [])

            # For each individual
            for individual in individuals:
                parent1, parent2 = None, None
                parents_dict[generation][individual["ID"]] = []
                if str(individual['ID']) in file_dict.keys():

           
                    parent1_ID = file_dict[str(individual['ID'])]['Parent1_ID']
                    parent2_ID = file_dict[str(individual['ID'])]['Parent2_ID']

                    
                    start_key = generation
                    
                    # Iterate over keys in reverse order from starting key to the beginning (excluding starting key)
                    for key in reversed(list(generation_dict.keys())[:list(generation_dict.keys()).index(start_key)]):
                        
                        posible_gen = generation_dict.get(key)
                        for possible_parent in posible_gen:
                            if str(possible_parent["ID"]) == str(parent1_ID):
                                parent1 = possible_parent
                                continue
                            if str(possible_parent["ID"]) == str(parent2_ID):
                                parent2 = possible_parent
                                continue
                        
                        # If parents were found break from loops
                        if parent1 != None and parent2 != None:
                            break
                    
                    # Sanity Check
                    if parent1 == None or parent2 == None:
                        print("ERROR!")       

                       
                    parents_dict[generation][individual["ID"]].append({"Parent":parent1})
                    parents_dict[generation][individual["ID"]].append({"Parent":parent2})
                
                # Elitism
                else:
                    parents_dict[generation][individual["ID"]].append({"Parent":individual})
                    parents_dict[generation][individual["ID"]].append({"Parent":individual})


    return parents_dict

def parseParentsFromFile():

    file_dict = {}
    with open("./GeST/log.out",'r') as file:
        for line in file:
            # Section of interest started
            if "Parent 1" in line:
                parent1 = line.split(":")[1].strip()
                continue
            elif "Parent 2" in line:
                parent2 = line.split(":")[1].strip()
                continue  
            # elif "The children created" in line:
            elif "The children created" in line:
                child1 = line.split()[-3]
                child2 = line.split()[-1]

                file_dict[child1] = {"Parent1_ID": parent1, "Parent2_ID": parent2}
                file_dict[child2] = {"Parent1_ID": parent2, "Parent2_ID": parent1}
                continue
            else:
                continue
            
    if file_dict == {}:
        print("Error")

    return file_dict

def display_generation_tree(generation_dict, parents_dict):
    print("Generation Tree:")
    
    for generation in generation_dict.keys():
        print("\n\n" + generation)
        individuals = generation_dict[generation]
        if generation != "generation 1":
            parent_gen = generation_dict.get("generation " + str(int(generation.split(" ")[-1]) - 1), [])
            for individual in individuals:
                parent1 , parent2 = None , None
                parents = parents_dict[generation][individual["ID"]]
                
                parent1 = parents[0]
                parent2 = parents[1]

                if parent1 == None or parent2 == None:
                    print("Error parents are Empty")
                

                if str(parent1['Parent']['ID']) != str(parent2['Parent']['ID']):
                    print( "  │ ")
                    print(f"  └─ Individual with ID- {individual['ID']:<3} , measurement- {individual['Value']:<9} and signature- {individual['Signature'][:10]} - {individual['Signature'][10:]}  that was mutated {getMutations(individual['Signature'], parent1['Parent']['Signature'], parent2['Parent']['Signature'])} times")
                    print( "      │")
                    print(f"      ├─ Parent with ID- {parent1['Parent']['ID']:<3} , measurement- {parent1['Parent']['Value']:<9} and signature- {parent1['Parent']['Signature'][:10]} - {parent1['Parent']['Signature'][10:]}")

                    print(f"      └─ Parent with ID- {parent2['Parent']['ID']:<3} , measurement- {parent2['Parent']['Value']:<9} and signature- {parent2['Parent']['Signature'][:10]} - {parent2['Parent']['Signature'][10:]}")

                else:
                    print( "  │ ")
                    print(f"  └─ Individual with ID- {individual['ID']:<3} , measurement- {individual['Value']:<9} and signature- {individual['Signature'][:10]} - {individual['Signature'][10:]} that was transfered due to elitism to this generation")

        else:
            for individual in individuals:
                print( "  │ ")
                print(f"  └─ Individual with ID- {individual['ID']:<3} , measurement- {individual['Value']:<9} and signature- {individual['Signature'][:10]} - {individual['Signature'][10:]}")



def parse_filename(generation, filename):
    # Split the input string by "_" to get the individual components
    components = filename.split("_")

    # Extract the ID from the second component (index 1) and convert it to an integer
    id = int(components[1])

    # Extract the value from the fourth and fifth components (indices 3 and 4),
    # replace "DOT" with "." and convert it to a float
    value = float(components[3].replace("DOT", "."))

    signature = getSignature(generation, id)
    

    # Create a dictionary with the extracted ID and value
    individual = {"ID": id, "Value": value, "Signature": signature}


    return individual

def getGeneration(generation):

    # Get a list of all files in the directory
    file_list = os.listdir('./Results')

    # Filter only the filenames not directories
    file_list = [filename for filename in file_list if filename.endswith(".txt")]
    
    # Filter only the files that are from the generation I want
    file_list = [filename for filename in file_list if filename.startswith(generation + "_")]

    # Sort the filenames based on the number after "_"
    file_list.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))

    individuals_list = []

    for filename in file_list:
        individual_dict = parse_filename(generation, filename)
        individuals_list.append(individual_dict)

    return individuals_list


def getSignature(generation, myID):

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

    
    # print("Attempting to open filename " + filename)
    signature = ""
    section_found = False
    try:
        with open(f"./Results/{filename}", 'r') as file:
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
                        number = re.search(r"\d+", text).group()
                        signature += number
    except:
        print("Couldn't open file \"" + filename + "\", ipc for this individual will be 0")
        return "-"

    return signature

######################################################
#                       MAIN                         #
######################################################

numgenerations = int(sys.argv[1])

# Check all individuals created and see if there are any duplicates
checkforDuplicates(numgenerations)


generation_dict = {}
# Fill generation dict 
for i in range(1,numgenerations+1,1):
    generation_dict[f"generation {i}"] = getGeneration(str(i))

# Get parents for each individual
#parents_dict = get_Parents(generation_dict)

# Display the generation tree
#display_generation_tree(generation_dict, parents_dict)

# Create a 
printPlotData(generation_dict, numgenerations)
