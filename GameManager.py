from Mover import Mover
from Prey import Prey
from Predetor import Predetor
import pymunk
from pymunk.vec2d import Vec2d
from random import randint
import pygame
import math
import numpy as np

def limit_velocity_500(body, gravity, damping, dt):
    max_velocity = 500
    pymunk.Body.update_velocity(body, gravity, damping, dt)
    l = body.velocity.length
    if l > max_velocity:
        scale = max_velocity / l
        body.velocity = body.velocity * scale

def limit_velocity_1000(body, gravity, damping, dt):
    max_velocity = 1000
    pymunk.Body.update_velocity(body, gravity, damping, dt)
    l = body.velocity.length
    if l > max_velocity:
        scale = max_velocity / l
        body.velocity = body.velocity * scale
def create_ball(radius, position,space, collision_type, identity):
    body= pymunk.Body()
    body.identity= identity
    body.health= 10
    body.contact_count= 0
    body.position= position
    shape= pymunk.Circle(body, radius)
    shape.mass= 0.4
    shape.collision_type= collision_type
    if collision_type == 1:
       body.velocity_func= limit_velocity_1000
    else:
        body.velocity_func= limit_velocity_500
    
    #use pivot joint
    pivot= pymunk.PivotJoint(space.static_body, body, (0,0),(0,0))
    pivot.max_bias= 0
    pivot.max_force= 700
    shape.body.pivot= pivot
    space.add(body,shape,pivot)
    return shape

def collide_begin(arbiter,space,end):
    shapes= arbiter.shapes
    shapes[0].body.contact_count += 1
    shapes[1].body.contact_count += 1
    return True





class GameManager:
    def __init__(self, space, width, height) -> None:
        self.id_prey= 10
        self.id_predetor= -10
        self.entities= []
        self.space = space
        collision_handler= self.space.add_collision_handler(1,2)
        collision_handler.begin= collide_begin

        self.static_body= space.static_body

        static_lines = [
            pymunk.Segment(space.static_body, Vec2d(0, 0), Vec2d(width, 0), 1),
            pymunk.Segment(space.static_body, Vec2d(0, 0), Vec2d(0, height), 1),
            pymunk.Segment(space.static_body, Vec2d(0, height), Vec2d(width, height), 1),
            pymunk.Segment(space.static_body, Vec2d(width, 0), Vec2d(width, height), 1),
        ]
        for l in static_lines:
            l.friction = 0.3
        space.add(*static_lines)



    def get_observations(self,screen):
        for entity in self.entities:
            self.get_observation(entity, screen)

    def get_observation(self, entity, screen= None):
        observations = []
        num_rays = 20
        angle_increment = math.radians(180 / (num_rays - 1))

        for i in range(num_rays):
            # Calculate the angle for each ray in radians
            ray_angle = entity.shape.body.angle + math.radians(-90) + i * angle_increment
            direction = Vec2d(1, 0).rotated(ray_angle)

            # Adjust the length of the ray based on its angle
            angle_difference = abs(ray_angle - entity.shape.body.angle)
            ray_length = 500

            start_point = entity.shape.body.position
            end_point = start_point + direction * ray_length

            # Perform the segment query
            query_infos = self.space.segment_query(start_point, end_point, radius=0, shape_filter=pymunk.ShapeFilter())

            # Filter out the entity's own shape from the results
            entity_id = entity.shape.body.id
            filtered_infos = [info for info in query_infos if info.shape.body.id != entity_id]

            # Reverse the order of the list
            filtered_infos.reverse()
            query_info = next((info for info in filtered_infos if info.shape.body.id != entity_id), None)

            collision_type= 4
            if query_info:
                ray_length = query_info.alpha * ray_length
                collision_type = query_info.shape.collision_type
            else:
                ray_length = ray_length  # No intersection, use the full ray length

            #observations.append((ray_length, collision_type))
            observations.append(collision_type)
            observations.append(ray_length)


            # Determine the end point of the ray based on intersection
            final_point = query_info.point if query_info else end_point

            # Determine the color based on intersection
            # Determine the color based on collision type
            if query_info:
                if query_info.shape.collision_type == 1:
                    color = (255, 0, 0)  # Red for collision type 1
                elif query_info.shape.collision_type == 2:
                    color = (0, 0, 255)  # Blue for collision type 2
                else:
                    color = (0, 255, 0)  # Default to green for other types
            else:
                color = (128, 128, 128)  # Gray if no intersection

            # Draw the ray
            #pygame.draw.line(screen, color, (start_point.x, start_point.y), (final_point.x, final_point.y))

        self.obs= observations
        return np.array(observations)

    def add_prey(self, radius, position) -> Prey:
        entity_shape= create_ball(radius, position, self.space,1,self.id_prey)
        entity= Prey(position, entity_shape)
        self.entities.append(entity)
        self.id_prey += 1
        return entity

    def add_predetor(self, radius, position) -> Predetor:
        entity_shape= create_ball(radius, position, self.space,2,self.id_predetor)
        entity= Predetor(position, entity_shape)
        self.entities.append(entity)
        self.id_predetor -= 1
        return entity

    def randomly_place(self,width, height, is_prey) -> Mover:
        position= Vec2d(randint(0,width), randint(0,height))
        if is_prey:
            return self.add_prey(Prey.radius, position)
        else:
            return self.add_predetor(Predetor.radius, position)
        
    def wander_entities(self)-> None:
        for entity in self.entities:
            entity.wander()

    def update(self):
        for i in range(len(self.entities)-1,-1,-1):
            entity= self.entities[i]
            entity.update()
