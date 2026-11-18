# DG-Talk PC

**Windows-versie van DG-Talk Android, gebouwd op dezelfde open-source TeamSpeak 3-spraakengine.**

> **Status:** eerste native Windows-port. De interface volgt de Android-indeling en bevat thema's en PTT. Dit is **geen pixel-perfecte of functie-voor-functie kopie**: Android-eigen functies en bepaalde apparaatknoppen vragen afzonderlijke Windows-implementaties en praktijktests.

## Downloaden

Open [Actions](https://github.com/michiel66/DG-Talk-PC./actions/workflows/windows.yml), kies een geslaagde **DG-Talk PC Windows EXE**-run en download onder **Artifacts** `DG-Talk-PC-Windows-x64`. Pak de ZIP uit en start `DG-Talk-PC.exe` in de map. **Laat de bestanden uit de map `_internal` staan**, anders start de toepassing niet.

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
