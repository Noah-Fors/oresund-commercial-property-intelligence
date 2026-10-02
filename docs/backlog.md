# Att göra senare

Saker vi medvetet har skjutit upp. Flytta en punkt till "Klart" när den är gjord.

## Fas 1 — Location scoring

- [ ] **Utöka motorvägsdefinitionen.** Just nu räknas bara motorvägar (E6/E20, E22, E4, Yttre ringvägen). Överväg att lägga till motortrafikleder och det tunga vägnätet (viktiga riksvägar för lastbilstrafik).
- [ ] **Ta med bussar i transit-poänget.** Idag räknas bara tåg och spårvagn, vilket undervärderar lägen med bra busstrafik (t.ex. Ringugnsgatan 14 i Limhamn). Riktig hållplatsdata finns hos Skånetrafiken.
- [ ] **Exakta koordinater för exempeldatan.** Nio av femton fastigheter, alla stationer och alla motorvägstrafikplatser har ungefärliga koordinater. Trafikplatserna kan avvika flera hundra meter.
- [ ] **Få Lantmäteriets API att fungera.** Prenumerationen är klar, men vi har inte lyckats hämta en access token ("Consumer key and secret not generated" i API Console).
- [ ] **Data för arbetsplatser och kommersiell täthet.** Två av location scorens parametrar saknar fortfarande data (SCB respektive Lantmäteriet).
- [ ] **Stadsdel som eget fält.** Områdesnamnen (Limhamn, Oxie, Råå …) försvann när adresserna lades in. Lägg till ett `district`-fält om de behövs i karta eller rapport.
- [ ] **Befolkning i närområdet som parameter.** Tätortshandel (t.ex. pizzerian på Käglingevägen 154) lever på boende i närheten, vilket ingen av parametrarna fångar idag. Data finns hos SCB.

## Klart

- [x] Datamodell för fastigheter och location score
- [x] Exempeldata: 15 fastigheter och 9 stationer
- [x] Transit-poäng med exponentiell distance decay (halveras var 700 m)
- [x] Interaktiv karta och tabell i Streamlit
- [x] Handel uppdelad i tätortshandel och externhandel
- [x] Motorvägsparameter: avstånd till närmaste trafikplats (halveras var 2 000 m)
- [x] Vikter per fastighetstyp och totalt location score
