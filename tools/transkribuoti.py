"""Transkribuoja konspektavimo aplankų garsą su faster-whisper (lokaliai, be interneto).

Kiekviename konspektavimas/*/ aplanke, kur yra garsas.mp3 ir dar nėra transkripcija.txt,
sukuria transkripcija.txt (su [mm:ss] žymomis) ir transkripcija.srt.

Paleidimas (venv python'u):
  python tools/transkribuoti.py [--modelis large-v3-turbo] [--nr 7 12] [--nuo-trumpiausio]
"""
import argparse
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'konspektavimas'

LANG = {'Lietuvių': 'lt', 'Anglų': 'en', 'Rusų': 'ru', 'Ukrainiečių': 'uk'}

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='replace')


def info_lang(folder):
    txt = (folder / 'info.md').read_text(encoding='utf-8')
    m = re.search(r'\*\*Skaitymo kalba:\*\* (.+)', txt)
    return LANG.get((m.group(1).strip() if m else ''), None)


def stamp(sec, srt=False):
    h, m, s = int(sec // 3600), int(sec % 3600 // 60), sec % 60
    if srt:
        return f'{h:02d}:{m:02d}:{int(s):02d},{int((s % 1) * 1000):03d}'
    return f'{h}:{m:02d}:{int(s):02d}' if h else f'{m:02d}:{int(s):02d}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modelis', default='large-v3-turbo')
    ap.add_argument('--nr', nargs='*', type=int, help='tik šie pranešimų numeriai')
    ap.add_argument('--nuo-trumpiausio', action='store_true')
    ap.add_argument('--praleisti', nargs='*', type=int, default=[], help='šių numerių netranskribuoti')
    ap.add_argument('--greitas', action='store_true',
                    help='beam_size=1 ir paketinis apdorojimas – greičiau, šiek tiek prasčiau')
    ap.add_argument('--paketas', type=int, default=8, help='paketo dydis su --greitas')
    args = ap.parse_args()

    folders = [f for f in sorted(OUT.iterdir()) if f.is_dir() and (f / 'garsas.mp3').exists()]
    if args.nr:
        folders = [f for f in folders if int(f.name[:2]) in args.nr]
    if args.praleisti:
        folders = [f for f in folders if int(f.name[:2]) not in args.praleisti]
    folders = [f for f in folders if not (f / 'transkripcija.txt').exists()]
    if args.nuo_trumpiausio:
        folders.sort(key=lambda f: (f / 'garsas.mp3').stat().st_size)
    if not folders:
        print('Nėra ko transkribuoti.')
        return

    from faster_whisper import WhisperModel
    print(f'Kraunamas modelis {args.modelis} (pirmą kartą siunčiamas ~1,6 GB)...', flush=True)
    model = WhisperModel(args.modelis, device='cpu', compute_type='int8',
                         cpu_threads=max(1, (os.cpu_count() or 4) - 1))
    runner = model
    if args.greitas:
        from faster_whisper import BatchedInferencePipeline
        runner = BatchedInferencePipeline(model=model)

    for i, folder in enumerate(folders, 1):
        lang = info_lang(folder)
        audio = folder / 'garsas.mp3'
        mb = audio.stat().st_size / 2 ** 20
        print(f'\n[{i}/{len(folders)}] {folder.name}  ({mb:.0f} MB, kalba: {lang or "auto"})', flush=True)
        t0 = time.time()
        kwargs = dict(language=lang, vad_filter=True, condition_on_previous_text=False,
                      beam_size=1 if args.greitas else 5,
                      vad_parameters={'min_silence_duration_ms': 700})
        if args.greitas:
            kwargs['batch_size'] = args.paketas
        segments, info = runner.transcribe(str(audio), **kwargs)
        txt, srt = [], []
        for n, seg in enumerate(segments, 1):
            line = seg.text.strip()
            if not line:
                continue
            txt.append(f'[{stamp(seg.start)}] {line}')
            srt.append(f'{n}\n{stamp(seg.start, True)} --> {stamp(seg.end, True)}\n{line}\n')
            if n % 25 == 0:
                print(f'   ... {stamp(seg.start)}', flush=True)
        (folder / 'transkripcija.txt').write_text('\n'.join(txt) + '\n', encoding='utf-8')
        (folder / 'transkripcija.srt').write_text('\n'.join(srt), encoding='utf-8')
        mins = (time.time() - t0) / 60
        print(f'   baigta per {mins:.1f} min., {len(txt)} eilučių, aptikta kalba: {info.language}', flush=True)


if __name__ == '__main__':
    sys.exit(main())
