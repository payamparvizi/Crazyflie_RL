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
from .networks import PolicyNetwork, ValueNetwork
from .utils import calculate_discounted_rewards
from .utils import calculate_discounted_rewards
from crazyflie_env.crazyflie_env import CrazyflieHoverEnv
from torch.distributions import Normal, Independent
from utils.compute_sm_v2 import compute_sm
import argparse
from utils.arguments import get_args
import os
import pickle

class PPOAgent:
    def __init__(self, env, policy_lr=1e-4, value_lr=1e-4, value_ratio=0.5, gamma=0.99, clip_epsilon=0.2, 
                 update_epochs=10, target_altitude=1.0, entropy_c=0, hidden_size_p=64,
                 hidden_size_v=64, task='simulation', seed_value=10, episodes_per_epoch=1, trial_no=1):
        
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
        self.episodes_per_epoch = episodes_per_epoch
        self._seed = seed_value
        
        # initial values used to save a policy and value function
        self.total_reward_0 = -200
        self.average_altitude_0 = -50
        self.act_fluc_0 = 30

        self.trial_no = trial_no

        # Networks
        self.policy_net = PolicyNetwork(input_dim=2, action_dim=1, hidden_size=hidden_size_p)  # 1 state input (altitude), 2 action outputs (up or down)
        self.value_net = ValueNetwork(input_dim=2, hidden_size=hidden_size_v)  # 1 state input (altitude)
        
        # Optimizers
        self.policy_optimizer = optim.Adam(self.policy_net.parameters(), lr=policy_lr)
        self.value_optimizer = optim.Adam(self.value_net.parameters(), lr=value_lr)
    
    def choose_action(self, state):
        state = torch.FloatTensor(state).unsqueeze(0)  # Ensure state is a tensor
        action, log_prob = self.policy_net.get_action(state)  # Get continuous action and log prob
        
        # Convert action to numpy if it's a multi-dimensional tensor
        action = action.detach().numpy()  # Convert the tensor to a numpy array if needed
    
        return action, log_prob  # Return the full action and log probability

    def compute_advantages(self, returns, states):
        returns = torch.FloatTensor(returns)
        states = torch.FloatTensor(states) 
        values = self.value_net(states).squeeze()
        advantages = returns - values.detach()
        
        return advantages
        
    
    def action_sampling(self, obs):
        (mean, log_std) = self.policy_net(obs)
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

        old_log_probs = torch.tensor(old_log_probs, dtype=torch.float32)
        rewards_tensor = torch.FloatTensor(rewards)
        
        states = torch.FloatTensor(states)
        next_states = torch.FloatTensor(next_states)
        actions = torch.FloatTensor(actions)

        for _ in range(self.update_epochs):
            _, log_probs, entropy = self.policy_net.evaluate(states, actions)
            
            state_values = self.value_net(states)
            
            ratios = torch.exp(log_probs - old_log_probs.detach())  

            advantages = torch.FloatTensor(advantages).detach()
            returns = torch.FloatTensor(returns).detach()
            
            # Compute action fluctuation statistics
            self.act_fluc, self.K_act, self.K_mean = self.action_fluctuation(states, next_states)
            
            # Clipped Surrogate Objective for PPO
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1.0 - self.clip_epsilon, 1.0 + self.clip_epsilon) * advantages
    
            # Compute the value loss
            returns_tensor = returns.squeeze()  
            state_values_tensor = state_values.squeeze()
            value_loss = torch.nn.MSELoss()(state_values_tensor, returns_tensor)
    
            loss = -torch.min(surr1, surr2).mean() - self.entropy_c * entropy.mean() + self.value_ratio * value_loss
    
            # Update policy network
            self.policy_optimizer.zero_grad()
            loss.backward(retain_graph=True)
            self.policy_optimizer.step()
    
            # Update value network
            self.value_optimizer.zero_grad()
            value_loss.backward()  
            self.value_optimizer.step()
            
            self.policy_loss = loss
            self.value_loss = value_loss


    def load_policy(self, file_path1="policy_net.pth", file_path2="value_net.pth"):
        """Load the policy and value function networks from a file."""
        state_dict1 = torch.load(file_path1, map_location=torch.device('cpu'), weights_only=True)  # Ensure only weights are loaded
        self.policy_net.load_state_dict(state_dict1)
        self.policy_net.eval()  # Set the network to evaluation mode
        
        state_dict2 = torch.load(file_path2, map_location=torch.device('cpu'), weights_only=True)  # Ensure only weights are loaded
        self.value_net.load_state_dict(state_dict2)
        self.value_net.eval()  # Set the network to evaluation mode
        
        print(f"Policy and value function networks loaded ....")
    
    
    def save_policies(self, file_path1="policy_net.pth", file_path2="value_net.pth"):
        """Save the policy network to a file."""
        torch.save(self.policy_net.state_dict(), file_path1)
        torch.save(self.value_net.state_dict(), file_path2)
        print(f"Policy and value function networks are saved ....")
    
    
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
        with open(file_path, 'wb') as file:
            pickle.dump(metadata, file)

    
    def wait_for_manual_reconnection(self, args: argparse.Namespace = get_args()):
        env = CrazyflieHoverEnv(target_altitude=args.target_altitude, max_steps=args.max_steps,
                                noise_threshold=args.noise_threshold, 
                                r_stab=args.r_stab, action_range=args.action_range, 
                                lag_factor=args.lag_factor, task=args.task, seed_value=args.seed)
        
        self.env = env


    def train(self, max_episodes=1000, max_steps=100, resume_from=False):
        """Optimized PPO training loop with episodic batch storage."""
        
        if resume_from:
            self.load_policy(f"policies_saved/policy_seed_{self._seed}.pth", 
                               f"policies_saved/value_seed_{self._seed}.pth")
            
        state_dim = 2 
        action_dim = 1
        episodes_per_epoch = self.episodes_per_epoch
        
        batch_states = np.zeros((episodes_per_epoch, max_steps, state_dim), dtype=np.float32)
        batch_next_states = np.zeros((episodes_per_epoch, max_steps, state_dim), dtype=np.float32)
        batch_actions = np.zeros((episodes_per_epoch, max_steps, action_dim), dtype=np.float32)
        batch_rewards = np.zeros((episodes_per_epoch, max_steps), dtype=np.float32)
        batch_log_probs = np.zeros((episodes_per_epoch, max_steps), dtype=np.float32)
        batch_returns = np.zeros((episodes_per_epoch, max_steps), dtype=np.float32)
        batch_ep_lens = np.zeros((episodes_per_epoch, max_steps), dtype=np.float32)
    
        episode_index = 0 
    
        for episode in range(max_episodes):

            state = self.env.reset()
            done = False
            
    
            states, next_states, actions, rewards, log_probs = [], [], [], [], []
            velocities, heights = [], []
            
            ep_lens = []
            ep_len = 0
    
            for step in range(max_steps):
                action, log_prob = self.choose_action(state)  # Get action from policy
                states.append(state)
    
                # Step the environment
                state, reward, done, _ = self.env.step(action)
                next_states.append(state)
                actions.append(action)
                rewards.append(reward)
                log_probs.append(log_prob)
                
                velocities.append(state[1])
                heights.append(state[0])
                
                ep_len += 1
                
                if done:
                    ep_lens.append(ep_len)
                    break
            
            returns = calculate_discounted_rewards(rewards, self.gamma)
            num_samples = len(states)
    
            batch_states[episode_index, :num_samples] = np.array(states, dtype=np.float32)
            batch_next_states[episode_index, :num_samples] = np.array(next_states, dtype=np.float32)
            batch_actions[episode_index, :num_samples] = np.array(actions, dtype=np.float32).reshape(num_samples, -1)
            batch_rewards[episode_index, :num_samples] = np.array(rewards, dtype=np.float32)
            batch_log_probs[episode_index, :num_samples] = np.array(
                [lp.detach().numpy().squeeze() for lp in log_probs], dtype=np.float32
            )
            batch_returns[episode_index, :num_samples] = np.array(returns, dtype=np.float32)
            batch_ep_lens[episode_index, :num_samples] = np.array(ep_lens, dtype=np.float32)
            
            episode_index += 1

            if self.task == 'real':
                
                print(f"episode {episode+1} / {max_episodes}")
                choice = input("Press 'R' to reboot Crazyflie: ").upper()
                
                if choice == 'R':
                    input("Please manually reboot the Crazyflie. If done, press Enter ...")
                    self.wait_for_manual_reconnection(get_args())
                    
                
                if choice != 'R':
                    input("Press Enter to start the next episode...")
    
            if (episode + 1) % episodes_per_epoch == 0:

                batch_states = batch_states[:episode_index, :, :]
                batch_next_states = batch_next_states[:episode_index, :, :]
                batch_actions = batch_actions[:episode_index, :, :]
                batch_rewards = batch_rewards[:episode_index, :]
                batch_log_probs = batch_log_probs[:episode_index, :]
                batch_returns = batch_returns[:episode_index, :]
                batch_ep_lens = batch_ep_lens[:episode_index, :]
                
                advantages = self.compute_advantages(batch_returns, batch_states)
                
                smoothness_value = compute_sm(batch_rewards, batch_actions, batch_ep_lens)
                
                total_reward = batch_rewards.mean(axis=0).sum()
                average_altitude = batch_rewards[:, -25:].mean(axis=0).sum()
                
                self.update_policy(batch_states, batch_actions, batch_log_probs, batch_returns, advantages, batch_rewards, batch_next_states)
    
                episode_index = 0
                    
                wandb.log({"total_reward": total_reward,
                            "action_fluctuation": self.act_fluc,
                            "policy_loss": self.policy_loss,
                            "value_loss": self.value_loss,
                            "average_altitude": average_altitude,
                            "smoothness_measure": smoothness_value
                          })
                
                print(f"episode {episode+1} / {max_episodes}")
                
                if self.task == 'simulation':
                    if total_reward > self.total_reward_0 and average_altitude > self.average_altitude_0:
                        self.total_reward_0 = total_reward
                        self.average_altitude_0 = average_altitude
                        
                        self.save_policies(f"policies_saved/policy_seed_{self._seed}.pth", 
                                           f"policies_saved/value_seed_{self._seed}.pth")
                        
                        with open(f"metadata_saved/total_reward_seed_{self._seed}.pkl", 'wb') as file:
                            pickle.dump(total_reward, file)
                        
                        with open(f"metadata_saved/average_altitude_seed_{self._seed}.pkl", 'wb') as file:
                            pickle.dump(average_altitude, file)
    
                        with open(f"metadata_saved/act_fluc_seed_{self._seed}.pkl", 'wb') as file:
                            pickle.dump(self.act_fluc, file)
    
                        with open(f"metadata_saved/velocities_seed_{self._seed}.pkl", 'wb') as file:
                            pickle.dump(velocities, file)
                            
                        with open(f"metadata_saved/heights_seed_{self._seed}.pkl", 'wb') as file:
                            pickle.dump(heights, file)
                            
                        with open(f"metadata_saved/episode_seed_{self._seed}.pkl", 'wb') as file:
                            pickle.dump(episode, file)
                        
                        with open(f"metadata_saved/sm_seed_{self._seed}.pkl", 'wb') as file:
                            pickle.dump(smoothness_value, file)
                        
                        
                elif self.task == 'real':
                    
                    with open(f"metadata_saved/total_reward_stg2_trial_{self.trial_no}.pkl", 'wb') as file:
                        pickle.dump(total_reward, file)
                    
                    with open(f"metadata_saved/average_altitude_stg2_trial_{self.trial_no}.pkl", 'wb') as file:
                        pickle.dump(average_altitude, file)

                    with open(f"metadata_saved/act_fluc_stg2_trial_{self.trial_no}.pkl", 'wb') as file:
                        pickle.dump(self.act_fluc, file)

                    with open(f"metadata_saved/velocities_stg2_trial_{self.trial_no}.pkl", 'wb') as file:
                        pickle.dump(velocities, file)
                        
                    with open(f"metadata_saved/heights_stg2_trial_{self.trial_no}.pkl", 'wb') as file:
                        pickle.dump(heights, file)
                        
                    with open(f"metadata_saved/episode_stg2_trial_{self.trial_no}.pkl", 'wb') as file:
                        pickle.dump(episode, file)
                    
                    with open(f"metadata_saved/sm_stg2_trial_{self.trial_no}.pkl", 'wb') as file:
                        pickle.dump(smoothness_value, file)
                        
                    self.save_policies(f"policies_saved/policy_stg2_trial_{self.trial_no}.pth", 
                                       f"policies_saved/value_stg2_trial_{self.trial_no}.pth")
                    
                    self.trial_no = self.trial_no + 1
                