# Reinforcement Learning on Crazyflie 2.1

## Overview 

This code implements the Proximal Policy Optimization (PPO) algorithm for the Crazyflie 2.1 drone. It includes both a simulated environment and a real-world setup for training the PPO algorithm to control the Crazyflie 2.1 to hover at a specific altitude. The figure of the Crazyflie 2.1 is shown below:

<p align="center">
  <img src="https://github.com/user-attachments/assets/e15c1612-ea9d-4a60-ac8f-029d1f8b9d1a" align="center" width="300">
</p>

## Installation Instructions

In this work, we used Linux operating system with Python 3.9.20 version. The installation process is as follows:

1. **Create and activate the environment:**

```
conda create --name crazyflie_env python=3.9.20
conda activate crazyflie_env
```
