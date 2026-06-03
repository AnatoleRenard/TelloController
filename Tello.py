import socket
import numpy as np
from threading import Thread, Lock

class Tello:
    #coms
    TELLO_IP     = "192.168.10.1"
    COMMAND_PORT = 8889
    STATE_PORT   = 8890
    LOCAL_PORT   = 9000

    #limits
    MIN_DIST = 20
    MAX_DIST = 500
    MIN_ROT  = 1
    MAX_ROT  = 360
    MIN_SPD  = 10
    MAX_SPD  = 100
    MIN_RC   = -100
    MAX_RC   = 100

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

    """Control Commands"""
    #note: return comes in once operation is done
    def takeoff(self) -> str:
        return self.sendCommandReturn("takeoff")
    
    def land(self) -> str:
        return self.sendCommandReturn("land")
    
    def streamon(self) -> str:
        return self.sendCommandReturn("streamon")
    
    def streamoff(self) -> str:
        return self.sendCommandReturn("streamoff")
    
    def emergency(self) -> str:
        return self.sendCommandReturn("emergency")
    
    #move commands, move in cm, 0-500 cm
    def up(self, x: int) -> str:
        x = np.clip(x, self.MIN_DIST, self.MAX_DIST)
        return self.sendCommandReturn(f"up {x}")
    
    def down(self, x: int) -> str:
        x = np.clip(x, self.MIN_DIST, self.MAX_DIST)
        return self.sendCommandReturn(f"down {x}")
    
    def left(self, x: int) -> str:
        x = np.clip(x, self.MIN_DIST, self.MAX_DIST)
        return self.sendCommandReturn(f"left {x}")
    
    def right(self, x: int) -> str:
        x = np.clip(x, self.MIN_DIST, self.MAX_DIST)
        return self.sendCommandReturn(f"right {x}")
    
    def forward(self, x: int) -> str:
        x = np.clip(x, self.MIN_DIST, self.MAX_DIST)
        return self.sendCommandReturn(f"forward {x}")
    
    def back(self, x: int) -> str:
        x = np.clip(x, self.MIN_DIST, self.MAX_DIST)
        return self.sendCommandReturn(f"back {x}")
    
    #rotate commands, in degrees, [0, 360]
    def rotateCW(self, x: int) -> str:
        x = np.clip(x, self.MIN_ROT, self.MAX_ROT)
        return self.sendCommandReturn(f"cw {x}")
    
    def rotateCCW(self, x: int) -> str:
        x = np.clip(x, self.MIN_ROT, self.MAX_ROT)
        return self.sendCommandReturn(f"ccw {x}")
    
    #flips
    def flip(self, dir: str) -> str: #dir = either l,r,b,f
        return self.sendCommandReturn(f"flip {dir}")
    
    def flipForward(self) -> str:
        return self.sendCommandReturn("flip f")
    
    def flipBackward(self) -> str:
        return self.sendCommandReturn("flip b")
    
    def flipLeft(self) -> str:
        return self.sendCommandReturn("flip l")
    
    def flipRight(self) -> str:
        return self.sendCommandReturn("flip r")
    
    #go to x,y,z (from current point)
    #note: x, y, and z can't be between -20 and 20 simultaneously
    def go(self, x: int, y: int, z: int, speed: int) -> str:
        x = np.clip(x, -self.MAX_DIST, self.MAX_DIST)
        y = np.clip(y, -self.MAX_DIST, self.MAX_DIST)
        z = np.clip(z, -self.MAX_DIST, self.MAX_DIST)
        speed = np.clip(speed, self.MIN_SPD, self.MAX_SPD)

        return self.sendCommandReturn(f"go {x} {y} {z} {speed}")
    
    #stop (works at any time)
    def stop(self):
        return self.sendCommandReturn("stop")
    
    #curve
    def curve(self):
        pass

    #todo: mission pads functions

    """Set Commands"""
    #set speed to x cm/s (10 - 100)
    def setSpeed(self, x: int) -> str:
        x = np.clip(x, self.MIN_SPD, self.MAX_SPD)
        return self.sendCommandReturn(f"speed {x}")
    
    #rc control
    def rc(self, right: int, forward: int, up: int, yaw: int) -> str:
        right = np.clip(right, self.MIN_RC, self.MAX_RC)
        forward = np.clip(forward, self.MIN_RC, self.MAX_RC)
        up = np.clip(up, self.MIN_RC, self.MAX_RC)
        yaw = np.clip(yaw, self.MIN_RC, self.MAX_RC)

        return self.sendCommandReturn(f"rc {right} {forward} {up} {yaw}")
    
    #setup wifi
    def setWifi(self, name: str, pswd: str) -> str:
        return self.sendCommandReturn(f"wifi {name} {pswd}")

    #mission pad on
    def missonPadOn(self) -> str:
        return self.sendCommandReturn(f"mon")

    #mission pad off
    def missonPadOff(self) -> str:
        return self.sendCommandReturn(f"moff")
    
    #turn misson pad detection on and off -> 0 down only, 1 forward only, 2 both
    def missionPadDetection(self, x: int) -> str:
        return self.sendCommandReturn(f"mdirection {x}")
    
    """Read Commands"""
    #get speed in cm/s
    def getSpeed(self) -> int:
        return int(self.sendCommandReturn("speed?"))
    
    #get battery
    def getBattery(self) -> int:
        return int(self.sendCommandReturn("battery?"))
    
    #get time of flight in seconds
    def getFlightTime(self) -> int:
        return int(self.sendCommandReturn("time?"))
    
    #get wifi quality
    def getWifiQuality(self) -> int:
        return int(self.sendCommandReturn("wifi?"))
    
    #get sdk
    def getSDKVersion(self) -> str:
        return self.sendCommandReturn("sdk?")

    #get serial number
    def getSerialNumber(self) -> str:
        return self.sendCommandReturn("sn?")