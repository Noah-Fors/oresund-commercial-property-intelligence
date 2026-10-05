# Öresund Commercial Property Intelligence Platform

Ett portfolioprojekt som kombinerar geospatial analys (lantmäteri), fastighetsvärdering (fastighetsekonomi) och dataverktyg — riktat mot roller inom fastighetsrådgivning och transaktionsrådgivning (t.ex. Savills, CBRE, JLL).

## Målbild

Bygga en interaktiv analysplattform som efterliknar arbetsflödet hos en junior analytiker på en internationell fastighetsrådgivningsfirma: hitta och poängsätta fastigheter geografiskt, värdera dem enligt branschstandard, och sammanställa marknadsdata i en läsbar rapport.

Slutresultat: en publik GitHub-repo + en körbar webbdemo (Streamlit) + en kort PDF-marknadsrapport genererad av verktyget självt.

Se [docs/plan.md](docs/plan.md) för den fullständiga fasplanen.

## Faser

| Fas | Innehåll | Tid | Status |
|---|---|---|---|
| 1 | Geospatial location scoring | 2–3 veckor | ✅ Exempeldata, karta och viktat location score (arbetsplatsdata saknas) |
| 2 | Värderingsmotor (DCF kontrakt för kontrakt) | 2 veckor | ✅ DCF, location score → yield, känslighetsmatris, Monte Carlo |
| 3 | Marknadsdashboard + PDF-rapport | 3–4 veckor | 🔲 Ej påbörjad |

## Teknisk stack

- **Python:** pandas, GeoPandas
- **Geodata:** [Lantmäteriets öppna API](https://www.lantmateriet.se/sv/geodata/vara-oppna-data/) (opendata.lantmateriet.se, CC0)
- **Befolknings-/pendlingsdata:** SCB (öppna data)
- **Visualisering:** Folium / Kepler.gl, Plotly/Matplotlib
- **Interaktiv app:** Streamlit (hostas via Streamlit Cloud)
- **Version control:** GitHub

## Projektstruktur

```
├── data/
│   ├── raw/            # Ohanterad data från Lantmäteriet/SCB/annonser
│   └── processed/       # Rensade/bearbetade dataset
├── docs/
│   └── plan.md          # Fullständig fasplan
├── notebooks/           # Utforskande analys
├── src/
│   ├── phase1_location_scoring/   # Fas 1: geospatial poängsättning
│   ├── phase2_valuation/          # Fas 2: värderingsmotor
│   └── phase3_market_report/      # Fas 3: marknadsdashboard + rapport
└── streamlit_app.py      # Appens startpunkt
```

## Kom igång

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Hur projektet används i ansökningar

- Länka GitHub-repo och den publicerade Streamlit-demon i CV och LinkedIn.
- Referera projektet konkret i personliga brev/mejl.
- Ha PDF-marknadsrapporten redo att visa upp i en intervju som konkret exempel på analytisk förmåga.
- Kompletterar ett eventuellt bostadsprisprediktionsprojekt (bostäder vs. kommersiellt, ML-prediktion vs. branschstandard-värdering).
