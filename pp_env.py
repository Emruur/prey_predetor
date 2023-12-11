from pettingzoo import ParallelEnv
from GameManager import GameManager
import pymunk
import pygame
from Predetor import Predetor
from Prey import Prey
from pymunk.vec2d import Vec2d
from gymnasium.spaces import Box
from gymnasium.spaces import Discrete
import math
import numpy as np

class pp_env(ParallelEnv):
    metadata = {
        "name": "pp_env_v0",
    }

    def __init__(self, max_steps= 100, render_mode= None):
        # Initialize Pygame
        
        # Set up the display
        self.width= 1200
        self.height= 800  # Width and height of the window
        if render_mode== "human" or render_mode=="pixel_array":
            pygame.init()
            self.display = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Prey-Predetor")  # Window title
        self.space= pymunk.Space()
        #draw_options= pymunk.pygame_util.DrawOptions(self.display)        
        self.time_step= 0
        self.game_manager= GameManager(self.space,self.width,self.height)
        self.FPS= 30
        self.clock= pygame.time.Clock()
        self.agents= []
        self.render_mode= render_mode
        self.max_time_step= max_steps

    def reset(self, seed=None, options=None):
        self.time_step= 0
        self.agents= []
        for body in self.space.bodies:
            for shape in body.shapes:
                self.space.remove(shape)
            self.space.remove(body)
        # Remove all constraints
        for constraint in self.space.constraints:
            self.space.remove(constraint)

        self.game_manager= GameManager(self.space,self.width,self.height)

        predetor_count= 3
        for i in range(predetor_count):
            self.agents.append(f"agent_{i}")
            self.game_manager.add_predetor(Predetor.radius, Vec2d(400, (self.height/(predetor_count + 1))*(i+1)))
        prey_count= 1
        for i in range(prey_count):
            self.agents.append(f"adversary_{i}")
            self.game_manager.add_prey(Prey.radius, Vec2d(self.width- 400, (self.height/(predetor_count + 1))*(i+1)))


        observations = {
            a: self.game_manager.get_observation(self.game_manager.entities[i])
            for i,a in enumerate(self.agents)
        }

        infos = {a: {} for a in self.agents}

        return observations, infos

    def step(self, actions):
        self.time_step += 1
        observations= {}
        rewards= {}
        terminations= {}

        for i,action in enumerate(actions.values()):
            agent= self.game_manager.entities[i]
            # Act the action
            if action == 0:
                # Do Nothing
                pass
            elif action == 1:
                agent.rotate(0.05)
            elif action == 2:
                agent.rotate(-0.05)
            elif action == 3:
                agent.move()
            elif action == 4:
                agent.rotate(0.05)
                agent.move()
            elif action == 5:
                agent.rotate(0.05)
                agent.move()

        if(self.render_mode== "human"):
            self.clock.tick(self.FPS)
        self.space.step(1/self.FPS)

        for i,(key, action) in enumerate(actions.items()):
            agent= self.game_manager.entities[i]
            obs= self.game_manager.get_observation(agent)
            observations[key]= obs
            
            terminations[key]= agent.shape.body.contact_count > 0 or self.time_step > self.max_time_step

            if isinstance(agent, Predetor):
                reward= -5
                for j in range(0,len(obs),2):
                    if obs[j] == 1:
                        #There is a prey in sight, if more rays intersect it closer we are to the prey
                        reward = reward / 2
                rewards[key]= reward
            else:
                reward = 1
                rewards[key]= reward

        if any(terminations.values()):
            self.agents = []

        infos = {a: {} for a in self.agents}
        return observations, rewards, terminations, terminations, infos
        

    def render(self):
        self.display.fill((0,25,20))  # Fill the background with black

        for entity in self.game_manager.entities:
            position = entity.shape.body.position
            angle = entity.shape.body.angle
            radius = entity.radius

            # Convert pymunk coordinates to pygame coordinates for the entity
            pygame_position = int(position.x), self.height - int(position.y)

            # Calculate the end point of the direction line
            end_x = pygame_position[0] + radius * math.cos(angle)
            end_y = pygame_position[1] - radius * math.sin(angle)  # Subtract because Pygame's y-axis is inverted

            # Draw the entity as a circle
            pygame.draw.circle(self.display, (155, 200, 255), pygame_position, radius)

            # Draw the direction line
            pygame.draw.line(self.display, (255, 0, 0), pygame_position, (end_x, end_y), 2)  # Red line with width=2


        pygame.display.flip()  # Update the full display Surface to the screen
        return pygame.surfarray.array3d(self.display)


    def observation_space(self, agent):
        return Box(low=np.array([-1.0] * 40), high=np.array([1.0] * 40), dtype=np.float32)

    def action_space(self, agent):
        return Discrete(3)
    
