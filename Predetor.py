from Mover import Mover
import pymunk
from pymunk.vec2d import Vec2d
import pygame
from random import randint
import math

class Predetor(Mover):
    radius= 30
    color= (75,0,130)

    def __init__(self, position, space) -> None:
        super().__init__(Predetor.radius, position, space)


