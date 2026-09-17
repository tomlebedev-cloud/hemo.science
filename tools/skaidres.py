"""Išrenka skaidrių kadrus iš video: kada vaizdas pasikeičia, toks kadras ir išsaugomas.

Veikia dviem žingsniais:
 1. ffmpeg išveda po vieną mažą pilką kadrą kas N sekundžių (pigu),
    Python palygina gretimus kadrus ir randa pokyčio momentus;
 2. tik tuos momentus ffmpeg iškerpa pilna raiška.

Jautrumas valdomas --riba (kuo mažesnė, tuo daugiau kadrų).

Paleidimas: python tools/skaidres.py [--nr 10 13] [--zingsnis 8] [--riba 6.0] [--perdaryti]
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'konspektavimas'
PRES = ROOT.parent / 'DS' / 'PRESENTATIONS'
W, H = 160, 90

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='replace')


def video_path(folder):
    txt = (folder / 'info.md').read_text(encoding='utf-8')
    m = re.search(r'\*\*Šaltinis:\*\* Video failas: `([^`]+)`', txt)
    return PRES.parent / m.group(1) if m else None


def coarse_frames(video, step):
    """Grąžina mažų pilkų kadrų sąrašą (bytes) kas `step` sekundžių."""
    proc = subprocess.run(
        ['ffmpeg', '-v', 'error', '-skip_frame', 'nokey', '-i', str(video), '-an',
         '-vf', f'fps=1/{step},scale={W}:{H},format=gray', '-f', 'rawvideo', 'pipe:'],
        capture_output=True)
    raw, size = proc.stdout, W * H
    return [raw[i:i + size] for i in range(0, len(raw) - size + 1, size)]


def diff(a, b):
    """Vidutinis pikselių skirtumas 0–255."""
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def cut(video, sec, dest):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(sec), '-i', str(video),
                    '-frames:v', '1', '-vf', "scale='min(1600,iw)':-2", '-q:v', '3', str(dest)],
                   check=True)


def process(folder, step, riba, redo):
    video = video_path(folder)
    if not video or not video.exists():
        return None
    sdir = folder / 'skaidres'
    if sdir.exists() and any(sdir.glob('*.jpg')):
        if not redo:
            return len(list(sdir.glob('*.jpg')))
        for f in sdir.glob('*.jpg'):
            f.unlink()
    sdir.mkdir(exist_ok=True)

    frames = coarse_frames(video, step)
    if not frames:
        return 0
    moments = [step // 2]
    prev = frames[0]
    for i, f in enumerate(frames[1:], 1):
        if diff(prev, f) >= riba:
            moments.append(i * step + 1)
            prev = f
    for sec in moments:
        cut(video, sec, sdir / f'{sec // 3600:01d}-{sec % 3600 // 60:02d}-{sec % 60:02d}.jpg')
    return len(moments)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--nr', nargs='*', type=int)
    ap.add_argument('--zingsnis', type=int, default=8, help='sekundės tarp tikrinamų kadrų')
    ap.add_argument('--riba', type=float, default=6.0, help='pokyčio riba 0–255')
    ap.add_argument('--perdaryti', action='store_true')
    args = ap.parse_args()

    folders = [f for f in sorted(OUT.iterdir()) if f.is_dir()]
    if args.nr:
        folders = [f for f in folders if int(f.name[:2]) in args.nr]
    for folder in folders:
        n = process(folder, args.zingsnis, args.riba, args.perdaryti)
        if n is not None:
            print(f'{folder.name[:60]:60} kadrų: {n}', flush=True)


if __name__ == '__main__':
    main()
