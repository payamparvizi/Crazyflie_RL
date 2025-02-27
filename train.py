# train.py

from crazyflie_env.crazyflie_env import CrazyflieHoverEnv
from ppo.ppo_agent import PPOAgent
import numpy as np
#import random
import torch
import wandb
import argparse
from utils.arguments import get_args


from crazyflie_env.crazyflie_env import CrazyflieHoverEnv
from ppo.ppo_agent import PPOAgent  # Import your PPOAgent class

def train_(args: argparse.Namespace = get_args()) -> None:
    
    wandb.init(project="crazyflie_experiment", config=vars(args))
    
    seed_value = args.seed
    torch.manual_seed(seed_value)
    np.random.seed(seed_value)
    
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed_value)
        torch.cuda.manual_seed_all(seed_value)
    
    max_steps = args.max_steps
    target_altitude = args.target_altitude
    max_episodes = args.max_episodes
    
    # Step 1: InitialiRze the environment
    env = CrazyflieHoverEnv(target_altitude=target_altitude, max_steps=max_steps,
                            noise_threshold=args.noise_threshold, r_stab=args.r_stab, 
                            action_range=args.action_range, lag_factor=args.lag_factor, 
                            task=args.task, seed_value=seed_value, aa=args.aa, bb=args.bb, 
                            cc=args.cc, dd=args.dd)
    
    # Step 2: Create a PPOAgent
    agent = PPOAgent(env=env, policy_lr=args.policy_lr, value_lr=args.value_lr, value_ratio=args.value_ratio, gamma=args.gamma, 
                     clip_epsilon=args.clip_epsilon, update_epochs=args.update_epochs, target_altitude=target_altitude,
                     entropy_c=args.entropy_c, hidden_size_p=args.hidden_size_p, hidden_size_v=args.hidden_size_v,
                     task=args.task, seed_value=seed_value,episodes_per_epoch=args.episodes_per_epoch, 
                     trial_no=args.trial_no)
    
    # Step 3: Start training and load the saved policy from "policies_saved/policy_net.pth"
    agent.train(max_episodes=max_episodes, max_steps=max_steps, resume_from=False)

    wandb.finish()
    
if __name__ == "__main__":
    train_(get_args())
