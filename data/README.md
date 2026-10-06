# Data

Rådata och bearbetad data checkas inte in i git (se `.gitignore`).

- `raw/` — ohanterad data hämtad från Lantmäteriet, SCB och annonssajter (Objektvision, Locatia m.fl.).
- `processed/` — rensade/sammanslagna dataset som används av `src/`-modulerna.
- `sample/` — exempeldata för Fas 1 och 2 (fastigheter, stationer, trafikplatser, OpenStreetMap-räkningar). Checkas in.
- `market/` — handinsamlade marknadsdata för Fas 3 (`office_market_data.xlsx`). Checkas in. Se `docs/fas3_insamling.md`.

Instruktioner för hur varje dataset hämtas läggs till i respektive fasmodul under `src/` allt eftersom de byggs.
