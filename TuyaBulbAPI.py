#!/usr/bin/python3

# *************************************************************************
# A Rest API for Tuya Smart Bulbs 
# Allows JSON requests to be sent over a network to control bulb colour,
#   brightness, and more, using FastAPI, uvicorn, and TinyTuya
# See https://github.com/TimboFimbo/TuyaSmartBulbs_API for more information

# *************************************************************************

import json
import tinytuya
from time import sleep
from fastapi import FastAPI
from pydantic import BaseModel
import os, sys, threading

app = FastAPI()

# Start by setting all the bulbs from the included snapshot.json file
# File can be obtained by running 'python3 -m tinytuya scan'
# File will only be generated correctly if 'python3 -m tinytuya wizard'
#   has previously been run successfully, and device keys obtained
# See https://pypi.org/project/tinytuya/#description for more information

CON_TIMEOUT = 2
RETRY_LIMIT = 1

class BulbObject:
    def __init__(self, name_in, dev_id_in, address_in, local_key_in, version_in):
        self.name = name_in
        self.bulb = tinytuya.BulbDevice(
            dev_id = dev_id_in,
            address = address_in,
            local_key = local_key_in,
            connection_timeout = CON_TIMEOUT,
            version = version_in
        )

bulbs : BulbObject = []
current_thread: threading.Thread
running_threads = [

]

# set path of snapshot file here, or place a copy into this folder
snapshot = os.path.join(sys.path[0], 'snapshot.json')
with open(snapshot, 'r') as infile:
    bulb_json = json.load(infile)

for bulb in bulb_json['devices']:
    bulbs.append(BulbObject(
    name_in=bulb['name'],
    dev_id_in=bulb['id'],
    address_in=bulb['ip'],
    local_key_in=bulb['key'],
    version_in=bulb['ver']
))
    
for this_bulb in bulbs:
    this_bulb.bulb.set_socketPersistent(True)
    this_bulb.bulb.set_socketRetryLimit(RETRY_LIMIT)

# Compile all the bulbs into a list with a true or false toggle
# This list will be added to the JSON classes below
# Multi toggles are being added, for setting bulbs to do different things

class BulbToggle(BaseModel):
    name: str = ""
    toggle: bool = True

class MultiRgbToggle(BulbToggle):
    red: int
    green: int
    blue: int

bulb_toggles : BulbToggle = []
multi_rgb_toggles : MultiRgbToggle = []

for this_bulb in bulbs:
    bulb_toggles.append(BulbToggle(
        name=this_bulb.name,
        toggle=True
    ))
    multi_rgb_toggles.append(MultiRgbToggle(
        name=this_bulb.name,
        red = 0,
        green = 0,
        blue = 0
    ))

# TODO add 'no_wait'
class PowerClass(BaseModel):
    global bulb_toggles
    power: bool = True
    toggles: list = bulb_toggles

class RgbClass(BaseModel):
    global bulb_toggles
    red: int
    green: int
    blue: int
    toggles: list = bulb_toggles

class MultiRgbClass(BaseModel):
    global multi_rgb_toggles
    toggles: list = multi_rgb_toggles

class BrightnessClass(BaseModel):
    global bulb_toggles
    brightness: int
    toggles: list = bulb_toggles

# Scenes

def stop_scenes():
    if len(running_threads) > 0: 
        running_threads.clear()
        current_thread.join()
    
def xmas_scene():
    sleep_time = 10
    thread_name = 'xmas_scene'
    running_threads.append(thread_name)
    number_of_bulbs = len(bulbs)
    while thread_name in running_threads:
        for this_bulb in bulbs:
            if this_bulb.name.__contains__("Light"): this_bulb.bulb.set_colour(255, 0, 0)
            else: this_bulb.bulb.set_colour(0, 100, 0)
        sleep(sleep_time)
        for this_bulb in bulbs:
            if this_bulb.name.__contains__("Light"): this_bulb.bulb.set_colour(0, 255, 0)
            else: this_bulb.bulb.set_colour(255, 0, 0)
        sleep(sleep_time)


# API endpoints

# TODO add 'no_wait'
@app.put("/set_power")
def set_bulb_power(power_in: PowerClass):
    stop_scenes()
    for this_bulb in bulbs:
        for this_toggle in power_in.toggles:
            if this_toggle['name'] == this_bulb.name and this_toggle['toggle'] == True:
                if power_in.power == True: this_bulb.bulb.turn_on()
                else: this_bulb.bulb.turn_off()

    return "Power On" if power_in.power == True else "Power Off"

@app.put("/set_colour")
def set_bulb_colour(rgb: RgbClass):
    stop_scenes()
    for this_bulb in bulbs:
        for this_toggle in rgb.toggles:
            if this_toggle['name'] == this_bulb.name and this_toggle['toggle'] == True:
                this_bulb.bulb.set_colour(rgb.red, rgb.green, rgb.blue)

    return "Colour changed to ({}, {}, {})".format(rgb.red, rgb.green, rgb.blue)

@app.put("/set_multi_colour")
def set_multi_colour(multi_rgb: MultiRgbClass):
    stop_scenes()
    for this_bulb in bulbs:
        for this_toggle in multi_rgb.toggles:
            if this_toggle['name'] == this_bulb.name and this_toggle['toggle'] == True:
                this_bulb.bulb.set_colour(this_toggle['red'], this_toggle['green'], this_toggle['blue'])

    return "Multi colours changed"

@app.put("/set_brightness")
def set_bulb_brightness(brightness_in: BrightnessClass):
    stop_scenes()
    for this_bulb in bulbs:
        for this_toggle in brightness_in.toggles:
            if this_toggle['name'] == this_bulb.name and this_toggle['toggle'] == True:
                this_bulb.bulb.set_brightness(brightness_in.brightness)

    return "Brightness changed to {}".format(brightness_in.brightness)

# Scenes - move these to another file

@app.put("/set_xmas_colours")
def set_xmas_colours():
    stop_scenes()
    for this_bulb in bulbs:
        if this_bulb.name == 'White Lamp': this_bulb.bulb.set_colour(0, 200, 0)
        if this_bulb.name == 'Wood Lamp': this_bulb.bulb.set_colour(0, 70, 0)
        if this_bulb.name == 'Black Lamp': this_bulb.bulb.set_colour(0, 50, 0)
        if this_bulb.name == 'Chair Light': this_bulb.bulb.set_colour(255, 0, 0)
        if this_bulb.name == 'Sofa Light': this_bulb.bulb.set_colour(255, 0, 0)
        if this_bulb.name == 'Den Light': this_bulb.bulb.set_colour(100, 0, 0)

    return "Xmas colours set"

@app.put("/start_xmas_scene")
def start_xmas_scene():
    global current_thread
    stop_scenes()
    current_thread = threading.Thread(target=xmas_scene)
    current_thread.start()

    return "Xmas Scene Started"

@app.put("/list_threads")
def list_current_threads():
    threads = []
    for thread in threading.enumerate(): 
        threads.append(thread.name)
    
    return threads + running_threads