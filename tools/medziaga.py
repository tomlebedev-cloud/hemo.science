"""Sudeda konspektuotiną medžiagą: metaduomenys + transkripcija su skaidrėmis pagal laiką.

Kiekviename konspektavimo aplanke sukuria medziaga.md, kuriame skaidrės įterptos
toje vietoje, kur jos pasirodo įraše. Atidarius Markdown peržiūroje matyti ir tekstas,
ir skaidrė, prie kurios tas tekstas kalbamas.

Paleidimas: python tools/medziaga.py [--nr 10 13]
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'konspektavimas'

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='replace')


def secs(stamp):
    p = [int(x) for x in stamp.split(':')]
    while len(p) < 3:
        p.insert(0, 0)
    return p[0] * 3600 + p[1] * 60 + p[2]


def slide_seconds(name):
    """Kadro laikas iš pavadinimo h-mm-ss.jpg; kitokie pavadinimai atmetami."""
    m = re.fullmatch(r'(\d+)-(\d{2})-(\d{2})', name.stem)
    if not m:
        return None
    h, mi, s = (int(x) for x in m.groups())
    return h * 3600 + mi * 60 + s


def build(folder):
    tr = folder / 'transkripcija.txt'
    if not tr.exists():
        return None
    info = (folder / 'info.md').read_text(encoding='utf-8').strip()
    lines = [l for l in tr.read_text(encoding='utf-8').splitlines() if l.strip()]
    slides = []
    if (folder / 'skaidres').exists():
        slides = sorted((p for p in (folder / 'skaidres').glob('*.jpg') if slide_seconds(p) is not None),
                        key=slide_seconds)

    out = [info, '', '---', '']
    if slides:
        out += [f'Skaidrių kadrai: {len(slides)}. Laikai nurodyti prie kiekvienos.', '']
    si = 0
    for line in lines:
        m = re.match(r'\[([\d:]+)\]\s*(.*)', line)
        t, text = (secs(m.group(1)), m.group(2)) if m else (None, line)
        while si < len(slides) and t is not None and slide_seconds(slides[si]) <= t:
            s = slides[si]
            out += ['', f'![Skaidrė {s.stem}](skaidres/{s.name})', '', f'*Skaidrė {s.stem}*', '']
            si += 1
        out.append(f'**[{m.group(1)}]** {text}' if m else line)
    for s in slides[si:]:
        out += ['', f'![Skaidrė {s.stem}](skaidres/{s.name})', '', f'*Skaidrė {s.stem}*', '']

    (folder / 'medziaga.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
    return len(lines), len(slides)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--nr', nargs='*', type=int)
    args = ap.parse_args()
    folders = [f for f in sorted(OUT.iterdir()) if f.is_dir()]
    if args.nr:
        folders = [f for f in folders if int(f.name[:2]) in args.nr]
    done = 0
    for f in folders:
        r = build(f)
        if r:
            done += 1
            print(f'{f.name[:58]:58} eilučių: {r[0]:4d}, skaidrių: {r[1]:3d}', flush=True)
    print(f'\nParuošta medziaga.md: {done}')


if __name__ == '__main__':
    main()
