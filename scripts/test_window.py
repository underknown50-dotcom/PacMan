"""Minimal display test script.

Verifies Pygame window initialization, 60 FPS clock, and key events.
"""

import pygame


def main() -> None:
    """Initialize test window and run a minimal square-moving event loop."""
    pygame.init()

    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("Pac-Man Window Test")

    clock = pygame.time.Clock()

    x = 320
    y = 240
    speed = 5

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            x -= speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            x += speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            y -= speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            y += speed

        screen.fill((0, 0, 0))
        pygame.draw.rect(screen, (255, 255, 0), (x, y, 20, 20))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
