import Tello, time, pygame

#Tello
tello = Tello.Tello()
tello.streamon()
tello.getBattery()
tello.motoron()

#pygame
pygame.init()
window = pygame.display.set_mode((960, 720))
clock = pygame.time.Clock()

run = True
while run:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            run = False
    
    frame = tello.getFrame()
    if frame is not None:
        window.blit(pygame.surfarray.make_surface(frame), (0, 0, 960, 720))

    pygame.display.flip()
    clock.tick(60)

tello.motoroff()
tello.streamoff()
tello.close()