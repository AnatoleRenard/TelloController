import socket
from threading import Thread, Lock
class Tello:
    #coms
    TELLO_IP     = "192.168.10.1"
    COMMAND_PORT = 8889
    STATE_PORT   = 8890
    LOCAL_PORT   = 9000

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(10)
        self.sock.bind(("", self.LOCAL_PORT))

        #set drone into sdk mode
        self.sendCommandReturn("command")

    def close(self):
        self.sock.close()
    
    def sendCommandNoReturn(self, command: str):
        #send command
        print(f"Sending Command: {command}")
        self.sock.sendto(command.encode('utf-8'), (self.TELLO_IP, self.COMMAND_PORT))

    def sendCommandReturn(self, command: str) -> str:
        #send command
        self.sendCommandNoReturn(command)

        #recv return
        data = "-1"
        try:
            data, address = self.sock.recvfrom(1024)
            data = data.decode('utf-8')
            print(f"Response: {data}")
        except socket.timeout:
            print("No response")
        
        return data

    def takeoff(self):
        self.sendCommandReturn("takeoff")
    
    def land(self):
        self.sendCommandReturn("land")
    