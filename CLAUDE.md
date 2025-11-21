# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a StreamController plugin that allows users to cycle through up to three different audio outputs (Speaker, Headphones, AirPods) with custom icons and real-time volume display. The plugin uses PulseAudio/PipeWire via `pactl` for audio backend and PIL (Pillow) for image composition.

## Plugin Architecture

### StreamController Plugin Structure

This plugin follows the StreamController plugin architecture:

- **Plugin ID**: `com_pol_audio_switch`
- **Entry Point**: `main.py` defines `AudioSwitchPlugin` class that extends `PluginBase`
- **Actions**: Located in `actions/` directory. Each action extends `ActionBase`
- **Configuration**: Stored via StreamController's settings system (accessed via `get_settings()`/`set_settings()`)

### Key Components

1. **AudioSwitchPlugin** (main.py:23):
   - Registers the plugin and its actions
   - Contains helper methods `get_sinks()` and `set_sink()` that use `pw-dump` and `wpctl` commands
   - Note: These PipeWire-specific methods are legacy code; the actual action uses `pactl` commands

2. **SwitchAudioAction** (actions/SwitchAudioAction.py:25):
   - Main action that handles audio switching and UI rendering
   - Uses `pactl` commands (NOT the plugin's `pw-dump`/`wpctl` methods) for audio operations
   - Manages GTK4/Adwaita configuration UI with ComboRow widgets
   - Generates composite PNG images on-the-fly using PIL
   - Supports Key, Dial, and Touchscreen inputs

### Audio Backend Implementation

The plugin uses **two different audio backends** which can be confusing:

- **Plugin-level methods** (main.py:51-76): Use PipeWire commands (`pw-dump`, `wpctl`)
- **Action-level methods** (SwitchAudioAction.py:311-371): Use PulseAudio commands (`pactl`)

**Currently, only the action-level `pactl` methods are actually used.** The plugin-level PipeWire methods are not called.

### Image Rendering System

Icons are stored as PNG files in `assets/`:
- Base icons: `speaker.png`, `headphones.png`, `airpods.png`
- White variants: `speaker_w.png`, `headphones_w.png`, `airpods_w.png`

The `generate_composite_icon()` method (SwitchAudioAction.py:98) creates a 144x144px composite image showing:
- Center: Current active output (100x100px, full opacity)
- Top-left: Previous output in cycle (50x50px, 70% opacity)
- Top-right: Next output in cycle (50x50px, 70% opacity)

Volume percentage is displayed separately using StreamController's `set_bottom_label()` method.

### Configuration UI

Uses GTK4 ComboRow widgets with two-model pattern:
- **Data model** (`Gtk.ListStore`): Stores actual values (sink names, icon filenames)
- **Display model** (`Gtk.ListStore`): Stores user-visible strings

Each output (A, B, C) has two configuration rows:
- Output selection: Shows available audio sinks from `pactl list sinks`
- Icon selection: Dropdown with "Speaker", "Headphones", "AirPods"

Settings are persisted with keys: `sink_a`, `sink_b`, `sink_c`, `icon_a`, `icon_b`, `icon_c`, `icon_color`

### Event Handling

- `on_ready()`: Called when action is loaded, initializes display
- `on_tick()`: Called periodically (updates display every 10 ticks)
- `on_key_down()`, `on_dial_down()`, `on_touch_start()`: Handle button presses, all call the same cycling logic
- `show_state()`: Main display update method that generates and sets the composite icon

## Development Commands

### Testing the Plugin

StreamController plugins must be tested within StreamController itself. There is no standalone test runner.

**Installation locations:**
- Flatpak: `~/.var/app/com.core447.StreamController/data/plugins/com_pol_audio_switch/`
- Native: `~/.config/streamcontroller/plugins/com_pol_audio_switch/`

**Testing workflow:**
1. Make code changes
2. Copy plugin to StreamController plugins directory (or symlink for development)
3. Restart StreamController
4. Add action to a button and test behavior

### Running the Test Script

There is a standalone test script for image generation:
```bash
python3 test_svg_gen.py
```
Note: This test references `generate_composite_svg()` which no longer exists (replaced with `generate_composite_icon()` for PNG generation). The test would need updating to work with current code.

### Manual Testing Commands

Test audio sink operations directly:
```bash
# List available sinks
pactl list sinks

# Get current default sink
pactl get-default-sink

# Set default sink
pactl set-default-sink <sink_name>

# Get volume
pactl get-sink-volume @DEFAULT_SINK@
```

## Code Conventions

- Use `loguru` logger (imported as `log`) for all logging
- Always set `LC_ALL=C` environment variable when calling `pactl` to ensure consistent English output parsing
- Image operations use PIL/Pillow with RGBA mode for transparency
- StreamController methods like `set_media()`, `set_bottom_label()` handle display updates
- GTK callbacks receive widget as first argument, custom data as additional arguments

## Important Implementation Notes

1. **Locale handling**: All subprocess calls to `pactl` must include `env["LC_ALL"] = "C"` to prevent localization breaking output parsing

2. **Icon caching**: Generated composite icons are saved to `cache/` directory with timestamped filenames to prevent conflicts

3. **Active sink detection**: Uses string comparison between `pactl get-default-sink` output and configured sink names. Whitespace is stripped but matching is case-sensitive.

4. **Cycling logic**: When button is pressed, finds current active sink index (0-2 for A-B-C), increments, and skips over any unconfigured slots

5. **GTK model synchronization**: ComboRow widgets need both the data model (for storing values) and display model (for rendering). Index positions must match between models.