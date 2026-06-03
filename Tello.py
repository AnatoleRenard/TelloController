import socket, av, time
import numpy as np
from threading import Thread, Lock, Event
from numpy.typing import NDArray
from PIL import Image
from datetime import datetime

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

    #speeds
    FAST_SPD = 100
    SLOW_SPD = 50

    #fps
    FPS_5  = "low"
    FPS_15 = "middle"
    FPS_30 = "high"

    #res
    HIGH = "high"
    LOW = "low"

    #time
    TIMEOUT = 0.05

    def __init__(self):
        #event
        self.endEvent = Event()

        #settings
        self.streamOn = False
        self.flying = False
        self.motorOn = False
        self.fastMode = False
        self.recording = False
        self.startRecording = False
        self.endRecording = False

        #time since last command
        self.lastCommandTime = time.time()

        #socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(10)
        self.sock.bind(("", self.LOCAL_PORT))

        #image
        self.frame: NDArray[np.uint8]
        self.frame = None
        self.imageLock = Lock()
        self.recordLock = Lock()
        self.outputContainer = None
        self.outputStream = None
        Thread(target=self.streamThread).start()

        #drone state
        self.state: dict[str, str] = {"mid": "-2", "x": "-200", "y": "-200", "z": "-200", "mpry": "0",
                                 "pitch": "0", "roll": "0", "yaw": "0", "vgx": "0", "vgy": "0", "vgz": "0",
                                 "templ": "0", "tmph": "0", "tof": "0", "h": "0", "bat": "0", "baro": "0",
                                 "time": "0", "agx": "0", "agy": "0", "agz": "0"}
        self.stateLock = Lock()
        Thread(target=self.stateThread).start()

        #set drone into sdk mode
        self.sendCommandReturn("command")

    def close(self):
        if self.motorOn:
            self.motoroff()
        
        if self.streamOn:
            if self.recording:
                self.video()
            self.streamoff()
        
        self.endEvent.set()
        self.sock.close()
    
    def sendCommandNoReturn(self, command: str):
        #send command
        self.sock.sendto(command.encode('utf-8'), (self.TELLO_IP, self.COMMAND_PORT))

    def sendCommandReturn(self, command: str) -> str:
        #make sure not too many commands sent at once
        while time.time() - self.lastCommandTime < self.TIMEOUT:
            time.sleep(0.01)
        
        #send command
        print(f"Sending Command: {command}")
        self.sendCommandNoReturn(command)
        
        #update time
        self.lastCommandTime = time.time()

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
        self.flying = True
        return self.sendCommandReturn("takeoff")
    
    def land(self) -> str:
        self.flying = False
        return self.sendCommandReturn("land")
    
    def streamon(self) -> str:
        resp = self.sendCommandReturn("streamon")
        self.streamOn = True
        return resp
    
    def streamoff(self) -> str:
        self.streamOn = False
        if self.recording:
            self.video()
        return self.sendCommandReturn("streamoff")
    
    def emergency(self) -> str:
        print("Sending Command: emergency")
        return self.sendCommandNoReturn("emergency")
    
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
    
    #turn motor on and off for cooling while on ground
    def motoron(self) -> str:
        self.motorOn = True
        return self.sendCommandReturn("motoron")
    
    def motoroff(self) -> str:
        self.motorOn = False
        return self.sendCommandReturn("motoroff")
    
    #throw to takeoff, launches within 5 seconds
    def throwfly(self) -> str:
        return self.sendCommandReturn("throwfly")
    
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

    #reboot drone (no response = success)
    def reboot(self) -> str:
        self.sendCommandReturn("streamoff")
        self.sendCommandReturn("motoroff")
        print("Sending Command: reboot")
        return self.sendCommandNoReturn("reboot")

    """Set Commands"""
    #set speed to x cm/s (10 - 100)
    def setSpeed(self, x: int) -> str:
        x = np.clip(x, self.MIN_SPD, self.MAX_SPD)
        return self.sendCommandReturn(f"speed {x}")
    
    #rc control
    def rc(self, right: int, forward: int, up: int, yaw: int):
        right = np.clip(right, self.MIN_RC, self.MAX_RC)
        forward = np.clip(forward, self.MIN_RC, self.MAX_RC)
        up = np.clip(up, self.MIN_RC, self.MAX_RC)
        yaw = np.clip(yaw, self.MIN_RC, self.MAX_RC)

        return self.sendCommandNoReturn(f"rc {right} {forward} {up} {yaw}")
    
    #setup wifi -> drone reboots after 3s
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
    
    #change port for state and video
    def changePorts(self, info: int, video: int) -> str:
        return self.sendCommandReturn(f"port {info} {video}")

    #change fps -> using pre defined settings
    def setFPS(self, fps: str) -> str:
        if self.recording: return "Error: Recording"
        return self.sendCommandReturn(f"setfps {fps}")
    
    #change bitrate for video - > (0 - 5) auto, 1Mbps, 2Mbps, 3Mbps, 4Mbps, 5Mbps
    def setBitRate(self, bitrate: int) -> str:
        if self.recording: return "Error: Recording"
        return self.sendCommandReturn(f"setbitrate {bitrate}")
    
    #set res to either 480p or 720p using "high" and "low"
    def setResolution(self, res: str) -> str:
        if self.recording: return "Error: Recording"
        return self.sendCommandReturn(f"setresolution {res}")
    
    #change camera to downvision 0 no 1 yes
    def setDownvision(self, downvision: int) -> str:
        return self.sendCommandReturn(f"downvision {downvision}")

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

    #get wifi version
    def getWifiVersion(self) -> str:
        return self.sendCommandReturn("wifiversion?")

    """Stream for Video"""
    #start video recording
    def startVideo(self, frame):
        self.startRecording = False
        self.recording = True

        self.outputContainer = av.open(datetime.now().strftime("output/%Y%m%d_%H%M%S.mp4"), mode="w")
        self.outputStream = self.outputContainer.add_stream("h264", rate=30)
        self.outputStream.width = frame.width
        self.outputStream.height = frame.height
        self.outputStream.pix_fmt = "yuv420p"

    def endVideo(self):
        if not self.recording:
            return
        
        self.endRecording = False
        self.recording = False

        #flush encoder
        for packet in self.outputStream.encode():
            self.outputContainer.mux(packet)
        
        self.outputContainer.close()

        self.outputContainer = None
        self.outputStream = None

    #get stream if video on
    def streamThread(self):
        while not self.endEvent.is_set():
            if self.streamOn:
                container = av.open("udp://0.0.0.0:11111", timeout=5)

                try:
                    for frame in container.decode(video=0):
                        if not self.streamOn:
                            break
                        
                        with self.recordLock:
                            if self.startRecording:
                                self.startVideo(frame)
                            if self.endRecording:
                                self.endVideo()
                        
                        if self.recording:
                            for packet in self.outputStream.encode(frame):
                                self.outputContainer.mux(packet)

                        img = frame.to_ndarray(format="rgb24")

                        with self.imageLock:
                            self.frame = np.transpose(img, (1, 0, 2))

                except Exception as e:
                    print("Stream error: ", e)
                
                #safety net
                if self.recording:
                    self.endVideo()
                
                container.close()
            time.sleep(1)
    
    def getFrame(self) -> NDArray[np.uint8]:
        if self.streamOn:
            with self.imageLock:
                return self.frame
        return None
    

    """Stream for State"""
    #get drone states
    def stateThread(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        sock.bind(("", self.STATE_PORT))

        while not self.endEvent.is_set():
            data = "-1"
            try:
                data, address = sock.recvfrom(1024)
                data = data.decode('utf-8')
            except socket.timeout:
                print("No State data for a Second!")

            with self.stateLock:
                for item in data.split(";"):
                    split = item.split(":")

                    if len(split) < 2:
                        continue

                    key = split[0]
                    value = split[1]
                    self.state[key] = value        
        sock.close()
    
    #get angles
    def getPitch(self) -> int:
        with self.stateLock:
            return int(self.state["pitch"])
    
    def getRoll(self) -> int:
        with self.stateLock:
            return int(self.state["roll"])
    
    def getYaw(self) -> int:
        with self.stateLock:
            return int(self.state["yaw"])
    
    #get velocity in cm/s
    def getVelocityX(self) -> int:
        with self.stateLock:
            return int(self.state["vgx"])
    
    def getVelocityY(self) -> int:
        with self.stateLock:
            return int(self.state["vgy"])
    
    def getVelocityZ(self) -> int:
        with self.stateLock:
            return int(self.state["vgz"])
    
    #get temp in degrees
    def getTempL(self) -> int:
        with self.stateLock:
            return int(self.state["templ"])
    
    def getTempH(self) -> int:
        with self.stateLock:
            return int(self.state["temph"])
    
    #distance of flight in cm
    def getTimeOfFlihgtDistance(self) -> int:
        with self.stateLock:
            return int(self.state["tof"])
    
    #height in cm (relative to takeoff point)
    def getHeight(self) -> int:
        with self.stateLock:
            return int(self.state["h"])
    
    #get battery percentage
    def getBatteryState(self) -> int:
        with self.stateLock:
            return int(self.state["bat"])

    #height (barometer, m)
    def getHeightBarometer(self) -> float:
        with self.stateLock:
            return float(self.state["baro"])
    
    #get motor on time (sec)
    def getMotorOnTime(self) -> int:
        with self.stateLock:
            return int(self.state["time"])
    
    #get accel in cm/s2
    def getAccelX(self) -> float:
        with self.stateLock:
            return float(self.state["agx"])
    
    def getAccelY(self) -> int:
        with self.stateLock:
            return float(self.state["agy"])
    
    def getAccelZ(self) -> int:
        with self.stateLock:
            return float(self.state["agz"])

    """None UDP commands"""
    #take bool to set mode
    def setFastMode(self, mode):
        self.fastMode = mode
    
    #take picture
    def picture(self):
        Image.fromarray(self.getFrame()).transpose(Image.Transpose.ROTATE_270).save("output/" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ".jpg")
    
    #start video
    def video(self):
        if self.streamOn:
            if self.recording:
                with self.recordLock:
                    self.endRecording = True
            else:
                with self.recordLock:
                    self.setResolution(self.HIGH)
                    self.setFPS(self.FPS_30)
                    self.startRecording = True