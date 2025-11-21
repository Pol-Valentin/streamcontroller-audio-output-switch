import sys
import os
import re

# Mock dependencies
class MockPluginBase:
    def __init__(self):
        self.PATH = "/home/pol/dev/perso/stream-controller/audio-output-switch"

class MockActionBase:
    def __init__(self, *args, **kwargs):
        self.plugin_base = MockPluginBase()
        self.cache_dir = os.path.join(self.plugin_base.PATH, "cache")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def set_media(self, *args, **kwargs):
        pass
        
    def get_settings(self):
        return {}

# Import the class to test (we need to mock imports first or just copy the relevant methods)
# Since importing the actual file might trigger other imports (Gtk), let's just copy the logic we want to test
# or try to import it if we can mock the Gtk modules.

# Let's try to import the file, mocking Gtk first.
from unittest.mock import MagicMock
sys.modules["GtkHelper.GtkHelper"] = MagicMock()
sys.modules["src.backend.PluginManager.ActionBase"] = MagicMock()
sys.modules["src.backend.DeckManagement.DeckController"] = MagicMock()
sys.modules["src.backend.PageManagement.Page"] = MagicMock()
sys.modules["src.backend.PluginManager.ActionInputSupport"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi"] = MagicMock()

# Now import the action
sys.path.append("/home/pol/dev/perso/stream-controller/audio-output-switch")
from actions.SwitchAudioAction import SwitchAudioAction

# Instantiate and test
action = SwitchAudioAction()
action.plugin_base = MockPluginBase() # Re-set in case super init didn't
action.cache_dir = os.path.join(action.plugin_base.PATH, "cache")

# Test generation
output_path = action.generate_composite_svg("speaker.svg", "headphones.svg", "airpods.svg", "50")
print(f"Output path: {output_path}")

if output_path and os.path.exists(output_path):
    with open(output_path, "r") as f:
        content = f.read()
        print("--- SVG Content Start ---")
        print(content[:500]) # Print first 500 chars
        print("...")
        print("--- SVG Content End ---")
        
        if "<path" in content or "<rect" in content:
            print("SUCCESS: SVG content found embedded.")
        else:
            print("FAILURE: No drawing elements found.")
else:
    print("FAILURE: No output file generated.")
