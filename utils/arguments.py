import argparse
import torch


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=36)
    parser.add_argument("--max_steps", type=int, default=100)
    parser.add_argument("--max_episodes", type=int, default=500)
    parser.add_argument("--target_altitude", type=float, default=1.0)
    parser.add_argument("--policy_lr", type=float, default=1e-4)
    parser.add_argument("--value_lr", type=float, default=5e-2)
    parser.add_argument("--gamma", type=float, default=0.90)
    parser.add_argument("--clip_epsilon", type=float, default=0.10)
    parser.add_argument("--update_epochs", type=int, default=15)
    parser.add_argument("--entropy_c", type=float, default=0.02)
    parser.add_argument("--hidden_size_p", type=int, default=64)
    parser.add_argument("--hidden_size_v", type=int, default=64)
    parser.add_argument("--alpha", type=float, default=0.0)
    parser.add_argument("--noise_threshold", type=float, default=0.02)
    parser.add_argument("--r_max", type=int, default=100)
    parser.add_argument("--k_rew", type=int, default=66)
    parser.add_argument("--r_stab", type=int, default=5)
    parser.add_argument("--action_range", type=float, default=0.2)
    parser.add_argument("--lag_factor", type=float, default=0.1)
    
    parser.add_argument("--ar_case", type=int, default=0)     # 0:vanilla, 1:A2PS
    parser.add_argument("--noise_a2ps", type=float, default=1e-7)
    parser.add_argument("--c_homog", type=float, default=1)
    parser.add_argument("--lambda_P", type=float, default=5)
    
    return parser.parse_args()
