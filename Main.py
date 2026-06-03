import Tello, time

tello = Tello.Tello()

tello.motoron()
time.sleep(4)
tello.motoroff()

tello.close()