import pygame

from project.pygame_globals import MEDIA_DIR, width, height
from project.move_behaviors import MoveBehavior, MoveXBehavior, MoveYBehavior, MoveYEnemyBehavior

import os
from abc import ABC, abstractmethod


def build(obj, image_path):
    obj.image = pygame.image.load(
        os.path.join(MEDIA_DIR, image_path)
    )
    obj.image = pygame.transform.scale(
        obj.image, (width // 20, height // 8)
    )
    obj.rect = obj.image.get_rect()
    obj.speed_y = 0


class Car(ABC):
    @abstractmethod
    def update(self):
        pass


class Player(Car, pygame.sprite.Sprite):
    def __init__(self, image_path):
        pygame.sprite.Sprite.__init__(self)
        build(self, image_path)
        self.rect.x = width // 2
        self.rect.y = height - self.rect.height
        self.speed_x = 0
        self.speed_y = 0
        self.move_x: MoveBehavior = MoveXBehavior()
        self.move_y: MoveBehavior = MoveYBehavior()

    def update(self):
        self.move_x.move(self)
        self.move_y.move(self)

    def ride(self, speed_x, speed_y):
        self.speed_x = speed_x
        self.speed_y = speed_y

    def stop(self):
        self.speed_x = 0
        self.speed_y = 0

    def set_move_x_behavior(self, move_behavior: MoveBehavior):
        self.move_x = move_behavior

    def set_move_y_behavior(self, move_behavior: MoveBehavior):
        self.move_y = move_behavior


class MovingDownObject(Car, pygame.sprite.Sprite):
    def __init__(self, image_path, x, y):
        pygame.sprite.Sprite.__init__(self)
        build(self, image_path)
        self.image = pygame.transform.rotate(self.image, 180)
        self.speed_y = 0
        self.rect.x = x
        self.rect.y = y
        self.move_y: MoveBehavior = MoveYEnemyBehavior()

    def update(self, speed_y):
        self.move_y.move(self, speed_y)


class Enemy(MovingDownObject):
    pass


class TimeBooster(MovingDownObject):
    pass


class SpeedBooster(MovingDownObject):
    pass