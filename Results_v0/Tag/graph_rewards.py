import os
import glob
import pickle
import numpy as np
import matplotlib.pyplot as plt

def running_reward(data, window_size=100):
    """Calculate running reward over a fixed window."""
    return np.convolve(data, np.ones(window_size), 'valid') / window_size

def plot_rewards(rewards_file):
    """Load rewards data from a file and plot it."""
    with open(rewards_file, 'rb') as file:
        data = pickle.load(file)

    rewards = data['rewards']
    adversaries = ['adversary_0', 'adversary_1', 'adversary_2']
    agent = 'agent_0'

    mean_adversary_reward = np.mean([rewards[adv] for adv in adversaries], axis=0)
    running_reward_adversaries = running_reward(mean_adversary_reward, 100)
    running_reward_agent = running_reward(rewards[agent], 100)

    plt.figure(figsize=(12, 8))
    plt.plot(mean_adversary_reward, label='Mean Adversary Reward')
    plt.plot(rewards[agent], label='Agent Reward')
    plt.plot(running_reward_adversaries, label='100-Step Running Reward (Adversaries)', linestyle='--')
    plt.plot(running_reward_agent, label='100-Step Running Reward (Agent)', linestyle='--')
    plt.title('Reward Trends and 100-Step Running Rewards Over Time')
    plt.xlabel('Time Step')
    plt.ylabel('Reward')
    plt.legend()

    plot_filename = os.path.join(os.path.dirname(rewards_file), 'rewards_plot.png')
    plt.savefig(plot_filename, format='png')
    plt.close()
    print(f"Plot saved: {plot_filename}")

# Find all 'rewards.pkl' files in the subdirectories
for rewards_file in glob.glob('**/rewards.pkl', recursive=True):
    print(f"Processing: {rewards_file}")
    plot_rewards(rewards_file)

