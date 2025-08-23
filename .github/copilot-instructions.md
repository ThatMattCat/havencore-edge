# HavenCore Edge Device

HavenCore Edge Device is a Python-based voice assistant application designed to run on Raspberry Pi 3 with a ReSpeaker USB 4 Mic Array. It provides wake word detection ("Hey Selene") and connects to a speech-to-text service via WebSocket.

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Critical Setup Requirements

**HARDWARE DEPENDENCIES:** This application requires specific hardware (Raspberry Pi 3 + ReSpeaker USB 4 Mic Array) and cannot be fully tested without physical devices. Many operations will fail in environments without the required hardware.

**NEVER CANCEL any long-running commands.** Setup and dependency installation can take 15-30 minutes. Always set timeouts of 60+ minutes for build commands.

## Working Effectively

### Bootstrap and Setup
1. **System Dependencies (Ubuntu/Debian):**
   ```bash
   sudo apt-get update
   sudo apt-get install -y libcairo2-dev libgirepository1.0-dev libportaudio2 portaudio19-dev pkg-config build-essential python3-dev
   ```
   - **Time: 5-10 minutes** - NEVER CANCEL. Set timeout to 20+ minutes.

2. **Git Submodules:**
   ```bash
   git submodule init && git submodule update
   ```
   - **Time: 1-2 minutes** - Downloads ReSpeaker USB 4 Mic Array support libraries.
   - **CRITICAL:** Required for hardware support. Contains usb_4_mic_array drivers and firmware.
   - **Location:** `usb_4_mic_array/` directory with tuning.py, dfu.py, and firmware binaries.

3. **Python Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   ```
   - **Time: 2-3 minutes**

4. **Dependencies Installation:**
   ```bash
   pip install -r requirements.txt
   ```
   - **Time: 10-15 minutes** - NEVER CANCEL. Set timeout to 30+ minutes.
   - **Common failure:** `pycairo` installation fails without system Cairo libraries (step 1 above).
   - **Common failure:** `pyaudio` installation fails without PortAudio development headers.
   - **Network issues:** May timeout due to large packages like `numpy`. Retry with longer timeouts.

5. **Configuration Setup:**
   ```bash
   cp config.py.tmpl config.py
   # Edit config.py with your specific values (see Configuration section below)
   ```

### Configuration Requirements

**CRITICAL:** The application will NOT run without proper configuration. Edit `config.py` and set:

- `DEVICE_ID`: Unique identifier for this device (e.g., "living_room_speaker")
- `STT_IP`: IP address of your speech-to-text service container/server
- `ACCESS_KEY`: Porcupine wake word detection API key (required for "Hey Selene" functionality)
- `LOKI_URL`: Grafana Loki logging endpoint (optional, can be left as template)

**Configuration template values that MUST be changed:**
```python
DEVICE_ID = "your_device_name"                    # Required
STT_IP = "192.168.1.100"                         # Required - your STT server IP
ACCESS_KEY = "your_porcupine_api_key_here"       # Required - from Picovoice
LOKI_URL = 'http://your_loki_ip:3100/loki/api/v1/push'  # Optional
```

**Test configuration validity:**
```bash
python3 -c "import config; print('Config loaded:', config.DEVICE_ID, config.STT_IP)"
```

### Running the Application

```bash
source venv/bin/activate
python audio_controller.py
```

**Expected behavior:**
- Application connects to WebSocket STT service
- Initializes ReSpeaker hardware (will fail without hardware)
- Starts listening for "Hey Selene" wake word
- **Time to start: 10-30 seconds** depending on hardware initialization

**Hardware-related failures are EXPECTED in non-Raspberry Pi environments.**

## Validation

**LIMITED VALIDATION POSSIBLE:** This application is hardware-dependent and cannot be fully validated without:
- Raspberry Pi 3
- ReSpeaker USB 4 Mic Array  
- External speech-to-text service
- Porcupine API key

### Syntax and Import Validation (Always Possible)
```bash
# Validate Python syntax
python3 -c "import ast; ast.parse(open('audio_controller.py').read()); print('Syntax OK')"

# Test configuration loading
python3 -c "import config; print('Config loaded successfully')"
```

### Hardware-Dependent Validation (Raspberry Pi Only)
```bash
# Check audio devices (requires pyaudio installation)
python list_devs.py

# Test wake word detection (requires hardware + API key)
python audio_controller.py
# Then say "Hey Selene" to test detection
```

**Hardware validation steps:**
- Connect ReSpeaker USB 4 Mic Array
- Verify device recognition with `python list_devs.py`
- Test wake word detection by saying "Hey Selene"
- Verify WebSocket connection to STT service
- Test audio streaming and silence detection

**ALWAYS document when validation cannot be completed due to hardware limitations.**

## Common Issues and Troubleshooting

### Dependency Installation Failures
- **pycairo fails:** Install system Cairo libraries first (see step 1 above)
- **pyaudio fails:** Install PortAudio development headers: `sudo apt-get install portaudio19-dev`
- **USB device access:** Run as root or add user to `audio` group
- **Network timeouts:** Retry with longer pip timeouts: `pip install --timeout 120 -r requirements.txt`

### Runtime Failures
- **"No module named 'config'":** Copy and edit `config.py.tmpl` to `config.py`
- **Hardware not found:** Verify ReSpeaker device is connected and recognized
- **WebSocket connection failed:** Verify STT service is running and accessible
- **Porcupine initialization failed:** Verify ACCESS_KEY is valid

### Build Timing Expectations
- **System dependencies:** 5-10 minutes (observed: 8-12 minutes in CI environments)
- **Python dependencies:** 10-20 minutes (can be longer with compilation of pycairo/pyaudio)
- **Total setup time:** 15-30 minutes
- **Application startup:** 10-30 seconds (hardware initialization dependent)

**CRITICAL TIMEOUTS:**
- Use `timeout: 1200` (20 minutes) minimum for system dependency installation
- Use `timeout: 1800` (30 minutes) minimum for Python dependency installation  
- Use `timeout: 120` (2 minutes) for application startup

**NEVER CANCEL builds that appear to hang.** Large packages like numpy and compilation of pycairo can take significant time.

## Common Tasks and File Reference

### Repository Structure Overview
```
/home/runner/work/havencore-edge/havencore-edge/
├── README.md                    # Basic setup and deprecation notice
├── requirements.txt             # Python dependencies  
├── config.py.tmpl              # Configuration template (COPY TO config.py)
├── audio_controller.py         # Main application entry point
├── speaker_controller.py       # Audio output via GStreamer
├── pixel_ring.py               # ReSpeaker LED control
├── trace_id.py                 # Distributed tracing utilities
├── list_devs.py                # Audio device detection utility
├── models/                     # Porcupine wake word models
│   └── Selene_en_raspberry-pi_v3_0_0.ppn
└── usb_4_mic_array/            # Git submodule for ReSpeaker support
    ├── tuning.py               # Microphone array configuration
    ├── dfu.py                  # Device firmware update
    ├── README.md               # Hardware-specific documentation
    └── test/                   # Hardware test utilities
```

### Frequently Referenced Files

**Check these files when troubleshooting:**
- `config.py` - All configuration parameters and API keys
- `audio_controller.py` lines 30-50 - Hardware initialization
- `requirements.txt` - All Python dependencies
- `usb_4_mic_array/README.md` - Hardware setup instructions

**Key Configuration Constants:**
- `SAMPLE_RATE = 16000` - Audio sampling rate
- `CHANNELS = 6` - ReSpeaker has 6 channels (4 mics + 2 processed)
- `STT_PORT = 6000` - WebSocket port for speech-to-text service
- `SPEAKER_PORT = 5100` - GStreamer audio output port

## Development Guidelines

### Code Structure
- **Main application:** `audio_controller.py` - WebSocket client, audio processing, wake word detection
- **Configuration:** `config.py.tmpl` - Template requiring customization
- **Hardware control:** `pixel_ring.py` - LED control for ReSpeaker
- **Audio output:** `speaker_controller.py` - GStreamer-based audio playback
- **Logging:** `trace_id.py` - Distributed tracing support
- **USB mic support:** `usb_4_mic_array/` - Git submodule for hardware libraries

### Testing Strategy
1. **Syntax validation** (always possible)
2. **Import testing** with mocked hardware dependencies
3. **Configuration validation**
4. **Hardware testing** (Raspberry Pi only)
5. **Integration testing** with STT service

**ALWAYS test syntax and imports before committing changes.**

### No Existing CI/CD or Linting
- No GitHub Actions workflows
- No linting configuration (flake8, pylint, etc.)
- No automated testing infrastructure
- Manual validation required for all changes

## Project Dependencies

### Core Python Packages
- `pvporcupine` - Wake word detection (requires API key)
- `pyaudio` - Audio input/output
- `websockets` - STT service communication  
- `numpy` - Audio processing
- `usb.core` (pyusb) - USB device control
- `fastapi`/`uvicorn` - Web service components
- `pycairo` - Graphics/LED control

### System Dependencies
- `libcairo2-dev` - Cairo graphics library
- `portaudio19-dev` - Audio system
- `build-essential` - Compilation tools
- `python3-dev` - Python development headers

### Hardware Dependencies  
- Raspberry Pi 3+ (tested platform)
- ReSpeaker USB 4 Mic Array
- Audio output device (speaker/headphones)

## External Service Dependencies

- **Speech-to-Text Service:** WebSocket server on configurable IP/port
- **Porcupine API:** Wake word detection service (requires account/key)
- **Grafana Loki:** Optional log aggregation service

**IMPORTANT:** Application cannot run without STT service and Porcupine API key configuration.

## Known Limitations and Workarounds

### Environmental Limitations
- **Cannot test on non-Raspberry Pi:** Hardware-specific USB drivers fail on other platforms
- **Cannot test without ReSpeaker:** Audio input requires specific microphone array
- **Cannot test without STT service:** WebSocket connection required for core functionality
- **Cannot test without Porcupine API key:** Wake word detection requires valid API credentials

### Development Workarounds
- **Syntax validation:** Always possible with `python3 -c "import ast; ast.parse(open('file.py').read())"`
- **Configuration testing:** Use `python3 -c "import config"` to validate config syntax
- **Dependency verification:** Check imports individually to identify missing packages
- **Mock testing:** Consider mocking hardware dependencies for unit testing (not currently implemented)

### Network-Related Issues
- **PyPI timeouts:** Use `pip install --timeout 180` for large packages
- **Download failures:** Retry with `pip install --retries 3`
- **Compilation issues:** Ensure system dependencies installed first (Cairo, PortAudio)

**When validation is impossible:** Always document that testing was limited by hardware/network constraints and specify what could not be verified.