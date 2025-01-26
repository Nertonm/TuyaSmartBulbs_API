import json
import os
import sys

import tinytuya
from pydantic import BaseModel

import Colours

CON_TIMEOUT = 10
RETRY_LIMIT = 1

# Let's get the bulb names right, as they are sometimes used
WHITE_LAMP = "White Lamp"
WOOD_LAMP = "Wood Lamp"
BLACK_LAMP = "Black Lamp"
DEN_LIGHT = "Den Light"
CHAIR_LIGHT = "Chair Light"
SOFA_LIGHT = "Sofa Light"


class BulbObject:
    def __init__(self, name_in, dev_id_in, address_in, local_key_in, version_in):
        self.name = name_in
        self.bulb = tinytuya.BulbDevice(
            dev_id=dev_id_in,
            address=address_in,
            local_key=local_key_in,
            connection_timeout=CON_TIMEOUT,
            version=version_in
        )


bulbs: BulbObject = []
running_scenes = []

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


def set_bulb_retry_limit(limit):
    for this_bulb in bulbs:
        this_bulb.bulb.set_socketRetryLimit(limit)


set_bulb_retry_limit(RETRY_LIMIT)


# Compile all the bulbs into a list with a true or false toggle
# This list will be added to the JSON classes below
# Multi toggles are being added, for setting bulbs to do different things

class BulbToggle(BaseModel):
    name: str = ""
    bright_mul: float = 1.0
    toggle: bool = True


class MultiRgbToggle(BulbToggle):
    red: int
    green: int
    blue: int


class RgbColour(BaseModel):
    red: int
    green: int
    blue: int


class LightningToggle(BaseModel):
    name: str = ""
    # red: int = 255
    # green: int = 255
    # blue: int = 255
    # colour: RgbColour = Colours.WHITE


bulb_toggles: BulbToggle = []
multi_rgb_toggles: MultiRgbToggle = []
lightning_toggles: LightningToggle = []
all_colours: RgbColour = []
multi_scene_toggles = [[], []]

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
