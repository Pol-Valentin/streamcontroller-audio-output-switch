# Design: Skip Unavailable Audio Sinks

**Date:** 2025-11-21
**Status:** Approved

## Overview

Enhance the Audio Output Switch plugin to automatically skip audio sinks that are unavailable (disconnected DACs, powered-off Bluetooth headphones, etc.) during cycling and display.

## Requirements

### User Requirements
1. When cycling through outputs, skip sinks that are not currently available
2. Display only available sinks in the composite icon
3. Show all configured sinks in the configuration UI, with unavailable ones clearly marked
4. Allow pre-configuration of devices that will be connected later

### Behavioral Requirements
- **On button press:** Automatically skip to the next available sink in the cycle (A→B→C)
- **Icon display:** Show only currently available sinks in the composite icon
- **Configuration UI:** Display all sinks with "(déconnecté)" suffix for unavailable ones

## Architecture

### Core Components

#### 1. Sink Availability Detection

**New method:** `get_available_sinks()` in `SwitchAudioAction.py`

**Purpose:** Query PulseAudio/PipeWire for currently available sinks

**Implementation:**
```python
def get_available_sinks(self):
    """
    Get list of currently available audio sinks.

    Returns:
        set: Set of sink names that are currently available
    """
    # Call: pactl list sinks short
    # Parse output to extract sink names
    # Return as set for fast lookup
```

**Technical details:**
- Execute `pactl list sinks short` with `LC_ALL=C` environment variable
- Parse output format: `<id>\t<name>\t<module>\t<sample_spec>\t<state>`
- Extract sink names (second column)
- Return as Python set for O(1) lookup during cycle logic

#### 2. Modified Cycling Logic

**Location:** Button press handlers (`on_key_down()`, `on_dial_down()`, `on_touch_start()`)

**Flow:**
1. Get list of available sinks with `get_available_sinks()`
2. Filter configured sinks (A, B, C) to only include available ones
3. Find current active sink index in the filtered list
4. Cycle to next available sink
5. If no sinks are available, do nothing (no-op)

**Example:**
- Configured: A=Speaker, B=Headphones, C=AirPods
- Available: Speaker, AirPods (Headphones disconnected)
- Current: Speaker
- Action: Skip Headphones, switch to AirPods

#### 3. Dynamic Icon Display

**Modified method:** `show_state()` in `SwitchAudioAction.py`

**Behavior:**
- Query available sinks before generating composite icon
- Filter configured sinks to only available ones
- Adapt icon composition based on number of available sinks:
  - **1 sink:** Display only that sink (centered, 100x100px)
  - **2 sinks:** Display current + next (no previous)
  - **3 sinks:** Normal behavior (previous/current/next)

**Icon layout examples:**
- 3 available: `[prev] [CURRENT] [next]` (normal)
- 2 available: `[CURRENT] [next]`
- 1 available: `[CURRENT]`

#### 4. Configuration UI Enhancement

**Modified method:** `_on_ready_in_gtk_thread()` in `SwitchAudioAction.py`

**Implementation:**
1. Get all sinks with `pactl list sinks`
2. Get available sinks with `get_available_sinks()`
3. For each sink in dropdown:
   - If available: Display normal name (e.g., "Built-in Audio Analog Stereo")
   - If unavailable: Append "(déconnecté)" (e.g., "AirPods (déconnecté)")
4. Store actual sink name (without suffix) in data model

**Benefits:**
- Users can pre-configure devices that aren't currently connected
- Clear visibility of device connection status
- Configuration persists across device connect/disconnect cycles

## Edge Cases

### Case 1: No Configured Sinks Available
**Behavior:**
- Button press: No-op (no sink change)
- Icon: Display error state or maintain current state
- Volume label: Display "N/A" or "--"

### Case 2: Active Sink Disconnects
**Behavior:**
- PulseAudio/PipeWire automatically switches to another available sink
- Next `on_tick()` updates display to reflect new active sink
- Icon updates to show current state

### Case 3: Only One Sink Available
**Behavior:**
- Button press: No-op or re-activates same sink
- Icon: Shows only that sink (no previous/next)
- Consistent, predictable behavior

### Case 4: Configured But Never Connected
**Behavior:**
- Appears in config UI with "(déconnecté)" suffix
- Never appears in cycle
- Not shown in composite icon
- Ready to use immediately when connected

## Error Handling

### pactl Command Failures
- Log errors with loguru logger
- Continue with previous state (no crash)
- Fail gracefully without breaking UI

### Locale Consistency
- Always set `LC_ALL=C` when calling `pactl`
- Ensures English output for consistent parsing
- Prevents localization from breaking string matching

## Implementation Changes

### Files to Modify
- `actions/SwitchAudioAction.py`: Core logic changes

### New Methods
- `get_available_sinks()`: Query available sinks

### Modified Methods
- `on_key_down()`, `on_dial_down()`, `on_touch_start()`: Add availability filtering to cycle logic
- `show_state()`: Add dynamic icon composition based on available sinks
- `_on_ready_in_gtk_thread()`: Add availability marking in config UI

### No Breaking Changes
- Existing configuration settings remain compatible
- Behavior gracefully degrades if all sinks configured are unavailable
- No migration needed for existing users

## Testing Considerations

### Manual Testing Scenarios
1. Configure 3 sinks, disconnect middle one, verify cycling skips it
2. Disconnect all but one sink, verify icon shows only that sink
3. Disconnect active sink, verify display updates to new active sink
4. Configure sink while disconnected, connect it later, verify it appears in cycle
5. Open config UI with mixed connected/disconnected sinks, verify marking

### Test Commands
```bash
# List available sinks
pactl list sinks short

# Get current default sink
pactl get-default-sink

# Simulate disconnect (requires admin/specific hardware)
# Typically tested with actual hardware connect/disconnect
```

## Success Criteria

- Plugin cycles only through currently available sinks
- Icon accurately reflects available devices at all times
- Configuration UI clearly distinguishes available vs unavailable sinks
- No crashes or errors when sinks become unavailable
- Behavior is intuitive and predictable for users