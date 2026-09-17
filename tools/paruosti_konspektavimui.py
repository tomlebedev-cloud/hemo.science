"""Paruošia konspektavimo medžiagą kiekvienam pranešimui.

Kiekvienam pranešimui sukuria aplanką konspektavimas/NN YYYY Tema/ su:
  info.md          – metaduomenys (tema, data, kalba, trukmė, nuoroda, šaltinis)
  garsas.mp3       – garso takelis transkripcijai (mono, 16 kHz, 48 kbps)
  skaidres/        – kadrai, kai keičiasi vaizdas (pavadinimas = laikas mm-ss)
Ir bendrą konspektavimas/SARASAS.md su būsena.

Paleidimas: python tools/paruosti_konspektavimui.py [--tik-info]
"""
import re
import subprocess
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
PRES = ROOT.parent / 'DS' / 'PRESENTATIONS'
XLSX = PRES / 'Pranešimų sąrašas 2026-09-17.xlsx'
OUT = ROOT / 'konspektavimas'
VIDEO_DIRS = [PRES / 'Video', PRES / 'Trombozės dienos']


def slug(text, n=70):
    t = re.sub(r'[\\/:*?"<>|„“”]', '', text)
    t = re.sub(r'\s+', ' ', t).strip().rstrip('.…')
    return t[:n].rstrip()


def hms(sec):
    if not sec:
        return ''
    return f'{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}'


def find_video(name):
    if not name:
        return None
    for d in VIDEO_DIRS:
        p = d / name
        if p.exists():
            return p
    return None


def load():
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws, ps = wb['Pranešimai'], wb['Puslapiui']
    page = {r[0]: r for r in ps.iter_rows(min_row=2, values_only=True) if isinstance(r[0], int)}
    items = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not isinstance(r[0], int):
            continue
        p = page[r[0]]
        dur = p[8]
        items.append({
            'nr': r[0], 'title': r[2], 'year': p[1], 'date': p[2], 'category': p[5],
            'lang': r[3], 'slides': p[7], 'duration': int(dur.total_seconds()) if dur else None,
            'link': r[6], 'file': find_video(r[7]), 'file_name': r[7], 'visibility': p[10],
        })
    return items


def write_info(it, folder):
    src = f'Video failas: `{it["file"].relative_to(PRES.parent)}`' if it['file'] else (
        f'Tik YouTube ({it["visibility"]}) – garsą reikia atsisiųsti' if it['link'] else 'Šaltinio nėra')
    date = it['date'].strftime('%Y-%m-%d') if it['date'] else (str(it['year']) if it['year'] else 'nežinoma')
    lines = [
        f'# {it["title"]}',
        '',
        f'- **Nr.:** {it["nr"]} (Excel lapas „Pranešimai“)',
        '- **Pranešėjas:** prof. dr. Julius Ptašekas' + (' ir kiti (konferencija)' if 'Trombozės dienos' in it['title'] else ''),
        f'- **Data:** {date}',
        f'- **Tema:** {it["category"]}',
        f'- **Skaitymo kalba:** {it["lang"] or "nežinoma"}',
        f'- **Skaidrių kalba:** {it["slides"] or "nežinoma"}',
        f'- **Trukmė:** {hms(it["duration"]) or "nežinoma"}',
        f'- **YouTube:** {it["link"] or "nėra"}',
        f'- **Šaltinis:** {src}',
        '',
    ]
    (folder / 'info.md').write_text('\n'.join(lines), encoding='utf-8')


def extract_audio(video, folder):
    out = folder / 'garsas.mp3'
    if out.exists() and out.stat().st_size > 0:
        return 'yra'
    tmp = folder / 'garsas.tmp.mp3'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-vn', '-ac', '1', '-ar', '16000',
                    '-b:a', '48k', str(tmp)], check=True)
    tmp.replace(out)
    return 'išgauta'


def extract_slides(video, folder):
    sdir = folder / 'skaidres'
    if sdir.exists() and any(sdir.glob('*.jpg')):
        return len(list(sdir.glob('*.jpg')))
    sdir.mkdir(exist_ok=True)
    # tik raktiniai kadrai + scenos pokytis; showinfo išveda kiekvieno kadro laiką
    proc = subprocess.run(
        ['ffmpeg', '-hide_banner', '-skip_frame', 'nokey', '-i', str(video), '-an',
         '-vf', "select='eq(n\\,0)+gt(scene\\,0.22)',scale='min(1600,iw)':-2,showinfo",
         '-fps_mode', 'vfr', '-q:v', '3', str(sdir / 'k%05d.jpg')],
        capture_output=True, text=True, encoding='utf-8', errors='replace')
    times = [float(t) for t in re.findall(r'pts_time:([\d.]+)', proc.stderr)]
    files = sorted(sdir.glob('k*.jpg'))
    for f, t in zip(files, times):
        s = int(t)
        f.rename(sdir / f'{s // 3600:01d}-{s % 3600 // 60:02d}-{s % 60:02d}.jpg')
    return len(files)


def main():
    only_info = '--tik-info' in sys.argv
    OUT.mkdir(exist_ok=True)
    items = load()
    rows = []
    for it in items:
        folder = OUT / f'{it["nr"]:02d} {it["year"] or "xxxx"} {slug(it["title"])}'
        folder.mkdir(exist_ok=True)
        write_info(it, folder)
        audio = slides = ''
        if it['file'] and not only_info:
            print(f'[{it["nr"]:02d}] {it["file"].name}', flush=True)
            audio = extract_audio(it['file'], folder)
            slides = extract_slides(it['file'], folder)
            print(f'     garsas: {audio}, skaidrių kadrai: {slides}', flush=True)
        has_audio = (folder / 'garsas.mp3').exists()
        n_slides = len(list((folder / 'skaidres').glob('*.jpg'))) if (folder / 'skaidres').exists() else 0
        has_tr = any(folder.glob('transkripcija*.txt'))
        rows.append((it, folder.name, has_audio, n_slides, has_tr))

    md = ['# Konspektavimo medžiaga', '',
          '| Nr. | Metai | Tema | Trukmė | Šaltinis | Garsas | Skaidrės | Transkripcija |',
          '|---:|---|---|---:|---|:-:|---:|:-:|']
    for it, name, a, s, t in rows:
        src = 'failas' if it['file'] else ('YouTube' if it['link'] else '—')
        md.append(f'| {it["nr"]} | {it["year"] or ""} | [{slug(it["title"], 80)}](<{name}/info.md>) | '
                  f'{hms(it["duration"])} | {src} | {"✓" if a else ""} | {s or ""} | {"✓" if t else ""} |')
    md += ['', f'Iš viso: {len(rows)} pranešimų; garsas paruoštas {sum(r[2] for r in rows)}, '
               f'transkripcija {sum(r[4] for r in rows)}.', '']
    (OUT / 'SARASAS.md').write_text('\n'.join(md), encoding='utf-8')
    print('SARASAS.md atnaujintas')


if __name__ == '__main__':
    main()
