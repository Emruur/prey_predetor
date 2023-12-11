import pymunk
import random
import math


class Mover:
    def __init__(self, radius,position, shape) -> None:
        self.radius= radius
        self.position= position
        self.shape= shape

        self.angle = 0  # Starting angle
        self.wander_angle = 0.1
        self.wander_strength = 0

    def rotate(self,angle):
        self.shape.body.angle += angle

    def move(self):
        self.shape.body.apply_force_at_local_point((1500,0),(0,0))
    def update(self):
        pass

    def is_dead(self):
        return self.shape.body.health<=0

    def wander(self):

        self.angle += random.uniform(-self.wander_angle, self.wander_angle)
        
        self.wander_strength += random.uniform(-1, 1) *1000
        if self.wander_strength > 1500:
            self.wander_strength= 0
        
        dx = self.wander_strength
        
        # Move in the resulting direction
        self.move()
        self.rotate(self.angle * 0.01)  # Slower rotation