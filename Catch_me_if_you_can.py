import pygame
from pytmx.util_pygame import load_pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Catch Me If You Can")
clock = pygame.time.Clock()
p_right = [pygame.transform.scale(pygame.image.load(fr"C:\Users\vignan\Desktop\carrot\p{i}.png"), (50, 50)) for i in range(1, 6)]
p_left = [pygame.transform.flip(img, True, False) for img in p_right]
r_right = [pygame.transform.scale(pygame.image.load(fr"C:\Users\vignan\Desktop\carrot\r{i}.png"), (50, 50)) for i in range(1, 6)]
r_left = [pygame.transform.flip(img, True, False) for img in r_right]
p_frames = p_right
r_frames = r_left
index_p = 0
index_r = 0
frame_timer = 0
frame_delay = 5
player1_x, player1_y = 30, 400
player2_x, player2_y = 730, 400
vel = 5
pygame.mixer.music.load(r"C:\Users\vignan\Desktop\carrot\a-hero-of-the-80s-126684.mp3")
pygame.mixer.music.play(-1)
tile_data = load_pygame(r"C:\Users\vignan\untitled.tmx")
font = pygame.font.SysFont(None, 48)
game_state = "menu"
button_rect = pygame.Rect(800 // 2 - 100, 600 // 2 - 25, 250, 50)
run = True
while run:
    keys = pygame.key.get_pressed()
    screen.fill((0, 0, 0))
    if game_state == "menu":
        pygame.draw.rect(screen, (0, 128, 255), button_rect)
        label = font.render("Start Game", True, (255, 255, 255))
        screen.blit(label, (button_rect.x + 30, button_rect.y + 10))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(event.pos):
                game_state = "playing"

    elif game_state == "playing":
        for layer in tile_data.visible_layers:
            for x, y, gid in layer:
                tile = tile_data.get_tile_image_by_gid(gid)
                if tile:
                    screen.blit(tile, (x * 32, y * 32))

        if keys[pygame.K_LEFT]:
            player1_x -= vel
            p_frames = p_left
        elif keys[pygame.K_RIGHT]:
            player1_x += vel
            p_frames = p_right

        if keys[pygame.K_UP]:
            player1_y -= vel
        if keys[pygame.K_DOWN]:
            player1_y += vel

        if keys[pygame.K_a]:
            player2_x -= vel
            r_frames = r_left
        elif keys[pygame.K_d]:
            player2_x += vel
            r_frames = r_right

        if keys[pygame.K_w]:
            player2_y -= vel
        if keys[pygame.K_s]:
            player2_y += vel

        frame_timer += 1
        if frame_timer >= frame_delay:
            index_p = (index_p + 1) % len(p_frames)
            index_r = (index_r + 1) % len(r_frames)
            frame_timer = 0

        screen.blit(p_frames[index_p], (player1_x, player1_y))
        screen.blit(r_frames[index_r], (player2_x, player2_y))

        pygame.draw.rect(screen, (255, 0, 0), (770, 30, 25, 25))
        pygame.draw.polygon(screen, (255, 255, 0), [(782.5, 10), (770, 30), (795, 30)])

        if player1_x + 50 >= 770 and player1_y <= 55:
            game_state = "won"

        if abs(player1_x - player2_x) < 40 and abs(player1_y - player2_y) < 40:
            game_state = "lost"

    elif game_state == "won":
        msg = font.render("Player 1 Wins!", True, (0, 255, 0))
        screen.blit(msg, (300, 250))
    elif game_state == "lost":
        msg = font.render("Player 2 Caught Player 1!", True, (255, 0, 0))
        screen.blit(msg, (200, 250))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()
    clock.tick(60)
pygame.quit()
