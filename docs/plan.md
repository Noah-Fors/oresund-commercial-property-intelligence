# Öresund Commercial Property Intelligence Platform — Fasplan

**Ett portfolioprojekt som kombinerar geospatial analys (lantmäteri), fastighetsvärdering (fastighetsekonomi) och dataverktyg — riktat mot roller inom fastighetsrådgivning och transaktionsrådgivning (t.ex. Savills, CBRE, JLL).**

## Målbild

Bygga en interaktiv analysplattform som efterliknar arbetsflödet hos en junior analytiker på en internationell fastighetsrådgivningsfirma: hitta och poängsätta fastigheter geografiskt, värdera dem enligt branschstandard, och sammanställa marknadsdata i en läsbar rapport.

Slutresultat: en publik GitHub-repo + en körbar webbdemo (Streamlit) + en kort PDF-marknadsrapport genererad av verktyget självt.

## Fas 1 — Geospatial location scoring (2–3 veckor)

**Mål:** poängsätta fastigheter i Malmö/Lund/Helsingborg baserat på läge.

1. Skapa konto och API-nyckel hos Lantmäteriets öppna dataportal (opendata.lantmateriet.se) — gratis, CC0-licens.
2. Hämta byggnadsregister, adresser och ortofoton för Öresundsregionen via API:et.
3. Komplettera med öppen pendlings-/befolkningsdata från SCB för att identifiera arbetsplatskoncentrationer.
4. Bygg en enkel "location score" per fastighet i Python (GeoPandas) baserat på:
   - Avstånd till närmaste kollektivtrafiknod
   - Närhet till arbetsplatskoncentrationer
   - Täthet av kommersiell verksamhet i närområdet
5. Visualisera resultatet som en interaktiv karta (Folium eller Kepler.gl).

**Leverabel:** en karta där man kan klicka på ett område i Malmö/Lund/Helsingborg och se dess location score.

## Fas 2 — Värderingsmotor (2 veckor)

**Mål:** implementera en riktig fastighetsekonomisk värderingsmodell, inte bara en ML-prediktion.

1. Implementera avkastningsmetoden (yield-baserad värdering) — standardmetoden för kommersiella fastigheter.
2. Bygg in justerbara antaganden i verktyget:
   - Direktavkastningskrav
   - Vakansgrad
   - Hyresnivå per kvm
3. Låt användaren ändra antagandena interaktivt och se hur fastighetsvärdet förändras (enkel känslighetsanalys/DCF).
4. Koppla ihop med Fas 1 så att location score kan påverka rimligt avkastningskrav (bättre läge → lägre yield-antagande).

**Leverabel:** en modul där man matar in en fastighets grunddata och antaganden, och får ut ett estimerat marknadsvärde med känslighetsanalys.

## Fas 3 — Marknadsdashboard och rapport (3–4 veckor)

**Mål:** sammanställa marknadsdata till något som liknar en professionell "market report".

1. Samla offentligt tillgängliga uthyrningsannonser (t.ex. Objektvision, Locatia) för kommersiella lokaler i regionen.
2. Bygg en egen liten databas över hyresnivåer per delområde.
3. Generera automatiskt grafer över hyrestrend, vakansgrad och transaktionsvolym per stadsdel.
4. Exportera en kort PDF-rapport i stil med de marknadsrapporter rådgivningsfirmor publicerar kvartalsvis.

**Leverabel:** en genererad PDF-rapport ("Öresund Commercial Property Market Snapshot") som kan bifogas i ansökningar.

## Teknisk stack

- **Python:** pandas, GeoPandas
- **Geodata:** Lantmäteriets öppna API
- **Visualisering:** Folium / Kepler.gl, Plotly/Matplotlib
- **Interaktiv app:** Streamlit (enkel att hosta gratis via Streamlit Cloud)
- **Version control:** GitHub, med tydlig README och dokumenterad metodik

## Hur projektet används i ansökningar

- Länka GitHub-repo och den publicerade Streamlit-demon i CV och LinkedIn.
- Referera projektet konkret i personliga brev/mejl: *"Jag byggde ett verktyg som efterliknar en junior analysts arbetsflöde inom fastighetsvärdering och marknadsanalys."*
- Ha PDF-marknadsrapporten redo att bifoga eller visa upp i en intervju som konkret exempel på analytisk förmåga.
- Uppdatera GitHub-portfolion parallellt med det befintliga bostadsprisprediktionsprojektet — de kompletterar varandra (bostäder vs. kommersiellt, ren ML-prediktion vs. branschstandard-värdering).

## Tidslinje (ungefärlig, deltid vid sidan av studier)

| Fas | Innehåll | Tid |
|---|---|---|
| 1 | Geospatial location scoring | 2–3 veckor |
| 2 | Värderingsmotor | 2 veckor |
| 3 | Marknadsdashboard + rapport | 3–4 veckor |
| **Totalt** | | **7–9 veckor** |
