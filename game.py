import pygame as pg
from math import cos, sin, tan, pi
import time
from settings import *
from enemies import *
from random import randint
import os

pg.init()

dt = 1
debug = False

UiText = pg.font.SysFont("arial", 30)
pg.mouse.set_visible(False)
pg.event.set_grab(True)

def get_texture(path, res=(TEXTURE_SIZE, TEXTURE_SIZE)):
    texture = pg.image.load(path)
    texture = pg.transform.scale(texture, res)
    return texture

def load_wall_textures():
    return {
        0: get_texture("textures/1.png"),
        1: get_texture("textures/2.png"),
        2: get_texture("textures/3.png")
    }

objects = [pg.rect.Rect(0, 0, WIDTH, 100), pg.rect.Rect(WIDTH-100, 0, 100, HEIGHT), pg.rect.Rect(0, HEIGHT-100, WIDTH, 100), pg.rect.Rect(0, 0, 100, HEIGHT), pg.rect.Rect(200, 200, 100, 100), pg.rect.Rect(400, 600, 100, 25)]
objectTypes = [0, 0, 0, 0, 1, 1]

enemies = []

textures = load_wall_textures()

class Player:
    def __init__(self, x, y, rot, num_rays):
        self.x = x
        self.y = y
        self.rot = rot
        self.num_rays = num_rays
        self.fov = FOV
        self.move_speed = 2.5
        self.rot_speed = 0.05
        self.health = 5
        self.score = 0

    def move(self, dx, dy):
        new_x = self.x + dx * dt * 32
        new_y = self.y + dy * dt * 32

        # Check if the new position is within the screen boundaries or doesn't collide with objects.
        if 0 < new_x < WIDTH and 0 < new_y < HEIGHT and not self.checkCollision(new_x, new_y):
            self.x = new_x
            self.y = new_y

    def checkCollision(self, x, y):
        for obj in objects:
            if x > obj.x and x < obj.x + obj.width and y > obj.y and y < obj.y + obj.height:
                return True

    def drawRay(self, angle, plainMap, objects) -> int:
        x = int(self.x)
        y = int(self.y)

        ox = x
        oy = y

        grad = (cos(angle), sin(angle))

        y_buff = []

        for i in range(int(DISTANCE)):
            for e, obj in enumerate(objects):
                if x > obj.x and x < obj.x + obj.width and y > obj.y and y < obj.y + obj.height:
                    if debug:
                        l = pg.draw.line(screen, (255, 255, 255), (ox, oy), (x, y))
                        pg.display.update(l)

                    y_buff.append((i, (x, y), obj, e, False))
                    return y_buff

            for e, enemy in enumerate(enemies):
                if x > enemy.x - enemy.image.get_width() / 2 and x < enemy.x + enemy.image.get_width() / 2 and y > enemy.y - enemy.image.get_height() / 2 and y < enemy.y + enemy.image.get_height() / 2:
                    if debug:
                        l = pg.draw.line(screen, (255, 255, 255), (ox, oy), (x, y))
                        pg.display.update(l)

                    y_buff.append((i, (x, y), enemy, e, True))

            x += grad[0]
            y += grad[1]

        if debug:
            l = pg.draw.line(screen, (255, 255, 255), (ox, oy), (x, y))
            pg.display.update(l)

        y_buff.append((DISTANCE, (x, y), None, None, False))
        return y_buff

    def rayTrace(self, plainMap, objects) -> list:
        y_buff = []
        rayAngle = self.fov / self.num_rays # maybe a - 1 after num rays

        for i in range(int(self.num_rays + 1)):
            #print((i+1)*rayAngle)
            ret = self.drawRay((self.rot - self.fov / 2) + i * rayAngle, plainMap, objects)
            #print((self.rot - self.fov / 2) + (i+1) * rayAngle * 57.2957795 * 21.333333333333)
            for distance, endPoint, obj, index, enemy in ret:
                distance *= cos(self.rot - (self.rot - self.fov / 2) + (i) * rayAngle + pi/2)
                y_buff.append((distance, endPoint, (self.rot - self.fov / 2) + i * rayAngle * 57.2957795 * 13.25, obj, index, enemy))

        return y_buff
    
    def castGunRay(self, plainMap, objects, enemies):
        rayAngle = self.rot
        x = int(self.x)
        y = int(self.y)

        ox = x
        oy = y

        grad = (cos(rayAngle), sin(rayAngle))

        distanceMultiplier = 2

        for i in range(int(DISTANCE/distanceMultiplier)):
            for e, obj in enumerate(objects):
                if x > obj.x and x < obj.x + obj.width and y > obj.y and y < obj.y + obj.height:
                    if debug:
                        l = pg.draw.line(screen, (255, 0, 255), (ox, oy), (x, y))
                        pg.display.update(l)
                    return None
                
            for e, enemy in enumerate(enemies):
                if x > enemy.x - enemy.image.get_width() / 2.5 and x < enemy.x + enemy.image.get_width() / 2.5 and y > enemy.y - enemy.image.get_height() / 2.5 and y < enemy.y + enemy.image.get_height() / 2.5:
                    if debug:
                        l = pg.draw.line(screen, (255, 0, 255), (ox, oy), (x, y))
                        pg.display.update(l)
                    return enemy

            x += grad[0] *distanceMultiplier
            y += grad[1] *distanceMultiplier

        return None
    
class Gun(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.idle = pg.image.load("shotgun/0.png").convert_alpha()
        self.idle = pg.transform.scale(self.idle, (int(self.idle.get_width() / 6), int(self.idle.get_height() / 3)))
        self.shoot = [pg.image.load("shotgun/1.png").convert_alpha(), pg.image.load("shotgun/2.png").convert_alpha(), pg.image.load("shotgun/3.png").convert_alpha(), pg.image.load("shotgun/4.png").convert_alpha(), pg.image.load("shotgun/5.png").convert_alpha()]
        self.shoot = [pg.transform.scale(i, (int(i.get_width() / 6), int(i.get_height() / 3))) for i in self.shoot]
        self.allAnimations = [self.idle]
        self.allAnimations.extend(self.shoot)
        self.currentAnimation = 0
        self.image = self.allAnimations[self.currentAnimation]
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH/2, HEIGHT/2)
        self.lastAnimation = time.time()
        self.animationSpeed = 0.1
        self.shooting = False
        self.rect.y = HEIGHT - self.rect.height
        self.shootSound = pg.mixer.Sound("sounds/shotgun.wav")

    def update(self):
        if self.shooting:
            if self.currentAnimation < len(self.allAnimations) - 1:
                if self.lastAnimation < time.time() - self.animationSpeed:
                    self.currentAnimation += 1
                    self.image = self.allAnimations[self.currentAnimation]
                    self.lastAnimation = time.time()
            else:
                self.shooting = False
                self.currentAnimation = 0
                self.image = self.allAnimations[self.currentAnimation]
    
def main(width, height, resolution_scale, fov, color_darken_scale, gameMap):
    global dt
    global RECTS_ON_SCREEN
    global RAY_HITS
    global screen
    
    global WIDTH
    global HEIGHT
    global RESOLUTION_SCALE
    global FOV
    global COLOR_DARKEN_SCALE

    global enemies

    WIDTH = width
    HEIGHT = height
    RESOLUTION_SCALE = resolution_scale
    FOV = fov
    COLOR_DARKEN_SCALE = color_darken_scale

    screen = pg.display.set_mode((WIDTH, HEIGHT), pg.DOUBLEBUF | pg.HWACCEL)
    pg.display.set_caption("Foxenstine")

    plainMap = []
    #objects = [pg.rect.Rect(200, 200, 100, 100), pg.rect.Rect(400, 600, 100, 25)]
    player = Player(600, 600, 3.14159265, int(WIDTH)/RESOLUTION_SCALE)
    lastSwitch = time.time()
    lastDt = time.time()

    gun = Gun()

    enemies = [caco(500, 500), caco(1000, 500)]

    theme = pg.mixer.Sound("sounds/theme.mp3")
    enemyHurt = pg.mixer.Sound("sounds/npc_pain.wav")
    enemyDeath = pg.mixer.Sound("sounds/npc_death.wav")
    playerPain = pg.mixer.Sound("sounds/player_pain.wav")
    # play theme 70% volume and loop forever
    theme.play(-1)
    theme.set_volume(0.7)

    try:
        with open(f"maps/{gameMap}.py", "r") as f:
            data = f.read()
            f.close()
    except FileNotFoundError:
        pg.quit()
        return
    
    with open("tempGameLoader.py", "w") as f:
        f.write(data)
        f.close()

    import tempGameLoader

    objects, objectTypes = tempGameLoader.loadMap()

    os.remove("tempGameLoader.py")

    clock = pg.time.Clock()
    running = True
    while running:
        pg.event.set_grab(True)
        clock.tick(60)
        pg.display.set_caption("Foxenstine!!!    |    FPS: " + str(int(clock.get_fps())) + "    Delta time: " + str(round(dt, 2)) + "    Resolution Scale: " + str(RESOLUTION_SCALE) + "    Resolution: " + str(WIDTH) + "x" + str(HEIGHT) + "    FOV: " + str(FOV) + "    Ray Hits: " + str(int(RAY_HITS)) + "%" + "    Color darken scale: " + str(COLOR_DARKEN_SCALE))
        screen.fill((0,0,0))

        dt = time.time() - lastDt
        lastDt = time.time()

        pg.draw.rect(screen, (0, 100, 255), (0, 0, WIDTH, HEIGHT/2))
        pg.draw.rect(screen, (140, 100, 0), (0, HEIGHT/2, WIDTH, HEIGHT))

        for enemy in enemies:
            updateResult = enemy.update(dt, player.x, player.y, objects)
            if updateResult > 0 and updateResult <= CACO_ATK_DIST:
                player.health -= 1
                playerPain.play()
                if player.health <= 0:
                    pg.quit()
                    running = False

        if running == False:
            break

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                running = False
            if event.type == pg.MOUSEMOTION:
                player.rot += event.rel[0] * 0.002
                player.rot += event.rel[1] * 0.002
 
        if running == False:
            break

        keys=pg.key.get_pressed()

        dx, dy = 0, 0

        if keys[pg.K_w]:
            dx = player.move_speed * cos(player.rot)
            dy = player.move_speed * sin(player.rot)
        if keys[pg.K_s]:
            dx = -player.move_speed * cos(player.rot)
            dy = -player.move_speed * sin(player.rot)
        if keys[pg.K_a]:
            dx = player.move_speed * cos(player.rot - pi/2)
            dy = player.move_speed * sin(player.rot - pi/2)
        if keys[pg.K_d]:
            dx = player.move_speed * cos(player.rot + pi/2)
            dy = player.move_speed * sin(player.rot + pi/2)

        player.move(dx, dy)

        if keys[pg.K_LEFT]:
            player.rot -= player.rot_speed * dt * 32
        if keys[pg.K_RIGHT]:
            player.rot += player.rot_speed * dt * 32

        if player.rot > pi*2:
            player.rot = 0
        elif player.rot < -(pi*2):
            player.rot = 0

        if keys[pg.K_LSHIFT] and lastSwitch < time.time() - 0.5:
            global debug
            debug = not debug
            lastSwitch = time.time()

        if keys[pg.K_SPACE] or pg.mouse.get_pressed()[0]:
            if not gun.shooting:
                gun.shootSound.play()
                gun.shooting = True
                objHit = player.castGunRay(plainMap, objects, enemies)

                if objHit != None:
                    objHit.health -= 1
                    if objHit.health <= 0:
                        enemyDeath.play()
                        objHit.dead = True
                        player.score += 1
                        enemies.remove(objHit)
                        enemies.append(caco(randint(100, WIDTH-100), randint(100, HEIGHT-100)))
                    else:
                        enemyHurt.play()

        if debug:
            for obj in objects:
                pg.draw.rect(screen, (255, 255, 255), obj)

            for enemy in enemies:
                smallEnemy = pg.transform.scale(enemy.image, (enemy.image.get_width() // 2, enemy.image.get_height() // 2))
                screen.blit(smallEnemy, enemy.rect)

        y_buff = player.rayTrace(plainMap, objects)

        if debug == False:
            if len(y_buff) > 0:
                RECTS_ON_SCREEN = 0

            lastObj = 99999999999
            x_clip_start = 0

            enemiesRendered = []
            enemyDistances = []
            enemiesEx = []

            for y in y_buff:
                if y[4] == None:
                    continue
                #if player.y + y[0] < HEIGHT:
                #    color = min(255, abs(255 / ((y[0] + 0.01) / 100)))
                #    l = pg.draw.line(screen, (color, color, color), (y[2], HEIGHT-min(HEIGHT/2, y[0])), (y[2], 0), RESOLUTION_SCALE)
                #    pg.display.update(l)

                # define all y values
                # y[0] = distance
                # y[1] = endpoint
                # y[2] = angle
                # y[3] = object
                # y[4] = object index
                # y[5] = enemy

                if y[5]:
                    if y[3].dead or y[3] in enemiesEx:
                        continue
                    enemiesRendered.append(y)
                    enemyDistances.append(y[0])
                    enemiesEx.append(y[3])
                    continue

                proj_height = abs((SCREEN_DIST / (y[0] + 0.01)) * 100)

                color = min(255, abs(255 / ((y[0] + 0.01) / COLOR_DARKEN_SCALE)))
                #pg.draw.line(screen, (color, color, color), (y[2], HEIGHT/2 - proj_height/2), (y[2], HEIGHT/2 + proj_height/2), RESOLUTION_SCALE)
                #pg.draw.rect(screen, (color, color, color), (y[2], HEIGHT/2 + proj_height/2, RESOLUTION_SCALE, abs(proj_height)))

                # draw textures
                texture = textures[objectTypes[y[4]]]

                # clip texture x to resolution scale
                #texture = texture.subsurface((int(y[0] * 0.1) % TEXTURE_SIZE, 0, 1, TEXTURE_SIZE))

                if lastObj != y[4] or x_clip_start > texture.get_width():
                    x_clip_start = 0
                else:
                    texture = texture.subsurface((x_clip_start, 0, 1, TEXTURE_SIZE))
                    x_clip_start += RESOLUTION_SCALE

                texture = pg.transform.scale(texture, (RESOLUTION_SCALE, int(proj_height)))

                # change texture color based on distance
                texture.fill((color, color, color), special_flags=pg.BLEND_MULT)

                #screen.blit(texture, (y[2] + (WIDTH/2 - player.x) % RESOLUTION_SCALE // 32, HEIGHT/2 - proj_height/2))
                screen.blit(texture, ((y[2]), HEIGHT/2 - proj_height/2))

                lastObj = y[4]

                RECTS_ON_SCREEN += 1

            for i, enemy in enumerate(enemiesRendered):
                distance = enemy[0]
                endpoint = enemy[1]
                angle = enemy[2]
                obj = enemy[3]
                index = enemy[4]
                enemy = enemy[5]
                #color = min(255, abs(255 / ((distance + 0.01) / COLOR_DARKEN_SCALE)))
                texture = obj.image
                #texture.fill((color, color, color), special_flags=pg.BLEND_MULT)
                # scale texture to distance
                proj_height = abs((SCREEN_DIST / (distance + 0.01)) * 100)
                try:
                    texture = pg.transform.scale(texture, (obj.image.get_width() // 3 * int(proj_height) / 100, obj.image.get_height() // 3 * int(proj_height) / 100))
                except:
                    texture = pg.transform.scale(texture, (obj.image.get_width() *2, obj.image.get_height() *2))
                    
                screen.blit(texture, (angle, HEIGHT/3))

        RAY_HITS = RECTS_ON_SCREEN / (1200 / RESOLUTION_SCALE + 1) * 100

        gun.update()
        screen.blit(gun.image, gun.rect)

        screen.blit(UiText.render("Health: " + str(player.health), True, (255, 255, 255)), (20, HEIGHT - 50))
        screen.blit(UiText.render("Score: " + str(player.score), True, (255, 255, 255)), (WIDTH - 200, HEIGHT - 50))

        pg.display.flip()

if __name__ == "__main__":
    main(WIDTH, HEIGHT, RESOLUTION_SCALE, FOV, COLOR_DARKEN_SCALE)