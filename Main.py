import Tello, time

tello = Tello.Tello()

tello.getBattery()
tello.getWifiQuality()
tello.getSDKVersion()

tello.close()