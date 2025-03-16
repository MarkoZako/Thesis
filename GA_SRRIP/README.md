# GA_SRRIP
Files needed to run a genetic algorithm (GeST) with ChampSim

This reposiroty includes the modified version of the genetic algorithm (GeST).


Under the folder SRRIP are the script used to run the simulator from the genetic algorithm and the script that calculates the average ipc and gives it to the GA as the fitness value.
These scripts should be added in the SRRIP folder that contain the Simulator.

The RunSimFromGeSt.py script takes as arguments either the generation number and ID of individual to run simulations only that individual or only the generation to run simulations for the whole generation.
The ipc_parcer.py script takes as arguments the generation number and ID of individual in order to find the directory in which the output files of the simulator for the specified individual are located.

Changes that will need to be done in order to run:
- In file MeasurementIPC.py change the path in the comands to match your device
- In file Algorithm.py change the path to match your device in methods:
  - intitializeAlgorithmAndRunParameters
  - setupDirs
  - getMeasurements
 
  
In order to run with specific individuals in the first generation:
- In file Algorithm.py in the method __CreateIndividualFromFile__ add the path were the files that contain each individual are located. * The filenames must have the format "number.txt" e.g 1.txt, starting the counting from 0
- In file Algorithm.py in the method createInitialPopulation change the if statement in order to specify how many custom individuals you need in the first generation


How to run:
- In order to run you just need to start the __init__.py file in the src folder of GeST and give it as a parameter the RRIP configuration file.


CheckGenerations.py and CheckIndividuals.py are files that you can use in order to make some validations for the run.
