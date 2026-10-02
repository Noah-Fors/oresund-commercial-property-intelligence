# Att göra senare

Saker vi medvetet har skjutit upp. Flytta en punkt till "Klart" när den är gjord.

## Fas 1 — Location scoring

- [ ] **Utöka motorvägsdefinitionen.** Just nu räknas bara motorvägar (E6/E20, E22, E4, Yttre ringvägen). Överväg att lägga till motortrafikleder och det tunga vägnätet (viktiga riksvägar för lastbilstrafik).
- [ ] **Ta med bussar i transit-poänget.** Idag räknas bara tåg och spårvagn, vilket undervärderar lägen med bra busstrafik (t.ex. Ringugnsgatan 14 i Limhamn). Riktig hållplatsdata finns hos Skånetrafiken.
- [ ] **Exakta koordinater för exempeldatan.** Nio av femton fastigheter, alla stationer och alla motorvägstrafikplatser har ungefärliga koordinater. Trafikplatserna kan avvika flera hundra meter.
- [ ] **Få Lantmäteriets API att fungera.** Prenumerationen är klar, men vi har inte lyckats hämta en access token ("Consumer key and secret not generated" i API Console).
- [ ] **Bättre källa för arbetsplatser.** SCB publicerar inte dagbefolkning (var folk arbetar) per DeSO som öppna data, bara per kommun. Kontorsräkning från OpenStreetMap testades men är opålitlig (Hyllie fick 1 kontor, Ideon 8), eftersom kontor sällan är inprickade. Alternativ: beställa dagbefolkning per DeSO från SCB, Lantmäteriets byggnadsregister (byggnadens ändamål), eller räkna kontorsbyggnader i OpenStreetMap.
- [ ] **Validera butiksräkningen från OpenStreetMap.** Emporia fick bara 62 verksamheter inom 500 m, vilket tyder på att butikerna inne i köpcentret inte är inprickade. Stickprovskontrollera några lägen mot verkligheten.
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
- [x] Kommersiell täthet från OpenStreetMap (verksamheter inom 500 m, mättnadskurva där 50 ger 50 poäng)
