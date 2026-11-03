# Game Library Renamer

Rename the game files on your PS5 (or any FTP/SFTP server) to clean, readable names —
automatically, from the PS4/PS5 Title ID found in each name.

```
PPSA08329-app.pkg          →  God_of_War_Ragnarok-PPSA08329-US-PS5.pkg
CUSA07408 God of War.pkg   →  God_of_War-CUSA07408-US-PS4.pkg
```

![Game Library Renamer](docs/screenshot-rename.png)

## Features

- **Connects to your PS5 over FTP or SFTP** and reads only the root of the folders you choose
  (subfolders are never opened). Each folder shows whether it exists.
- **Finds the Title ID** (`PPSA`, `CUSA`, …) in every file name and shows the game name, cover,
  platform, region, publisher and Content ID.
- **Proposes the new name** `Game_Name-TITLEID-REGION-PS4|PS5` (no accents or special characters,
  spaces become `_`, the file extension is kept) with a **Rename** button per game.
- **Safe renaming**: never overwrites an existing item, detects two items that would get the same name,
  and moves the already correct ones ("NAME OK") to the end of the list.
- **Fast**: game names come from a local database of ~71,000 titles
  ([andshrew/PlayStation-Titles](https://github.com/andshrew/PlayStation-Titles)), downloaded when the app
  starts and only when it changes. Covers and publisher names come from
  [prosperopatches.com](https://prosperopatches.com) (PS5), [orbispatches.com](https://orbispatches.com)
  (PS4) and the PS Store, and are cached on disk.
- **Manual lookup** tab: paste codes or file names, copy the new names, or export TXT/CSV.
- **Store** and **YouTube** buttons for each game.
- English, Português (BR) and Español.
- Runs in its own window (WebView2, no browser is opened) and closes completely when the window is closed.
- Only files are renamed: folders and compressed files (`.zip`, `.rar`, `.7z`...) are ignored.
- Patches and backports (file name with `patch`, `backport` or `update`) are listed but never renamed,
  so they do not get the game's name.

## Install

1. Download `GameLibraryRenamer_<version>_Setup.exe` from the [Releases](../../releases) page.
2. Run it. No administrator rights are needed (it installs to `%LOCALAPPDATA%\Programs\Game Library Renamer`).
   Windows SmartScreen may warn because the installer is not code-signed: click **More info → Run anyway**.

When uninstalling you can choose whether to also delete your settings and cached data.

## Using it with a PS5

1. Start an FTP payload on the console. The default settings match
   [ftpsrv](https://github.com/ps5-payload-dev/ftpsrv), the most used one: **FTP, port 2121, no user,
   no password**. The etaHEN FTP uses port **1337**.
2. In the app, enter the PS5 IP address, click **Save** and **Connect**.
3. Add or remove folders right in the app (defaults: `/data/homebrew/` and `/mnt/ext1/homebrew/`).
4. Click **Rename** on each game you want to rename, or **Rename all** to rename every ready item.
   Use the **Found / Not found / All** buttons to filter the list (not found = no code in the name or code not found).
5. Each item shows its full path length (folder + name), now and after renaming.

### ShadowMountPlus and long names

ShadowMountPlus mounts each image at `/mnt/shadowmnt/<name without extension>_<8-char hash>`
(`/mnt/shadowmnt/pfsc/` for `.ffpfsc`), and the PS5 kernel refuses mount points longer than 87
characters ("File name too long"). So the image name without the extension must be at most 63
characters (58 for `.ffpfsc`). For `.ffpkg`, `.exfat`, `.ffpfs` and `.ffpfsc` images the app keeps the
name at 58 characters or less, shortening only the title and keeping `-TITLEID-REGION-PS5`, and
flags images that are already too long. `.pkg` files are not affected.

## Settings file

`GameLibraryRenamer.ini`, next to the program (**Edit INI** opens it in Notepad, **Reload INI** reads it again):

```ini
[app]
language = en

[ps5]
protocol = ftp
host = 192.168.0.10
port = 2121
user =
password =

[folders]
folder1 = /data/homebrew/
folder2 = /mnt/ext1/homebrew/
```

> The password is stored as plain text in this file.

## Run from source

Requires Windows and Python 3.12+.

```bat
pip install paramiko pywebview
python app_ps5.py
```

Command-line lookup without the UI: `python consulta_ps5.py PPSA08329 CUSA07408`.

### Build the installer

Requires `pip install pyinstaller pillow paramiko pywebview` and [Inno Setup 6](https://jrsoftware.org/isinfo.php).
Set `VERSAO` in `ftp_ps5.py`, then run:

```powershell
powershell -ExecutionPolicy Bypass -File instalador\gerar_instalador.ps1
```

The installer is written to `instalador\saida\`.

## Credits

- Title database: [andshrew/PlayStation-Titles](https://github.com/andshrew/PlayStation-Titles) (MIT).
- Game pages and covers: [prosperopatches.com](https://prosperopatches.com) and [orbispatches.com](https://orbispatches.com).
- FTP payload: [ps5-payload-dev/ftpsrv](https://github.com/ps5-payload-dev/ftpsrv).

This project is not affiliated with Sony Interactive Entertainment. "PlayStation", "PS4" and "PS5" are
trademarks of Sony Interactive Entertainment Inc.

## License

Copyright © 2026 PristMC

This program is free software: you can redistribute it and/or modify it under the terms of the
[GNU General Public License](LICENSE) as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version (GPL-3.0-or-later). It is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; see the license for details.

Releases published before November 3, 2026 (v1.0) were distributed under the MIT license and remain available
under those terms.
