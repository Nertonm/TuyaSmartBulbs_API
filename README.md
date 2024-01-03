# Tuya Smart Bulbs API

This is an API for Tuya-powered Smart Bulbs, using FastAPI, uvicorn, and TinyTuya. At the moment
it's very minimal, triggering some of the standard bulb commands and few scenes, but I plan 
on adding more.

The bulbs I'm using are e-luminate Smart Candle E14, as well as a couple of other Tuya-powered
models. Intstructions for setting up the bulbs and getting the dev keys can be found at 
https://pypi.org/project/tinytuya/ - once you have the demo API working, getting this one 
going should be fairly straightforward.

UPDATE: I was learning as I was working on it, and it became such as mess of hard-coded
names and weird functions that it needed a re-write. It's much better now - all it needs 
is a copy of the snapshot.json file that's generated when you set up the bulbs, and
the rest is done dynamically: No bulb naming, no synching, and much easier to follow.
Instead of updating, I replaced the repository, as the old one was terrible and would
probably make even a moderately-experienced coder cry.

I'm also working on a controller for it, using a Pico RGB Keypad, which you can find at
https://github.com/TimboFimbo/Pico_TuyaBulb_Remote

Notes and TODOs:

- It doesn't always wait for a response from the bulbs, in order to speed things up.
    However, this means some commands are missed - I may fix it, but for now some
    commands may have to be input twice.

- There aren't any safety measures to encrypt the requests being sent,
    so don't run it on a busy network or one with untrusted devices.

- I'm setting this up for holiday displays (along with other things), but I haven't
    verified the security of the bulbs. However, I know that they constantly send
    data back to Tuya, which I plan on blocking, if possible. If not, I won't keep them 
    up year-long, so use at your own discretion, as you should with all IoT devices.

- I've started adding scenes, but I'm going to move them into a separate module, as I 
    don't want bulb names included in the main one. Check the comments within the script
    for info on how to use them. I plan on changing pre-set scenes, such as the Xmas one,
    to trigger existing scenes with pre-set values, rather than have their own methods.

- The script is getting a little long, so I'll split it up into separate files at some
    point, once I figure out the best way of structuring them.