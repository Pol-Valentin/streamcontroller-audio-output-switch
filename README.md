# Audio Output Switch Plugin for StreamController

A StreamController plugin that allows you to quickly cycle through up to three different audio outputs with custom icons and real-time volume display.

## Features

- **Cycle Through 3 Audio Outputs**: Switch between Speaker, Headphones, AirPods (or any PulseAudio/PipeWire sinks)
- **Custom Icons**: Assign unique icons to each output
- **Visual Feedback**: 
  - Main icon shows the current active output
  - Small preview icons show previous and next outputs in the cycle
  - Real-time volume percentage display at the bottom
- **One-Button Control**: Press the button to cycle to the next output
- **Auto-Detection**: Automatically highlights the currently active output

## Requirements

- StreamController (Flatpak or native installation)
- PulseAudio or PipeWire audio system
- `pactl` command-line tool (usually pre-installed)

## Installation

1. Copy the plugin directory to your StreamController plugins folder:
   ```bash
   cp -r audio-output-switch ~/.var/app/com.core447.StreamController/data/plugins/com_pol_audio_switch
   ```
   
   For native installations:
   ```bash
   cp -r audio-output-switch ~/.config/streamcontroller/plugins/com_pol_audio_switch
   ```

2. Restart StreamController

3. The plugin will appear in the Actions menu as "Switch Audio Output"

## Configuration

When you add the action to a button, you can configure:

### Output A, B, C
Select which audio sink (output device) should be assigned to each position:
- **Output A**: First output in the cycle
- **Output B**: Second output in the cycle  
- **Output C**: Third output in the cycle

### Icon A, B, C
Choose which icon to display for each output:
- **Speaker**: Floor-standing speaker icon
- **Headphones**: Over-ear headphones icon
- **AirPods**: Wireless earbuds icon

## Usage

1. **Add the Action**: Drag "Switch Audio Output" to a button on your Stream Deck
2. **Configure Outputs**: Select your audio devices (e.g., Speakers for A, Headphones for B, AirPods for C)
3. **Choose Icons**: Assign corresponding icons to match your devices
4. **Press the Button**: Each press cycles to the next configured output

## Visual Layout

The button displays:
- **Top Left Corner**: Previous output icon (grayed out)
- **Center**: Current active output icon (large, white)
- **Top Right Corner**: Next output icon (grayed out)
- **Bottom**: Current volume percentage

## Troubleshooting

### Plugin doesn't load
- Ensure StreamController has been restarted after installation
- Check that the plugin directory name is `com_pol_audio_switch`

### Audio doesn't switch
- Verify that `pactl` is available: `flatpak run --command=pactl com.core447.StreamController list sinks`
- Make sure you've configured at least one output in the settings

### Icons don't appear
- Ensure PNG files exist in `assets/` directory: `speaker.png`, `headphones.png`, `airpods.png`
- Icons should be transparent PNG format

## Development

### File Structure
```
com_pol_audio_switch/
├── main.py                 # Plugin entry point
├── actions/
│   └── SwitchAudioAction.py # Main action logic
├── assets/
│   ├── icon.png           # Plugin icon
│   ├── speaker.png        # Speaker icon
│   ├── headphones.png     # Headphones icon
│   └── airpods.png        # AirPods icon
└── README.md
```

### Technology
- **Audio Backend**: PulseAudio/PipeWire via `pactl`
- **Image Composition**: PIL (Pillow)
- **UI Framework**: GTK4 / Adwaita

## License

This plugin is provided as-is for use with StreamController.

## Credits

Developed for StreamController - https://core447.com/streamcontroller/
