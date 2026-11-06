# Data

Rådata och bearbetad data checkas inte in i git (se `.gitignore`).

- `raw/` — ohanterad data hämtad från Lantmäteriet, SCB och annonssajter (Objektvision, Locatia m.fl.).
- `processed/` — rensade/sammanslagna dataset som används av `src/`-modulerna.
- `sample/` — exempeldata för Fas 1 och 2 (fastigheter, stationer, trafikplatser, OpenStreetMap-räkningar). Checkas in.
- `market/` — handinsamlade marknadsdata för Fas 3 (`office_market_data.xlsx`). Checkas in. Se `docs/fas3_insamling.md`.

Instruktioner för hur varje dataset hämtas läggs till i respektive fasmodul under `src/` allt eftersom de byggs.

## Licensierad data (MSCI Property Intel)

Data från MSCI Property Intel (tidigare Datscha) används via Lunds tekniska högskolas licens och får inte publiceras.

- Lägg exporter och utdrag **endast** i `data/raw/`, som inte checkas in i git.
- I repot får bara egna beräkningar och sammanställningar finnas, till exempel en median eller ett intervall, med källan angiven.
- Kopiera aldrig enskilda transaktioner, hyresgäster eller ägaruppgifter till filer som checkas in.
