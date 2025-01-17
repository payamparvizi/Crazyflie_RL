#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 26 16:05:25 2024

@author: payam
"""
import wandb

import torch
import torch.optim as optim
import numpy as np
from .networks import PolicyNetwork#, ValueNetwork
from .utils import calculate_discounted_rewards
from crazyflie_env.crazyflie_env import CrazyflieHoverEnv
from torch.distributions import Normal, Independent
from utils.compute_sm import compute_sm
import argparse
from utils.arguments import get_args
import os
import pickle

class PPOAgent:
    def __init__(self, env, policy_lr=1e-4, value_ratio=0.5, gamma=0.99, clip_epsilon=0.2, 
                 update_epochs=10, target_altitude=1.0, entropy_c=0, hidden_size_p=64,
                 hidden_size_v=64, task='simulation', seed_value=10):
        
        torch.manual_seed(seed_value)
        np.random.seed(seed_value)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed_value)
            torch.cuda.manual_seed_all(seed_value)
        
        self.env = env
        self.gamma = gamma
        self.clip_epsilon = clip_epsilon
        self.update_epochs = update_epochs
        self.target_altitude = target_altitude
        self.entropy_c = entropy_c
        self.task = task
        self.value_ratio = value_ratio

        # Networks
        self.policy_net = PolicyNetwork(input_dim=2, action_dim=1, hidden_size=hidden_size_p)  # 1 state input (altitude), 2 action outputs (up or down)
        # self.value_net = ValueNetwork(input_dim=2, hidden_size=hidden_size_v)  # 1 state input (altitude)
        
        # Optimizers
        self.policy_optimizer = optim.Adam(self.policy_net.parameters(), lr=policy_lr)
        # self.value_optimizer = optim.Adam(self.value_net.parameters(), lr=value_lr)
    
    def choose_action(self, state):
        state = torch.FloatTensor(state).unsqueeze(0)  # Ensure state is a tensor
        action, log_prob = self.policy_net.get_action(state)  # Get continuous action and log prob
        
        # Convert action to numpy if it's a multi-dimensional tensor
        action = action.detach().numpy()  # Convert the tensor to a numpy array if needed
    
        return action, log_prob  # Return the full action and log probability

    def compute_advantages(self, returns, states):
        returns = torch.FloatTensor(returns).unsqueeze(0)
        states = torch.FloatTensor(states).unsqueeze(0)
        _, _, values = self.policy_net(states)
        advantages = returns - values.detach()
        
        return advantages
        
    
    def action_sampling(self, obs):
        (mean, log_std, _) = self.policy_net(obs)
        mean = mean.squeeze()
        std = torch.exp(log_std.squeeze())
        
        P = Normal(mean, std)
        P = Independent(P, 1) 
        act = P.sample()
        log_prob = P.log_prob(act)
        return mean, act, log_prob.exp()

    def action_fluctuation(self, states, next_states):
        
        
        mean, act, _ = self.action_sampling(states)
        mean_next, act_next, _ = self.action_sampling(next_states)
        
        obs = states.squeeze()
        obs_next = next_states.squeeze()
        
        act_fluc = torch.norm(act - act_next, p=2, dim=-1).cpu()
        mu_fluc = torch.norm(mean - mean_next, p=2, dim=-1).cpu()
        obs_fluc = torch.norm(obs - obs_next, p=2, dim=-1).cpu().mean(dim=-1)
        
        K_act = act_fluc/obs_fluc
        K_mu = mu_fluc/obs_fluc
        
        return act_fluc.mean(), K_act.mean(), K_mu.mean()

    def update_policy(self, states, actions, old_log_probs, returns, advantages, rewards, next_states):
        """Update the policy using PPO."""
        old_log_probs = torch.stack(old_log_probs)  # Convert list to tensor
        rewards_tensor = torch.FloatTensor(rewards)
    
        for _ in range(self.update_epochs):
            
            states = torch.FloatTensor(states).unsqueeze(0)  # Ensure state is a tensor
            next_states = torch.FloatTensor(next_states).unsqueeze(0)
            actions = torch.FloatTensor(actions).unsqueeze(0)  # Ensure action is a tensor
            
            _, log_probs, entropy = self.policy_net.evaluate(states, actions)
            
            # Get state value from the value network
            _, _, state_values = self.policy_net(states)
    
            # Compute the ratio of new and old probabilities
            ratios = torch.exp(log_probs - old_log_probs.detach())  # Detach old_log_probs to avoid modifying the original tensor
            advantages = torch.FloatTensor(advantages).detach() # Detach advantages from the computation graph
            returns = torch.FloatTensor(returns).detach()  # Detach returns from the computation graph
    
            self.act_fluc, self.K_act, self.K_mean = self.action_fluctuation(states, next_states)
            
            # Clipped PPO loss
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1.0 - self.clip_epsilon, 1.0 + self.clip_epsilon) * advantages

            # Compute the value loss
            returns_tensor = torch.FloatTensor(returns).squeeze()  # Squeeze removes any extra dimensions
            state_values_tensor = torch.FloatTensor(state_values).squeeze()
            value_loss = torch.nn.MSELoss()(state_values_tensor, returns_tensor)

            loss = -torch.min(surr1, surr2).mean() - self.entropy_c * entropy.mean() + self.value_ratio * value_loss
            policy_loss = loss
            
            # Update policy network
            self.policy_optimizer.zero_grad()
            policy_loss.backward(retain_graph=True)  # Retain graph for multiple backward passes
            self.policy_optimizer.step()
    
            # # Update value network
            # self.value_optimizer.zero_grad()
            # value_loss.backward()  # No need to retain graph here
            # self.value_optimizer.step()
            
            self.policy_loss = policy_loss
            self.value_loss = value_loss


    def load_policy(self, file_path="policy_net.pth"):
        """Load the policy network from a file."""
        state_dict = torch.load(file_path, map_location=torch.device('cpu'), weights_only=True)  # Ensure only weights are loaded
        self.policy_net.load_state_dict(state_dict)
        self.policy_net.eval()  # Set the network to evaluation mode
        print(f"Policy network loaded ....")
    
    
    def save_policy(self, file_path="policy_net.pth"):
        """Save the policy network to a file."""
        torch.save(self.policy_net.state_dict(), file_path)
        print(f"Policy network saved ....")
        
    
    def load_metadata(self, file_path="metadata.pkl"):
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                metadata = pickle.load(file)
        else:
            metadata = []
        
        return metadata
        
    
    def save_metadata(self, total_reward, act_fluc, policy_loss, value_loss, average_altitude, metadata, file_path):
        
        x = [total_reward, act_fluc.item(), policy_loss.item(), value_loss.item(), average_altitude]
        metadata.append(x)
        with open(file_path, 'wb') as file:  # 'wb' mode for writing in binary
            pickle.dump(metadata, file)

    
    def wait_for_manual_reconnection(self, args: argparse.Namespace = get_args()):
        env = CrazyflieHoverEnv(target_altitude=args.target_altitude, max_steps=args.max_steps,
                                alpha=args.alpha, noise_threshold=args.noise_threshold, 
                                r_max=args.r_max, k_rew=args.k_rew, r_stab=args.r_stab, 
                                action_range=args.action_range, lag_factor=args.lag_factor, 
                                task=args.task, seed_value=args.seed)
        
        self.env = env
        
    def train(self, max_episodes=1000, max_steps=100, resume_from=False):
        """Train the PPO agent with manual reconnection after crashes."""
        
        if resume_from:
            self.load_policy("policies_saved/policy_net.pth")
            
        metadata = self.load_metadata("metadata_saved/metadata.pkl")
        
        for episode in range(max_episodes):
            # os.system('clear')
            # print(f"Episode {episode + 1} has started ... ")
            
            state = self.env.reset()  # Reset the environment at the start of each episode
            done = False
            states = []
            next_states = []
            actions = []
            rewards = []
            log_probs = []
            values = []
            next_values = []
            total_reward = 0
            total_altitude = 0
            
            for step in range(max_steps):
                # Choose an action and get the log probability from the policy
                action, log_prob = self.choose_action(state)
                states.append(state)
    
                # Step the environment and get the next state, reward, and whether the episode is done
                state, reward, done, _ = self.env.step(action)
                
                if step > int(max_steps*3/4 - 1):
                    total_altitude += abs(state[0] - 1)
                    
                next_state = state
                
                # Store trajectory data
                next_states.append(state)
                actions.append(action)
                rewards.append(reward)
                log_probs.append(log_prob)
                
                total_reward += reward
                
                # If the episode is done (e.g., Crazyflie crashes or reaches the end of the episode), stop the Crazyflie and break
                if done:
                    break

            average_altitude = total_altitude/(int(max_steps/4))
            # print(average_altitude)
            # Calculate the returns and advantages
            returns = calculate_discounted_rewards(rewards, self.gamma)  # You already have a function for this
            
            states = np.array(states)
            next_states = np.array(next_states)
            actions = np.array(actions)
            
            advantages = self.compute_advantages(returns, states)  # Calculate advantages
            # advantages = self.compute_advantages(rewards, states)  # Calculate advantages
            
            if (step+1) == max_steps:
                # Update the policy and value networks with PPO
                self.update_policy(states, actions, log_probs, returns, advantages, rewards, next_states)
                
                wandb.log({"total_reward": total_reward,
                            # "steps": step, 
                           "action_fluctuation": self.act_fluc,
                           # "K_mean": self.K_mean,
                           # "K_act": self.K_act,
                            "policy_loss": self.policy_loss,
                            "value_loss": self.value_loss,
                           # "smoothness value": smoothness_value,
                           "average_altitude": average_altitude,
                          })
                
                # self.save_metadata(total_reward, self.act_fluc, self.policy_loss, 
                #                    self.value_loss, average_altitude, metadata, "metadata_saved/metadata.pkl")
                
                if self.task == 'simulation':
                    
                    if episode%100 == 0:
                        # smoothness_value = compute_sm(self.env, self.policy_net)
                        self.save_policy(f"policies_saved/policy_net.pth")
                
            # wandb.log({"total_reward": total_reward,
            #             # "steps": step, 
            #            "action_fluctuation": self.act_fluc,
            #            # "K_mean": self.K_mean,
            #            # "K_act": self.K_act,
            #             "policy_loss": self.policy_loss,
            #             "value_loss": self.value_loss,
            #            # "smoothness value": smoothness_value,
            #            "average_altitude": average_altitude,
            #           })
            
            print(f"Episode {episode + 1} done after {step + 1}/{max_steps} steps with total reward: {total_reward}")
            
            if self.task == 'real':
                choice = input("Press 'R' to reboot Crazyflie: ").upper()
                
                self.save_metadata(total_reward, self.act_fluc, self.policy_loss, 
                                   self.value_loss, average_altitude, metadata, "metadata_saved/metadata.pkl")
                
                self.save_policy(f"policies_saved/policy_net.pth")
                
            #     if choice == 'R':
            #         # print("Please manually reboot the Crazyflie and reconnect.")
            #         input("Please manually reboot the Crazyflie. If done, press Enter ...")
            #         self.wait_for_manual_reconnection(get_args())
                    
                if choice != 'R':
                    input("Press Enter to start the next episode...")

            #     # Reset the Crazyflie before the next episode begins
            #     self.env.reset()






