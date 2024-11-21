import numpy as np
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.commander import Commander
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
from cflib.crazyflie.log import LogConfig
from time import sleep
from cflib.utils.power_switch import PowerSwitch
# import sys

class CrazyflieHoverEnv:
    def __init__(self, target_altitude, max_steps, alpha=0, noise_threshold=0,
                 r_max=100, k_rew=66, r_stab=5, action_range=0.2, lag_factor=0.1,
                 task='simulation', seed_value=10, aa=0.9, bb=0.9, cc=0.9, dd=0.9):
        
        np.random.seed(seed_value) 
        
        self.alpha = alpha
        self.noise_threshold = noise_threshold
        self.r_max = r_max
        self.k_rew = k_rew
        self.r_stab = r_stab
        self.action_range = action_range
        self.lag_factor = lag_factor
        self.task = task
        
        self._a = aa
        self._b = bb
        self._c = cc
        self._d = dd
        
        self.target_altitude = target_altitude
        self.max_steps = max_steps
        self.steps = 0
        self.initial_altitude = None  # Placeholder for zero-reference altitude at each reset
        self.current_altitude = 0.0  # The calibrated altitude
        self.done = False
        
        
        if self.task == 'real':
            
            # Initialize the Crazyflie
            uri = uri_helper.uri_from_env(default='radio://0/100/2M/E7E7E7E704')
            
            self.uri = uri
            cflib.crtp.init_drivers()
            cf = Crazyflie(rw_cache='./cache')
            self.scf = SyncCrazyflie(uri, cf=cf)
            self.scf.open_link()
    
            # Commander to control the Crazyflie velocities
            self.commander = self.scf.cf.commander
            self.mc = MotionCommander(self.scf)
    

            # Set up another logging configuration for stabilizer (roll, pitch, yaw)
            self.log_config_stabilizer = LogConfig(name='Stabilizer', period_in_ms=100)
            self.log_config_stabilizer.add_variable('stabilizer.roll', 'float')
            self.log_config_stabilizer.add_variable('stabilizer.pitch', 'float')
            self.log_config_stabilizer.add_variable('stabilizer.yaw', 'float')
            
            # Add the logging configuration for stabilizer
            self.scf.cf.log.add_config(self.log_config_stabilizer)
            self.log_config_stabilizer.data_received_cb.add_callback(self._log_data_callback)
            self.log_config_stabilizer.start()
            
            self.log_config = LogConfig(name='StateEstimate', period_in_ms=100)
            self.log_config.add_variable('stateEstimate.z', 'float')
            # self.log_config.add_variable('stateEstimateZ.y', 'float')
            # self.log_config.add_variable('stateEstimateZ.x', 'float')
    
            # Add the logging configuration to the Crazyflie
            self.scf.cf.log.add_config(self.log_config)
            self.log_config.data_received_cb.add_callback(self._log_data_callback)
            self.log_config.start()
        
        
    def _log_data_callback(self, timestamp, data, logconf):
        """Callback to update the current altitude."""
        if 'stateEstimate.z' in data:
            self.current_altitude = data['stateEstimate.z']
        
        # if 'stateEstimate.x' in data:
        #     self.current_x = data['stateEstimate.x']
            
        # if 'stateEstimate.y' in data:
        #     self.current_y = data['stateEstimate.y']

            # Calibrate initial altitude (set zero reference) at reset
            # if self.initial_altitude is None:
            #     self.initial_altitude = current_altitude  # Set the zero reference on reset

            # Adjust the altitude based on the initial zero reference
            # self.current_altitude = current_altitude - self.initial_altitude

        if 'stabilizer.roll' in data:
            self.current_roll = data['stabilizer.roll'] 
        
        if 'stabilizer.pitch' in data:
            self.current_pitch = data['stabilizer.pitch'] 
            
        if 'stabilizer.yaw' in data:
            self.current_yaw = data['stabilizer.yaw'] 
    
            
    def reset(self):
        """Reset the environment and re-calibrate the z-axis."""
        self.steps = 0
        self.initial_altitude = None  # Reset the initial altitude to allow recalibration
        self.done = False
        self.r_stab_count = 0
        
        # if len(sys.argv) != 2:
        #     print("Error: uri is missing")
        #     print('Usage: {} uri'.format(sys.argv[0]))
        #     sys.exit(-1)
        
        if self.task == 'real':
            # PowerSwitch(self.uri).stm_power_cycle()
            sleep(5)
            # self.mc = MotionCommander(self.scf)
            # sleep(1)
            # self.commander.send_stop_setpoint()
            # sleep(1)
            self.mc.take_off(0.1, 0.2)
            sleep(1)
            # self.mc.move_distance(1, 0, 0, 0.5)
            # sleep(5)
            # self.mc.move_distance(-1, 0, 0, 0.5)
            # sleep(5)
            # self.mc.move_distance(0, 1, 0, 0.5)
            # sleep(5)
            # self.mc.move_distance(0, -1, 0, 0.5)
            # sleep(5)
            # self.mc.land()
            # sleep(10)
            
        
        elif self.task == 'simulation':
            self.current_altitude = np.random.uniform(-self.noise_threshold, self.noise_threshold) + 0.1
        
        state = np.array([self.current_altitude, 0])
        
        return state 


    def step(self, action):
        
        velocity_z = np.clip(action, -0.2, 0.2)
        # velocity_z = 0.2
        vz = velocity_z.item()
        
        # vz = 0.2
        # vz = 0.2

        # if self.current_altitude > 0.98 and self.current_altitude < 1.02:
        #     vz = 0
        # elif self.current_altitude < 0.98:
        #     vz = 0.2
        # elif self.current_altitude > 1.02:
        #     vz = -0.2
        
        if self.task == 'simulation':
            change_x = vz * self.lag_factor
            self.current_altitude += change_x
            
            if self.current_altitude < -self.noise_threshold:
                self.current_altitude = -self.noise_threshold
            
            self.current_altitude = self.current_altitude + np.random.uniform(-self.noise_threshold, self.noise_threshold)
            
            
        elif self.task == 'real':
            # self.commander.send_velocity_world_setpoint(0, 0, vz, 0)
            self.mc.start_linear_motion(0, 0, vz, rate_yaw=0.0)
            # print(self.current_altitude)
            sleep(self.lag_factor)
            
        
        reward = self.compute_reward(vz, self.current_altitude)

        # collision constraints:
            
        if self.task == 'simulation':
            altitude_range = self.current_altitude < (self.target_altitude+1.5) 

            if not altitude_range:
                print('the crazyflie crashed')
                self.done = True
                
        elif self.task == 'real':
            roll_range = self.current_roll > -90 and self.current_roll < 90
            pitch_range = self.current_pitch > -60 and self.current_pitch < 60
            altitude_range = self.current_altitude < (self.target_altitude+1.5)
            
            if not roll_range or not pitch_range:
                print('the crazyflie crashed')
                self.done = True
                self.commander.send_stop_setpoint()
            
            if not altitude_range:
                print('the crazyflie passed the box')
                self.done = True
                # self.commander.send_velocity_world_setpoint(0, 0, -0.5, 0)
                self.mc.land(0.5)
                sleep(3)
                # self.commander.send_stop_setpoint()
                # sleep(1)
                
        self.steps += 1
        
        if self.steps >= self.max_steps:  # Check if Crazyflie is too low (possible crash)
            self.done = True
            
            if self.task == 'real':
                print('end of the episode')
                # self.commander.send_velocity_world_setpoint(0, 0, -0.5, 0)
                self.mc.land(0.5)
                sleep(3)
                # self.commander.send_stop_setpoint()
                # sleep(1)
        
        next_state = np.array([self.current_altitude, vz])
        
        return next_state, reward, self.done, {self.steps}


    def compute_reward(self, vz, z):
        
        altitude_error = z - self.target_altitude
        
        # Altitude penalty (closer to target is better)
        reward_altitude = -abs(altitude_error)
        
        # Velocity direction alignment reward
        if altitude_error > 0 and vz < 0:  # Too high, moving downward
            velocity_direction_alignment = 1
        elif altitude_error < 0 and vz > 0:  # Too low, moving upward
            velocity_direction_alignment = 1
        else:  # Moving in the wrong direction
            velocity_direction_alignment = -1
        
        reward_direction = 1.0 * velocity_direction_alignment
        
        if abs(altitude_error) < 0.02:
            reward_bonus = 1
            self.r_stab_count += 1
        else:
            reward_bonus = 0
            self.r_stab_count = 0
        
        # Total reward
        a = self._a
        b = self._b
        c = self._c
        d = self._d
        
        total_reward =  (a)   *   reward_altitude + \
                        (b)   *   reward_direction + \
                        (c)   *   reward_bonus + \
                        (d)   *   self.r_stab_count*self.r_stab

        return total_reward
        # return reward
        
    def close(self):
        """Safely close the Crazyflie connection."""
        self.commander.send_stop_setpoint()
        self.scf.close_link()

    def render(self):
        """Render the environment (print altitude for now)."""
        print(f"Current Altitude: {self.current_altitude}")
