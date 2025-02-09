### Tuya Smart Bulbs API

This API allows you to control Tuya-powered Smart Bulbs using FastAPI, Uvicorn, and TinyTuya. It currently supports basic bulb commands and a selection of scenes, with plans for future expansions.

#### Supported Bulbs

This API works with the following bulbs:

- e-luminate Smart Candle E14
- Other Tuya-powered models

#### Setup Instructions

1. Set up the bulbs and obtain the developer keys by following the instructions on [TinyTuya on PyPI](https://pypi.org/project/TinyTuya/).
2. Once the demo API is running, setting up this API should be straightforward.

#### Required Snapshots File

To use this API, you need a `snapshots.json` file in the following format:

```json
{
    "timestamp": 1737800349.758159,
    "devices": [
        {
            "name": "White Lamp",
            "id": "",
            "ip": "",
            "key": "",
            "ver": ""
        }
    ]
}
```

#### Additional Information

This repository is a fork of [TuyaSmartBulbs_API](https://github.com/Nertonm/TuyaSmartBulbs_API), and I appreciate the original work.

- The API does not always wait for a response from the bulbs to speed up operations. As a result, some commands may need to be input twice.
- Requests are not encrypted, so it is recommended to avoid running this on busy or untrusted networks.
- The bulbs continually send data back to Tuya. You may want to block this data if possible.
- Scenes will be moved to a separate module to prevent hardcoding bulb names in the main script.
- The script will be split into multiple files for better structure and maintainability.
