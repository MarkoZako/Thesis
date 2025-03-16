'''
Copyright 2019 ARM Ltd. and University of Cyprus
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, 
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''
import random
from time import sleep
import subprocess
from Measurement.Measurement import Measurement


class MeasurementIPC(Measurement):
    '''
    classdocs
    '''

    def __init__(self, confFile):
        super().__init__(confFile)

    def init(self):
        super().init()
        self.timeToMeasure = self.tryGetIntValue('time_to_measure')

    def move(self, generation, myID):
        super().moveFile(generation, myID)

    def RunSimulations(self, generation):
        execution_command = "cd /home/npapak01/Thesis/SADRRIP ; python3 RunSimFromGeSt.py " + str(generation) + " >> trash.txt"
        subprocess.run(execution_command, shell=True)

        sleep(3600)
        # print("Checking if job is finshed after 60 min")
        while True:
            output = subprocess.check_output("squeue -u npapak01 | wc -l", shell=True)
            output = output.decode().replace("\n", "")
            # print(output)
            if output == "1":
                break
            else:
                # print("Jobs not finished there are still " + str(output) + "more jobs")
                sleep(300)

    def GetMeasurement(self, generation, myID):

        output_command = "cd /home/npapak01/Thesis/SADRRIP ; python3 ipc_parser.py " + str(generation) + " " + str(myID)
        ipc = subprocess.check_output(output_command, shell=True)
        ipc = ipc.decode().replace("\n", "")
        # print("Average IPC of individuals is " + ipc)

        measurements = [];
        measurements.append(ipc);
        return measurements;

    def measure(self, generation, myID):

        super().moveFile(generation, myID)

        execution_command = "cd /home/npapak01/Thesis/SADRRIP ; python3 RunSimFromGeSt.py " + str(generation) + " " + str(myID)
        output_command = "cd /home/npapak01/Thesis/SADRRIP ; python3 ipc_parser.py " + str(generation) + " " + str(myID)
        subprocess.run(execution_command, shell=True)

        sleep(2400)
        # print("Checking if job is finshed after 40 min")
        while True:
            output = subprocess.check_output("squeue -u npapak01 | wc -l", shell=True)
            output = output.decode().replace("\n", "")
            # print(output)
            if output == "1":
                break
            else:
                print("Jobs not finished there are still " + str(output) + "more jobs")
                sleep(300)

        ipc = subprocess.check_output(output_command, shell=True)
        ipc = ipc.decode().replace("\n", "")
        #ipc = random.random()
        # print("Average IPC of individuals is " + ipc)

        # for line in stdout:
        #     #print ("line is "+line)
        #     try:
        #         test=float(line)
        #         ipc=test
        #     except ValueError:
        #         print ("Exception line not ipc")
        measurements = [];
        measurements.append(ipc);
        return measurements;
        # return ipc;
