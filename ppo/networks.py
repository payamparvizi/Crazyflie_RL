#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 26 16:04:55 2024

@author: payam
"""

import torch
import torch.nn as nn
# import torch.distributions as dist
from torch.distributions import MultivariateNormal, Normal
import numpy as np
import torch.nn.init as init

class PolicyNetwork(nn.Module):
    def __init__(self, input_dim, action_dim, hidden_size, init_w=3e-3):
        super(PolicyNetwork, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_size)
        init.uniform_(self.fc1 .weight, -1./np.sqrt(input_dim), 1./np.sqrt(input_dim))
        init.uniform_(self.fc1.bias, -1./np.sqrt(input_dim), 1./np.sqrt(input_dim))
        
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        init.uniform_(self.fc2 .weight, -1./np.sqrt(hidden_size), 1./np.sqrt(hidden_size))
        init.uniform_(self.fc2.bias, -1./np.sqrt(hidden_size), 1./np.sqrt(hidden_size))
        
        self.mean_layer = nn.Linear(hidden_size, action_dim)
        self.mean_layer.weight.data.uniform_(-init_w, init_w)
        self.mean_layer.bias.data.uniform_(-init_w, init_w)
        
        self.log_std_layer = nn.Linear(hidden_size, action_dim)
        self.log_std_layer.weight.data.uniform_(-init_w, init_w)
        self.log_std_layer.bias.data.uniform_(-init_w, init_w)
        
        # self.log_std = nn.Parameter(torch.zeros(output_dim))
        

    def forward(self, state):
        x = torch.relu(self.fc1(state))
        x = torch.relu(self.fc2(x))
        mean = self.mean_layer(x)   # Constrain output to [-1, 1] using tanh
        # std = torch.exp(self.log_std)  # Exponentiate log std to get the standard deviation
        log_std = self.log_std_layer(x)
        return mean, log_std

    def get_action(self, state):
        cov_var = torch.full(size=(1,), fill_value=0.5)
        cov_mat = torch.diag(cov_var)
        mean, log_std = self.forward(state)
        std = torch.exp(log_std)
        
        # dist = MultivariateNormal(mean, cov_mat)
        dist = Normal(mean, std)
        action = dist.rsample()
        log_prob = dist.log_prob(action)
        return action, log_prob

    def evaluate(self, state, action_):
        cov_var = torch.full(size=(1,), fill_value=0.5)
        cov_mat = torch.diag(cov_var)
        mean, log_std = self.forward(state)
        std = torch.exp(log_std)
        # dist = MultivariateNormal(mean, cov_mat)
        dist = Normal(mean, std)
        log_prob = dist.log_prob(action_)
        
        entropy = 0.5 + 0.5 * torch.log(2 * torch.pi * torch.exp(log_std * 2)).squeeze()

        return mean, log_prob, entropy
    

class ValueNetwork(nn.Module):
    def __init__(self, input_dim, hidden_size, init_w = 3e-3):
        super(ValueNetwork, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_size)
        init.uniform_(self.fc1 .weight, -1./np.sqrt(input_dim), 1./np.sqrt(input_dim))
        init.uniform_(self.fc1.bias, -1./np.sqrt(input_dim), 1./np.sqrt(input_dim))
        
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        init.uniform_(self.fc2 .weight, -1./np.sqrt(hidden_size), 1./np.sqrt(hidden_size))
        init.uniform_(self.fc2.bias, -1./np.sqrt(hidden_size), 1./np.sqrt(hidden_size))
        
        self.value_layer = nn.Linear(hidden_size, 1)  # Output a single value (scalar)
        self.value_layer.weight.data.uniform_(-init_w, init_w)
        self.value_layer.bias.data.uniform_(-init_w, init_w)

    def forward(self, state):
        x = torch.relu(self.fc1(state))
        x = torch.relu(self.fc2(x))
        value = self.value_layer(x)  # Output the scalar value
        return value