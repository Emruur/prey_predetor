import os
import pickle
import numpy as np
import matplotlib.pyplot as plt

def running_reward(data, window_size=100):
    """Calculate running reward over a fixed window."""
    return np.convolve(data, np.ones(window_size), 'valid') / window_size

def load_and_process_rewards(file_path):
    """Load rewards from a file and return running averages for agents."""
    with open(file_path, 'rb') as file:
        data = pickle.load(file)

    rewards = data['rewards']
    agents = ['agent_0', 'agent_1', 'agent_2']

    mean_agent_reward = np.mean([rewards[agent] for agent in agents], axis=0)
    running_reward_agents = running_reward(mean_agent_reward, 100)

    return running_reward_agents

# Define file paths
maddpg_file = './maddpg_results.pkl'
ddpg_file = './ddpg_results.pkl'

# Process each file
maddpg_agents = load_and_process_rewards(maddpg_file)
ddpg_agents = load_and_process_rewards(ddpg_file)

# Plotting
plt.figure(figsize=(12, 8))
plt.plot(maddpg_agents, label='MADDPG - 100-Step Running Reward (Mean Agents)', linestyle='--')
plt.plot(ddpg_agents, label='DDPG - 100-Step Running Reward (Mean Agents)', linestyle='--')
plt.title('Comparison of 100-Step Running Rewards - MADDPG vs DDPG')
plt.xlabel('Time Step')
plt.ylabel('Reward')
plt.legend()
plt.savefig('comparison_plot_agents.png', format='png')
plt.show()

