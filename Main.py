import Tello, time

tello = Tello.Tello()

tello.takeoff()
time.sleep(2)

tello.land()

tello.close()