import Tello, time, pygame

#Tello
tello = Tello.Tello()

#pygame
IMAGE_SIZE = (640, 480)
WINDOW_SIZE = (960, 720)
pygame.init()
window = pygame.display.set_mode(WINDOW_SIZE)
clock = pygame.time.Clock()

#joystick
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()
axis = [0.0, 0.0, 0.0, 0.0, -1.0, -1.0]

run = True
while run:
    flipped = False

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            run = False
        
        elif e.type == pygame.JOYAXISMOTION:
            axis[e.axis] = e.value if e.value > 0.1 or e.value < -0.1 else 0
        
        elif e.type == pygame.JOYBUTTONDOWN:
            if e.button == 0: #a
                tello.throwfly()
            elif e.button == 1: #b
                if tello.streamOn:
                    tello.streamoff()
                else:
                    tello.streamon()
            elif e.button == 2: #x
                if tello.motorOn:
                    tello.motoroff()
                else:
                    tello.motoron()
            elif e.button == 3: #y
                tello.emergency()
            elif e.button == 9: #lBump
                tello.picture()
            elif e.button == 10: #rBump
                tello.video()
            elif e.button == 4: #Back
                tello.reboot()
                run = False
            elif e.button == 6: #Start
                tello.stop()
            elif e.button == 5: #Home
                if tello.flying:
                    tello.land()
                else:
                    tello.takeoff()
            elif e.button == 7: #LStick
                if tello.fastMode:
                    tello.setFastMode(False)
                else:
                    tello.setFastMode(True)
            elif e.button == 8: #RStick
                pass
            
            #dpad
            elif e.button == 11 and not flipped: #up
                tello.flipForward()
                flipped = True
            elif e.button == 12 and not flipped: #down
                tello.flipBackward()
                flipped = True
            elif e.button == 13 and not flipped:
                tello.flipLeft()
                flipped = True
            elif e.button == 14 and not flipped:
                tello.flipRight()
                flipped = True
    
    maxSpd = tello.FAST_SPD if tello.fastMode else tello.SLOW_SPD
    tello.rc(maxSpd * axis[0], maxSpd * -axis[1], maxSpd * -axis[3], maxSpd * axis[2])
    
    frame = tello.getFrame()
    if frame is not None:
        window.blit(pygame.transform.scale(pygame.surfarray.make_surface(frame), IMAGE_SIZE), (0, 0))

    pygame.display.flip()
    clock.tick(60)

tello.close()