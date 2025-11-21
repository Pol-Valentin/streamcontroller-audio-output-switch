# Import StreamController modules
from GtkHelper.GtkHelper import ComboRow
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionInputSupport import ActionInputSupport
from loguru import logger as log

# Import python modules
import os
import subprocess
import json
import time
import re

# Import PIL for image composition
from PIL import Image, ImageDraw

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Pango

class SwitchAudioAction(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.old_state: int = None
        self.tick_counter = 0
        self.key_press_time = None  # For long press detection

        self.sink_model = Gtk.ListStore.new([str, str]) # Name, Display Name
        self.sink_display_model = Gtk.ListStore.new([str]) # Display Name

        self.icon_model = Gtk.ListStore.new([str]) # Icon Filename
        self.icon_display_model = Gtk.ListStore.new([str]) # Icon Name

        self.color_model = Gtk.ListStore.new([str])
        self.color_display_model = Gtk.ListStore.new([str])
        for color in ["White", "Black"]:
            self.color_model.append([color.lower()])
            self.color_display_model.append([color])

        # Populate icon model - Using PNGs now
        self.icons = {
            "Speaker": "speaker.png",
            "Headphones": "headphones.png",
            "AirPods": "airpods.png"
        }
        for name in self.icons.keys():
            self.icon_model.append([self.icons[name]])
            self.icon_display_model.append([name])

        # Ensure cache directory exists
        self.cache_dir = os.path.join(self.plugin_base.PATH, "cache")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def on_ready(self):
        self.old_state = None
        self.show_state()

    def show_state(self) -> None:
        settings = self.get_settings()
        available_sinks = self.get_available_sinks()

        # Build list of configured and available sinks with their indices
        available_configs = []
        for i, key_suffix in enumerate(["a", "b", "c"]):
            sink_name = settings.get(f"sink_{key_suffix}")
            if sink_name and sink_name in available_sinks:
                available_configs.append(i)

        if not available_configs:
            # No available sinks - show error or default state
            volume = "--"
            self.set_bottom_label(volume, font_size=12)
            return

        # Find current active sink in available configs
        active_index = self.get_active_sink_index()
        current_position = -1
        if active_index in available_configs:
            current_position = available_configs.index(active_index)
        else:
            current_position = 0

        icon_color = settings.get("icon_color", "white")

        def get_icon_path(idx):
            key_suffix = ["a", "b", "c"][idx]
            icon_name = settings.get(f"icon_{key_suffix}", "Speaker")
            filename = self.icons.get(icon_name, "speaker.png")

            # Use _w suffix for white icons
            if icon_color == "white":
                filename = filename.replace(".png", "_w.png")

            return os.path.join(self.plugin_base.PATH, "assets", filename)

        # Get icon paths based on available sinks
        current_idx = available_configs[current_position]
        current_icon_path = get_icon_path(current_idx)

        # Only show prev/next if there are multiple available sinks
        prev_icon_path = None
        next_icon_path = None

        if len(available_configs) >= 2:
            next_position = (current_position + 1) % len(available_configs)
            next_idx = available_configs[next_position]
            next_icon_path = get_icon_path(next_idx)

        if len(available_configs) >= 3:
            prev_position = (current_position - 1) % len(available_configs)
            prev_idx = available_configs[prev_position]
            prev_icon_path = get_icon_path(prev_idx)

        volume = self.get_volume()

        image_path = self.generate_composite_icon(current_icon_path, prev_icon_path, next_icon_path)

        if image_path:
            self.set_media(media_path=image_path, size=1.0)

        # Set volume as bottom label to use configured color
        self.set_bottom_label(volume, font_size=12)

    def generate_composite_icon(self, current_path, prev_path, next_path):
        try:
            size = (144, 144)
            canvas = Image.new("RGBA", size, (0, 0, 0, 0))

            def load_and_resize(path, target_size, opacity=255):
                try:
                    if not os.path.exists(path):
                        # Fallback
                        img = Image.new("RGBA", target_size, (0,0,0,0))
                        draw = ImageDraw.Draw(img)
                        draw.ellipse((0,0,target_size[0],target_size[1]), fill=(255,255,255,255))
                    else:
                        img = Image.open(path).convert("RGBA")
                        img = img.resize(target_size, Image.Resampling.LANCZOS)

                    if opacity < 255:
                        r, g, b, a = img.split()
                        a = a.point(lambda p: p * (opacity / 255))
                        img = Image.merge("RGBA", (r, g, b, a))
                    return img
                except Exception as e:
                    log.error(f"Error loading image {path}: {e}")
                    return Image.new("RGBA", target_size, (0, 0, 0, 0))

            # Center Icon (Active)
            center_size = (100, 100)
            center_img = load_and_resize(current_path, center_size, opacity=255)
            center_pos = ((size[0] - center_size[0]) // 2, (size[1] - center_size[1]) // 2 + 5)
            canvas.alpha_composite(center_img, center_pos)

            # Prev Icon (Top Left) - only if provided
            if prev_path is not None:
                corner_size = (50, 50)
                prev_img = load_and_resize(prev_path, corner_size, opacity=179) # 70% opacity
                canvas.alpha_composite(prev_img, (5, 5))

            # Next Icon (Top Right) - only if provided
            if next_path is not None:
                corner_size = (50, 50)
                next_img = load_and_resize(next_path, corner_size, opacity=179) # 70% opacity
                canvas.alpha_composite(next_img, (size[0] - corner_size[0] - 5, 5))

            # Save to cache
            output_filename = f"icon_{id(self)}_{int(time.time())}.png"
            output_path = os.path.join(self.cache_dir, output_filename)

            canvas.save(output_path)
            return output_path

        except Exception as e:
            log.error(f"Error generating composite icon: {e}")
            return None

    def get_config_rows(self) -> list:
        rows = []
        self.load_sink_model()

        # Icon color selection
        color_row = ComboRow(title="Icon Color", model=self.color_display_model)
        color_renderer = Gtk.CellRendererText()
        color_row.combo_box.pack_start(color_renderer, True)
        color_row.combo_box.add_attribute(color_renderer, "text", 0)
        color_row.combo_box.connect("changed", self.on_color_change)
        self.color_row = color_row
        rows.append(color_row)

        for i, label in enumerate(["A", "B", "C"]):
            sink_row = ComboRow(title=f"Output {label}", model=self.sink_display_model)
            sink_renderer = Gtk.CellRendererText(ellipsize=Pango.EllipsizeMode.END, max_width_chars=30)
            sink_row.combo_box.pack_start(sink_renderer, True)
            sink_row.combo_box.add_attribute(sink_renderer, "text", 0)

            icon_row = ComboRow(title=f"Icon {label}", model=self.icon_display_model)
            icon_renderer = Gtk.CellRendererText()
            icon_row.combo_box.pack_start(icon_renderer, True)
            icon_row.combo_box.add_attribute(icon_renderer, "text", 0)

            sink_row.combo_box.connect("changed", self.on_sink_change, i)
            icon_row.combo_box.connect("changed", self.on_icon_change, i)

            rows.append(sink_row)
            rows.append(icon_row)

            setattr(self, f"sink_row_{i}", sink_row)
            setattr(self, f"icon_row_{i}", icon_row)

        self.load_config_settings()
        return rows

    def load_sink_model(self):
        self.sink_model.clear()
        self.sink_display_model.clear()
        sinks = self.get_sinks()
        available_sinks = self.get_available_sinks()

        for sink in sinks:
            display_name = f"{sink['description']} ({sink['name']})"

            # Mark unavailable sinks
            if sink['name'] not in available_sinks:
                display_name += " (déconnecté)"

            self.sink_model.append([sink['name'], display_name])
            self.sink_display_model.append([display_name])

    def load_config_settings(self):
        settings = self.get_settings()

        # Load icon color
        icon_color = settings.get("icon_color", "white")
        self.color_row.combo_box.set_active(-1)
        for idx, row in enumerate(self.color_display_model):
            if row[0].lower() == icon_color:
                self.color_row.combo_box.set_active(idx)
                break

        for i, key_suffix in enumerate(["a", "b", "c"]):
            sink_name = settings.get(f"sink_{key_suffix}")
            icon_name = settings.get(f"icon_{key_suffix}")

            sink_row = getattr(self, f"sink_row_{i}")
            icon_row = getattr(self, f"icon_row_{i}")

            sink_row.combo_box.set_active(-1)
            icon_row.combo_box.set_active(-1)

            if sink_name:
                for idx, row in enumerate(self.sink_model):
                    if row[0] == sink_name:
                        sink_row.combo_box.set_active(idx)
                        break

            if icon_name:
                for idx, row in enumerate(self.icon_display_model):
                    if row[0] == icon_name:
                        icon_row.combo_box.set_active(idx)
                        break

    def on_sink_change(self, combo_box, index):
        key_suffix = ["a", "b", "c"][index]
        sink_row = getattr(self, f"sink_row_{index}")
        idx = sink_row.combo_box.get_active()
        if idx >= 0 and idx < len(self.sink_model):
            sink_name = self.sink_model[idx][0]
            settings = self.get_settings()
            settings[f"sink_{key_suffix}"] = sink_name
            self.set_settings(settings)
            self.show_state()

    def on_icon_change(self, combo_box, index):
        key_suffix = ["a", "b", "c"][index]
        icon_row = getattr(self, f"icon_row_{index}")
        idx = icon_row.combo_box.get_active()
        if idx >= 0 and idx < len(self.icon_display_model):
            icon_name = self.icon_display_model[idx][0]
            settings = self.get_settings()
            settings[f"icon_{key_suffix}"] = icon_name
            self.set_settings(settings)
            self.show_state()

    def on_color_change(self, combo_box):
        idx = self.color_row.combo_box.get_active()
        if idx >= 0 and idx < len(self.color_display_model):
            color = self.color_display_model[idx][0].lower()
            settings = self.get_settings()
            settings["icon_color"] = color
            self.set_settings(settings)
            self.show_state()

    def on_tick(self):
        self.tick_counter += 1
        if self.tick_counter % 10 == 0:  # Update every 10 seconds
            self.show_state()

    def get_active_sink_index(self) -> int:
        settings = self.get_settings()
        current_default = self.get_default_sink_name()
        if not current_default:
            return -1
        for i, key_suffix in enumerate(["a", "b", "c"]):
            sink_name = settings.get(f"sink_{key_suffix}")
            if sink_name and sink_name.strip() == current_default.strip():
                return i
        return -1

    def on_key_down(self):
        # Record press time for long press detection
        self.key_press_time = time.time()

    def on_key_up(self):
        # Calculate press duration
        if self.key_press_time is None:
            press_duration = 0
        else:
            press_duration = time.time() - self.key_press_time
            self.key_press_time = None

        # Long press (>= 0.5s): just refresh display
        if press_duration >= 0.5:
            available_sinks = self.get_available_sinks()
            log.info(f"Long press detected - refreshing display. Available sinks: {list(available_sinks)}")
            self.show_state()
            return

        # Short press: cycle to next sink
        settings = self.get_settings()
        available_sinks = self.get_available_sinks()

        # Build list of configured and available sinks with their indices
        available_configs = []
        for i, key_suffix in enumerate(["a", "b", "c"]):
            sink_name = settings.get(f"sink_{key_suffix}")
            if sink_name and sink_name in available_sinks:
                available_configs.append((i, sink_name))

        if not available_configs:
            log.warning("No available sinks configured for cycling")
            self.show_error(1)
            self.show_state()
            return

        # Find current active sink in available configs
        current_index = self.get_active_sink_index()
        current_position = -1
        for pos, (idx, _) in enumerate(available_configs):
            if idx == current_index:
                current_position = pos
                break

        # Cycle to next available sink
        next_position = (current_position + 1) % len(available_configs)
        next_sink = available_configs[next_position][1]

        self.set_sink(next_sink)
        self.show_state()

    def on_dial_down(self):
        self.on_key_down()

    def on_dial_up(self):
        self.on_key_up()

    def on_touch_start(self):
        self.on_key_down()

    def on_touch_stop(self):
        self.on_key_up()

    # --- Backend Helpers (pactl) ---

    def get_available_sinks(self):
        """
        Get set of currently available audio sink names.

        Returns:
            set: Set of sink names that are currently connected and available
        """
        try:
            env = os.environ.copy()
            env["LC_ALL"] = "C"
            output = subprocess.check_output(["pactl", "list", "sinks", "short"], text=True, env=env)

            available_sinks = set()
            for line in output.splitlines():
                line = line.strip()
                if line:
                    # Format: <id>\t<name>\t<module>\t<sample_spec>\t<state>
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        sink_name = parts[1]
                        available_sinks.add(sink_name)

            return available_sinks
        except Exception as e:
            log.error(f"Error getting available sinks: {e}")
            return set()

    def get_default_sink_name(self):
        try:
            env = os.environ.copy()
            env["LC_ALL"] = "C"
            output = subprocess.check_output(["pactl", "get-default-sink"], text=True, env=env)
            return output.strip()
        except Exception:
            return None

    def get_volume(self):
        try:
            env = os.environ.copy()
            env["LC_ALL"] = "C"
            output = subprocess.check_output(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], text=True, env=env)
            if "/" in output:
                parts = output.split("/")
                if len(parts) > 1:
                    vol_str = parts[1].strip().replace("%", "")
                    return vol_str
            return "??"
        except Exception:
            return "??"

    def get_sinks(self):
        try:
            env = os.environ.copy()
            env["LC_ALL"] = "C"
            output = subprocess.check_output(["pactl", "list", "sinks"], text=True, env=env)
            
            sinks = []
            current_sink = {}
            
            for line in output.splitlines():
                line = line.strip()
                if line.startswith("Sink #"):
                    if current_sink:
                        sinks.append(current_sink)
                    current_sink = {}
                elif line.startswith("Name: "):
                    current_sink["name"] = line.split("Name: ", 1)[1]
                elif line.startswith("Description: "):
                    current_sink["description"] = line.split("Description: ", 1)[1]
            
            if current_sink:
                sinks.append(current_sink)
                
            return sinks
        except Exception as e:
            log.error(f"Error getting sinks: {e}")
            return []

    def set_sink(self, sink_name):
        try:
            env = os.environ.copy()
            env["LC_ALL"] = "C"
            subprocess.run(["pactl", "set-default-sink", str(sink_name)], check=True, env=env)
            log.info(f"Set default sink to: {sink_name}")
        except subprocess.CalledProcessError as e:
            log.error(f"Error setting sink: {e}")
