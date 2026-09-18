"""Sujungia dvi tos pačios įrašo transkripcijas skirtingomis kalbomis (pvz. lt ir en).

Konferencijose kalbama keliomis kalbomis; nustačius vieną kalbą, kitos kalbos atkarpos
virsta beprasmiu pasikartojančiu tekstu. Šis skriptas eina per pagrindinę transkripciją
ir kiekvieną sugadintą eilutę pakeičia antrosios kalbos eilutėmis iš to paties laiko lango.

Paleidimas: python tools/sujungti_kalbas.py --nr 22 34 [--antra .en]
Rezultatas: transkripcija.txt (sujungta); originalas išsaugomas kaip transkripcija.lt.txt
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

LINE = re.compile(r'\[([\d:]+)\]\s*(.*)')


def secs(stamp):
    p = [int(x) for x in stamp.split(':')]
    while len(p) < 3:
        p.insert(0, 0)
    return p[0] * 3600 + p[1] * 60 + p[2]


def parse(path):
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        m = LINE.match(line)
        if m:
            rows.append((secs(m.group(1)), m.group(1), m.group(2)))
    return rows


def garbage(text):
    """Ar eilutė yra pasikartojantis „haliucinacijos“ tekstas."""
    words = re.findall(r'\w+', text.lower())
    if len(words) < 6:
        return False
    uniq = len(set(words)) / len(words)
    # dažniausio žodžio dalis
    top = max(words.count(w) for w in set(words)) / len(words)
    return uniq < 0.35 or top > 0.3


def merge(folder, second):
    main_p = folder / 'transkripcija.txt'
    orig_p = folder / 'transkripcija.lt.txt'
    sec_p = folder / f'transkripcija{second}.txt'
    if not sec_p.exists():
        return None
    if not orig_p.exists():
        orig_p.write_text(main_p.read_text(encoding='utf-8'), encoding='utf-8')
    main, sec = parse(orig_p), parse(sec_p)
    out, replaced, used = [], 0, set()
    for i, (t, stamp, text) in enumerate(main):
        if not garbage(text):
            out.append((t, stamp, text))
            continue
        t_end = main[i + 1][0] if i + 1 < len(main) else t + 60
        cand = [(ts, st, tx) for j, (ts, st, tx) in enumerate(sec)
                if t - 2 <= ts < t_end and j not in used and not garbage(tx)]
        for j, row in enumerate(sec):
            if row in cand:
                used.add(j)
        if cand:
            out.extend(cand)
            replaced += 1
        # jei ir antroje kalboje nieko gero — eilutė praleidžiama
    out.sort(key=lambda r: r[0])
    main_p.write_text('\n'.join(f'[{st}] {tx}' for _, st, tx in out) + '\n', encoding='utf-8')
    bad = sum(1 for r in main if garbage(r[2]))
    return len(main), bad, replaced, len(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--nr', nargs='+', type=int, required=True)
    ap.add_argument('--antra', default='.en')
    args = ap.parse_args()
    for f in sorted(OUT.iterdir()):
        if f.is_dir() and int(f.name[:2]) in args.nr:
            r = merge(f, args.antra)
            if r:
                print(f'{f.name[:50]}: eilučių {r[0]}, sugadintų {r[1]}, pakeista {r[2]}, rezultate {r[3]}')
            else:
                print(f'{f.name[:50]}: nėra antros kalbos failo')


if __name__ == '__main__':
    main()
