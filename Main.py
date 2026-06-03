import Tello, time, pygame

#Tello
tello = Tello.Tello()
tello.streamon()
tello.getBattery()
tello.motoron()

#pygame
IMAGE_SIZE = (640, 480)
WINDOW_SIZE = (960, 720)
pygame.init()
window = pygame.display.set_mode(WINDOW_SIZE)
clock = pygame.time.Clock()

run = True
while run:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            run = False
                
    
    frame = tello.getFrame()
    if frame is not None:
        window.blit(pygame.transform.scale(pygame.surfarray.make_surface(frame), IMAGE_SIZE), (0, 0))

    pygame.display.flip()
    clock.tick(60)

tello.motoroff()
tello.streamoff()
tello.close()