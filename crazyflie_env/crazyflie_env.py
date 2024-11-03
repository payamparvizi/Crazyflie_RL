import numpy as np
#import cflib.crtp
#from cflib.crazyflie import Crazyflie
#from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
#from cflib.crazyflie.commander import Commander
#from cflib.positioning.motion_commander import MotionCommander
#from cflib.utils import uri_helper
#from cflib.crazyflie.log import LogConfig
#from time import sleep
#import sys
#import random

class CrazyflieHoverEnv:
    def __init__(self, target_altitude, max_steps, alpha=0, noise_threshold=0,
                 r_max=100, k_rew=66, r_stab=5, action_range=0.2, lag_factor=0.1):
        
        self.alpha = alpha
        self.noise_threshold = noise_threshold
        self.r_max = r_max
        self.k_rew = k_rew
        self.r_stab = r_stab
        self.action_range = action_range
        self.lag_factor = lag_factor
        
        self.target_altitude = target_altitude
        self.max_steps = max_steps
        self.steps = 0
        self.initial_altitude = None  # Placeholder for zero-reference altitude at each reset
        self.current_altitude = 0.0  # The calibrated altitude
        self.done = False
        
        self.smoothed_altitude = 0.0
        
        # Initialize the Crazyflie
        # uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E705')
        # cflib.crtp.init_drivers()
        # cf = Crazyflie(rw_cache='./cache')
        # self.scf = SyncCrazyflie(uri, cf=cf)
        # self.scf.open_link()

        # # Commander to control the Crazyflie velocities
        # self.commander = self.scf.cf.commander
        # self.mc = MotionCommander(self.scf)

        # self.log_config = LogConfig(name='Altitude', period_in_ms=100)
        # self.log_config.add_variable('stateEstimate.z', 'float')

        # # Add the logging configuration to the Crazyflie
        # self.scf.cf.log.add_config(self.log_config)
        # self.log_config.data_received_cb.add_callback(self._log_data_callback)
        # self.log_config.start()
        
        # # Set up another logging configuration for stabilizer (roll, pitch, yaw)
        # self.log_config_stabilizer = LogConfig(name='Stabilizer', period_in_ms=100)
        # self.log_config_stabilizer.add_variable('stabilizer.roll', 'float')
        # self.log_config_stabilizer.add_variable('stabilizer.pitch', 'float')
        # self.log_config_stabilizer.add_variable('stabilizer.yaw', 'float')
        
        # # Add the logging configuration for stabilizer
        # self.scf.cf.log.add_config(self.log_config_stabilizer)
        # self.log_config_stabilizer.data_received_cb.add_callback(self._log_data_callback)
        # self.log_config_stabilizer.start()
    
    # def _log_data_callback(self, timestamp, data, logconf):
    #     """Callback to update the current altitude."""
    #     if 'stateEstimate.z' in data:
    #         current_altitude = data['stateEstimate.z']

    #         # Calibrate initial altitude (set zero reference) at reset
    #         if self.initial_altitude is None:
    #             self.initial_altitude = current_altitude  # Set the zero reference on reset
    #             # print(f"Calibrated! Initial altitude set to {self.initial_altitude} (zero reference).")
    #         # Adjust the altitude based on the initial zero reference
    #         self.current_altitude = current_altitude - self.initial_altitude
    #         # self.current_altitude = self.get_smoothed_altitude(self.current_altitude)
    #         # self.current_altitude = round(self.current_altitude, 1)

    #     if 'stabilizer.roll' in data:
    #         self.current_roll = data['stabilizer.roll'] 
        
    #     if 'stabilizer.pitch' in data:
    #         self.current_pitch = data['stabilizer.pitch'] 
            
    #     if 'stabilizer.yaw' in data:
    #         self.current_yaw = data['stabilizer.yaw'] 
    
     
    def get_smoothed_altitude(self, current_altitude):
        # Apply Exponential Moving Average (EMA) to smooth the altitude reading
        self.smoothed_altitude = self.alpha * self.smoothed_altitude + (1 - self.alpha) * current_altitude
        return self.smoothed_altitude
            
    def reset(self):
        """Reset the environment and re-calibrate the z-axis."""
        self.steps = 0
        self.initial_altitude = None  # Reset the initial altitude to allow recalibration
        self.done = False
        
        self.r_stab_count = 0

        # self.commander.send_stop_setpoint()
        # sleep(1)
        # altitude_to_go = 1.0
        # self.mc.take_off(height=altitude_to_go)
        # sleep(3)
        # self.mc.land()
        # print("Environment reset: z-axis will be recalibrated.")
        self.avg_altitude = np.random.uniform(-self.noise_threshold, self.noise_threshold) 
        state = np.array([self.avg_altitude, 0])
        return state  # Return zeroed altitude for the first observation


    def step(self, action):

        velocity_z = np.clip(action, -self.action_range, self.action_range)
        # velocity_y = np.clip(action[0][1], -0.05, 0.05)
        # velocity_z = np.clip(action[0][2], -2, 2)
        
        """
        Take an action (apply vertical velocity).
        Action space: [-1, 1], where -1 means downward velocity and 1 means upward velocity.
        """
        self.steps += 1
    
        # Command Crazyflie movement (e.g., apply vertical velocity)
        # self.commander.send_velocity_world_setpoint(0, 0, velocity_z, 0)  # Set only vertical velocity
        # self.mc.start_linear_motion(0, 0, velocity_z, 0)  # Command zero velocity
        change_x = velocity_z * self.lag_factor
        
        self.avg_altitude += change_x
        self.avg_altitude = self.avg_altitude.item()
        
        if self.avg_altitude < -self.noise_threshold:
            self.avg_altitude = -self.noise_threshold
            
        self.avg_altitude = self.avg_altitude + np.random.uniform(-self.noise_threshold, self.noise_threshold)
        
        self.avg_altitude_ = self.get_smoothed_altitude(self.avg_altitude)
        # self.avg_altitude_ = np.mean([self.avg_altitude_, self.avg_altitude])
        
        # Calculate reward based on how close the altitude is to the target
        # distance_to_target = abs(self.current_altitude - self.target_altitude)
        # distance_to_target = abs(self.avg_altitude_ - self.target_altitude)
        # reward = (self.target_altitude - distance_to_target) * 100
        # if reward <= 0:
        #     reward = 0

        # if (self.avg_altitude) > 2:
        #     reward = 0

        ## new reward
        if self.avg_altitude_ < self.target_altitude + self.noise_threshold and self.avg_altitude_ > self.target_altitude - self.noise_threshold:
            self.r_stab_count  += 1
        else:
            self.r_stab_count = 0
            
        altitude_error = abs(1.0 - self.avg_altitude_)
        
        if altitude_error <= self.noise_threshold:
            reward = self.r_max + self.r_stab*self.r_stab_count
        else:
            reward = self.r_max - self.k_rew * altitude_error


        # roll_range = self.current_roll > -90 and self.current_roll < 90
        # pitch_range = self.current_pitch > -60 and self.current_pitch < 60
        altitude_range = self.avg_altitude < (self.target_altitude+1.5) #and self.current_altitude  > 0 

        # if not roll_range or not pitch_range or not altitude_range:
        if not altitude_range:
        # if self.current_altitude > 1.0:# or self.current_altitude < 0.01:
            print('the crazyflie crashed')
            self.done = True
            # self.commander.send_stop_setpoint()
        
        
        if self.steps >= self.max_steps:  # Check if Crazyflie is too low (possible crash)
            self.done = True
            # self.commander.send_velocity_world_setpoint(0, 0, -0.2, 0)
            # sleep(2)
            # self.commander.send_stop_setpoint()
        
        next_state = np.array([self.avg_altitude, velocity_z.item()])
        
        return next_state, reward, self.done, {self.steps}

    def close(self):
        """Safely close the Crazyflie connection."""
        self.commander.send_stop_setpoint()
        self.scf.close_link()

    def render(self):
        """Render the environment (print altitude for now)."""
        print(f"Current Altitude: {self.current_altitude}")
