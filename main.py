# Import StreamController modules
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.DeckManagement.InputIdentifier import Input
from src.backend.PluginManager.ActionInputSupport import ActionInputSupport

import sys
import os
import subprocess
import json
from loguru import logger as log

log.debug("Loading com_pol_audio_switch main.py")

# Add plugin to sys.paths
sys.path.append(os.path.dirname(__file__))

# Import actions
try:
    from .actions.SwitchAudioAction import SwitchAudioAction
except ImportError:
    from actions.SwitchAudioAction import SwitchAudioAction

class AudioSwitchPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        
        log.info("Initializing Audio Output Switch Plugin")

        # Register actions
        switch_audio_holder = ActionHolder(
            plugin_base=self,
            action_base=SwitchAudioAction,
            action_id_suffix="SwitchAudio",
            action_name="Switch Audio Output",
            action_support={
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.SUPPORTED,
                Input.Touchscreen: ActionInputSupport.SUPPORTED,
            },
        )
        self.add_action_holder(switch_audio_holder)

        # Register plugin
        self.register(
            plugin_name="Audio Output Switch",
            github_repo="",
            plugin_version="0.1.0",
            app_version="1.5.0"
        )

    def get_sinks(self):
        try:
            output = subprocess.check_output(["pw-dump"], text=True)
            data = json.loads(output)
            sinks = []
            for item in data:
                props = item.get("info", {}).get("props", {})
                if props.get("media.class") == "Audio/Sink":
                    sinks.append({
                        "id": item.get("id"),
                        "name": props.get("node.name"),
                        "description": props.get("node.description"),
                        "nick": props.get("node.nick")
                    })
            return sinks
        except Exception as e:
            log.error(f"Error getting sinks: {e}")
            return []

    def set_sink(self, sink_id):
        try:
            # sink_id can be the integer ID or the name
            subprocess.run(["wpctl", "set-default", str(sink_id)], check=True)
            log.info(f"Set default sink to: {sink_id}")
        except subprocess.CalledProcessError as e:
            log.error(f"Error setting sink: {e}")
