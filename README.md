# Vibe Effects

AI // This was vibe-coded as a fun side project in a few hours — not rigorously tested. Use and tweak freely!

This repository contains two Python scripts for animating OpenRGB-controlled LEDs:

## audio_pulses.py  
Listens to your system’s audio output (via WASAPI loopback or Stereo Mix) and spawns colorful pulses that sweep along each LED zone in response to the music.

## rgb_wave.py  
A simple “wave” animation that scrolls a color gradient across all your LED zones at a configurable speed.

## 📦 Requirements

All Python dependencies are pinned in requirements.txt. To install:

    python3 -m pip install --upgrade pip  
    pip install -r requirements.txt

Key dependencies:

- numpy  
- sounddevice  
- openrgb-python  
- (built-in) colorsys

## ⚙️ Prerequisites

**OpenRGB Server**

- Download & install OpenRGB (https://openrgb.org/).  
- Launch OpenRGB as Administrator on Windows (or with root privileges on Linux).  
- In the GUI, go to Settings → SDK Server, enable it on port 6742.

**Audio Loopback (for audio_pulses.py)**

- WASAPI loopback (Windows): your output device must support loopback.  
- Check device indices with `sd.query_devices()`.  
- If loopback fails, enable Windows Stereo Mix and point sounddevice at that instead.

**Python 3.13+**

- Tested on Python 3.13

## 🚀 Usage

1. **Run the RGB wave**

        python rgb_wave.py

2. **Run the Audio Pulses**

        python audio_pulses.py

    Configure your audio loopback device index in `audio_pulses.py`.  
    Tweak spawn rate, pulse width, decay, sensitivity, etc. in the CONFIG section.

## 🔧 Configuration

The scripts are configured slightly differently. Audio Pulses has many more global configuration options, whereas rgb_wave is configured through a config object in the main function. 

For 
- Frame rate & timing: `FPS`, `SUBSTEPS`, `SPAWN_INTERVAL`  
- Pulse shape & speed: `PULSE_WIDTH`, `SPEED`, `DECAY_RATE`  
- Color mapping: `HUE_SWING` / `HUE_CONTRAST`, `AMPLITUDE_POWER`, `HUE_CYCLE_SPEED`  
- Audio sensitivity: `SENSITIVITY`

Experiment to find your perfect look!

## s📝 Note: The OpenRGB Effects Plugin seems to have much faster update speeds than the python API, so the animations in the OpenRGB Effects Plugin tends to look a lot smoother at high speeds. If you like the audio pulses effect, I would recommennd the "Audio Sync" effect in the OpenRGB Effects Plugin.

