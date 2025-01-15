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
  5. We don't need this interface. The only thing we need to get from here is the Crazyflie address (e.g. ```0xE7E7E7E7E7```). We can close this interface.
     
## Final checks before Implementation

### Connecting with a crazyflie:

  Make sure ```cflib``` has been installed. If not, run the following command:

  ```
  pip3 install cflib
  ```
  
  Follow the steps given in the [Step-by-Step: Connecting, logging and parameters](https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/user-guides/sbs_connect_log_param/) webpage.

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


 
