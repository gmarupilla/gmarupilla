"""Composite the saved planting state onto the reusable animated clay garden."""
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont, ImageSequence

ART = Path(__file__).resolve().parents[1] / 'garden' / 'art'
WIDTH, HEIGHT = 960, 680
REVISION = 'clay-1'


def font(size):
    for path in (ART / 'DejaVuSans.ttf', Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def version(state, day):
    """Include artwork and renderer bytes so visual changes invalidate GitHub's cache."""
    h = hashlib.sha256()
    h.update(json.dumps({'state': state, 'day': str(day), 'revision': REVISION}, sort_keys=True).encode())
    h.update(Path(__file__).read_bytes())
    for path in sorted(ART.glob('*')):
        if path.suffix in ('.gif', '.png', '.json', '.ttf'):
            h.update(path.read_bytes())
    return h.hexdigest()[:12]


def plot_positions():
    """Each terracotta bed has a back row A-C and a front row D-F."""
    layout = json.loads((ART / 'layout.json').read_text())
    positions = {}
    for number, corners in enumerate(layout['beds'], 1):
        # Coordinates of soil quadrilateral: far-left, far-right, near-right, near-left.
        a, b, c, d = corners
        for row in range(2):
            v = (row + .5) / 2
            for column in range(3):
                u = (column + .5) / 3
                x = (1-v)*((1-u)*a[0]+u*b[0]) + v*((1-u)*d[0]+u*c[0])
                y = (1-v)*((1-u)*a[1]+u*b[1]) + v*((1-u)*d[1]+u*c[1])
                positions[f'{"ABCDEF"[row*3+column]}{number}'] = (round(x), round(y))
    return positions


def plant_sprite(plant, day):
    age = max(0, (day - date.fromisoformat(plant['planted'])).days)
    if age == 0:
        name, height = 'sprout', 36
    elif plant['seed'] == 'Oak':
        name, height = ('oak-young', 46) if age < 4 else ('oak', 60)
    else:
        name = plant['seed'].lower()
        height = (40 if age < 4 else 54) if name != 'mushroom' else (29 if age < 4 else 38)
    im = Image.open(ART / f'{name}.png').convert('RGBA')
    return im.resize((max(1, round(im.width * height / im.height)), height), Image.Resampling.LANCZOS)


def layer(state, day, phase=0):
    overlay = Image.new('RGBA', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(overlay)
    positions = plot_positions()
    draw.text((30, 20), 'T I N Y   W O R L D', font=font(24), fill='#f1e0bc')
    draw.text((31, 54), 'A garden we grow together.', font=font(13), fill='#b8c9b9')
    draw.text((WIDTH-30, 25), f'{len(state["plots"]):02d} / 48 GROWING', font=font(16), fill='#e5d8b9', anchor='ra')
    draw.text((WIDTH-30, 50), f'Tended {day} UTC', font=font(11), fill='#b8c9b9', anchor='ra')
    for plot, (x, y) in positions.items():
        draw.ellipse((x-3, y-1, x+3, y+1), fill='#4b382c')
    for number, corners in enumerate(json.loads((ART / 'layout.json').read_text())['beds'], 1):
        x = round((corners[2][0] + corners[3][0]) / 2)
        y = round((corners[2][1] + corners[3][1]) / 2) + 12
        draw.ellipse((x-9, y-7, x+9, y+7), fill='#d8be8e', outline='#96734d')
        draw.text((x, y), str(number), font=font(11), fill='#3d3026', anchor='mm')
    # Complete each plot back to front: a rear label never overlays a foreground plant.
    for plot, (x, y) in sorted(positions.items(), key=lambda item: item[1][1]):
        plant = state['plots'].get(plot)
        if plant:
            sprite = plant_sprite(plant, day)
            sprite = sprite.rotate(1.4 * math.sin(phase + x / 60), Image.Resampling.BICUBIC,
                                   center=(sprite.width/2, sprite.height), expand=False)
            draw.ellipse((x-8, y-2, x+8, y+3), fill=(35, 31, 20, 90))
            overlay.alpha_composite(sprite, (x-sprite.width//2, y-sprite.height))
        draw.text((x, y+3), plot if plant else plot[0], font=font(9),
                  fill='#fff3c6' if plant else '#c0aa91', anchor='mt', stroke_width=1, stroke_fill='#46372d')
    draw.line((30, 635, 930, 635), fill='#406369', width=1)
    draw.text((30, 649), '8 beds · 6 plots per bed · Choose a plot below', font=font(13), fill='#d5d9c5')
    draw.text((930, 649), f'{len(state["gardeners"])} gardener(s)', font=font(13), fill='#b8c9b9', anchor='ra')
    return overlay


def render_animation(state, day, assets):
    name = f'garden-{version(state, day)}.gif'
    target = assets / name
    if not target.exists():
        frames, durations = [], []
        with Image.open(ART / 'empty-world.gif') as source:
            for index, frame in enumerate(ImageSequence.Iterator(source)):
                canvas = Image.new('RGBA', (WIDTH, HEIGHT), '#0b414d')
                canvas.paste(frame.convert('RGB'), (0, 0))
                canvas.alpha_composite(layer(state, day, 2 * math.pi * index / source.n_frames))
                frames.append(canvas.convert('RGB'))
                durations.append(frame.info.get('duration', 100))
        # One shared palette avoids color flicker between GIF frames.
        palette = frames[0].quantize(colors=192)
        frames = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
        frames[0].save(target, save_all=True, append_images=frames[1:], duration=durations,
                       loop=0, optimize=True, disposal=1)
        frames[0].convert('RGB').save(assets / 'garden-still.png')
    for previous in assets.glob('garden-*.gif'):
        if re.fullmatch(r'garden-[0-9a-f]{12}\.gif', previous.name) and previous != target:
            previous.unlink()
    return name
