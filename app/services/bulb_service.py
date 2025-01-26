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