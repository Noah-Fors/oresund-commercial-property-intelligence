# Fas 3 — Insamling av kontorsdata

All data samlas för hand i `data/market/office_market_data.xlsx`. Arbetsboken har tre flikar:

| Flik | Innehåll | En rad = |
|---|---|---|
| Instruktioner | Reglerna nedan i kortform | – |
| Nyckeltal | Siffror ur publicerade marknadsrapporter | ett nyckeltal för ett delområde |
| Annonser | Lediga kontorslokaler från annonssajter | en lokal |

Håll muspekaren över en rubrik i Excel för att se vad kolumnen ska innehålla.

## Steg 1 — Nyckeltal ur marknadsrapporter

### Nyckeltalen

| metric | Enhet | Betydelse |
|---|---|---|
| `prime_rent` | kr/kvm/år | Hyran för de bästa lokalerna i det bästa läget. Ett tak, inte ett snitt. |
| `rent_range` | kr/kvm/år | Normalt hyresintervall i ett delområde eller en lägesklass (A/B/C). |
| `vacancy_rate` | % | Andel av kontorsbeståndet (kvm) som står ledig. |
| `prime_yield` | % | Direktavkastningskravet för de bästa fastigheterna. Motsvarar basyielden i Fas 2. |
| `take_up` | kvm | Uthyrd yta under perioden. Mäter efterfrågan. |
| `transaction_volume` | Mkr | Köp och försäljningar av fastigheter under perioden. Mäter investerarnas aktivitet. |

### Segment

Varje nyckeltal gäller ett segment: `office` (kontor), `retail` (butik) eller `industrial` (industri, lager och logistik). Rapporten fokuserar på kontor, men hyresnivåer för butik och industri samlas också in, eftersom de används för att kontrollera Fas 2:s antagna marknadshyror för alla fastighetstyper.

Hyrorna skiljer sig kraftigt mellan segmenten, eftersom hyresgästerna betalar för olika saker. Kontor: tillgänglighet för de anställda och byggnadens standard. Butik: kundflöde, som kan skilja sig mycket på några meter. Industri: stora, enkla ytor och närhet till motorväg. Lägesklasserna definieras olika per segment, så de går inte att jämföra rakt av mellan segmenten.

### Datum

| Källan anger | Skriv i published |
|---|---|
| Ett exakt datum | Det datumet |
| Ett kvartal, t.ex. "Q2 2026" | Kvartalets sista dag: `2026-06-30` |
| Bara ett år, eller "uppdateras löpande" | Datumet du läste sidan, och årtalet i source |

### Var siffrorna finns

- **Objektvision, Marknadsstatistik, Hyresnivåer:** hyresintervall per lägesklass (AA/A/B/C) för kontor, butik och industri, bland annat i Malmö, Lund och Helsingborg. Siffrorna kommer från Newsec. Detta är den enda källan som täcker alla tre städerna.
- **Cushman & Wakefield, MarketBeat och Office Snapshot Sweden:** prime rent, vacancy och prime yield för Malmö CBD, kvartalsvis.
- **JLL, Nordic Office Insight:** prime rent och prime yield för de nordiska huvudstäderna och Malmö, halvårsvis.
- **Citymark:** vakansgrad för Malmös kontorsmarknad per delområde, två gånger per år.
- **SEPREF (Samhällsbyggarna):** konsensusprognos för prime yield, bland annat för Malmö.
- **Rådgivningsfirmor som Savills, Newsec och Colliers:** publicerar också rapporter om Sverige, men de täcker oftast bara Stockholm, Göteborg och Malmö.

Rapporterna är ofta PDF-filer på engelska. Nyckeltalen brukar stå på första sidan i en tabell som heter något i stil med "Market indicators".

### Varför källorna inte stämmer överens

Två källor kan ge olika prime yield för Malmö samma kvartal, till exempel 4,50 % och 4,85 %. Det beror sällan på att någon räknat fel. Vanliga orsaker:

1. **Olika definitioner.** "CBD" kan avgränsas olika. Vissa mäter vakans i hela beståndet, andra bara i moderna lokaler.
2. **Olika mätmetod.** Citymark räknar annonserade lediga ytor. Andra frågar hyresvärdarna.
3. **Prognos eller utfall.** SEPREF publicerar prognoser, MarketBeat rapporterar utfall.
4. **Olika tidpunkt.** Ett kvartal kan vara skillnaden mellan två räntelägen.

Därför har varje rad en källa och ett datum, och därför skriver vi in båda siffrorna i stället för att välja en.

## Steg 3 — Kontorsannonser

### Var annonserna finns

- **Objektvision** och **Lokalguiden:** de största annonssajterna för kommersiella lokaler.
- **Hyresvärdarnas egna sajter:** Wihlborgs (stor i alla tre städerna), Castellum och Vasakronan.

Läs annonserna och skriv in fakta för hand. Ladda inte ner sidorna automatiskt (web scraping), eftersom sajternas användarvillkor brukar förbjuda det. Kopiera inte annonstexter eller bilder. Adress, area, hyra och länk räcker.

### Hur många

Målet är 30–40 annonser: ungefär 15–20 i Malmö och 8–10 vardera i Lund och Helsingborg. Sprid dem över flera stadsdelar, eftersom analysen jämför delområden. Fem annonser i samma hus säger mindre än fem annonser i fem olika stadsdelar.

### Regler för hyran

- **Alltid kr/kvm/år.** Om annonsen anger månadshyra: månadshyra × 12 / kvm. Om den anger total årshyra: årshyra / kvm.
- **Ett intervall** (t.ex. "1 800–2 200 kr/kvm"): om annonsen listar flera lokaler, gör en rad per lokal. Annars, skriv mittvärdet och ange intervallet i `rent_terms`.
- **"Hyra enligt överenskommelse":** ta med raden men lämna hyran tom. Andelen annonser utan hyra är också information.
- **`rent_terms`:** skriv vad annonsen säger att hyran inkluderar. Svenska kontorshyror anges oftast exklusive moms, inklusive värme och ibland kyla, och med tillägg för fastighetsskatt. Hyror med olika villkor är inte helt jämförbara.

### Koordinater (valfritt, men rekommenderat)

Högerklicka på adressen i Google Maps. Det första talet i menyn är latitude och det andra longitude. Med koordinater kan vi räkna fram location score från Fas 1 för varje annons och testa om läget förklarar hyran.

## Kontrollera arbetsboken

Spara och stäng Excel. Kör sedan i PowerShell, i projektmappen:

```
python -m src.phase3_market_report.check_data
```

Skriptet visar hur många rader som är giltiga och pekar ut varje fel med radnummer, till exempel `Annonser, rad 7: city: Input should be 'malmo', 'lund' or 'helsingborg'`.
