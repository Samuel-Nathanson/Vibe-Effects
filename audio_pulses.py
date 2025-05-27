import numpy as np
import sounddevice as sd
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor
import colorsys
import time

# === CONFIG ===
OUTPUT_DEVICE_INDEX = 26     # NVIDIA loopback WASAPI index
SAMPLE_RATE         = 48000  # Hz
BUFFER_SIZE         = 1024   # samples per callback
FPS                 = 180     # visible frames per second
SUBSTEPS            = 1      # internal updates per frame
SPAWN_INTERVAL      = 0.05    # seconds between pulses
PULSE_WIDTH         = 1      # LEDs on either side of center
SPEED               = 360    # LEDs per second
DECAY_RATE          = 0.1   # tail fade (0–1)
SENSITIVITY         = 0.5    # audio sensitivity multiplier
HUE_CYCLE_SPEED     = 0.25    # Adding some hue cycling in for color diversity

# Derived timings
dt_frame = 1.0 / FPS
dt       = dt_frame / SUBSTEPS

# === AUDIO CALLBACK STATE ===
audio_buffer = np.zeros((BUFFER_SIZE, 2), dtype=np.float32)
buffer_ready = False

def audio_callback(indata, frames, time_info, status):
    global audio_buffer, buffer_ready
    audio_buffer[:] = indata
    buffer_ready = True

# === MAIN ===
def main():
    global buffer_ready

    # 1) OpenRGB & zones
    client = OpenRGBClient()
    zones  = [z for dev in client.devices for z in dev.zones if z.leds]
    if not zones:
        print("❌ No zones found."); return

    n_zones    = len(zones)
    led_counts = [len(z.leds) for z in zones]

    # 2) Precompute frequencies for FFT bins
    freqs = np.fft.rfftfreq(BUFFER_SIZE, 1.0/SAMPLE_RATE)  # length BUFFER_SIZE//2+1
    nyq   = SAMPLE_RATE / 2

    # 3) Initialize per-zone state
    zone_states = []
    for count in led_counts:
        zone_states.append({
            'pos'     : np.zeros((0,), dtype=np.float32),
            'amp'     : np.zeros((0,), dtype=np.float32),
            'rgb'     : np.zeros((0,3), dtype=np.float32),
            'prev_rgb': np.zeros((count,3), dtype=np.float32),
            'idx'     : np.arange(count, dtype=np.float32),
        })

    # 4) Flash red
    red = RGBColor(255,0,0)
    for z in zones:
        z.set_colors([red] * len(z.leds))
    time.sleep(0.5)

    # 5) Start WASAPI loopback input
    stream = sd.InputStream(
        device=OUTPUT_DEVICE_INDEX,
        channels=2,
        samplerate=SAMPLE_RATE,
        blocksize=BUFFER_SIZE,
        dtype='float32',
        callback=audio_callback
    )
    stream.start()
    print("Running…")

    global_hue_power = 0.0
    last_spawn = time.perf_counter()

    try:
        while True:
            t0 = time.perf_counter()
            global_hue_power = (global_hue_power + HUE_CYCLE_SPEED * dt_frame % 1.0)

            # Capture & mix to mono
            if buffer_ready:
                stereo = audio_buffer.copy()
                buffer_ready = False
                mono = stereo.mean(axis=1)
            else:
                mono = None

            # Envelope (peak)
            if mono is not None:
                raw_env = np.max(np.abs(mono))
                env     = min(raw_env * SENSITIVITY, 1.0)
            else:
                env = 0.0

            # Compute FFT magnitudes on mono
            if mono is not None:
                windowed = mono * np.hanning(len(mono))
                mag = np.abs(np.fft.rfft(windowed))
                # find dominant bin
                dom_idx = np.argmax(mag)
                # normalize [0,1]
                hue_norm = (dom_idx / (mag.size - 1)) ** global_hue_power
            else:
                hue_norm = 0.0

            # Spawn pulses in every zone with that hue
            now = t0
            if now - last_spawn >= SPAWN_INTERVAL:
                last_spawn += SPAWN_INTERVAL
                # build RGB once
                r, g, b = colorsys.hsv_to_rgb(hue_norm, 1.0, 1.0)
                rgb_vec = np.array([r, g, b], dtype=np.float32)
                for state in zone_states:
                    state['pos'] = np.concatenate([state['pos'], [0.0]])
                    state['amp'] = np.concatenate([state['amp'], [env]])
                    state['rgb'] = np.vstack([state['rgb'], rgb_vec[None,:]])

            # SUBSTEPS: advance & render
            for _ in range(SUBSTEPS):
                for z, state in zip(zones, zone_states):
                    idx   = state['idx']
                    pos   = state['pos'] + SPEED * dt
                    amp   = state['amp']
                    rgbp  = state['rgb']

                    # cull out-of-range pulses
                    mask = (pos >= -PULSE_WIDTH) & (pos <= idx.size + PULSE_WIDTH)
                    pos  = pos[mask]
                    amp  = amp[mask]
                    rgbp = rgbp[mask]

                    # triangular brightness
                    dist   = np.abs(pos[:,None] - idx[None,:])
                    tri    = np.clip((PULSE_WIDTH - dist)/PULSE_WIDTH, 0,1)
                    bright = tri * amp[:,None]

                    # raw RGB sum
                    raw_rgb = (bright[:,:,None] * rgbp[:,None,:]).sum(axis=0)

                    # decay tail
                    prev    = state['prev_rgb']
                    new_rgb = np.maximum(raw_rgb, prev * DECAY_RATE)
                    state['prev_rgb'] = new_rgb

                    # send to device
                    final   = np.clip(new_rgb, 0,1)
                    rgb_list= [
                        RGBColor(int(rf*255), int(gf*255), int(bf*255))
                        for rf, gf, bf in final
                    ]
                    z.set_colors(rgb_list)

                    # update state
                    state['pos'] = pos
                    state['amp'] = amp
                    state['rgb'] = rgbp

                time.sleep(dt)

    except KeyboardInterrupt:
        stream.stop()
        print("Stopped by user.")

if __name__ == "__main__":
    main()
