import gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg
import cairo
import os

def convert_svg_to_png(svg_path, png_path, width=512, height=512):
    if not os.path.exists(svg_path):
        print(f"Error: {svg_path} not found")
        return

    handle = Rsvg.Handle.new_from_file(svg_path)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    context = cairo.Context(surface)
    
    # Scale to fit
    dimensions = handle.get_dimensions()
    scale_x = width / dimensions.width
    scale_y = height / dimensions.height
    scale = min(scale_x, scale_y)
    
    context.scale(scale, scale)
    
    # Render
    handle.render_cairo(context)
    
    surface.write_to_png(png_path)
    print(f"Converted {svg_path} to {png_path}")

assets_dir = "/home/pol/dev/perso/stream-controller/audio-output-switch/assets"
icons = ["speaker", "headphones", "airpods"]

for icon in icons:
    svg_path = os.path.join(assets_dir, f"{icon}.svg")
    png_path = os.path.join(assets_dir, f"{icon}.png")
    convert_svg_to_png(svg_path, png_path)
