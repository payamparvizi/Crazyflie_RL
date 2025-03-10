import argparse
import torch


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default='simulation')   # 'simulation' or 'real'
    parser.add_argument("--seed", type=int, default=10) 
    parser.add_argument("--trial_no", type=int, default=1)
    
    parser.add_argument("--max_steps", type=int, default=100)
    parser.add_argument("--max_episodes", type=int, default=10001)
    
    parser.add_argument("--target_altitude", type=float, default=1.0)
    
    parser.add_argument("--policy_lr", type=float, default=5e-4)
    parser.add_argument("--value_lr", type=float, default=1e-3)
    parser.add_argument("--value_ratio", type=float, default=0.1)
    parser.add_argument("--gamma", type=float, default=1.0)
    parser.add_argument("--clip_epsilon", type=float, default=0.2)
    parser.add_argument("--update_epochs", type=int, default=10)
    parser.add_argument("--entropy_c", type=float, default=0)
    parser.add_argument("--hidden_size_p", type=int, default=64)
    parser.add_argument("--hidden_size_v", type=int, default=64)
    parser.add_argument("--alpha", type=float, default=0.0)
    parser.add_argument("--noise_threshold", type=float, default=0.01)
    parser.add_argument("--episodes_per_epoch", type=int, default=10)
    
    parser.add_argument("--r_stab", type=int, default=5)
    parser.add_argument("--aa", type=float, default=0)
    parser.add_argument("--bb", type=float, default=0) 
    parser.add_argument("--cc", type=float, default=0) 
    parser.add_argument("--dd", type=float, default=0)
    
    parser.add_argument("--action_range", type=float, default=0.2)
    parser.add_argument("--lag_factor", type=float, default=0.1)
    
    return parser.parse_args()
