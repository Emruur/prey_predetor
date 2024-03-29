import logging
import os
import pickle
from Agent import MLPNetwork
import numpy as np
import torch
import torch.nn.functional as F
from copy import deepcopy
from Agent import Agent
from Buffer import Buffer
from torch.optim import Adam
from typing import List
from torch import nn, Tensor

def setup_logger(filename):
    """ set up logger with filename. """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(filename, mode='w')
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s--%(levelname)s--%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


class MADDPG:
    """A MADDPG(Multi Agent Deep Deterministic Policy Gradient) agent"""

    def __init__(self, dim_info, capacity, batch_size, actor_lr, critic_lr, res_dir):
        # sum all the dims of each agent to get input dim for critic
        global_obs_act_dim = sum(sum(val) for val in dim_info.values())

        #Single critic in scddpg
        self.critic= MLPNetwork(global_obs_act_dim, 1)
        self.target_critic = deepcopy(self.critic)
        self.critic_optimizer = Adam(self.critic.parameters(), lr=critic_lr)

        self.agent_critic= deepcopy(self.critic)
        self.agent_target_critic= deepcopy(self.critic)
        self.agent_critic_optimizer= Adam(self.agent_critic.parameters(), lr=critic_lr)

        # create Agent(actor-critic) and replay buffer for each agent
        self.agents = {}
        self.buffers = {}
        for agent_id, (obs_dim, act_dim) in dim_info.items():
            self.agents[agent_id] = Agent(obs_dim, act_dim, global_obs_act_dim, actor_lr, critic_lr, self.critic, self.target_critic)
            self.buffers[agent_id] = Buffer(capacity, obs_dim, act_dim, 'cpu')
        self.dim_info = dim_info

        self.batch_size = batch_size
        self.res_dir = res_dir  # directory to save the training result
        self.logger = setup_logger(os.path.join(res_dir, 'maddpg.log'))

    def add(self, obs, action, reward, next_obs, done):
        # NOTE that the experience is a dict with agent name as its key
        for agent_id in obs.keys():
            o = obs[agent_id]

            a = action[agent_id]
            if isinstance(a, int):
                # the action from env.action_space.sample() is int, we have to convert it to onehot
                a = np.eye(self.dim_info[agent_id][1])[a]

            r = reward[agent_id]
            next_o = next_obs[agent_id]
            d = done[agent_id]
            self.buffers[agent_id].add(o, a, r, next_o, d)

    def sample(self, batch_size):
        """sample experience from all the agents' buffers, and collect data for network input"""
        # get the total num of transitions, these buffers should have same number of transitions
        total_num = len(self.buffers['agent_0'])
        indices = np.random.choice(total_num, size=batch_size, replace=False)

        # NOTE that in MADDPG, we need the obs and actions of all agents
        # but only the reward and done of the current agent is needed in the calculation
        obs, act, reward, next_obs, done, next_act = {}, {}, {}, {}, {}, {}
        for agent_id, buffer in self.buffers.items():
            o, a, r, n_o, d = buffer.sample(indices)
            obs[agent_id] = o
            act[agent_id] = a
            reward[agent_id] = r
            next_obs[agent_id] = n_o
            done[agent_id] = d
            # calculate next_action using target_network and next_state
            next_act[agent_id] = self.agents[agent_id].target_action(n_o)

        return obs, act, reward, next_obs, done, next_act

    def select_action(self, obs):
        actions = {}
        for agent, o in obs.items():
            o = torch.from_numpy(o).unsqueeze(0).float()
            a = self.agents[agent].action(o)  # torch.Size([1, action_size])
            # NOTE that the output is a tensor, convert it to int before input to the environment
            actions[agent] = a.squeeze(0).argmax().item()
            self.logger.info(f'{agent} action: {actions[agent]}')
        return actions

    def update_critic(self, loss):
        self.critic_optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.critic.parameters(), 0.5)
        self.critic_optimizer.step()

    def critic_value(self, state_list: List[Tensor], act_list: List[Tensor]):
        x = torch.cat(state_list + act_list, 1)
        return self.critic(x).squeeze(1)  # tensor with a given length

    def target_critic_value(self, state_list: List[Tensor], act_list: List[Tensor]):
        x = torch.cat(state_list + act_list, 1)
        return self.target_critic(x).squeeze(1)  # tensor with a given length
    
    def update_critic_a(self, loss):
        self.agent_critic_optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.agent_critic.parameters(), 0.5)
        self.agent_critic_optimizer.step()

    def critic_value_a(self, state_list: List[Tensor], act_list: List[Tensor]):
        x = torch.cat(state_list + act_list, 1)
        return self.agent_critic(x).squeeze(1)  # tensor with a given length

    def target_critic_value_a(self, state_list: List[Tensor], act_list: List[Tensor]):
        x = torch.cat(state_list + act_list, 1)
        return self.agent_target_critic(x).squeeze(1)  # tensor with a given length

    def learn(self, batch_size, gamma):
        #TODO implement single critic learning
        obs, act, reward, next_obs, done, next_act = self.sample(batch_size)

        done_a = deepcopy(done)
        reward_a= deepcopy(reward)

        critic_value = self.critic_value(list(obs.values()), list(act.values()))
        # calculate target critic value
        next_target_critic_value = self.target_critic_value(list(next_obs.values()),
                                                                list(next_act.values()))
        

        #ADVERSARIAL CRITIC UPDATE
        d = torch.zeros_like(next(iter(done.values())))

        # Sum the tensors
        for agent_id,tensor in done.items():
            if agent_id.startswith("adversary_"):
                d = d + tensor

        r = torch.zeros_like(next(iter(reward.values())))

        # Sum the tensors
        for agent_id, tensor in reward.items():
            if agent_id.startswith("adversary_"):
                r = r + tensor

        target_value = r + gamma * next_target_critic_value * (1 - d)

        critic_loss = F.mse_loss(critic_value, target_value.detach(), reduction='mean')
        self.update_critic(critic_loss)

        #AGENT CRITIC UPDATE
        critic_value_a = self.critic_value_a(list(obs.values()), list(act.values()))
        # calculate target critic value
        next_target_critic_value_a = self.target_critic_value_a(list(next_obs.values()),
                                                                list(next_act.values()))
        

        d_a = torch.zeros_like(next(iter(done_a.values())))

        # Sum the tensors
        for agent_id,tensor in done.items():
            if agent_id.startswith("agent_"):
                d_a = d_a + tensor

        r_a = torch.zeros_like(next(iter(reward_a.values())))

        # Sum the tensors
        for agent_id, tensor in reward.items():
            if agent_id.startswith("agent_"):
                r_a = r_a + tensor

        target_value_a = r_a + gamma * next_target_critic_value_a * (1 - d_a)

        critic_loss_a = F.mse_loss(critic_value_a, target_value_a.detach(), reduction='mean')
        self.update_critic_a(critic_loss_a)


        for agent_id, agent in self.agents.items():
            obs, act, reward, next_obs, done, next_act = self.sample(batch_size)

            # update actor
            # action of the current agent is calculated using its actor
            action, logits = agent.action(obs[agent_id], model_out=True)
            act[agent_id] = action
            actor_loss = -self.critic_value(list(obs.values()), list(act.values())).mean() if agent_id.startswith("adversary_") else -self.critic_value_a(list(obs.values()), list(act.values())).mean()
            actor_loss_pse = torch.pow(logits, 2).mean()
            agent.update_actor(actor_loss + 1e-3 * actor_loss_pse)
            # self.logger.info(f'agent{i}: critic loss: {critic_loss.item()}, actor loss: {actor_loss.item()}')

    def update_target(self, tau):
        def soft_update(from_network, to_network):
            """ copy the parameters of `from_network` to `to_network` with a proportion of tau"""
            for from_p, to_p in zip(from_network.parameters(), to_network.parameters()):
                to_p.data.copy_(tau * from_p.data + (1.0 - tau) * to_p.data)


        soft_update(self.critic, self.target_critic)
        soft_update(self.agent_critic, self.agent_target_critic)

        for agent in self.agents.values():
            soft_update(agent.actor, agent.target_actor)
            

    def save(self, reward):
        """save actor parameters of all agents and training reward to `res_dir`"""
        torch.save(
            {name: agent.actor.state_dict() for name, agent in self.agents.items()},  # actor parameter
            os.path.join(self.res_dir, 'model.pt')
        )
        with open(os.path.join(self.res_dir, 'rewards.pkl'), 'wb') as f:  # save training data
            pickle.dump({'rewards': reward}, f)

    @classmethod
    def load(cls, dim_info, file):
        """init maddpg using the model saved in `file`"""
        instance = cls(dim_info, 0, 0, 0, 0, os.path.dirname(file))
        data = torch.load(file)
        for agent_id, agent in instance.agents.items():
            agent.actor.load_state_dict(data[agent_id])
        return instance
