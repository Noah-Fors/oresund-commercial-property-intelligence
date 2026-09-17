# Data

Rådata och bearbetad data checkas inte in i git (se `.gitignore`).

- `raw/` — ohanterad data hämtad från Lantmäteriet, SCB och annonssajter (Objektvision, Locatia m.fl.).
- `processed/` — rensade/sammanslagna dataset som används av `src/`-modulerna.

Instruktioner för hur varje dataset hämtas läggs till i respektive fasmodul under `src/` allt eftersom de byggs.
