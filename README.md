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
  4. In the cfclient interface, press ```scan```. You will start to see the radio and the drone.
     - If couldn't find the drone. In the address section write: ```0xE7E7E7E7E7```. I changed mine so it is: ```0xE7E7E7E704```.
  5. fg
     



 
