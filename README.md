# HavenCore Edge Device

### This is being deprecated for [ESP32-Box-3](https://github.com/espressif/esp-box)
---
Edge device code for the [HavenCore Project](https://github.com/ThatMattCat/havencore)

'Hey Selene' is the wake trigger (still needs Porcupine API Key/Account)

Tested with Python 3.10.12 on Raspberry Pi 3 using ReSpeaker Mic Array and generic speaker connected straight to Pi

**NOTE:** This will likely be replaced by an ESP32 solution (eg: [ESP32-S3-BOX-3 Development Board](https://www.amazon.com/Espressif-ESP32-S3-BOX-3-Development-Board/dp/B0CL6HD8JX)) which will be cheaper and have better functionality for this use-case. Should allow removing dependencies on third-party libraries.


### Setup
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python audio_controller.py
```

### Run

```
source venv/bin/activate
python audio_controller.py
```
