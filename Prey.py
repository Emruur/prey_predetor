from Mover import Mover
import pymunk
import pygame
from pymunk.vec2d import Vec2d
from random import randint
import math

class Prey(Mover):
    radius= 20
    color= (75,0,130)

    def __init__(self, position, space) -> None:
        super().__init__(Prey.radius, position, space)