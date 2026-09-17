"""Atsisiunčia garsą iš YouTube tiems pranešimams, kurių vietinio video failo nėra.

Naudoja yt-dlp (reikia JavaScript vykdyklės – Deno) ir įrašo garsas.mp3 (mono, 16 kHz, 48 kbps)
į atitinkamą konspektavimo aplanką. Privatūs video neatsisiunčia – juos pirma reikia
pakeisti į „Neįtrauktas į sąrašą“ (unlisted).

Paleidimas: python tools/atsisiusti_garsa.py [--nr 1 2 3]
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'konspektavimas'
VENV = Path(os.environ['LOCALAPPDATA']) / 'hemo-science' / 'venv' / 'Scripts'
YTDLP = VENV / 'yt-dlp.exe'
DENO_DIR = Path(os.environ['LOCALAPPDATA']) / 'Microsoft' / 'WinGet' / 'Packages' / \
    'DenoLand.Deno_Microsoft.Winget.Source_8wekyb3d8bbwe'

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='replace')


def link(folder):
    txt = (folder / 'info.md').read_text(encoding='utf-8')
    m = re.search(r'\*\*YouTube:\*\* (https?://\S+)', txt)
    return m.group(1) if m else None


def download(url, folder):
    env = dict(os.environ, PATH=f'{DENO_DIR};{os.environ["PATH"]}')
    proc = subprocess.run(
        [str(YTDLP), '--remote-components', 'ejs:github', '--no-warnings', '--no-playlist',
         '-f', 'bestaudio/best', '-x', '--audio-format', 'mp3', '--audio-quality', '48K',
         '--postprocessor-args', 'ExtractAudio:-ac 1 -ar 16000',
         '-o', str(folder / 'garsas.%(ext)s'), url],
        capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
    if proc.returncode == 0 and (folder / 'garsas.mp3').exists():
        return True, f'{(folder / "garsas.mp3").stat().st_size / 2**20:.0f} MB'
    err = [l for l in proc.stderr.splitlines() if l.startswith('ERROR')]
    return False, (err[-1][:120] if err else 'nepavyko')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--nr', nargs='*', type=int)
    args = ap.parse_args()

    folders = [f for f in sorted(OUT.iterdir()) if f.is_dir() and not (f / 'garsas.mp3').exists()]
    if args.nr:
        folders = [f for f in folders if int(f.name[:2]) in args.nr]

    ok = fail = skip = 0
    for folder in folders:
        url = link(folder)
        if not url:
            print(f'{folder.name[:55]:55} – nuorodos nėra', flush=True)
            skip += 1
            continue
        good, msg = download(url, folder)
        print(f'{folder.name[:55]:55} {"✓ " + msg if good else "✗ " + msg}', flush=True)
        ok, fail = ok + good, fail + (not good)
    print(f'\nAtsisiųsta: {ok}, nepavyko: {fail}, be nuorodos: {skip}')


if __name__ == '__main__':
    main()
