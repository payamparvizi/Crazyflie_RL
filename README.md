# Reinforcement Learning with Crazyflie 2.1

## Overview 

This project implements the Proximal Policy Optimization (PPO) algorithm for the Crazyflie 2.1 drone. It includes both a simulated environment and a real-world setup to train the PPO algorithm for controlling the Crazyflie 2.1 to hover at a specific altitude. Below is an image of the Crazyflie 2.1:

<p align="center">
  <img src="https://github.com/user-attachments/assets/e15c1612-ea9d-4a60-ac8f-029d1f8b9d1a" align="center" width="300">
</p>

## Requirements:

- Linux Opearating System
- Crazyflie 2.1
- Crazyflie Radio
- Flow deck v2
- Batteries

## Installation Instructions

This project uses a Linux operating system with Python 3.9.20. Follow the steps below to set up the environment:

### 1. Create and activate the environment:

Open your terminal and run the following commands:

Upgrade ```pip``` and install the necessary modules using:

  ```bash
  conda create --name crazyflie_env python=3.9.20
  conda activate crazyflie_env

  ```

### 2. Install Related Modules:

  ```
  pip3 install --upgrade pip
  pip3 install cfclient
  ```

### 3. Verify the Installation:

  To ensure the installation was successful, run the following command in the terminal:
  
  ```
  cfclient
  ```

  If the installation is successful, you should see the following interface:
  
  <p align="center">
    <img src="https://github.com/user-attachments/assets/9d2658ad-227c-4f8a-993d-25e5ca59db67" align="center" width="500">
  </p>

  Note: If the command does not work, repeat the steps above until the issue is resolved or troubleshoot the issue.

  ### 4. Download the Crazyflie Firmware:

   Verify that ```git``` is installed by running:

  ```
  git --version
  ```

  If ```git``` is not installed, use the following commands to install it:

  ```
  sudo apt update
  sudo apt install git
  ```

  Next, create a folder where you want to download the firmware. Use the following commands to set up the directory and download the required files:
  I created the folder in my Documents

  ```
  cd /home/payam/Documents
  mkdir crazyflie_doc
  cd crazyflie_doc
  ```

  Follow the steps outlined in this [installation guide](https://github.com/bitcraze/crazyflie-firmware/blob/master/docs/building-and-flashing/build.md). Let's proceed together!

  #### Install the Dependencies:
  
  ```
  sudo apt-get install make gcc-arm-none-eabi
  ```

  #### Tkinter Installation:

Verify that ```tkinter``` is installed by running:

  ```
  python3 -m tkinter
  ```

  If ```tkinter``` is not installed, use the following commands to install it:

  ```
  sudo apt install python3-tk
  ```

  If the installation is successful, you should see the following interface:

  <p align="center">
    <img src="https://github.com/user-attachments/assets/e590f081-c63b-4665-8b51-2dfb0ffb7a84" align="center" width="250">
  </p>

  Press "QUIT".

  #### Clone the Firmware Repository:

  Download the Crazyflie firmware by running the following command:

  ```
  git clone --recursive https://github.com/bitcraze/crazyflie-firmware.git
  ```

  Verify that the firmware has been downloaded by checking the created folder (crazyflie_doc).

  #### Initialize and Update Submodules:

  Run the following commands to initialize and update the submodules:

  ```
  cd crazyflie-firmware
  git submodule init
  git submodule update
  ```

  Make sure no errors encountered

  #### Compile the Firmware:

  Compile the firmware using:

  ```
  make cf2_defconfig
  make -j$(nproc)
  ```

  If no errors occur, the setup is complete.
  
  ## Connecting the Crazyflie and Radio

  1. Connect the Crazyflie radio to your laptop or PC.
  2. Turn on the Crazyflie drone
  3. Verify communication between the drone and the radio:
     - Run the following command in the terminal:
     
      ```
      cfclient
      ```
  4. In the cfclient interface, press ```scan```. The interface should detect the radio and drone.
     - If the drone isn’t detected, enter the address manually by writing ```0xE7E7E7E7E7```. I changed mine, so the modified address is ```0xE7E7E7E704```.
     - press ```connect```.
     - If you move the drone, you will start to see changes in the ```Fligh Data``` part.
  5. We don't need this interface. The only thing we need to get from here is the Crazyflie radio and address information (e.g. ```'radio://0/80/2M/E7E7E7E7E7'```). We can close this interface.
     
## Final checks before Implementation

### Connecting with a crazyflie:

  Make sure ```cflib``` has been installed. If not, run the following command:

  ```
  pip3 install cflib
  ```
  
  Follow the steps given in the [Step-by-Step: Connecting, logging and parameters](https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/user-guides/sbs_connect_log_param/) webpage to check if the Crazyflie is connected or not. Let's proceed together!

  ```
  import logging
  import time
  
  import cflib.crtp
  from cflib.crazyflie import Crazyflie
  from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
  
  # URI to the Crazyflie to connect to
  uri = 'radio://0/80/2M/E7E7E7E7E7'
  
  def simple_connect():
  
      print("Yeah, I'm connected! :D")
      time.sleep(3)
      print("Now I will disconnect :'(")
  
  if __name__ == '__main__':
      # Initialize the low-level drivers
      cflib.crtp.init_drivers()
  
      with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
  
          simple_connect()
  ```

  If any error encountered, it is most probably from URI. Go back to ```cfclient``` interface and check the ```radio``` and ```address``` information and fix the code accordingly. For example, my URI is: ```uri = 'radio://0/100/2M/E7E7E7E704'```.

  If the code works properly, you will see commands below:
  
  ```
  Yeah, I'm connected! :D
  Now I will disconnect :'(
  ```

  ### Connecting with a Flow Deck:

  Flow Deck is a sensor that provides the detailed information about the position of the drone. We need to make sure it is connected. 
  Run the following code:

  ```
  import logging
  import sys
  import time
  from threading import Event
  
  import cflib.crtp
  from cflib.crazyflie import Crazyflie
  from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
  from cflib.utils import uri_helper
  
  URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')
  
  deck_attached_event = Event()
  
  logging.basicConfig(level=logging.ERROR)
  
  def param_deck_flow(_, value_str):
      value = int(value_str)
      print(value)
      if value:
          deck_attached_event.set()
          print('Deck is attached!')
      else:
          print('Deck is NOT attached!')
  
  
  if __name__ == '__main__':
      cflib.crtp.init_drivers()
  
      with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
  
          scf.cf.param.add_update_callback(group='deck', name='bcFlow2',
                                           cb=param_deck_flow)
          time.sleep(1)
  
  
  ```

If the FLow Deck connected properly, you will see commands below:

  ```
  Deck is attached!
  ```

More detailed infomration is provided in [Step-by-Step: Motion Commander](https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/user-guides/sbs_motion_commander/).

### Simple Motion Test:

Before assigning specific tasks, test basic motions such as take-off, forward movement, backward movement, and landing. Place the drone in a safe, open area to prevent any accidents.

Run the following code:

  ```
import logging
import sys
import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

DEFAULT_HEIGHT = 0.5

deck_attached_event = Event()
logging.basicConfig(level=logging.ERROR)


def move_linear_simple(scf):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        time.sleep(1)
        mc.forward(0.5)
        time.sleep(1)
        mc.back(0.5)
        time.sleep(1)
        mc.land()

def param_deck_flow(_, value_str):
    value = int(value_str)
    print(value)
    if value:
        deck_attached_event.set()
        print('Deck is attached!')
    else:
        print('Deck is NOT attached!')

if __name__ == '__main__':
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:

        scf.cf.param.add_update_callback(group='deck', name='bcFlow2',
                                         cb=param_deck_flow)
        time.sleep(1)

        if not deck_attached_event.wait(timeout=5):
            print('No flow deck detected!')
            sys.exit(1)

        move_linear_simple(scf)
  ```

The other commands for the motion of the Crazyflie can be found in [motion_commander](https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/api/cflib/positioning/motion_commander/) and [commander](https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/api/cflib/crazyflie/commander/) webpages.

### Logging while Flying:

To check the information of the position and oriantation of the Crazyflie, we need to have log to export and analyze it.

Run the following code, we can get the x, y and z position of the Crazyflie in real-time:

```
import logging
import sys
import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper


URI = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E707')

DEFAULT_HEIGHT = 0.5

deck_attached_event = Event()

logging.basicConfig(level=logging.ERROR)

position_estimate = [0, 0, 0]

def move_linear_simple(scf):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        time.sleep(1)
        mc.land()


def log_pos_callback(timestamp, data, logconf):
    print(data)
    global position_estimate
    position_estimate[0] = data['stateEstimate.x']
    position_estimate[1] = data['stateEstimate.y']
    position_estimate[2] = data['stateEstimate.z']

            
def param_deck_flow(_, value_str):
  value = int(value_str)
  print(value)
  if value:
      deck_attached_event.set()
      print('Deck is attached!')
  else:
      print('Deck is NOT attached!')

if __name__ == '__main__':
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:

        scf.cf.param.add_update_callback(group='deck', name='bcFlow2',
                                         cb=param_deck_flow)
        time.sleep(1)

        logconf = LogConfig(name='Position', period_in_ms=10)
        logconf.add_variable('stateEstimate.x', 'float')
        logconf.add_variable('stateEstimate.y', 'float')
        logconf.add_variable('stateEstimate.z', 'float')
        scf.cf.log.add_config(logconf)
        logconf.data_received_cb.add_callback(log_pos_callback)

        if not deck_attached_event.wait(timeout=5):
            print('No flow deck detected!')
            sys.exit(1)

        logconf.start()

        move_linear_simple(scf)
        logconf.stop()
  ```

Also, if interested in Roll, Pitch and Yaw orienations of the Crazyflie, replace the position information with orientation, or use both.

```
logconf = LogConfig(name='Stabilizer', period_in_ms=10)
logconf.add_variable('stabilizer.roll', 'float')
logconf.add_variable('stabilizer.pitch', 'float')
logconf.add_variable('stabilizer.yaw', 'float')
scf.cf.log.add_config(logconf)
logconf.data_received_cb.add_callback(log_pos_callback)
```

## Running the RL Environment

This work utilizes the Proximal Policy Optimization (PPO) algorithm in both simulated and real-world Crazyflie environments to achieve stable hovering at a specified altitude.  

### Choosing the Environment

To train the PPO algorithm in the simulated Crazyflie environment, use the following command:

```
python train.py --task simulation
```


To train the PPO algorithm in the real-world Crazyflie environment, use this command:

```
python train.py --task real
```

### Setting the Target Altitude

To specify the desired altitude, use the following command:

```
python train.py --target_altitude 1.0
```

In the example above, the target altitude is set to 1 meter.

### Defining the Action Range

For safety, it is recommended to specify the maximum allowable velocity (±) for the Crazyflie's actions. Use the following command to define the range:

```
python train.py --action_range 0.20
```
In this example, the maximum velocity is set to 0.20 meters per second.

### Example of a Combined Command

A command that incorporates these parameters might look like this:

```
python train.py --task real --target_altitude 1.0 --action_range 0.20
```
### Modifying Additional Parameters

Other parameters can also be adjusted in a similar manner using command line arguments. Alternatively, they can be manually edited in the [arguments.py](./utils/arguments.py) file.


## How it works

### [train.py](train.py)

The [train.py](train.py) file is the main executable responsible for parsing the arguments defined in [arguments.py](./utils/arguments.py). It also initializes both the environment and RL algorithm using the parameters specified in the file.

### [arguments.py](./utils/arguments.py)

The [arguments.py](./utils/arguments.py) file defines a set of arguments intended to be parsed from the command line. These arguments are utilized by the [train.py](train.py) file to configure the RL algorithm and the Crazyflie environment. Detailed instructions for using the command line can be found in the ```Running the RL Environment``` section.

### [networks.py](./ppo/networks.py)

network.py contains neural networks used to define policy and value function networks in PPO algorithm. The parameters of the neural networks can be modified from [arguments.py](./utils/arguments.py) file. 

The [networks.py](./ppo/networks.py) file contains the neural network architectures for the policy and value function used in the PPO algorithm. Parameters for these neural networks can be adjusted either in the [arguments.py](./utils/arguments.py) file or directly via the command line.

### [ppo_agent.py](./ppo/ppo_agent.py)

The [ppo_agent.py](./ppo/ppo_agent.py) file implements the PPO algorithm and manages the training process.
