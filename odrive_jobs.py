import threading
import queue
import logging
import time
import math
import random
import yaml
import odrive
import numpy
from odrive.enums import *


speed_limit = 10
cfg_speed = 0
config = None
cfg_filename = 'odrive.yaml'

thread_data = {'count' : 0,
                'volts' : 0,
                'current_limit' : 0,
                'speed' : 0
            }


def read_config(config):
    with open (cfg_filename, 'r') as cfgfile:
        config = yaml.load(cfgfile)
    return config

def write_config(config):
    rfile = open(cfg_filename,'w')
    rfile.write(yaml.dump(config))
    rfile.close()

def process_odrive_config(formargs):
    for key, value in formargs.items():
        if 'submit' in key:
            pass
        else: 
            config[key] = value

    write_config(config)



# Calibrate motor and wait for it to finish, set in position mode
def calibrate_axis0():
    print("starting calibration...")
    my_drive.axis0.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
    while my_drive.axis0.current_state != AXIS_STATE_IDLE:
        time.sleep(0.1)

    my_drive.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
    my_drive.axis0.controller.config.control_mode = CTRL_MODE_POSITION_CONTROL

def get_odrive_data():
    thread_data['volts'] = '{:.{prec}f}'.format(my_drive.vbus_voltage, prec=2)
    thread_data['speed'] = '{:.{prec}f}'.format(my_drive.axis0.controller.config.vel_limit, prec=2)
    
    print("BUS Volts:{} CURRENT Limit:{}  SPEED:{}".format(thread_data['volts'],thread_data['current_limit'],thread_data['speed']))
    """
    for i in [1,2,3,4]:
        print('voltage on GPIO{} is {} Volt'.format(i, my_drive.get_adc_voltage(i)))
    """

def read_position():
    return my_drive.axis0.encoder.pos_estimate

def set_current(current_limit):
    my_drive.axis0.motor.config.current_lim = current_limit
    thread_data['current_limit'] = current_limit
    print('Current Set to: {}'.format(current_limit))

def test_run(to_pos):
    for i in range(0,10):
        print('Cycle: {}'.format(i))
        my_drive.axis0.controller.pos_setpoint = to_pos
        time.sleep(0.01)
        while abs(my_drive.axis0.encoder.vel_estimate) > speed_limit:
            time.sleep(0.01)
        my_drive.axis0.controller.pos_setpoint = 0
        time.sleep(0.01)
        while abs(my_drive.axis0.encoder.vel_estimate) > speed_limit:
            time.sleep(0.01)

def time_run(to_pos):
    for i in range(0,10):
        print('Cycle: {}'.format(i))
        my_drive.axis0.controller.pos_setpoint = to_pos
        time.sleep(0.2)
        my_drive.axis0.controller.pos_setpoint = 0
        time.sleep(0.2)

def speed_run(to_pos, wait=None):
    if wait:
        wait = float(wait)
    else:
        wait = (int(to_pos)/36000) + 0.02  # 0.02 to allow for initial acceleration
        
    print ('Speed Run at: {}'.format(wait))
    for i in range(0,10):
        print('Cycle: {}'.format(i))
        my_drive.axis0.controller.pos_setpoint = to_pos
        time.sleep(wait)
        my_drive.axis0.controller.pos_setpoint = 0
        time.sleep(wait)

def move_to(to_pos):
    my_drive.axis0.controller.pos_setpoint = to_pos

def trajectory_to(to_pos,speed=None):
    print('trajectory_to called pos:{} and speed:{}'.format(to_pos,speed))
    if speed:
        my_drive.axis0.trap_traj.config.vel_limit = speed
    my_drive.axis0.controller.move_to_pos(to_pos)

def cancel_trajectory():
    trajectory_to(my_drive.axis0.encoder.pos_estimate,20000)

#
#   Run on Start-up
#
config = read_config(config)
# Find a connected ODrive (this will block until you connect one)
print("finding an odrive...")
my_drive = odrive.find_any()

calibrate_axis0()
get_odrive_data()
cfg_speed = float(thread_data['speed'])   # save for future use

