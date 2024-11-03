import numpy as np
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.commander import Commander
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
from cflib.crazyflie.log import LogConfig
from time import sleep

class CrazyflieHoverEnv:
    def __init__(self, target_altitude, max_steps, alpha=0, noise_threshold=0,
                 r_max=100, k_rew=66, r_stab=5, action_range=0.2, lag_factor=0.1,
                 task='simulation', seed_value=10):
        
        np.random.seed(seed_value) 
        
        self.alpha = alpha
        self.noise_threshold = noise_threshold
        self.r_max = r_max
        self.k_rew = k_rew
        self.r_stab = r_stab
        self.action_range = action_range
        self.lag_factor = lag_factor
        self.task = task
        
        self.target_altitude = target_altitude
        self.max_steps = max_steps
        self.steps = 0
        self.initial_altitude = None  # Placeholder for zero-reference altitude at each reset
        self.current_altitude = 0.0  # The calibrated altitude
        self.done = False
        
        if self.task == 'real':
            
            # Initialize the Crazyflie
            uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E705')
            cflib.crtp.init_drivers()
            cf = Crazyflie(rw_cache='./cache')
            self.scf = SyncCrazyflie(uri, cf=cf)
            self.scf.open_link()
    
            # Commander to control the Crazyflie velocities
            self.commander = self.scf.cf.commander
            self.mc = MotionCommander(self.scf)
    
            self.log_config = LogConfig(name='Altitude', period_in_ms=100)
            self.log_config.add_variable('stateEstimate.z', 'float')
    
            # Add the logging configuration to the Crazyflie
            self.scf.cf.log.add_config(self.log_config)
            self.log_config.data_received_cb.add_callback(self._log_data_callback)
            self.log_config.start()
            
            # Set up another logging configuration for stabilizer (roll, pitch, yaw)
            self.log_config_stabilizer = LogConfig(name='Stabilizer', period_in_ms=100)
            self.log_config_stabilizer.add_variable('stabilizer.roll', 'float')
            self.log_config_stabilizer.add_variable('stabilizer.pitch', 'float')
            self.log_config_stabilizer.add_variable('stabilizer.yaw', 'float')
            
            # Add the logging configuration for stabilizer
            self.scf.cf.log.add_config(self.log_config_stabilizer)
            self.log_config_stabilizer.data_received_cb.add_callback(self._log_data_callback)
            self.log_config_stabilizer.start()
        
        
    def _log_data_callback(self, timestamp, data, logconf):
        """Callback to update the current altitude."""
        if 'stateEstimate.z' in data:
            current_altitude = data['stateEstimate.z']

            # Calibrate initial altitude (set zero reference) at reset
            if self.initial_altitude is None:
                self.initial_altitude = current_altitude  # Set the zero reference on reset

            # Adjust the altitude based on the initial zero reference
            self.current_altitude = current_altitude - self.initial_altitude

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
        
        if self.task == 'real':
            self.commander.send_stop_setpoint()
            sleep(1)
        
        elif self.task == 'simulation':
            self.current_altitude = np.random.uniform(-self.noise_threshold, self.noise_threshold)
        
        state = np.array([self.current_altitude, 0])
        
        return state 


    def step(self, action):
        
        velocity_z = np.clip(action, -self.action_range, self.action_range)
        
        if self.task == 'simulation':
            change_x = velocity_z * self.lag_factor
            self.current_altitude += change_x.item()
            
            if self.current_altitude < -self.noise_threshold:
                self.current_altitude = -self.noise_threshold
            
            self.current_altitude = self.current_altitude + np.random.uniform(-self.noise_threshold, self.noise_threshold)
            
            
        elif self.task == 'real':
            # self.commander.send_velocity_world_setpoint(0, 0, velocity_z, 0)
            sleep(self.lag_factor)
            
            
        ## reward calculation
        if self.current_altitude < self.target_altitude + self.noise_threshold and self.current_altitude > self.target_altitude - self.noise_threshold:
            self.r_stab_count  += 1
        else:
            self.r_stab_count = 0
            
        altitude_error = abs(1.0 - self.current_altitude)
        
        if altitude_error <= self.noise_threshold:
            reward = self.r_max + self.r_stab*self.r_stab_count
        else:
            reward = self.r_max - self.k_rew * altitude_error


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
            
            if not altitude_range or not roll_range or not pitch_range:
                print('the crazyflie crashed')
                self.done = True
                self.commander.send_stop_setpoint()
                
        
        self.steps += 1
        
        if self.steps >= self.max_steps:  # Check if Crazyflie is too low (possible crash)
            self.done = True
            
            if self.task == 'real':
                self.commander.send_stop_setpoint()
        
        
        next_state = np.array([self.current_altitude, velocity_z.item()])
        
        return next_state, reward, self.done, {self.steps}

    def close(self):
        """Safely close the Crazyflie connection."""
        self.commander.send_stop_setpoint()
        self.scf.close_link()

    def render(self):
        """Render the environment (print altitude for now)."""
        print(f"Current Altitude: {self.current_altitude}")
