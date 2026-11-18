# DG-Talk PC

**Windows-versie van DG-Talk Android, gebouwd op dezelfde open-source TeamSpeak 3-spraakengine.**

> **Status:** eerste native Windows-port. De interface volgt de Android-indeling en bevat thema's en PTT. Dit is **geen pixel-perfecte of functie-voor-functie kopie**: Android-eigen functies en bepaalde apparaatknoppen vragen afzonderlijke Windows-implementaties en praktijktests.

## DG-Talk PC 1.1.0 – eigen Windows Radio Console

Omdat de Android-achtige Windows-boom niet goed werkte op verschillende schermen, is de **verbonden hoofdinterface compleet vervangen** door een eigen, brede Windows-mobilofoon. De *werkende* TeamSpeak 3/Rust/Opus-engine, Windows-microfoon, audio, PTT, rogerpiep, fysieke PTT en verbindingsinstellingen zijn **niet herschreven**.

- **Nieuwe desktopindeling**: een donkere radio-console met statusbalk, grote scrollbare kanalenlijst en een vast rechter paneel met de actuele kanaalnaam, gebruikersnaam, RX-/TX-status, signaalbalken, grote zendknop en audio-bediening.
- **Geen Treeview of witte Unicode-iconen** meer in de hoofdweergave: alle kanalen en gebruikers worden met scherpe lettertypen en echte gekleurde afbeeldingen op een **native Tk Canvas** getekend.
- **Echte spacers als lijnen**: `[*spacer619]──` is een geometrische scheidingslijn, niet een technisch label of herhaalde tekens. `[cspacer]`, `[lspacer]`, `[rspacer]` worden als uitgelijnde tekst getekend. Lijnen passen zichzelf aan na het vergroten of verkleinen van het scherm.
- **Interactief**: dubbelklik om een gewoon kanaal te betreden, rechtsklik voor de kanaalactie, dubbelklik op een gebruiker voor een privégesprek, inklappen van subkanalen en zoeken op kanaal of gebruikersnaam.
- **DPI-/4K-geschikt**: fonts en vormen worden direct op de huidige Windows-resolutie getekend in plaats van als bitmap opgerekt. De vier thema's Standaard, Kerst, 27MC en Space behouden elk hun accentkleur.
- **Eigen verbindingsscherm**, passend bij deze radio-console. De bestaande instellingen blijven beschikbaar.

De nieuwe GUI heeft een **aparte Windows-regressietest**: hiermee worden de getekende TeamSpeak-lijnen, labels, TX/RX, schermgrootte, PTT-gebeurtenissen en kanaalacties gecontroleerd zonder dat de live server hoeft te worden belast. Daarnaast blijft de volledige Windows-EXE/Setup-build bestaan.

**Installeren:** kies op de nieuwste geslaagde [Windows build](https://github.com/michiel66/DG-Talk-PC./actions/workflows/windows.yml) onder **Artifacts** `DG-Talk-PC-Setup-Windows-x64`. Installeer over de bestaande versie; de setup maakt opnieuw het bureaubladicoon en bewaart de gebruikersinstellingen.

## DG-Talk PC 1.0.2 – zichtbare spacerlijnen en scherpe 4K/HiDPI-weergave

Op verzoek van gebruikers van TS-HEERLEN:

- **Echte TeamSpeak-3-spacers**: regels zoals `[*spacer619]──`, `[*spacer0]___`, `[cspacer0]Welkom`, `[lspacer]` en `[rspacer]` worden nu herkend en **zonder de technische tag** in de kanaalboom weergegeven. Speciale herhaallijnen (doorgetrokken, streepjes, puntjes) vullen de beschikbare breedte. Gestructureerde kopteksten worden links, gecentreerd of rechts uitgelijnd.
- **Automatische aanpassing**: spacerlijnen worden opnieuw opgemeten wanneer de gebruiker het venster breder of smaller maakt. Een spacer kan niet per ongeluk als spraakkanaal worden geopend.
- **Scherper op 4K-monitoren**: per-monitor Windows-DPI-awareness (met fallback voor oudere Windows-versies) voorkomt dat Windows het complete 96-DPI venster als een wazige bitmap vergroot. De vensterafmetingen, rijen en de reeds gekleurde RGBA-icoontjes worden naar de native DPI geschaald. Geen aanpassing aan TeamSpeak, PTT, microfoon, instellingen of rogerpiep.
- **Begrenzing**: dit is resolutie-onafhankelijke scherpe rendering op 4K/1440p/HiDPI-beeldschermen, geen kunstmatig "4K video"-filter. De uiteindelijke scherpte hangt ook af van de ingestelde Windows-beeldschaling en het gebruikte scherm.
- **Automatische regressietests**: parser, herhaallijnen, centrering en de nieuwe Windows-DPI-module worden bij elke nieuwe EXE-build gecontroleerd.

Installeer de nieuwe **DG-Talk-PC-Setup-Windows-x64** over de bestaande versie. De instellingen in `%LOCALAPPDATA%\\DG-Talk-PC\\settings.json` blijven behouden.

## DG-Talk PC 1.0.1 – gekleurde pictogrammen en bureaubladicoon

Deze update herstelt de twee gemelde Windows-problemen zonder de werkende TeamSpeak-, microfoon- of PTT-functionaliteit te wijzigen:

- De app gebruikt nu **echte, gekleurde RGBA-pictogrammen**, niet langer Windows-emoji die als witte symbolen verschijnen. Dit geldt voor de knoppen, kanaalboom, gebruikersstatus en de speciale thema-iconen van Kerst, 27MC en Space.
- Het DG-Talk-logo wordt als **Windows-appicoon (.ico)** opgenomen in de EXE, het venster, de taakbalk en de Windows-setup.
- De **Windows-setup maakt voortaan altijd een bureaubladsnelkoppeling en Startmenu-snelkoppeling** voor het huidige Windows-account. Je hoeft geen optioneel vakje te selecteren.
- Dezelfde app-id en dezelfde installatiemap blijven behouden: installatie over de vorige versie is mogelijk, met behoud van gebruikersinstellingen in `%LOCALAPPDATA%\DG-Talk-PC\settings.json`.

**Let op:** download de nieuwe **DG-Talk-PC-Setup-Windows-x64** via de geslaagde GitHub Actions-run; de losse portable versie maakt geen bureaubladsnelkoppeling, omdat die niet wordt geïnstalleerd.

## Downloaden

Open [Actions](https://github.com/michiel66/DG-Talk-PC./actions/workflows/windows.yml), kies de nieuwste geslaagde **DG-Talk PC Windows EXE**-run en download onder **Artifacts** bij voorkeur `DG-Talk-PC-Setup-Windows-x64`. Pak het ZIP-bestand uit en voer `DG-Talk-PC-Setup.exe` uit. De setup zet automatisch het gekleurde DG-Talk-icoon op je bureaublad. Voor portable gebruik is er ook `DG-Talk-PC-Windows-x64`: pak die ZIP uit en start `DG-Talk-PC.exe` in de map. **Laat de bestanden uit de map `_internal` staan**, anders start de toepassing niet.

De app opent als **zelfstandig Windows-venster** met Tkinter: er is geen webbrowser en er is geen lokale webserver. Windows 10/11 x64.

## Dezelfde basis als Android

- **Oorspronkelijke TeamSpeak 3-client-engine**: `tscore` uit [michiel66/DG-Talk](https://github.com/michiel66/DG-Talk); de Windows-build haalt deze vastgepinde bron op en compileert `tscore.dll`. Het is **geen** ServerQuery-bot en geen web-overlay.
- Server `heerlen.mijnts3.nl` staat standaard ingevuld. Eigen nickname, TS3-identiteit, serverwachtwoord en kanaalwachtwoord.
- Live kanaalboom met gebruikers, dubbelklikken om een kanaal te betreden, privélijst, serverchat en kanaalchat.
- Full-duplex audio via **Windows audioapparaten** (`sounddevice`/PortAudio): 48 kHz, mono-microfoon en stereo-uitgang, Opus via de oorspronkelijke Rust-engine.
- **PTT vasthouden = TX; loslaten = RX.** Knop in venster, toets F8 of zelf aangeleerde fysieke Windows-/Bluetooth-HID-toets; andere audiomodi (Voice Activation / Continuous).
- **3-tonige rogerpiep**, apart aan/uit en een testknop. Signaal wordt via dezelfde microfoon-naar-TeamSpeak-audiostroom verzonden; andere deelnemers kunnen het horen.
- Dezelfde kleurgroepen **Standaard, Kerst, 27MC, Space**, met originele ontwerp-previews uit Android.
- Microfoon dempen, luidspreker dempen, gebruikersnaam, instellingen die tussen sessies blijven bestaan.

## Belangrijke grenzen

**Externe PTT:** werkt met Windows-toetsgebeurtenissen, bijvoorbeeld Bluetooth-HID-toetsen. Sommige Android-portofoonknoppen en Bluetooth-accessoires hebben merkgebonden drivers/protocollen; die werken mogelijk niet automatisch onder Windows. Koppelen moet eerst in Windows.

**Windows-audio:** een microfoon- en afspeelapparaat dat 48 kHz/16-bit ondersteunt, moet aanwezig zijn. De eerste Windows-versie heeft nog niet alle Android-functies (kanaalbeheer, avataruploads, uitgebreide rechten, wolksynchronisatie, zwevende bediening). Er wordt geen 100% functionele gelijkheid beloofd totdat deze zijn overgezet en getest.

**Merk en licenties:** de oorspronkelijke DG-Talk-code staat onder MIT (Copyright 2026 NotMurPh); de vendored TeamSpeak-protocolbibliotheek onder MIT/Apache-2.0, UniFFI onder MPL-2.0 en overige componenten hebben eigen voorwaarden. [Licentieoverzicht bronproject](https://github.com/michiel66/DG-Talk/blob/main/THIRD_PARTY.md). Originele TeamSpeak-artwork of geluiden worden **niet** in de Windows-release opgenomen.

## Projectstructuur

```
desktop/
  main.py             native Windows-gebruikersinterface
  backend.py          TeamSpeak-controller, identiteit, audio, PTT en rogerpiep
  requirements.txt    Python Windows-bibliotheken
  assets/             optioneel, previews worden tijdens CI uit DG-Talk gehaald
.github/workflows/windows.yml
```

## Ontwikkelen

Windows x64 + Rust 1.99, Python 3.11. Gebruik `.github/workflows/windows.yml` als reproduceerbaar bouwrecept: checkout van [DG-Talk](https://github.com/michiel66/DG-Talk), build `tscore.dll`, genereer UniFFI-Pythonbindingen, installeer dependencies, bouw met PyInstaller tot zelfstandige .exe.

**Android blijft volledig onaangetast**: deze repository bevat alleen de Windows-port.
