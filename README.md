# HyperSpin MAME Vertical & Naomi Database Builder

A complete **Python-based pipeline** to generate, clean, and organize
**HyperSpin-compatible XML databases** from **MAME**, with a strong
focus on **vertical (TATE) arcade games** and **Sega Naomi**.

This project automates what is usually a long, manual, and error-prone
process when building serious HyperSpin setups.

------------------------------------------------------------------------

## What This Does

### MAME

-   Generates a fresh `mame.xml` using `mame.exe -listxml`
-   Filters **vertical-only (90° / 270°) games**
-   Injects missing HyperSpin entries when needed
-   Produces multiple curated databases:
    -   Vertical games (main wheel)
    -   Vertical games by **genre**
    -   Vertical games by **manufacturer**
    -   Vertical **Shoot-'Em-Up** games by manufacturer
    -   Manufacturer → Genre sub-wheels
-   Normalizes XML-safe genre strings (`Shoot-&apos;Em-Up`, etc.)

### Sega Naomi

-   Extracts **Naomi games directly from MAME source data**
-   Keeps **vertical Naomi titles only**
-   Removes known unwanted / problematic games
-   Completes missing `<genre>` tags using a full MAME database
-   Generates **genre-based Naomi HyperSpin databases**

------------------------------------------------------------------------

## Generated Folder Structure

    databases/
    ├── Mame 0.284 Vertical.xml
    ├── Naomi_Vertical.xml
    ├── genres - vertical/
    ├── manufacturer - vertical/
    ├── manufacturer - shmups/
    ├── manufacturer - vertical by genres/
    ├── genres - naomi/

All output files are **ready to use in HyperSpin**.

------------------------------------------------------------------------

## Requirements

-   Windows
-   Python 3.10+
-   MAME (tested with MAME 0.284)
-   HyperSpin-compatible XML databases

Required input files: - `Mame 0.284.xml` - `Mame 0.284 All games.xml` [(Source)](http://r0man0.free.fr/index.php/download-mame-xml-lists-and-generator/)

------------------------------------------------------------------------

## ⚙️ Configuration

Edit paths at the top of the script:

``` python
BASE = Path(r"C:\Users\PC\Desktop\HS2026\files")
MAME_EXE = BASE / "mame.exe"
```

------------------------------------------------------------------------

## How to Run

``` bash
python build_hyperspin_databases.py
```

The script runs end-to-end with no manual intervention.

------------------------------------------------------------------------

## Intended Audience

-   Arcade cabinet builders
-   TATE / vertical setups
-   Shmup-focused HyperSpin builds
-   Advanced MAME database curation

This project is **not** a frontend or emulator.

------------------------------------------------------------------------
