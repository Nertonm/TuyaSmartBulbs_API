# API endpoints
from flask import app


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