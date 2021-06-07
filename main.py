import pygame
from pygame.locals import *

import sys
import time
import random
import json
import os


CARS = ['car1.png', 'car2.png', 'car3.png', 'car4.png', 'car5.png', 'car6.png', 'car7.png', 'car8.png']

settings = open("settings.txt", "r", encoding="utf-8")
all_settings = json.loads(settings.read())
settings.close()
# Globals and initialization
SCORES = []
pygame.init()
begin_time = time.time()
fps = all_settings['fps']
fpsClock = pygame.time.Clock()

width, height = all_settings["width"], all_settings["height"]
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Drag Racing")
pygame.display.set_icon(pygame.image.load("media/icon.png"))

# Game images
game_over_image = pygame.image.load('media/game_over.png')
game_over_image = pygame.transform.scale(game_over_image, (width, height))

# Music
pygame.mixer.init()
pygame.mixer.music.load("music/music.wav")
pygame.mixer.music.play(-1)
music_stopped = False


def quit_game():
    global SCORES
    output = open("data.txt", "w", encoding="utf-8")
    for score in SCORES:
        output.write(f"{score}\n")

    settings_write = open("settings.txt", "w", encoding="utf-8")
    settings_write.write(json.dumps(all_settings, indent=4))
    settings_write.close()
    exit()


def buy_car(number):
    global screen
    if all_settings['player_money'] < (number + 1) * 100:
        notification = pygame.font.Font('FiraCodeBold.ttf', 18)
        notification_surface = notification.render(f'Not enough money', True, (255, 255, 255))
        screen.blit(notification_surface, (0, 0))
        return
    if number in all_settings['cars_bought']:
        return
    all_settings['player_money'] -= number * 100
    all_settings['player_car'] = f'car{number}.png' 
    all_settings['player_speed'] = 15 + 2 * (number - 1)
    all_settings['cars_bought'].append(number)
    bought_notification = pygame.font.Font('FiraCodeBold.ttf', 18)
    bought_notification_surface = bought_notification.render(f'Bought car {number}', True, (255, 255, 255))
    screen.blit(bought_notification_surface, (0, 0))


def use_car(number):
    global screen
    if not number in all_settings['cars_bought']: 
        not_bought_notification = pygame.font.Font('FiraCodeBold.ttf', 18)
        not_bought_notification_surface = not_bought_notification.render(f'You did not buy car {number}', True, (255, 255, 255))
        screen.blit(not_bought_notification_surface, (0, 0))
        return
    all_settings['player_car'] = f'car{number}.png' 
    all_settings['player_speed'] = 15 + 2 * (number - 1)


background_image = pygame.image.load('media/road2.png')
background_image = pygame.transform.scale(background_image, (width - width // 3, height * 2))
mountains = pygame.image.load('media/mountains.png')
mountains = pygame.transform.rotate(mountains, 270)
mountains = pygame.transform.scale(mountains, (width // 3, height * 2))


class Widget(pygame.Rect):
    def __init__(self, left, top, width, height, text, screen):
        super().__init__((left, top), (width, height))
        self.font = pygame.font.Font('FiraCodeBold.ttf', 18)
        self.screen = screen
        self.font_surface = self.font.render(text, True,
                                             (255, 255, 255))


class Car(pygame.sprite.Sprite):
    def __init__(self, image_path):
        super().__init__()
        self.image = pygame.image.load(os.path.join('media', image_path))
        self.image = pygame.transform.scale(self.image, (width // 20, height // 8))
        self.rect = self.image.get_rect()
        self.speed_y = 0

    def update(self):
        self.rect.y += self.speed_y


class Player(Car):
    def __init__(self, image_path):
        super().__init__(image_path)
        # self.image = pygame.transform.rotate(self.image, 180)
        self.rect.x = width // 2
        self.rect.y = height - self.rect.height
        self.speed_x = 0

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if self.rect.x < width // 10:
            self.rect.x = width // 10 
        if self.rect.x > width - width // 3 - self.rect.width - width // 9:
            self.rect.x = width - self.rect.width - width // 3 - width // 9
        # if self.rect.x > width:
        #     self.rect.x = width
        if self.rect.y < self.rect.height // 5:
            self.rect.y = self.rect.height // 5
        if self.rect.y > height - self.rect.height:
            self.rect.y = height - self.rect.height

    def ride(self, speed_x, speed_y):
        self.speed_x = speed_x
        self.speed_y = speed_y

    def stop(self):
        self.speed_x = 0
        self.speed_y = 0


class MovingDownObject(Car):
    def __init__(self, image_path, x, y):
        super().__init__(image_path)
        self.image = pygame.transform.rotate(self.image, 180)
        self.rect.x = x
        self.rect.y = y

    def update(self, speed_y):
        self.speed_y = speed_y
        self.rect.y += self.speed_y
        if self.rect.y > height:
            self.kill()


class Enemy(MovingDownObject):
    pass


class TimeBooster(MovingDownObject):
    pass


class SpeedBooster(MovingDownObject):
    pass


class BoosterFabrique: 
    
    @staticmethod
    def get_booster(string):
        kwargs = {'x': random.randint(width // 10, width - width // 3 - width // 9 - 30), 'y': -100}
        
        if string == 'TimeBooster':
            kwargs['image_path'] = 'clock.png' 
            return TimeBooster(**kwargs)
        elif string == 'SpeedBooster':
            kwargs['image_path'] = 'speed.png'
            return SpeedBooster(**kwargs)


class GameState:
    def __init__(self):
        self.state = 'menu'

    def main_game(self):
        global screen, width, height
        prev_time = time.time()
        normal_prev_time = time.time()
        prev_booster_time = time.time()
        boost_time = None
        speed_boost_time = None
        time_boosted = False

        # Sprites

        # Player
        player_speed = all_settings['player_speed']
        player = Player(all_settings['player_car'])
        players = pygame.sprite.Group()
        players.add(player)
        
        # Boosters
        time_boosters = pygame.sprite.Group()
        speed_boosters = pygame.sprite.Group() 

        # spoiler = pygame.image.load("media/spoiler.png")
        # spoiler = pygame.transform.scale(spoiler, (player.rect.width, player.rect.height // 10))
        
        # Enemy
        enemies = pygame.sprite.Group()
        enemy_speed = 30 
        # Score

        score_number = 0
        speed_number = 120
        score = pygame.font.Font('FiraCodeBold.ttf', 25)
        current_car_speed = pygame.font.Font("FiraCodeBold.ttf", 25)
        score_surf = score.render(str(score_number), True, (255, 255, 255))
        current_car_speed_surf = current_car_speed.render(f"{speed_number} km/h", True, (255, 255, 255))
        # player.image.blit(spoiler, (0, player.rect.height * 9 // 10))
        
        y = 0 
        background_speed = 20
        slow_down = False
        while True:
            rel_y = y % (height * 2)
            
            screen.fill((0, 0, 0))
            screen.blit(background_image, (0, rel_y))
            screen.blit(mountains, (width - width // 3, rel_y))
            if rel_y >= 0:
                screen.blit(background_image, (0, rel_y - height * 2))
                screen.blit(mountains, (width - width // 3, rel_y - height * 2))
            screen.blit(score_surf, (0, 0))
            screen.blit(current_car_speed_surf, (width - width // 3 - width // 6, 0))
            y += background_speed

            current_time = time.time()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    SCORES.append(score_number)
                    quit_game()

                if event.type == KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        player.ride(-player_speed, 0)
                    elif event.key == pygame.K_RIGHT:
                        player.ride(player_speed, 0)
                    elif event.key == pygame.K_UP:
                        player.ride(0, -player_speed)
                    elif event.key == pygame.K_DOWN:
                        player.ride(0, player_speed)
                if event.type == KEYUP:
                    player.stop()
            
            time_lapse = 0.5
            if time_boosted:
                time_lapse = 6
            
            if current_time - normal_prev_time >= 0.5:
                score_number += 1
                normal_prev_time = current_time
            score_surf = score.render(
                             str(score_number), 
                             True, 
                             (255, 255, 255)
                         )

            if current_time - prev_time >= time_lapse:
                prev_time = current_time
                image_path = CARS[random.randint(0, 7)]
                enemy = Enemy(image_path, random.randint(
                              width // 10, width - width // 3 - width // 9 - 30), -100)
                enemies.add(enemy)
                speed_number += 0.1
                speed_number = round(speed_number, 2)
                background_speed += 0.1
                enemy_speed += 0.1
                current_car_speed_surf = current_car_speed.render(
                                            f"{speed_number} km/h",
                                            True,
                                            (255, 255, 255)
                                         )
            if current_time - (random.randint(20, 30) * time_lapse) >= prev_booster_time:
                random_booster_class = random.choice(['SpeedBooster', 'TimeBooster'])
                random_booster = BoosterFabrique.get_booster(random_booster_class)
                if random_booster_class == 'SpeedBooster':
                    speed_boosters.add(random_booster)
                elif random_booster_class == 'TimeBooster':
                    time_boosters.add(random_booster)

                prev_booster_time = time.time()

            players.draw(screen)
            players.update()
        
            enemies.draw(screen)

            time_boosters.draw(screen)
            time_boosters.update(enemy_speed)
            
            speed_boosters.draw(screen)
            speed_boosters.update(enemy_speed)

            if (current_time - begin_time) % (time_lapse * 20) == 0:
                if enemy_cars < 7:
                    enemy_cars += 1

            enemies.update(enemy_speed)
            collision_die = pygame.sprite.groupcollide(
                enemies, players, False, True)
            collision_time_boost = pygame.sprite.groupcollide(
                time_boosters, players, True, False
            )
            collision_speed_boost = pygame.sprite.groupcollide(
                speed_boosters, players, True, False
            )

            if collision_die:
                SCORES.append(score_number)
                all_settings['player_money'] += score_number
                self.state = 'game_over'

            pygame.display.flip()
            
            if collision_time_boost:
                fpsClock.tick(5)
                boost_time = time.time() 
                time_boosted = True
            elif not boost_time is None and current_time - boost_time < 10:
                fpsClock.tick(5)
            else:
                fpsClock.tick(fps)
                time_boosted = False

            if collision_speed_boost:
                speed_boost_time = time.time()
                player_speed = all_settings['player_speed'] * 2
            
            elif speed_boost_time is None or current_time - speed_boost_time > 10:
                player_speed = all_settings['player_speed']

            if self.state == 'game_over':

                self.game_over()

    def game_over(self):
        global screen, game_over_background
        screen.fill((0, 0, 0))
        screen.blit(game_over_image, (0, 0))
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_game()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.state = 'menu'

            pygame.display.flip()
            fpsClock.tick(fps)

            if self.state == 'menu':
                self.menu()
    
    def menu(self):

        global screen, music_stopped
        # Widgets
        play_button = Widget(width // 10, height // 3, width //
                             15, height // 15, 'play', screen)
        quit_button = Widget(width // 10, height // 2.4, width //
                             15, height // 15, 'quit', screen)
        music_off_button = Widget(width // 10, height // 2,
                                  width // 15, height // 15, 'toggle music', screen)
        garage_button = Widget(width // 10, height // 1.7,
                        width // 15, height // 15, 
                        'garage', screen)

        screen.fill((0, 0, 0))
        screen.blit(play_button.font_surface, (play_button.x, play_button.y))
        screen.blit(quit_button.font_surface, (quit_button.x, quit_button.y))
        screen.blit(music_off_button.font_surface,
                    (music_off_button.x, music_off_button.y))
        screen.blit(garage_button.font_surface, (garage_button.x, garage_button.y)) 

        while True:
            mouse_x, mouse_y = None, None
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = event.pos
                if event.type == pygame.QUIT:
                    quit_game()

            if mouse_x is not None:
                if play_button.collidepoint(mouse_x, mouse_y):
                    self.state = 'main_game'
                if quit_button.collidepoint(mouse_x, mouse_y):
                    quit_game()
                if music_off_button.collidepoint(mouse_x, mouse_y):
                    if not music_stopped:
                        pygame.mixer.music.stop()
                        music_stopped = True
                    else:
                        music_stopped = False
                        pygame.mixer.music.play(-1)
                if garage_button.collidepoint(mouse_x, mouse_y):
                    self.state = 'garage'

            pygame.display.flip()
            fpsClock.tick(fps)

            if self.state == 'main_game':
                self.main_game()
            
            elif self.state == 'garage':
                self.garage()

    def garage(self):
        global screen, music_stopped
        # Widgets
        buttons = [
            Widget(width // 15, height // 3, 
                   width // 15, height // 15, 
                   'buy', screen),
            Widget(width // 6, height // 3, 
                   width // 15, height // 15, 
                   'buy', screen),
            Widget(width * 0.25, height // 3,
                   width // 15, height // 15, 
                   'buy', screen),
            Widget(width * 0.33, height // 3,
                   width // 15, height // 15, 
                   'buy', screen),
            Widget(width * 0.40, height // 3,
                   width // 15, height // 15, 
                   'buy', screen),
            Widget(width * 0.48 , height // 3,
                   width // 15, height // 15, 
                   'buy', screen),
            Widget(width * 0.56, height // 3,
                   width // 15, height // 15, 
                   'buy', screen),
            Widget(width // 15, height * 0.66, 
                   width // 15, height // 15, 
                   'menu', screen)
        ]
        use_buttons = [
            Widget(width // 15, height // 5, 
                   width // 15, height // 15, 
                   'use', screen),
            Widget(width // 6, height // 5, 
                   width // 15, height // 15, 
                   'use', screen),
            Widget(width * 0.25, height // 5,
                   width // 15, height // 15, 
                   'use', screen),
            Widget(width * 0.33, height // 5,
                   width // 15, height // 15, 
                   'use', screen),
            Widget(width * 0.40, height // 5,
                   width // 15, height // 15, 
                   'use', screen),
            Widget(width * 0.48 , height // 5,
                   width // 15, height // 15, 
                   'use', screen),
            Widget(width * 0.56, height // 5,
                   width // 15, height // 15, 
                   'use', screen)
        ]

        car6 = pygame.image.load(os.path.join('media', 'car6.png'))
        car6_image = pygame.transform.scale(car6, (width // 20, height // 8))
        car_images = [
            pygame.image.load(os.path.join('media', 'car2.png')), pygame.image.load(os.path.join('media', 'car3.png')),
            pygame.image.load(os.path.join('media', 'car4.png')), pygame.image.load(os.path.join('media', 'car5.png')),
            car6_image, pygame.image.load(os.path.join('media', 'car7.png')),
            pygame.image.load(os.path.join('media', 'car8.png'))
        ]
                 
        screen.fill((0, 0, 0))
        
        money_amount_font = pygame.font.Font('FiraCodeBold.ttf', 18)
        money_amount_surf = money_amount_font.render(str(all_settings['player_money']), True, (255, 255, 255))
        
        money_icon = pygame.image.load(os.path.join('media', 'dollar.png'))
        money_icon = pygame.transform.scale(money_icon, (width // 50, height // 40))
        screen.blit(money_icon, (width * 0.75, height * 0.75))
        screen.blit(money_amount_surf, (width * 0.72, height * 0.75))

        for button in buttons:
            screen.blit(button.font_surface, (button.x, button.y))
        
        for use_button in use_buttons:
            screen.blit(use_button.font_surface, (use_button.x, use_button.y))

        for i in range(len(car_images)):
            car_image = car_images[i]
            screen.blit(car_image, (buttons[i].x, buttons[i].y + height // 7))

        while True:
            mouse_x, mouse_y = None, None
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = event.pos
                if event.type == pygame.QUIT:
                    quit_game()

            if mouse_x is not None:
                # if play_button.collidepoint(mouse_x, mouse_y):
                #     self.state = 'main_game'
                for i in range(len(buttons)):
                    button = buttons[i]
                    if button.collidepoint(mouse_x, mouse_y):
                        if i == len(buttons) - 1:
                            self.state = 'menu'
                        else:
                            surf = pygame.Surface((width // 2, height // 7))
                            surf.fill((0, 0, 0))
                            screen.blit(surf, (0, 0))
                            buy_car(i + 2)
                            money_amount_surf = money_amount_font.render(str(all_settings['player_money']), True, (255, 255, 255))
                for i in range(len(use_buttons)):
                    button = use_buttons[i]
                    if button.collidepoint(mouse_x, mouse_y):
                        if i == len(buttons) - 1:
                            self.state = 'menu'
                        else:
                            surf = pygame.Surface((width // 2, height // 7))
                            surf.fill((0, 0, 0))
                            screen.blit(surf, (0, 0))
                            use_car(i + 2)

            pygame.display.flip()
            fpsClock.tick(fps)
            
            if self.state == 'menu':
                self.menu()
            

if __name__ == '__main__':
    current_state = GameState()
    current_state.menu()
