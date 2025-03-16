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

from abc import ABC, abstractmethod
from xml.dom import minidom
# from paramiko import SSHClient, client
# import paramiko
# import socket
import platform
import os
from time import sleep
import subprocess

class Measurement(ABC):
    '''
    classdocs
    '''

    def __init__(self, confFile):
        '''
        Constructor
        '''
        self.confFile=confFile
        self.xmldoc = minidom.parse(confFile)
        
        #most of the below are expected to be initialized in init function (should be called after constructor)
        self.targetRunDir= None
        self.targetHostname= None
        self.targetSSHusername= None
        self.targetSSHpassword = None
        self.coresToUse=None
        self.sourceFilePath=None #to be set in setSourceFilePath funtion
        super().__init__() #abstract class init
        
    def init(self): #should be called after constructor.. this can be overridden by child measurement classes to add new or use other configuration parameters..

        self.targetRunDir= self.tryGetStringValue('targetRunDir')
        self.targetHostname= self.tryGetStringValue('targetHostname')
        self.targetSSHusername= self.tryGetStringValue('targetSSHusername')
        self.targetSSHpassword = self.tryGetStringValue('targetSSHpassword')
        coresToUseString=self.tryGetStringValue('coresToUse')
        self.coresToUse=[]
        for core in coresToUseString.split(" "):
            self.coresToUse.append(int(core))
    
    def setSourceFilePath(self,sourceFilePath): #should be called before measurement or in the begining of the GA run if the source file path doesn't changes
        self.sourceFilePath=sourceFilePath
        
    ##helper functions to make clearer the code.. on exception the code doesn't terminate immediately but it does produce a warning message.. 
    ##This is the case because sometimes this might be desirable based on the functionality.. For instance bare metal runs won't use the ssh parameters 
    def tryGetStringValue(self,key):
        try:
            value=self.xmldoc.getElementsByTagName(key)[0].attributes['value'].value;
            return value
        except:
            print("Warning failed to read "+str(key))
        
    def tryGetIntValue(self,key):
        try:
            value=int(self.xmldoc.getElementsByTagName(key)[0].attributes['value'].value);
            return value
        except:
            print("Warning failed to read "+str(key))
    
    def tryGetFloatValue(self,key):
        try:
            value=float(self.xmldoc.getElementsByTagName(key)[0].attributes['value'].value);
            return value
        except:
            print("Warning failed to read "+str(key))
        
    #this function should return an array of results.. at least one item should be returned.. the defaultFitness.py class (that calculates indidual's fitness) assumes by convention that the first array
    #item is the fitness value 
    @abstractmethod
    def measure(self): 
        pass
    
    ## utility function for executing commands over ssh connection.. very common functionality
    def executeSSHcommand(self, command, continousAttempt=True, max_tries=10, wait=False):
        tries=0

        # print(f"Executing command: {command}")

        while True:
            try:
                ssh = SSHClient()
                ssh.set_missing_host_key_policy(client.AutoAddPolicy())
                ssh.connect(self.targetHostname, username=self.targetSSHusername, password=self.targetSSHpassword)
                stdin,stdout,stderr =ssh.exec_command(command)
                output = stdout.read().decode()

                # print(output)

                if "[1]" in output:
                    # print("Its a pid")
                    pid = output.strip().split()[1]
                    # print(f"pid: {pid} ")
                    # check if the process is still running
                    while True:
                        stdin, stdout, stderr = ssh.exec_command(f"ps -u {self.targetSSHusername} | awk '{{ print $1 }}'")

                        original_list = stdout.readlines()

                        # create a new list to store the numbers
                        running_pids = []

                        # iterate over the original list and convert each element to an integer
                        for element in original_list:
                            if element != 'PID\n':
                                running_pids.append(element.strip())

                        # print(running_pids)

                        if pid not in running_pids:
                            # process has finished
                            # print("Not found")
                            break
                        else:
                            # process is still running, sleep for 1s
                            # print("Process is still running. Sleeping")
                            sleep(1)

                    ssh.close()
                    return
                else:
                    # print("Its a result")
                    print("Average IPC : ", output.replace("\n", ""))
                    ssh.close()
                    return output.replace("\n", "")
                # lines=[]
                #
                # for line in stdout.readlines():
                #     lines.append(line)
                # ssh.close()
                # return lines
            except:
                if continousAttempt and tries<max_tries:
                    tries=tries+1
                    continue
                else:
                    raise("Exception: Unable to execute command "+str(command))


    # def executeSSHcommand(self, command, continuousAttempt=True, max_tries=10):
    #     tries = 0
    #     while True:
    #         try:
    #             ssh = SSHClient()
    #             ssh.set_missing_host_key_policy(client.AutoAddPolicy())
    #             ssh.connect(self.targetHostname, username=self.targetSSHusername, password=self.targetSSHpassword)
    #
    #             stdin, stdout, stderr = ssh.exec_command(command)
    #             # read the PID from the output
    #             pid = int(stdout.readline().strip())
    #
    #             # wait for the script to finish
    #             while True:
    #                 # check if the process has finished
    #                 exit_status = ssh.exec_command('kill -0 %d ; echo $?' % pid)[1].read().decode().strip()
    #                 if exit_status == '0':
    #                     sleep(1)  # wait for a second before checking again
    #                 else:
    #                     break
    #         except:
    #             if continuousAttempt and tries < max_tries:
    #                 tries = tries + 1
    #                 continue
    #             else:
    #                 raise Exception("Unable to execute command " + str(command))

    def executeSSHcommandNonBlocking(self,command,continousAttempt=True,max_tries=10):
        tries=0
        while True:
            try:
                ssh = SSHClient()
                ssh.set_missing_host_key_policy(client.AutoAddPolicy()) 
                ssh.connect(self.targetHostname, username=self.targetSSHusername, password=self.targetSSHpassword)
                ssh.exec_command(command)
                ssh.close()
                return
            except:
                if continousAttempt and tries<max_tries:
                    tries=tries+1
                    continue
                else:
                    raise("Exception: Unable to execute command "+str(command))


    def moveFile(self, generation, myID):

        command = "cp " + self.sourceFilePath + " " + self.targetRunDir + "/" + str(generation) + "_" + str(myID) + ".txt"
        # print("executing: " + command)
        subprocess.run(command,shell=True)


    #### utility function for copying the source file over ssh connection.. very common functionality        
    def copyFileOverFTP(self,continousAttempt=True):

        while True:
            try:
                ssh = SSHClient()
                ssh.set_missing_host_key_policy(client.AutoAddPolicy()) 
                ssh.connect(self.targetHostname, username=self.targetSSHusername, password=self.targetSSHpassword)
                sftp=ssh.open_sftp();
                sftp.put(self.sourceFilePath,self.targetRunDir+"/main.s")
                sftp.close()
                ssh.close()
                break    
            except:
                if continousAttempt:
                    continue
                else:
                    raise("Exception: Unable to copy file")
        
        
    def ping (self,host):
        """
        Returns True if host responds to a ping request
        """
        # Ping parameters as function of OS
        ping_str = "-n 1" if  platform.system().lower()=="windows" else "-c 1"
        
        # Ping
        return os.system("ping " + ping_str + " " + host) == 0  
            
    
    