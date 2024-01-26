import os
import pickle
import numpy as np
import matplotlib.pyplot as plt

def running_reward(data, window_size=1000):
    """Calculate running reward over a fixed window."""
    return np.convolve(data, np.ones(window_size), 'valid') / window_size

def load_and_process_rewards(file_path):
    """Load rewards from a file and return running averages."""
    with open(file_path, 'rb') as file:
        data = pickle.load(file)

    rewards = data['rewards']
    adversaries = ['adversary_0', 'adversary_1', 'adversary_2']
    agent = 'agent_0'

    mean_adversary_reward = np.mean([rewards[adv] for adv in adversaries], axis=0)
    running_reward_adversaries = running_reward(mean_adversary_reward, 1000)
    running_reward_agent = running_reward(rewards[agent], 1000)

    return running_reward_adversaries, running_reward_agent

# Define file paths for your .pkl files
maddpg_file = './maddpg_results.pkl'  # Adjust path as needed
ddpg_file = './ddpg_results.pkl'      # Adjust path as needed
scddpg_file = './scddpg_results.pkl'  # Adjust path as needed

# Process each file
maddpg_adversaries, maddpg_agent = load_and_process_rewards(maddpg_file)
#ddpg_adversaries, ddpg_agent = load_and_process_rewards(ddpg_file)
scddpg_adversaries, scddpg_agent = load_and_process_rewards(scddpg_file)

# Plotting
plt.figure(figsize=(12, 8))
plt.ylim(-30, 30)  # Setting y-axis range

plt.plot(maddpg_adversaries, label='MADDPG - 100-Step Running Reward (Adversaries)', linestyle='--')
plt.plot(maddpg_agent, label='MADDPG - 100-Step Running Reward (Agent)', linestyle='--')
#plt.plot(ddpg_adversaries, label='DDPG - 100-Step Running Reward (Adversaries)', linestyle='--')
#plt.plot(ddpg_agent, label='DDPG - 100-Step Running Reward (Agent)', linestyle='--')
plt.plot(scddpg_adversaries, label='SCDDPG - 100-Step Running Reward (Adversaries)', linestyle='-.')
plt.plot(scddpg_agent, label='SCDDPG - 100-Step Running Reward (Agent)', linestyle='-.')
plt.title('Comparison of 1000-Step Running Rewards - MADDPG vs SCDDPG')
plt.xlabel('Time Step')
plt.ylabel('Reward')
plt.legend()
plt.savefig("maddpg_scddpg_1000_window.png")
plt.show()
