#!/usr/bin/python3

# *************************************************************************
# A Rest API for Tuya Smart Bulbs 
# Allows JSON requests to be sent over a network to control bulb colour,
#   brightness, and more, using FastAPI, uvicorn, and TinyTuya
# See https://github.com/TimboFimbo/TuyaSmartBulbs_API for more information

# *************************************************************************

import json
import tinytuya
from time import sleep, time, ctime, strftime
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import os, sys, threading
import asyncio
from random import random, choice, randrange
import Colours

app = FastAPI()

# Start by setting all the bulbs from the included snapshot.json file
# File can be obtained by running 'python3 -m tinytuya scan'
# File will only be generated correctly if 'python3 -m tinytuya wizard'
#   has previously been run successfully, and device keys obtained
# See https://pypi.org/project/tinytuya/#description for more information

CON_TIMEOUT = 10
RETRY_LIMIT = 1

# Let's get the bulb names right, as they are sometimes used
WHITE_LAMP = "White Lamp"
WOOD_LAMP = "Wood Lamp"
BLACK_LAMP = "Black Lamp"
DEN_LIGHT = "Den Light"
CHAIR_LIGHT = "Chair Light"
SOFA_LIGHT = "Sofa Light"

bulbs: BulbObject = []
running_scenes = []


def set_bulb_retry_limit(limit):
    for this_bulb in bulbs:
        this_bulb.bulb.set_socketRetryLimit(limit)


set_bulb_retry_limit(RETRY_LIMIT)

# Compile all the bulbs into a list with a true or false toggle
# This list will be added to the JSON classes below
# Multi toggles are being added, for setting bulbs to do different things


# set up defaults

for this_bulb in bulbs:
    multi_rgb_toggles.append(MultiRgbToggle(
        name=this_bulb.name,
        red=0,
        green=0,
        blue=0
    ))
    if this_bulb.name == "Black Lamp":
        multi_scene_toggles[0].append(BulbToggle(
            name=this_bulb.name,
            bright_mul=0.5,
            toggle=True
        ))
        bulb_toggles.append(BulbToggle(
            name=this_bulb.name,
            bright_mul=0.5,
            toggle=True
        ))
    elif "Light" in this_bulb.name:
        multi_scene_toggles[0].append(BulbToggle(
            name=this_bulb.name,
            bright_mul=2.0,
            toggle=True
        ))
        bulb_toggles.append(BulbToggle(
            name=this_bulb.name,
            bright_mul=2.0,
            toggle=True
        ))
    else:
        multi_scene_toggles[1].append(BulbToggle(
            name=this_bulb.name,
            bright_mul=1.0,
            toggle=True
        ))
        bulb_toggles.append(BulbToggle(
            name=this_bulb.name,
            bright_mul=1.0,
            toggle=True
        ))

# set up lightning toggles

for this_bulb in bulbs:
    if this_bulb.name == DEN_LIGHT:
        lightning_toggles.append(LightningToggle(
            name=this_bulb.name,
        ))
    elif this_bulb.name == WHITE_LAMP:
        lightning_toggles.append(LightningToggle(
            name=this_bulb.name,
        ))
    elif this_bulb.name == WOOD_LAMP:
        lightning_toggles.append(LightningToggle(
            name=this_bulb.name,
        ))
    elif this_bulb.name == BLACK_LAMP:
        lightning_toggles.append(LightningToggle(
            name=this_bulb.name,
        ))

for col in Colours.ALL_COLOURS:
    all_colours.append(RgbColour(
        red=col["red"],
        green=col["green"],
        blue=col["blue"]
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


class RandomColourSceneClass(BaseModel):
    global bulb_toggles
    wait_time: int = 600
    toggles: list = bulb_toggles
    colour_list: list = all_colours


class LightningSceneClass(BaseModel):
    global lightning_toggles
    lightning_colour: RgbColour = Colours.WHITE
    lightning_percent_chance: int = 20
    lightning_length: float = 0.4
    default_brightness: int = 10
    # low_flash_brightness: int = 50
    # high_flash_brightness: int = 125
    storm_brightness_range: list = [15, 50]
    # lightning_flash_brightness: int = 255
    wait_time_range: list = [0.25, 1]
    toggles: list = lightning_toggles


class XmasSceneClass(BaseModel):
    wait_time: int = 600


# the bulb lists and colours are examples, which starts a scene by default
class MultiColourSceneClass(BaseModel):
    global multi_scene_toggles
    wait_time: int = 600
    bulb_lists: list = multi_scene_toggles
    colour_list: list = [Colours.ORANGE,
                         Colours.ROSE,
                         Colours.AZURE,
                         Colours.CHARTRUESE,
                         Colours.VIOLET]


# Shared functions

# Calulates final colours based on brighness multiplier
# Will only multiply up to the point that the colours start changing
# For example, (128, 64, 0) will top out at *2 multiplier, and
# (10, 5, 0) will bottom out at *0.2 multiplier (this is just an
# example - setting this low will probably result in darkness)

def get_final_colours(red, green, blue, init_mul):
    init_cols = [red, green, blue]
    final_cols = [red, green, blue]

    if init_mul > 1:
        high_num = max(red, green, blue)
        max_mul = round(256 / high_num, 2)
        for i in range(len(final_cols)):
            mul = min(init_mul, max_mul)
            final_cols[i] = int(min(init_cols[i] * mul, 255))

    elif init_mul < 1:
        non_zeros = []
        for val in (red, green, blue):
            if val != 0:
                non_zeros.append(val)
        low_num = min(non_zeros)
        min_mul = round(1 / low_num, 2)
        for i in range(len(final_cols)):
            mul = max(init_mul, min_mul)
            final_cols[i] = int(init_cols[i] * mul)

    return final_cols


def set_colour_async(this_bulb: BulbObject, red, green, blue):
    this_bulb.bulb.set_colour(red, green, blue)
    print(f"{this_bulb.name} started at {strftime('%X')}")


def lightning_flash(this_bulb: BulbObject, bulb_num, lightning_flash_brightness, lightning_length, default_brightness,
                    flash_delay, bulb_delay):
    sleep_time = flash_delay * bulb_num + bulb_delay
    sleep(sleep_time)

    this_bulb.bulb.set_colour(lightning_flash_brightness, lightning_flash_brightness, lightning_flash_brightness)
    print("{} : with delay: {} : flashed at {}".format(this_bulb.name, str(bulb_delay), int(time() * 1000)))
    sleep(lightning_length / (bulb_num + 1))

    if bulb_num == 0:
        this_bulb.bulb.set_colour(default_brightness, default_brightness, default_brightness)
    else:
        this_bulb.bulb.set_colour(1, 1, 1)


def lightning_flash_alt(lightning_bulbs, lightning_colour: RgbColour, lightning_length, default_brightness):
    for i in range(len(lightning_bulbs)):
        lightning_bulbs[i].bulb.set_colour(lightning_colour.red, lightning_colour.green, lightning_colour.blue)
        print("{} : flashed at {}".format(this_bulb.name, int(time() * 1000)))

    sleep(lightning_length / (i + 1))

    for i in range(len(lightning_bulbs)):
        if i == 0:
            lightning_bulbs[i].bulb.set_colour(default_brightness, default_brightness, default_brightness)
        else:
            lightning_bulbs[i].bulb.set_colour(1, 1, 1)

    # for this_bulb in lightning_bulbs:
    #     this_bulb.bulb.set_colour(lightning_flash_brightness, lightning_flash_brightness, lightning_flash_brightness)


# Scenes

def stop_scenes():
    if len(running_scenes) > 0:
        running_scenes.clear()
        sleep(2)  # gives time for scene to end before next command


async def xmas_scene(wait_time: int):
    scene_id = random()
    current_time = time()
    light_red = True
    print("{} : Wait {} : Started at {}".format("xmas_scene", wait_time, ctime(current_time)))
    running_scenes.append(scene_id)
    set_bulb_retry_limit(10)  # ensures bulb reponds if wait time is high

    while scene_id in running_scenes:
        for this_bulb in bulbs:
            if light_red == True:
                if this_bulb.name.__contains__("Light"):
                    this_bulb.bulb.set_colour(255, 0, 0)
                else:
                    this_bulb.bulb.set_colour(0, 100, 0)
            else:
                if this_bulb.name.__contains__("Light"):
                    this_bulb.bulb.set_colour(0, 255, 0)
                else:
                    this_bulb.bulb.set_colour(100, 0, 0)
        print("Light Red = {} at {}".format(light_red, ctime(time())))
        light_red = not light_red
        while time() - current_time < wait_time and scene_id in running_scenes:
            await asyncio.sleep(0.1)
        current_time = time()

    print("{} : Wait {} : Stopped at {}".format("xmas_scene", wait_time, ctime(current_time)))
    set_bulb_retry_limit(1)


async def multi_colour_scene(multi_class: MultiColourSceneClass):
    scene_id = random()
    current_time = time()
    colour_offsets = []
    b_list_length = len(multi_class.bulb_lists)
    c_list_length = len(multi_class.colour_list)
    print("{} : Wait {} : Started at {}"
          .format("multi_colour_scene", multi_class.wait_time, ctime(current_time)))
    running_scenes.append(scene_id)
    set_bulb_retry_limit(10)

    for i in range(b_list_length):
        colour_offsets.append(i)

    if c_list_length < b_list_length:
        for x in range(b_list_length - c_list_length):
            multi_class.colour_list.append(Colours.WHITE)
            c_list_length = len(multi_class.colour_list)

    # yeah, there are C-stye loops here. I have to sync up two lists and just find this way easier
    # there are also a bunch of print lines for debugging, but they can be removed if desired
    while scene_id in running_scenes:
        for i in range(b_list_length):
            for j in multi_class.bulb_lists[i]:
                for this_bulb in bulbs:
                    if this_bulb.name == j['name']:
                        col = multi_class.colour_list[colour_offsets[i]]
                        final_cols = get_final_colours(col['red'], col['green'], col['blue'], j['bright_mul'])
                        this_bulb.bulb.set_colour(final_cols[0], final_cols[1], final_cols[2])
                        print("{} set to ({}, {}, {})".format(this_bulb.name, final_cols[0], final_cols[1],
                                                              final_cols[2]))

        count = 0

        for i in range(len(colour_offsets)):
            # print ("Offset {} start: {}".format(str(i), str(colour_offsets[i])))
            colour_offsets[i] = colour_offsets[i] + 1
            # print ("Offset {} + 1: {}".format(str(i), str(colour_offsets[i])))
            if colour_offsets[i] >= c_list_length:
                colour_offsets[i] = 0
            # print ("Offset {} final: {}".format(str(i), str(colour_offsets[i])))

        # print("Offsets: {}".format(colour_offsets))
        print()

        while time() - current_time < multi_class.wait_time and scene_id in running_scenes:
            await asyncio.sleep(0.1)
        current_time = time()

    print("{} : Wait {} : Stopped at {}"
          .format("multi_colour_scene", multi_class.wait_time, ctime(current_time)))
    set_bulb_retry_limit(1)


async def multi_colour_scene_async(multi_class: MultiColourSceneClass):
    bulb_tasks = []
    scene_id = random()
    current_time = time()
    colour_offsets = []
    b_list_length = len(multi_class.bulb_lists)
    c_list_length = len(multi_class.colour_list)
    print("{} : Wait {} : Started at {}"
          .format("multi_colour_scene", multi_class.wait_time, ctime(current_time)))
    running_scenes.append(scene_id)
    set_bulb_retry_limit(10)

    for i in range(b_list_length):
        colour_offsets.append(i)

    if c_list_length < b_list_length:
        for x in range(b_list_length - c_list_length):
            multi_class.colour_list.append(Colours.WHITE)
            c_list_length = len(multi_class.colour_list)

    # yeah, there are C-stye loops here. I have to sync up two lists and just find this way easier
    # there are also a bunch of print lines for debugging, but they can be removed if desired
    while scene_id in running_scenes:
        for i in range(b_list_length):
            for j in multi_class.bulb_lists[i]:
                for this_bulb in bulbs:
                    if this_bulb.name == j['name']:
                        col = multi_class.colour_list[colour_offsets[i]]
                        final_cols = get_final_colours(col['red'], col['green'], col['blue'], j['bright_mul'])
                        bulb_tasks.append(
                            asyncio.to_thread(set_colour_async, this_bulb, final_cols[0], final_cols[1], final_cols[2]))
                        print("{} set to ({}, {}, {})".format(this_bulb.name, final_cols[0], final_cols[1],
                                                              final_cols[2]))

        await asyncio.gather(*bulb_tasks)
        bulb_tasks.clear()
        count = 0

        for i in range(len(colour_offsets)):
            # print ("Offset {} start: {}".format(str(i), str(colour_offsets[i])))
            colour_offsets[i] = colour_offsets[i] + 1
            # print ("Offset {} + 1: {}".format(str(i), str(colour_offsets[i])))
            if colour_offsets[i] >= c_list_length:
                colour_offsets[i] = 0
            # print ("Offset {} final: {}".format(str(i), str(colour_offsets[i])))

        # print("Offsets: {}".format(colour_offsets))
        print()

        while time() - current_time < multi_class.wait_time and scene_id in running_scenes:
            await asyncio.sleep(0.1)
        current_time = time()

    print("{} : Wait {} : Stopped at {}"
          .format("multi_colour_scene", multi_class.wait_time, ctime(current_time)))
    set_bulb_retry_limit(1)


async def random_colour_scene(random_class: RandomColourSceneClass):
    scene_id = random()
    current_time = time()
    print("{} : Wait {} : Started at {}"
          .format("random_colour_scene", random_class.wait_time, ctime(current_time)))
    running_scenes.append(scene_id)
    set_bulb_retry_limit(10)  # ensures bulb reponds if wait time is high

    while scene_id in running_scenes:
        for this_bulb in bulbs:
            for this_toggle in random_class.toggles:
                if this_toggle['name'] == this_bulb.name:
                    ran_col = choice(random_class.colour_list)
                    final_cols = get_final_colours(ran_col['red'], ran_col['green'], ran_col['blue'],
                                                   this_toggle['bright_mul'])
                    this_bulb.bulb.set_colour(final_cols[0], final_cols[1], final_cols[2])
                    print("{} set to ({}, {}, {})".format(this_bulb.name, final_cols[0], final_cols[1], final_cols[2]))

        print()
        while time() - current_time < random_class.wait_time and scene_id in running_scenes:
            await asyncio.sleep(0.1)
        current_time = time()

    print("{} : Wait {} : Stopped at {}"
          .format("random_colour_scene", random_class.wait_time, ctime(current_time)))
    set_bulb_retry_limit(1)


async def random_colour_scene_async(random_class: RandomColourSceneClass):
    bulb_tasks = []
    scene_id = random()
    current_time = time()
    print("{} : Wait {} : Started at {}"
          .format("random_colour_scene", random_class.wait_time, ctime(current_time)))
    running_scenes.append(scene_id)
    set_bulb_retry_limit(10)  # ensures bulb reponds if wait time is high

    while scene_id in running_scenes:
        for this_bulb in bulbs:
            for this_toggle in random_class.toggles:
                if this_toggle['name'] == this_bulb.name:
                    ran_col = choice(random_class.colour_list)
                    final_cols = get_final_colours(ran_col['red'], ran_col['green'], ran_col['blue'],
                                                   this_toggle['bright_mul'])
                    bulb_tasks.append(
                        asyncio.to_thread(set_colour_async, this_bulb, final_cols[0], final_cols[1], final_cols[2]))
                    print("{} set to ({}, {}, {})".format(this_bulb.name, final_cols[0], final_cols[1], final_cols[2]))

        await asyncio.gather(*bulb_tasks)
        bulb_tasks.clear()
        print()

        while time() - current_time < random_class.wait_time and scene_id in running_scenes:
            await asyncio.sleep(0.1)
        current_time = time()

    print("{} : Wait {} : Stopped at {}"
          .format("random_colour_scene", random_class.wait_time, ctime(current_time)))
    set_bulb_retry_limit(1)


async def lightning_scene_async(lightning_class: LightningSceneClass):
    bulb_tasks = []
    scene_id = random()
    current_time = time()
    wait_divider = 6
    print("{} : Started at {}"
          .format("lightning_scene", ctime(current_time)))
    running_scenes.append(scene_id)
    set_bulb_retry_limit(1)  # ensures bulb reponds if wait time is high

    lightning_bulbs = []
    for this_toggle in lightning_class.toggles:
        for this_bulb in bulbs:
            if this_toggle['name'] == this_bulb.name:
                lightning_bulbs.append(this_bulb)

    while scene_id in running_scenes:
        rand_brightness = randrange(lightning_class.storm_brightness_range[0],
                                    lightning_class.storm_brightness_range[1])

        rand_wait = randrange((lightning_class.wait_time_range[0] * 1000),
                              (lightning_class.wait_time_range[1] * 1000)) / 1000

        rand_strike_number = randrange(0, int((100 / lightning_class.lightning_percent_chance)))
        lightning_happening = (rand_strike_number == 0)

        print("Random brightness: " + str(rand_brightness))
        print(str(rand_strike_number))
        print("Strike happening: " + str(lightning_happening))

        if (lightning_happening):
            await asyncio.to_thread(lightning_flash_alt, lightning_bulbs,
                                    lightning_class.lightning_colour,
                                    lightning_class.lightning_length,
                                    lightning_class.default_brightness)

            while time() - current_time < lightning_class.lightning_length and scene_id in running_scenes:
                await asyncio.sleep(0.1)
            current_time = time()

        else:
            lightning_bulbs[0].bulb.set_colour(rand_brightness, rand_brightness, rand_brightness)
            await asyncio.sleep(rand_wait / wait_divider)
            lightning_bulbs[0].bulb.set_colour(lightning_class.default_brightness,
                                               lightning_class.default_brightness,
                                               lightning_class.default_brightness)

            for i in range(len(lightning_bulbs)):  # just to keep all bulbs responding - update to do this every second
                if i != 0:
                    lightning_bulbs[i].bulb.set_colour(1, 1, 1)

            while time() - current_time < rand_wait and scene_id in running_scenes:
                await asyncio.sleep(0.1)
            current_time = time()

            await asyncio.sleep(rand_wait)

    print("{} : Stopped at {}"
          .format("lightning_scene", ctime(current_time)))
    # set_bulb_retry_limit(1)


# API endpoints

# TODO add 'no_wait'
@app.put("/set_power")
def set_bulb_power(power_in: PowerClass):
    stop_scenes()
    for this_bulb in bulbs:
        for this_toggle in power_in.toggles:
            if this_toggle['name'] == this_bulb.name and this_toggle['toggle'] == True:
                if power_in.power == True:
                    this_bulb.bulb.turn_on()
                else:
                    this_bulb.bulb.turn_off()

    return "Power On" if power_in.power == True else "Power Off"


@app.put("/set_colour")
def set_bulb_colour(rgb: RgbClass):
    stop_scenes()
    for this_bulb in bulbs:
        for this_toggle in rgb.toggles:
            if this_toggle['name'] == this_bulb.name and this_toggle['toggle'] == True:
                final_cols = get_final_colours(rgb.red, rgb.green, rgb.blue, this_toggle['bright_mul'])
                this_bulb.bulb.set_colour(final_cols[0], final_cols[1], final_cols[2])
                print("{} set to ({}, {}, {})".format(this_toggle['name'],
                                                      final_cols[0], final_cols[1], final_cols[2]))

    return "Colour changed to ({}, {}, {})".format(rgb.red, rgb.green, rgb.blue)


@app.put("/set_colour_async")
async def set_bulb_colour_async(rgb: RgbClass):
    bulb_tasks = []
    stop_scenes()
    for this_bulb in bulbs:
        for this_toggle in rgb.toggles:
            if this_toggle['name'] == this_bulb.name and this_toggle['toggle'] == True:
                final_cols = get_final_colours(rgb.red, rgb.green, rgb.blue, this_toggle['bright_mul'])
                bulb_tasks.append(
                    asyncio.to_thread(set_colour_async, this_bulb, final_cols[0], final_cols[1], final_cols[2]))

                print("{} set to ({}, {}, {})".format(this_toggle['name'],
                                                      final_cols[0], final_cols[1], final_cols[2]))

    await asyncio.gather(*bulb_tasks)
    # bulb_tasks.clear()
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


# Scene endpoints

# This one is a little more complex - You pass in multiple lists of bulbs (no repeats bulbs
# between lists), along with a list of colours. The lists of bulbs will cycle though the
# colour list at the wait time provided, with all bulbs in each list staying in sync. Having
# more colours than bulb lists is fine - you just won't see all the colours at once. Having
# more bulb lists than colours uses white as default for the missing ones, letting you know
# you are missing some colours without the application crashing. Check the default in the API
# for an example (triggers a scene that cycles though five colors).

@app.post("/start_multi_colour_scene")
def start_multi_colour_scene(multi_class: MultiColourSceneClass, background_tasks: BackgroundTasks):
    # Check that no lights appear in multiple lists
    duplicate_bulb = ""
    for i in range(len(multi_class.bulb_lists)):
        for j in range(len(multi_class.bulb_lists)):
            for bulb in multi_class.bulb_lists[i]:
                if bulb in multi_class.bulb_lists[j] and i != j:
                    duplicate_bulb = bulb

    if duplicate_bulb == "":
        stop_scenes()
        background_tasks.add_task(multi_colour_scene, multi_class)

    return "Multi Colour Scene started" if duplicate_bulb == "" else "{} appears on multiple lists".format(
        duplicate_bulb)


@app.post("/start_multi_colour_scene_async")
def start_multi_colour_scene_async(multi_class: MultiColourSceneClass, background_tasks: BackgroundTasks):
    # Check that no lights appear in multiple lists
    duplicate_bulb = ""
    for i in range(len(multi_class.bulb_lists)):
        for j in range(len(multi_class.bulb_lists)):
            for bulb in multi_class.bulb_lists[i]:
                if bulb in multi_class.bulb_lists[j] and i != j:
                    duplicate_bulb = bulb

    if duplicate_bulb == "":
        stop_scenes()
        background_tasks.add_task(multi_colour_scene_async, multi_class)

    return "Multi Colour Scene started" if duplicate_bulb == "" else "{} appears on multiple lists".format(
        duplicate_bulb)


# This one picks a random colour for each selected bulb at the selected wait time

@app.post("/start_random_colour_scene")
def start_random_colour_scene(random_class: RandomColourSceneClass, background_tasks: BackgroundTasks):
    stop_scenes()
    background_tasks.add_task(random_colour_scene, random_class)

    return "Random Colour Scene started"


@app.post("/start_random_colour_scene_async")
def start_random_colour_scene_async(random_class: RandomColourSceneClass, background_tasks: BackgroundTasks):
    stop_scenes()
    background_tasks.add_task(random_colour_scene_async, random_class)

    return "Random Colour Scene started"


# pass in a list of bulbs to get a lighning scene that randomly sends strikes in bulb order

@app.post("/start_lightning_scene")
def start_lightning_scene(lightning_class: LightningSceneClass, background_tasks: BackgroundTasks):
    stop_scenes()
    background_tasks.add_task(lightning_scene_async, lightning_class)

    return "Lightning Scene started"


# Scene triggers - move these to another file / change to activate existing methods

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


@app.post("/start_xmas_scene")
async def start_xmas_scene(xmas_class: XmasSceneClass, background_tasks: BackgroundTasks):
    stop_scenes()
    background_tasks.add_task(xmas_scene, xmas_class.wait_time)

    return "Xmas Scene Started"
