#! /usr/bin/env python3
import argparse
import json
import shutil
import subprocess
from itertools import chain
from pathlib import Path

from PIL import Image
from PIL.Image import Resampling

PLAYER_COLOUR = (0, 119, 228)
# PLAYER_COLOUR = (236,9,9)

TARGET_SIZE = (48, 48)

COLOURS = {
    "Blue": {
        "Text": [110, 166, 235, 255],
        "TextOutline": [0, 0, 0, 255],
        "Icons": [0, 0, 255, 255],
        "HealthBar": [110, 166, 235, 255],
        "TimelineDark": [60, 60, 150, 255],
        "TimelineLight": [75, 74, 200, 255],
        "MiniMap": [0, 0, 255, 255],
        "TechtreePreviewCiv": [110, 166, 235, 255]
    },
    "Red": {
        "Text": [255, 100, 100, 255],
        "TextOutline": [0, 0, 0, 255],
        "Icons": [255, 0, 0, 255],
        "HealthBar": [255, 100, 100, 255],
        "TimelineDark": [160, 35, 35, 255],
        "TimelineLight": [200, 35, 35, 255],
        "MiniMap": [254, 0, 0, 255],
        "TechtreePreviewCiv": [255, 100, 100, 255]
    },
    "Green": {
        "Text": [0, 255, 0, 255],
        "TextOutline": [0, 0, 0, 255],
        "Icons": [0, 255, 0, 255],
        "HealthBar": [0, 255, 0, 255],
        "TimelineDark": [45, 135, 45, 255],
        "TimelineLight": [35, 200, 35, 255],
        "MiniMap": [0, 255, 0, 255],
        "TechtreePreviewCiv": [0, 255, 0, 255]
    },
    "Yellow": {
        "Text": [255, 255, 0, 255],
        "TextOutline": [0, 0, 0, 255],
        "Icons": [215, 215, 30, 255],
        "HealthBar": [255, 255, 0, 255],
        "TimelineDark": [150, 150, 20, 255],
        "TimelineLight": [200, 200, 25, 255],
        "MiniMap": [255, 255, 1, 255],
        "TechtreePreviewCiv": [255, 255, 0, 255]
    },
    "Aqua": {
        "Text": [0, 255, 225, 255],
        "TextOutline": [0, 0, 0, 255],
        "Icons": [126, 242, 225, 255],
        "HealthBar": [0, 255, 225, 255],
        "TimelineDark": [60, 140, 140, 255],
        "TimelineLight": [35, 175, 175, 255],
        "MiniMap": [0, 255, 225, 255],
        "TechtreePreviewCiv": [0, 255, 225, 255]
    },
    "Purple": {
        "Text": [241, 108, 232, 255],
        "TextOutline": [0, 0, 0, 255],
        "Icons": [150, 15, 250, 255],
        "HealthBar": [241, 108, 232, 255],
        "TimelineDark": [140, 45, 140, 255],
        "TimelineLight": [200, 35, 200, 255],
        "MiniMap": [255, 0, 255, 255],
        "TechtreePreviewCiv": [241, 108, 232, 255]
    },
    "Grey": {
        "Text": [172, 172, 172, 255],
        "TextOutline": [0, 0, 0, 255],
        "Icons": [99, 103, 112, 255],
        "HealthBar": [100, 100, 100, 255],
        "TimelineDark": [64, 64, 64, 255],
        "TimelineLight": [136, 136, 136, 255],
        "MiniMap": [67, 67, 67, 255],
        "TechtreePreviewCiv": [172, 172, 172, 255]
    },
    "Orange": {
        "Text": [255, 180, 21, 255],
        "TextOutline": [0, 0, 0, 255],
        "Icons": [255, 180, 21, 255],
        "HealthBar": [255, 150, 5, 255],
        "TimelineDark": [145, 85, 20, 255],
        "TimelineLight": [200, 130, 50, 255],
        "MiniMap": [255, 130, 1, 255],
        "TechtreePreviewCiv": [255, 180, 21, 255]
    },
    "White": {
        "Text": [232, 238, 255, 255],
        "TextOutline": [0, 0, 0, 255],
        "Icons": [232, 238, 255, 255],
        "HealthBar": [232, 238, 255, 255],
        "TimelineDark": [200, 200, 200, 255],
        "TimelineLight": [255, 255, 255, 255],
        "MiniMap": [255, 255, 255, 255],
        "TechtreePreviewCiv": [232, 238, 255, 255]
    }
}


def fmt_size(b: float) -> str:
    for unit in ('B', 'KB', 'MB', 'GB'):
        if b < 1024:
            return f'{b:.1f} {unit}'
        b /= 1024
    return f'{b:.1f} TB'


def scale(v):
    return (int(PLAYER_COLOUR[0] * (v[0] / 255)), int(PLAYER_COLOUR[1] * (v[1] / 255)),
            int(PLAYER_COLOUR[2] * (v[2] / 255)), 255)


def main():
    parser = argparse.ArgumentParser(description='Generate building/tech/unit images from AoE2DE assets.')
    parser.add_argument('aoe2de_path', type=Path, help='Path to AoE2DE installation (e.g. ~/.steam/steam/steamapps/common/AoE2DE)')
    parser.add_argument('--resize', action='store_true', help=f'Resize images to {TARGET_SIZE[0]}x{TARGET_SIZE[1]}')
    args = parser.parse_args()

    aoe2de_path = args.aoe2de_path.expanduser().resolve()
    base_path = aoe2de_path / 'widgetui' / 'textures' / 'ingame'
    techtreesdir = aoe2de_path / 'resources' / '_common' / 'dat' / 'CivTechTrees'

    ids = {'Unit': set(), 'Building': set(), 'Tech': set()}
    print(techtreesdir)
    for json_file in sorted(techtreesdir.glob('*.json')):
        data = json.loads(json_file.read_text())
        for item in chain(data['civ_techs_buildings'], data['civ_techs_units']):
            ids[item['Use Type']].add(item['Picture Index'])

    tmp_dir = Path('/tmp/gbtui-uwu')
    tmp_dir.mkdir(exist_ok=True)
    tmp_to_target = {}
    total_bytes = 0

    for type_, ids_for_type in sorted(ids.items()):
        for picture_index in sorted(ids_for_type):
            sourcetype = 'tech' if type_ == 'Tech' else 'buildings' if type_ == 'Building' else 'units'
            source_dds_list = (list((base_path / sourcetype).glob(f'{picture_index:03}_*.dds')) +
                          list((base_path / sourcetype).glob(f'{picture_index:03}_*.DDS')))
            if len(source_dds_list) > 1:
                print(source_dds_list)
                raise AssertionError(f'list too long for {type_=}, {picture_index=}')
            if len(source_dds_list) < 1:
                print(source_dds_list)
                raise AssertionError(f'list too short for {type_=}, {picture_index=}')
            source_dds = source_dds_list[0]
            target_file = Path(__file__).parent.resolve().parent / 'img' / type_ / f'{picture_index}.png'
            tmp_file = tmp_dir / f'{type_}_{picture_index}.png'
            w, h = process_dds(source_dds, tmp_file, args.resize)
            file_bytes = tmp_file.stat().st_size
            total_bytes += file_bytes
            print(f'  {type_} {picture_index}: {w}x{h}, {fmt_size(file_bytes)}  (total: {fmt_size(total_bytes)})')
            tmp_to_target[tmp_file] = target_file

    backgrounds_src = aoe2de_path / 'widgetui' / 'textures' / 'backgrounds'
    backgrounds_dst = Path(__file__).parent.resolve().parent / 'img' / 'backgrounds'
    print(f'Processing backgrounds from {backgrounds_src}')
    for source_dds in sorted(chain(backgrounds_src.glob('*.dds'), backgrounds_src.glob('*.DDS'))):
        tmp_file = tmp_dir / f'backgrounds_{source_dds.stem}.png'
        w, h = process_dds(source_dds, tmp_file, args.resize)
        file_bytes = tmp_file.stat().st_size
        total_bytes += file_bytes
        print(f'  backgrounds {source_dds.name}: {w}x{h}, {fmt_size(file_bytes)}  (total: {fmt_size(total_bytes)})')
        tmp_to_target[tmp_file] = backgrounds_dst / f'{source_dds.stem}.png'

    print(f'Running pngquant on {len(tmp_to_target)} files...')
    subprocess.run(['pngquant', '--ext', '.png', '--force', *map(str, tmp_to_target)], check=True)

    for tmp_file, target_file in tmp_to_target.items():
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tmp_file, target_file)
        tmp_file.unlink()

    backgrounds_dst.mkdir(parents=True, exist_ok=True)
    for png_file in sorted(chain(backgrounds_src.glob('*.png'), backgrounds_src.glob('*.PNG'))):
        print(f'Copying {png_file.name} → {backgrounds_dst}')
        shutil.copy2(png_file, backgrounds_dst / png_file.name)

    staticons_src = base_path / 'staticons'
    staticons_dst = Path(__file__).parent.resolve().parent / 'img' / 'staticons'
    print(f'Copying {staticons_src} → {staticons_dst}')
    shutil.copytree(staticons_src, staticons_dst, dirs_exist_ok=True)

    emblems_src = base_path / 'emblems'
    emblems_dst = Path(__file__).parent.resolve().parent / 'img' / 'emblems'
    print(f'Copying {emblems_src} → {emblems_dst}')
    shutil.copytree(emblems_src, emblems_dst, dirs_exist_ok=True)

    civs_src = base_path.parent / 'menu' / "civs"
    civs_dst = Path(__file__).parent.resolve().parent / 'img' / 'civs'
    print(f'Copying {civs_src} → {civs_dst}')
    shutil.copytree(civs_src, civs_dst, dirs_exist_ok=True)
    if (tmp_file := (civs_dst / "indians.png")).exists():
        shutil.copy2(tmp_file, civs_dst / "hindustanis.png")

    techtree_src = base_path.parent / 'menu' / "techtree"
    techtree_dst = Path(__file__).parent.resolve().parent / 'img' / 'techtree'
    print(f'Copying {techtree_src} → {techtree_dst}')
    shutil.copytree(techtree_src, techtree_dst, dirs_exist_ok=True)


def process_dds(source_dds: Path, target_file: Path, resize: bool) -> tuple[int, int]:
    assert source_dds.is_file()
    print(f'Converting {source_dds} → {target_file}')
    with Image.open(source_dds) as im:
        r, g, b, a = im.split()

        rgb = Image.merge("RGB", (r, g, b))
        rgb.putalpha(255)

        overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))

        w, h = im.size
        for x in range(w):
            for y in range(h):
                grayscalevalue = rgb.getpixel((x, y))
                overlay.putpixel((x, y), scale(grayscalevalue))

        composite = Image.composite(rgb, overlay, a)
        if resize:
            composite = composite.resize(TARGET_SIZE, resample=Resampling.BICUBIC)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        composite.save(target_file)
        return composite.size


if __name__ == '__main__':
    main()
