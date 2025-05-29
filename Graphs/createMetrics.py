import os

import re



def extract_info_from_filename(filename):

    pattern = r'^\d+_(\d+)_([0-9A-Z]+)_'

    match = re.match(pattern, filename)

    if match:

        id_str = match.group(1)

        speedup_str = match.group(2).replace('DOT', '.')

        try:

            return int(id_str), float(speedup_str)

        except ValueError:

            return None

    return None



def extract_id_from_dirname(dirname):

    parts = dirname.split('-')

    for part in reversed(parts):

        if part.isdigit():

            return int(part)

    return None



def parse_mcf_out(file_path):

    instructions = None

    access = None

    miss = None

    sim_time = None  # New field



    try:

        with open(file_path, 'r') as f:

            for line in f:

                if "INSTR RETIRED" in line:

                    match = re.search(r"INSTR RETIRED:\s*(\d+)", line)

                    if match:

                        instructions = int(match.group(1))



                if line.startswith("LLC TOTAL"):

                    access_match = re.search(r'ACCESS:\s+(\d+)', line)

                    miss_match = re.search(r'MISS:\s+(\d+)', line)

                    if access_match and miss_match:

                        access = int(access_match.group(1))

                        miss = int(miss_match.group(1))



                if "Simulation time" in line:

                    match = re.search(r'Simulation time:\s*(.*?)\)', line)

                    if match:

                        sim_time = match.group(1).strip()



        if instructions and access is not None and miss is not None:

            mpki = (miss / instructions) * 1000

            return access, miss, instructions, mpki, sim_time

    except FileNotFoundError:

        print(f"File not found: {file_path}")

        return None

    return None




def process_txt_directory(directory, output_path):

    results = []

    for file in os.listdir(directory):

        if file.endswith('.txt'):

            info = extract_info_from_filename(file)

            if info:

                results.append(info)

    results.sort(key=lambda x: x[0])  # Sort by ID



    with open(output_path, 'w') as f:

        for id_val, speedup_val in results:

            f.write(f"ID: {id_val}, Speedup: {speedup_val}\n")



def process_mcf_directory(base_dir, output_path):

    with open(output_path, 'w') as f:

        for dir_name in os.listdir(base_dir):

            dir_path = os.path.join(base_dir, dir_name)

            if os.path.isdir(dir_path):

                id_val = extract_id_from_dirname(dir_name)

                mcf_path = os.path.join(dir_path, 'Mcf.out')

                result = parse_mcf_out(mcf_path)

                if id_val is not None and result:

                    access, miss, instr, mpki, sim_time = result

                    f.write(f"ID: {id_val}, ACCESS: {access}, MISS: {miss}, INSTRUCTIONS: {instr}, MPKI: {mpki:.3f}, TIME: {sim_time}\n")



if __name__ == "__main__":

    txt_dir = "/home/mzako001/Thesis/Results"           # ← Replace with path to your TXT files

    mcf_dir = "/home/mzako001/Thesis/SADRRIP/Results"       # ← Replace with path to directories containing Mcf.out



    process_txt_directory(txt_dir, 'speedup_results.txt')

    process_mcf_directory(mcf_dir, 'mpki_results.txt')


