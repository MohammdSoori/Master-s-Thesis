# -*- coding: utf-8 -*-
"""TreasureHunt.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1qF3IwU00kwYk78sGj-9gjfTRCK8LRO-0
"""

!pip install torch torchvision torchaudio
!pip install gym

import numpy as np
import random
import gym
from gym import spaces

class TreasureExplorerEnv(gym.Env):
    def __init__(self):
        super(TreasureExplorerEnv, self).__init__()
        self.grid_size = 6
        self.max_steps = 30
        self.delta=0.5
        # State: (explorer_x, explorer_y, steps_remaining)
        self.observation_space = spaces.Box(low=np.array([0, 0, 0]),
                                            high=np.array([self.grid_size - 1, self.grid_size - 1, self.max_steps]),
                                            dtype=np.int32)

        # Actions: 0 = explore, 1 = dig, 2 = hint
        self.action_space = spaces.Discrete(3)

        # Fixed treasure position
        self.treasure_pos = (random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1))

        # Initialize game state
        self.reset()

    def reset(self):
        self.steps = 0

        # Place explorer at random position
        self.explorer_pos = (random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1))

        # Ensure explorer and treasure do not start at the same position
        while self.explorer_pos == self.treasure_pos:
            self.explorer_pos = (random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1))

        return self._get_observation()

    def _get_observation(self):
        x, y = self.explorer_pos
        steps_remaining = self.max_steps - self.steps
        return np.array([x, y, steps_remaining], dtype=np.int32)

    def step(self, action):
        self.steps += 1
        x, y = self.explorer_pos
        reward = 0  # Initialize reward

        if action == 0:  # Explore
            self._explore()
            reward = -1 + np.random.uniform(-self.delta, self.delta)
        elif action == 1:  # Dig
            if self.explorer_pos == self.treasure_pos:
                reward = 50
                done = True
                return self._get_observation(), reward, done, {}
            else:
                reward = -2 + np.random.uniform(-self.delta, self.delta)
        elif action == 2:  # Hint
            reward = -3 + np.random.uniform(-self.delta, self.delta)
            if self._is_treasure_adjacent():
                self.explorer_pos = self.treasure_pos

        done = self.steps >= self.max_steps
        return self._get_observation(), reward, done, {}

    def _explore(self):
        x, y = self.explorer_pos
        possible_moves = self._get_adjacent_positions(x, y)
        self.explorer_pos = random.choice(possible_moves)

    def _get_adjacent_positions(self, x, y):
        # Get all valid adjacent positions
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1),
                      (1, 1), (1, -1), (-1, 1), (-1, -1)]
        positions = [(x + dx, y + dy) for dx, dy in directions]
        return [(nx, ny) for nx, ny in positions if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size]

    def _is_treasure_adjacent(self):
        x, y = self.explorer_pos
        return self.treasure_pos in self._get_adjacent_positions(x, y)

    def render(self, mode='human'):
        grid = np.zeros((self.grid_size, self.grid_size))
        tx, ty = self.treasure_pos
        ex, ey = self.explorer_pos
        grid[tx, ty] = 2  # Treasure position
        grid[ex, ey] = 1  # Explorer position
        print(grid)

import matplotlib.pyplot as plt

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from IPython.display import HTML

class DQNAgent:
    def __init__(self, state_dim, action_dim,gamma=0.99, lr=0.001, epsilon=1.0, epsilon_decay=0.999, epsilon_min=0.1, batch_size=64, memory_size=20000):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.batch_size = batch_size
        self.memory = deque(maxlen=memory_size)


        # Neural networks
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)

        # Update target model weights
        self.update_target_model()

        # To store policy history for animation
        self.policy_history = []

    def _build_model(self):
        """Build the neural network model."""
        return nn.Sequential(
            nn.Linear(self.state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, self.action_dim)
        )

    def update_target_model(self):
        """Copy weights from the model to the target model."""
        self.target_model.load_state_dict(self.model.state_dict())

    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay memory."""
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        """Choose an action based on epsilon-greedy policy."""
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_dim)
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            act_values = self.model(state_tensor)
        return torch.argmax(act_values[0]).item()

    def replay(self):
        """Train the model using random samples from replay memory."""
        if len(self.memory) < self.batch_size:
            return

        minibatch = random.sample(self.memory, self.batch_size)
        for state, action, reward, next_state, done in minibatch:
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0)

            # Q-value update
            target = reward
            if not done:
                with torch.no_grad():
                    target = reward + self.gamma * torch.max(self.target_model(next_state_tensor)[0]).item()

            target_f = self.model(state_tensor)
            target_f[0][action] = target

            # Compute loss and perform gradient descent
            self.optimizer.zero_grad()
            loss = nn.MSELoss()(self.model(state_tensor), target_f)
            loss.backward()
            self.optimizer.step()

        # Epsilon decay
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def get_policy(self):
        """Get current policy (action probabilities) for every state in the grid."""
        policies = []
        for i in range(env.grid_size):
            for j in range(env.grid_size):
                state = np.array([i, j, 0], dtype=np.float32)  # Fixed steps_remaining for simplicity
                state_tensor = torch.FloatTensor(state).unsqueeze(0)

                with torch.no_grad():
                    q_values = self.model(state_tensor).numpy().flatten()
                max_q_value = np.max(q_values)
                stable_q_values = q_values - max_q_value
                policy = np.exp(stable_q_values) / np.sum(np.exp(stable_q_values))  # Softmax to get action probabilities

                policies.append(policy)
        return policies

    def train(self, env, episodes=1000, target_update_freq=10):
        rewards = []
        for e in range(episodes):
            state = env.reset()
            state = np.array(state, dtype=np.float32)
            episode_reward = 0
            done = False
            while not done:
                action = self.act(state)
                next_state, reward, done, _ = env.step(action)
                next_state = np.array(next_state, dtype=np.float32)
                episode_reward += reward
                self.remember(state, action, reward, next_state, done)
                state = next_state
                self.replay()

            rewards.append(episode_reward)

            # Record policy for animation
            self.policy_history.append(self.get_policy())

            print(f"Episode {e + 1}/{episodes}, Reward: {episode_reward}, Epsilon: {self.epsilon}")

            # Update target network
            if e % target_update_freq == 0:
                self.update_target_model()

        return rewards

# Initialize the environment and agent with new parameters
env = TreasureExplorerEnv()
agent = DQNAgent(state_dim=3, action_dim=3, gamma=0.99, lr=0.001, epsilon=1.0, epsilon_decay=0.999, epsilon_min=0.1, batch_size=64, memory_size=20000)

# Train the agent and record policies
rewards = agent.train(env, episodes=300)

# Plotting the training rewards
plt.figure(figsize=(10, 6))
plt.plot(rewards, marker='o')
plt.title('Training Rewards Over Episodes')
plt.xlabel('Episodes')
plt.ylabel('Total Reward')
plt.grid()
plt.show()

def animate_policy(agent, grid_size):
    # Define the vertices of the simplex triangle for 3 actions
    vertices = np.array([[0, 0], [1, 0], [0.5, np.sqrt(3)/2]])

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-0.1, np.sqrt(3)/2 + 0.1)

    # Plot the simplex triangle
    ax.plot([vertices[0, 0], vertices[1, 0]], [vertices[0, 1], vertices[1, 1]], 'k-')
    ax.plot([vertices[1, 0], vertices[2, 0]], [vertices[1, 1], vertices[2, 1]], 'k-')
    ax.plot([vertices[2, 0], vertices[0, 0]], [vertices[2, 1], vertices[0, 1]], 'k-')

    # Mark each vertex with its corresponding action
    ax.text(vertices[0, 0] - 0.05, vertices[0, 1] - 0.05, 'Explore', fontsize=12)
    ax.text(vertices[1, 0] + 0.02, vertices[1, 1], 'Dig', fontsize=12)
    ax.text(vertices[2, 0], vertices[2, 1] + 0.02, 'Hint', fontsize=12)

    # Initialize policy points
    points, = ax.plot([], [], 'bo')

    def update(frame):
        policies = agent.policy_history[frame]
        points.set_data([], [])

        for policy in policies:
            point = np.dot(policy, vertices)
            points.set_data(np.append(points.get_xdata(), point[0]), np.append(points.get_ydata(), point[1]))

        ax.set_title(f'Policy Evolution - Frame {frame + 1}/{len(agent.policy_history)}')
        return points,

    ani = FuncAnimation(fig, update, frames=len(agent.policy_history), blit=True, repeat=False)

    # Save the animation as HTML
    ani.save('policy_animation.html', writer='html')

    plt.close(fig)
    return ani

# Create the animation and display it
animation = animate_policy(agent, env.grid_size)
HTML(animation.to_jshtml())

import matplotlib.pyplot as plt
import numpy as np

def plot_action_preferences(agent, grid_size, max_steps):
    # Prepare data for plotting
    step_counts = np.arange(max_steps + 1)
    action_probs = {0: [], 1: [], 2: []}  # Dictionary to store probabilities for each action

    # Iterate over each possible remaining step count
    for steps_remaining in step_counts:
        # For simplicity, let's use the middle of the grid as the state space for analysis
        x, y = grid_size // 2, grid_size // 2

        # Construct the state for the given number of remaining steps
        state = np.array([x, y, steps_remaining], dtype=np.float32)
        state_tensor = torch.FloatTensor(state).unsqueeze(0)

        # Get the Q-values and compute action probabilities
        with torch.no_grad():
            q_values = agent.model(state_tensor).numpy().flatten()
        max_q_value = np.max(q_values)
        stable_q_values = q_values - max_q_value
        policy = np.exp(stable_q_values) / np.sum(np.exp(stable_q_values))

        # Append the probabilities to the dictionary
        for action in range(3):
            action_probs[action].append(policy[action])

    # Plot the action probabilities as a function of remaining steps
    plt.figure(figsize=(10, 6))
    plt.plot(step_counts, action_probs[0], label='Explore (Action 0)', marker='o')
    plt.plot(step_counts, action_probs[1], label='Dig (Action 1)', marker='o')
    plt.plot(step_counts, action_probs[2], label='Hint (Action 2)', marker='o')

    plt.title('Action Preferences Based on Steps Remaining')
    plt.xlabel('Steps Remaining')
    plt.ylabel('Action Probability')
    plt.legend()
    plt.grid()
    plt.show()

# Run the plot function with the trained agent
plot_action_preferences(agent, grid_size=env.grid_size, max_steps=env.max_steps)

import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm  # For progress bar

def run_experiments(agent, env_class, num_experiments=1000, max_steps=40):
    all_rewards = []

    for _ in tqdm(range(num_experiments), desc="Running experiments"):
        env = env_class()  # Create a new environment instance
        state = env.reset()
        state = np.array(state, dtype=np.float32)
        cumulative_rewards = []  # To store rewards for the current experiment
        cumulative_reward = 0  # Initialize cumulative reward
        done = False

        while not done:
            action = agent.act(state)  # Choose action using the trained agent
            next_state, reward, done, _ = env.step(action)
            state = np.array(next_state, dtype=np.float32)

            cumulative_reward = reward
            cumulative_rewards.append(cumulative_reward)

            if len(cumulative_rewards) >= max_steps:  # Limit to max steps
                break

        # Pad the reward list to max_steps with the last value (cumulative_reward)
        cumulative_rewards.extend([cumulative_reward] * (max_steps - len(cumulative_rewards)))
        all_rewards.append(cumulative_rewards)

    # Convert all_rewards to a NumPy array for easier manipulation
    all_rewards = np.array(all_rewards)

    # Compute mean rewards over time
    mean_rewards = np.mean(all_rewards, axis=0)

    # Plotting the mean rewards over time
    plt.figure(figsize=(10, 6))
    plt.plot(mean_rewards, marker='o')
    plt.title('Mean Cumulative Rewards Over Time (1000 Experiments)')
    plt.xlabel('Steps')
    plt.ylabel('Mean Cumulative Reward')
    plt.grid()
    plt.show()

# Run the 10000 experiments and plot mean rewards
run_experiments(agent, TreasureExplorerEnv, num_experiments=10000, max_steps=30)

import numpy as np
import random
import gym
from gym import spaces

class RegularizedTreasureExplorerEnv(gym.Env):
    def __init__(self, delta=0.5, alpha=0.1):
        super(RegularizedTreasureExplorerEnv, self).__init__()
        self.grid_size = 6
        self.max_steps = 30
        self.delta = delta  # Uncertainty parameter for reward
        self.alpha = alpha  # Regularization coefficient

        # State: (explorer_x, explorer_y, steps_remaining)
        self.observation_space = spaces.Box(low=np.array([0, 0, 0]),
                                            high=np.array([self.grid_size - 1, self.grid_size - 1, self.max_steps]),
                                            dtype=np.int32)

        # Actions: 0 = explore, 1 = dig, 2 = hint
        self.action_space = spaces.Discrete(3)

        # Fixed treasure position
        self.treasure_pos = (random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1))

        # Initialize game state
        self.reset()

    def reset(self):
        self.steps = 0

        # Place explorer at random position
        self.explorer_pos = (random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1))

        # Ensure explorer and treasure do not start at the same position
        while self.explorer_pos == self.treasure_pos:
            self.explorer_pos = (random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1))

        return self._get_observation()

    def _get_observation(self):
        x, y = self.explorer_pos
        steps_remaining = self.max_steps - self.steps
        return np.array([x, y, steps_remaining], dtype=np.int32)

    def step(self, action):
        self.steps += 1
        x, y = self.explorer_pos
        reward = 0  # Initialize reward

        if action == 0:  # Explore
            self._explore()
            reward = -1 + np.random.uniform(-self.delta, self.delta)
        elif action == 1:  # Dig
            if self.explorer_pos == self.treasure_pos:
                reward = 10
                done = True
                return self._get_observation(), reward, done, {}
            else:
                reward = -2 + np.random.uniform(-self.delta, self.delta)
        elif action == 2:  # Hint
            reward = -3 + np.random.uniform(-self.delta, self.delta)
            if self._is_treasure_adjacent():
                self.explorer_pos = self.treasure_pos

        # Regularization term proportional to the norm of the policy
        policy_regularization = -self.alpha * np.linalg.norm(np.ones(self.action_space.n) / self.action_space.n)
        reward += policy_regularization

        done = self.steps >= self.max_steps
        return self._get_observation(), reward, done, {}

    def _explore(self):
        x, y = self.explorer_pos
        possible_moves = self._get_adjacent_positions(x, y)
        self.explorer_pos = random.choice(possible_moves)

    def _get_adjacent_positions(self, x, y):
        # Get all valid adjacent positions
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1),
                      (1, 1), (1, -1), (-1, 1), (-1, -1)]
        positions = [(x + dx, y + dy) for dx, dy in directions]
        return [(nx, ny) for nx, ny in positions if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size]

    def _is_treasure_adjacent(self):
        x, y = self.explorer_pos
        return self.treasure_pos in self._get_adjacent_positions(x, y)

    def render(self, mode='human'):
        grid = np.zeros((self.grid_size, self.grid_size))
        tx, ty = self.treasure_pos
        ex, ey = self.explorer_pos
        grid[tx, ty] = 2  # Treasure position
        grid[ex, ey] = 1  # Explorer position
        print(grid)

# Initialize the environment and agent with new parameters
env = RegularizedTreasureExplorerEnv()
regulized_agent = DQNAgent(state_dim=3, action_dim=3, gamma=0.99, lr=0.001, epsilon=1.0, epsilon_decay=0.999, epsilon_min=0.1, batch_size=64, memory_size=20000)

# Train the agent and record policies
regulized_rewards = regulized_agent.train(env, episodes=200)

# Plotting the training rewards
plt.figure(figsize=(10, 6))
plt.plot(regulized_rewards, marker='o')
plt.title('Training Rewards Over Episodes')
plt.xlabel('Episodes')
plt.ylabel('Total Reward')
plt.grid()
plt.show()

animation = animate_policy(regulized_agent, env.grid_size)
HTML(animation.to_jshtml())

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import deque
import matplotlib.pyplot as plt

class DQNAgent:
    def __init__(self, state_dim, action_dim, gamma=0.99, lr=0.001, epsilon=1.0, epsilon_decay=0.995, epsilon_min=0.1, batch_size=64, memory_size=20000, alpha=0.5):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.batch_size = batch_size
        self.memory = deque(maxlen=memory_size)
        self.alpha = alpha  # Regularization coefficient

        # Neural networks
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)

        # Update target model weights
        self.update_target_model()

    def _build_model(self):
        """Build the neural network model."""
        return nn.Sequential(
            nn.Linear(self.state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, self.action_dim)
        )

    def update_target_model(self):
        """Copy weights from the model to the target model."""
        self.target_model.load_state_dict(self.model.state_dict())

    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay memory."""
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        """Choose an action based on epsilon-greedy policy."""
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_dim)
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            act_values = self.model(state_tensor)
        return torch.argmax(act_values[0]).item()

    def compute_policy(self, q_values):
        """Compute the policy distribution using softmax over Q-values."""
        max_q = np.max(q_values)
        exp_q = np.exp(q_values - max_q)  # Softmax trick for numerical stability
        policy = exp_q / np.sum(exp_q)
        return policy

    def replay(self):
        """Train the model using random samples from replay memory."""
        if len(self.memory) < self.batch_size:
            return

        minibatch = random.sample(self.memory, self.batch_size)
        for state, action, reward, next_state, done in minibatch:
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0)

            # Q-value update
            target = reward
            if not done:
                with torch.no_grad():
                    target = reward + self.gamma * torch.max(self.target_model(next_state_tensor)[0]).item()

            target_f = self.model(state_tensor)
            q_values = target_f.detach().numpy().flatten()

            # Compute the current policy
            policy = self.compute_policy(q_values)

            # Compute the norm-2 penalty term for the policy
            norm_2_penalty = -self.alpha * np.linalg.norm(policy, ord=2)

            # Adjust reward with the regularization term
            adjusted_reward = reward + norm_2_penalty
            target = adjusted_reward + (self.gamma * torch.max(self.target_model(next_state_tensor)[0]).item() if not done else 0)

            target_f[0][action] = target

            # Compute loss and perform gradient descent
            self.optimizer.zero_grad()
            loss = nn.MSELoss()(self.model(state_tensor), target_f)
            loss.backward()
            self.optimizer.step()

        # Epsilon decay
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def train(self, env, episodes=1000, target_update_freq=10):
        rewards = []
        for e in range(episodes):
            state = env.reset()
            state = np.array(state, dtype=np.float32)
            episode_reward = 0
            done = False
            while not done:
                action = self.act(state)
                next_state, reward, done, _ = env.step(action)
                next_state = np.array(next_state, dtype=np.float32)
                episode_reward += reward
                self.remember(state, action, reward, next_state, done)
                state = next_state
                self.replay()

            rewards.append(episode_reward)
            print(f"Episode {e + 1}/{episodes}, Reward: {episode_reward}, Epsilon: {self.epsilon}")

            # Update target network
            if e % target_update_freq == 0:
                self.update_target_model()

        return rewards

# Initialize the environment and agent with new parameters
env = TreasureExplorerEnv()
regulized_agent = DQNAgent(state_dim=3, action_dim=3, gamma=0.99, lr=0.001, epsilon=1.0, epsilon_decay=0.995, epsilon_min=0.1, batch_size=64, memory_size=20000, alpha=0.5)

# Train the agent
regulized_rewards = regulized_agent.train(env, episodes=250)

# Plotting the training rewards
plt.figure(figsize=(10, 6))
plt.plot(regulized_rewards, marker='o')
plt.title('Training Rewards Over Episodes')
plt.xlabel('Episodes')
plt.ylabel('Total Reward')
plt.grid()
plt.show()

plot_action_preferences(regulized_agent, grid_size=env.grid_size, max_steps=env.max_steps)

run_experiments(regulized_agent, TreasureExplorerEnv, num_experiments=10000, max_steps=30)

import numpy as np
import random
import gym
from gym import spaces

class RegularizedTreasureExplorerEnv(gym.Env):
    def __init__(self, delta=0.5):
        super(RegularizedTreasureExplorerEnv, self).__init__()
        self.grid_size = 6
        self.max_steps = 30
        self.delta = delta  # Uncertainty parameter for reward

        # State: (explorer_x, explorer_y, steps_remaining)
        self.observation_space = spaces.Box(low=np.array([0, 0, 0]),
                                            high=np.array([self.grid_size - 1, self.grid_size - 1, self.max_steps]),
                                            dtype=np.int32)

        # Actions: 0 = explore, 1 = dig, 2 = hint
        self.action_space = spaces.Discrete(3)

        # Fixed treasure position
        self.treasure_pos = (random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1))

        # Initialize game state
        self.reset()

    def reset(self):
        self.steps = 0

        # Place explorer at random position
        self.explorer_pos = (random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1))

        # Ensure explorer and treasure do not start at the same position
        while self.explorer_pos == self.treasure_pos:
            self.explorer_pos = (random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1))

        return self._get_observation()

    def _get_observation(self):
        x, y = self.explorer_pos
        steps_remaining = self.max_steps - self.steps
        return np.array([x, y, steps_remaining], dtype=np.int32)

    def step(self, action):
        self.steps += 1
        x, y = self.explorer_pos
        reward = 0  # Initialize reward

        if action == 0:  # Explore
            self._explore()
            reward = -1 + np.random.uniform(-self.delta, self.delta) -self.delta * np.linalg.norm(np.ones(self.action_space.n) / self.action_space.n)
        elif action == 1:  # Dig
            if self.explorer_pos == self.treasure_pos:
                reward = 10
                done = True
                return self._get_observation(), reward, done, {}
            else:
                reward = -2 + np.random.uniform(-self.delta, self.delta) -self.delta * np.linalg.norm(np.ones(self.action_space.n) / self.action_space.n)
        elif action == 2:  # Hint
            reward = -3 + np.random.uniform(-self.delta, self.delta) -self.delta * np.linalg.norm(np.ones(self.action_space.n) / self.action_space.n)
            if self._is_treasure_adjacent():
                self.explorer_pos = self.treasure_pos

        done = self.steps >= self.max_steps
        return self._get_observation(), reward, done, {}

    def _explore(self):
        x, y = self.explorer_pos
        possible_moves = self._get_adjacent_positions(x, y)
        self.explorer_pos = random.choice(possible_moves)

    def _get_adjacent_positions(self, x, y):
        # Get all valid adjacent positions
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1),
                      (1, 1), (1, -1), (-1, 1), (-1, -1)]
        positions = [(x + dx, y + dy) for dx, dy in directions]
        return [(nx, ny) for nx, ny in positions if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size]

    def _is_treasure_adjacent(self):
        x, y = self.explorer_pos
        return self.treasure_pos in self._get_adjacent_positions(x, y)

    def render(self, mode='human'):
        grid = np.zeros((self.grid_size, self.grid_size))
        tx, ty = self.treasure_pos
        ex, ey = self.explorer_pos
        grid[tx, ty] = 2  # Treasure position
        grid[ex, ey] = 1  # Explorer position
        print(grid)