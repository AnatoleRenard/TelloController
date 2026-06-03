import Tello, time

tello = Tello.Tello()

tello.streamon()

tello.setDownvision(1)

tello.motoron()
time.sleep(4)
tello.motoroff()

tello.setDownvision(0)
tello.streamoff()

tello.close()