from openrgb import OpenRGBClient
from openrgb.utils import RGBColor
import matplotlib.pyplot as plt
from openrgb.orgb import Device, Zone
import time
import math
import colorsys

def to_mpl_colors(colors: list[RGBColor]):
    """
    colors: a list of openrgb.utils.RGBColor
    returns: same structure, but with matplotlib (r, g, b) floats 0–1
    """
    mpl_colors = [
        (c.red   / 255.0,
          c.green / 255.0,
          c.blue  / 255.0)
        for c in colors
    ]
    return mpl_colors

def plot_zones(zones, waves, colors):
    """
    zones   : list of zone objects, each must have a .name attribute
    waves   : list of lists of wave-values (floats 0–1) per zone
    colors  : list of lists of RGB tuples (r,g,b) or matplotlib-acceptable colors per zone
    """
    n = len(zones)
    fig, axes = plt.subplots(n, 1, figsize=(8, 2 * n), sharex=False)
    if n == 1:
        axes = [axes]  # make it iterable

    for ax, zone, wave, cols in zip(axes, zones, waves, colors):
        x = list(range(len(wave)))
        ax.scatter(x, wave, c=cols, s=50)
        ax.set_title(zone.name)
        ax.set_ylabel("Wave")
        ax.set_xlim(-0.5, len(wave) - 0.5)
        ax.set_ylim(0, 1)
        ax.grid(True)

    plt.xlabel("LED Index in Zone")
    plt.tight_layout()
    plt.show()

def animate_wave(
  zones: list[Zone],
  frequency_s: int = 1,
  modulate_hue: bool = True,
  modulate_saturation: bool = False,
  modulate_value: bool = False,
  base_hue: int = 360,
  base_saturation: int = 100,
  base_value: int = 100,
  steps: int = 10,
  reversed: bool = False,
  plot_test: bool = False,
  ):
  
  i = 0
  period_s = 1 / frequency_s
  
  zones_to_leds = {zone: len(zone.leds) for zone in zones}
  max_leds = max(zones_to_leds.values())
  offset_delta = 2 * math.pi / steps

  while True:
    wave = [0.5 * (1 + math.sin(i * offset_delta + x * 2 * math.pi * (1/max_leds))) for x in range(0, max_leds)]
    waves = []
    mpl_colors = []

    for zone in zones:
      zone_leds = zones_to_leds[zone]
      step = max_leds / zone_leds
      wave_downsampled = [wave[int(i * step)] for i in range(zone_leds)]

      h_l = [h * 360 for h in wave_downsampled] if modulate_hue else [base_hue] * len(wave_downsampled)
      s_l = [s * 100 for s in wave_downsampled] if modulate_saturation else [base_saturation] * len(wave_downsampled)
      v_l = [v * 100 for v in wave_downsampled] if modulate_value else [base_value] * len(wave_downsampled)

      colors = [RGBColor.fromHSV(h, s, l) for h, s, l in zip(h_l, s_l, v_l)]
      if reversed:
        colors = colors.reverse()

      zone.set_colors(colors)

      if config["PLOT_TEST"]:
        waves.append(wave_downsampled)
        mpl_colors.append(to_mpl_colors(colors))
    
    if config["PLOT_TEST"]:
      plot_zones(zones, waves, mpl_colors)

    i += 1
    time.sleep(period_s / steps)


def main(config: dict={}):
  client = OpenRGBClient()
  devices = client.ee_devices

  zones = []
  for dev in devices:
    print("Zones:")
    for zone in dev.zones:
      print(f"  • {zone.name}: LEDs {len(zone.leds)}")
      zones.append(zone)
  
  try:
      animate_wave(
        zones, 
        config["FREQUENCY_SECONDS"], 
        steps=config["STEPS"], 
        plot_test=config["PLOT_TEST"],
        modulate_value=config["MODULATE_VALUE"])

  except KeyboardInterrupt:
      print("Stopping wave...")

if __name__ == "__main__":
  config = {
    "PLOT_TEST": False,
    "DEFAULT_COLOR": RGBColor(0, 100, 255),
    "FREQUENCY_SECONDS": 3,
    "STEPS": 35,
    "MODULATE_VALUE": True
  }

  main(config)