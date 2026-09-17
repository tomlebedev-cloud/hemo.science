# hemo.science

Prof. dr. Juliaus Ptašeko pranešimų archyvas: hemostazė, krešėjimo sistemos biožymenys,
venų tromboembolija, antikoaguliantų ir antiagregantų terapijos kontrolė.

Statinis puslapis (HTML, CSS, JS be priklausomybių), talpinamas GitHub Pages.

## Struktūra

- `index.html` – puslapis
- `assets/style.css`, `assets/app.js` – išvaizda, filtrai, grotuvas
- `data/pranesimai.json` – pranešimų sąrašas
- `tools/build_data.py` – JSON generavimas iš Excel sąrašo (lapas „Puslapiui“)

## Sąrašo atnaujinimas

```bash
python tools/build_data.py "kelias/iki/Pranešimų sąrašas.xlsx"
```

Be argumento skaitomas `../DS/PRESENTATIONS/Pranešimų sąrašas 2026-09-17.xlsx`.

## Vietinė peržiūra

```bash
python -m http.server 8117
```

Video rodomi per `youtube-nocookie.com`. Privatūs YouTube video puslapyje neatsidaro –
jiems reikia matomumo „Neįtrauktas į sąrašą“ (unlisted).
