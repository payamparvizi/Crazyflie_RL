#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 26 16:06:08 2024

@author: payam
"""

import numpy as np

def calculate_discounted_rewards(rewards, gamma):
    discounted_rewards = np.zeros_like(rewards)
    cumulative_reward = 0
    for t in reversed(range(len(rewards))):
        cumulative_reward = rewards[t] + gamma * cumulative_reward
        discounted_rewards[t] = cumulative_reward
    return discounted_rewards
