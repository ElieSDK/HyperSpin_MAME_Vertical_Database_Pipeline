"""
Generate mame.xml from mame.exe
"""

import subprocess

mame_exe = r"C:\Users\PC\Desktop\HS2026\files\mame.exe"
output_xml = r"C:\Users\PC\Desktop\HS2026\files\mame.xml"

with open(output_xml, "w", encoding="utf-8") as f:
    subprocess.run(
        [mame_exe, "-listxml"],
        stdout=f,
        stderr=subprocess.DEVNULL,
        check=True
    )

print("mame.xml generated successfully")


"""
Keep vertical games only
"""

import xml.etree.ElementTree as ET
from pathlib import Path

# -------------------------------------------------
# Paths
# -------------------------------------------------
BASE = Path(r"C:\Users\PC\Desktop\HS2026\files")

MAME_XML = BASE / "mame.xml"
HS_XML   = BASE / "Mame 0.284.xml"
OUT_XML  = BASE / "Mame 0.284 Vertical.xml"

# -------------------------------------------------
# 1) Parse MAME XML → find vertical machines
# -------------------------------------------------
print("Loading MAME XML...")
mame_tree = ET.parse(MAME_XML)
mame_root = mame_tree.getroot()

vertical = set()

for machine in mame_root.findall("machine"):
    name = machine.get("name")
    display = machine.find("display")
    if display is not None:
        rotate = display.get("rotate", "0")
        if rotate in ("90", "270"):
            vertical.add(name)

print(f"Vertical machines found: {len(vertical)}")

# -------------------------------------------------
# 2) Parse HyperSpin XML → keep only vertical games
# -------------------------------------------------
print("Loading HyperSpin XML...")
hs_tree = ET.parse(HS_XML)
hs_root = hs_tree.getroot()

new_root = ET.Element(hs_root.tag)

kept = 0
parents = 0
clones = 0

for game in hs_root.findall("game"):
    name = game.get("name")
    cloneof = (game.findtext("cloneof") or "").strip()

    # orientation inherited from parent
    parent = cloneof if cloneof else name

    if parent in vertical:
        new_root.append(game)
        kept += 1

        if cloneof:
            clones += 1
        else:
            parents += 1

# -------------------------------------------------
# 3) Save new HyperSpin XML
# -------------------------------------------------
ET.ElementTree(new_root).write(
    OUT_XML,
    encoding="utf-8",
    xml_declaration=True
)

# -------------------------------------------------
# 4) Final summary
# -------------------------------------------------
print("\n=== RESULT ===")
print(f"Total games : {kept}")
print(f"Parents     : {parents}")
print(f"Clones      : {clones}")
print(f"Output file : {OUT_XML}")


"""
Split vertical games by genres
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import re

BASE = Path(r"C:\Users\PC\Desktop\HS2026\files")
INPUT_XML = BASE / "Mame 0.284 Vertical.xml"
OUT_DIR = BASE / "genres - vertical"

OUT_DIR.mkdir(exist_ok=True)

def clean(name):
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', '', name)
    return name or "Unknown"

tree = ET.parse(INPUT_XML)
root = tree.getroot()

by_genre = defaultdict(list)

for game in root.findall("game"):
    genre = clean(game.findtext("genre") or "Unknown")
    by_genre[genre].append(game)

for genre, games in sorted(by_genre.items()):
    menu = ET.Element("menu")
    for game in games:
        menu.append(game)

    out = OUT_DIR / f"{genre}.xml"
    ET.ElementTree(menu).write(out, encoding="utf-8", xml_declaration=True)
    print(f"{genre}: {len(games)} games")

print("Done.")


"""
Add DoDonPachi SaiDai-Ou-Jou
ddpsdoj.zip
"""

xml_file = "C:/Users/PC/Desktop/HS2026/files/Mame 0.284 Vertical.xml"

target_description = "DoDonPachi Dai-Ou-Jou Tamashii (V201, China)"

new_game_entry = """<game name="ddpsdoj" index="" image="">
	<description>DoDonPachi SaiDaiOuJou (2012/ 4/20)</description>
	<cloneof />
	<crc />
	<manufacturer>Cave</manufacturer>
	<year>2012</year>
	<genre>Shoot-'Em-Up</genre>
	<rating />
	<enabled>Yes</enabled>
</game>
"""

# Read the existing file
with open(xml_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
inserted = False
skip_until_game_end = False

for line in lines:
    new_lines.append(line)

    if not inserted and target_description in line:
        skip_until_game_end = True

    if skip_until_game_end and "</game>" in line:
        # insert the new game after this line
        new_lines.append(new_game_entry + "\n")
        inserted = True
        skip_until_game_end = False

if not inserted:
    print("Warning: Target description not found. No insertion made.")

# Overwrite the same XML file
with open(xml_file, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Insertion complete — file overwritten!")


"""
Split vertical games by 27 manufacturers
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import re

# -------------------------------
# Paths
# -------------------------------
BASE = Path(r"C:\Users\PC\Desktop\HS2026\files")
INPUT_XML = BASE / "Mame 0.284 Vertical.xml"
OUT_DIR = BASE / "manufacturer - vertical"

OUT_DIR.mkdir(exist_ok=True)

# -------------------------------
# Priority list of 27 manufacturers
# -------------------------------
PRIORITY = [
    "AMCOE",
    "Atari",
    "Bally",
    "BFM",
    "Capcom",
    "Cave",
    "Data East",
    "Gaelco",
    "IGS",
    "IGT",
    "Irem",
    "Jaleco",
    "Kaneko",
    "Konami",
    "Midway",
    "Namco",
    "Nichibutsu",
    "Nintendo",
    "Novotech",
    "Psikyo",
    "Sammy",
    "Sega",
    "Seibu Kaihatsu",
    "SNK",
    "Taito",
    "Williams"
]

# -------------------------------
# Helpers
# -------------------------------
def normalize(name: str) -> str:
    """Remove parentheses, trim, etc."""
    name = name.strip()
    name = re.sub(r"\s*\(.*?\)", "", name)
    return name

def pick_manufacturer(raw: str) -> str:
    """Pick one manufacturer from priority list"""
    parts = re.split(r"\s*/\s*|\s*&\s*|\s*\+\s*", raw)
    parts = [normalize(p) for p in parts if p]
    for p in parts:
        if p in PRIORITY:
            return p
    return None

# -------------------------------
# Load XML
# -------------------------------
tree = ET.parse(INPUT_XML)
root = tree.getroot()

parent_count = defaultdict(int)
total_parents_main = 0

for game in root.findall("game"):
    cloneof = (game.findtext("cloneof") or "").strip()
    if not cloneof:
        total_parents_main += 1
        manu_raw = game.findtext("manufacturer") or "Unknown"
        manu = pick_manufacturer(manu_raw)
        if manu:
            parent_count[manu] += 1

# -------------------------------
# Write XML per manufacturer (optional)
# -------------------------------
for manu in PRIORITY:
    manu_games = [g for g in root.findall("game")
                  if pick_manufacturer(g.findtext("manufacturer") or "") == manu]
    if manu_games:
        menu = ET.Element("menu")
        for g in manu_games:
            menu.append(g)
        ET.ElementTree(menu).write(OUT_DIR / f"{manu} Games.xml",
                                   encoding="utf-8",
                                   xml_declaration=True)

# -------------------------------
# Print summary
# -------------------------------
total_parents_27 = sum(parent_count.values())

print("\n=== Parent Games Summary ===\n")
for manu in PRIORITY:
    count = parent_count.get(manu, 0)
    print(f"{manu:20}: {count} parents")

print(f"\nTotal parents in 27 manufacturers: {total_parents_27} over {total_parents_main} total parents in Mame 0.284 Vertical.xml")


"""
Split vertical shmups by 27 manufacturers
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import re

# -------------------------------
# Paths
# -------------------------------
BASE = Path(r"C:\Users\PC\Desktop\HS2026\files\genres - vertical")
INPUT_XML = BASE / "Shoot-'Em-Up.xml"
OUT_DIR = BASE / "manufacturer - shmups"

OUT_DIR.mkdir(exist_ok=True)

# -------------------------------
# Priority list of 27 manufacturers
# -------------------------------
PRIORITY = [
    "AMCOE",
    "Atari",
    "Bally",
    "BFM",
    "Capcom",
    "Cave",
    "Data East",
    "Gaelco",
    "IGS",
    "IGT",
    "Irem",
    "Jaleco",
    "Kaneko",
    "Konami",
    "Midway",
    "Namco",
    "Nichibutsu",
    "Nintendo",
    "Novotech",
    "Psikyo",
    "Sammy",
    "Sega",
    "Seibu Kaihatsu",
    "SNK",
    "Taito",
    "Williams"
]

# -------------------------------
# Helpers
# -------------------------------
def normalize(name: str) -> str:
    """Remove parentheses, trim, etc."""
    name = name.strip()
    name = re.sub(r"\s*\(.*?\)", "", name)
    return name

def pick_manufacturer(raw: str) -> str:
    """Pick one manufacturer from priority list"""
    parts = re.split(r"\s*/\s*|\s*&\s*|\s*\+\s*", raw)
    parts = [normalize(p) for p in parts if p]
    for p in parts:
        if p in PRIORITY:
            return p
    return None

# -------------------------------
# Load XML
# -------------------------------
tree = ET.parse(INPUT_XML)
root = tree.getroot()

parent_count = defaultdict(int)
total_parents_main = 0

for game in root.findall("game"):
    cloneof = (game.findtext("cloneof") or "").strip()
    if not cloneof:
        total_parents_main += 1
        manu_raw = game.findtext("manufacturer") or "Unknown"
        manu = pick_manufacturer(manu_raw)
        if manu:
            parent_count[manu] += 1

# -------------------------------
# Write XML per manufacturer (optional)
# -------------------------------
for manu in PRIORITY:
    manu_games = [g for g in root.findall("game")
                  if pick_manufacturer(g.findtext("manufacturer") or "") == manu]
    if manu_games:
        menu = ET.Element("menu")
        for g in manu_games:
            menu.append(g)
        ET.ElementTree(menu).write(OUT_DIR / f"{manu} Games.xml",
                                   encoding="utf-8",
                                   xml_declaration=True)

# -------------------------------
# Print summary
# -------------------------------
total_parents_27 = sum(parent_count.values())

print("\n=== Parent Games Summary ===\n")
for manu in PRIORITY:
    count = parent_count.get(manu, 0)
    print(f"{manu:20}: {count} parents")

print(f"\nTotal parents in 27 manufacturers: {total_parents_27} over {total_parents_main} total parents in Mame 0.284 Vertical.xml")



"""
Split vertical manufacturer games by genre
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import re

# -------------------------------
# Paths
# -------------------------------
BASE = Path(r"C:\Users\PC\Desktop\HS2026\files")
INPUT_XML = BASE / "Mame 0.284 Vertical.xml"
OUT_DIR = BASE / "manufacturer - vertical by genres"

OUT_DIR.mkdir(exist_ok=True)

# -------------------------------
# Priority list of manufacturers
# -------------------------------
PRIORITY = [
    "AMCOE", "Atari", "Bally", "BFM", "Capcom", "Cave", "Data East",
    "Gaelco", "IGS", "IGT", "Irem", "Jaleco", "Kaneko", "Konami",
    "Midway", "Namco", "Nichibutsu", "Nintendo", "Novotech",
    "Psikyo", "Sammy", "Sega", "Seibu Kaihatsu", "SNK",
    "Taito", "Williams"
]

# -------------------------------
# Helpers
# -------------------------------
def normalize(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s*\(.*?\)", "", text)
    return text

def pick_manufacturer(raw: str) -> str | None:
    parts = re.split(r"\s*/\s*|\s*&\s*|\s*\+\s*", raw)
    parts = [normalize(p) for p in parts if p]
    for p in parts:
        if p in PRIORITY:
            return p
    return None

def clean_genre(raw: str) -> str:
    if not raw:
        return "Unknown"
    return raw.strip()

def safe_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name)

# -------------------------------
# Load XML
# -------------------------------
tree = ET.parse(INPUT_XML)
root = tree.getroot()

# manufacturer → genre → list[game]
buckets = defaultdict(lambda: defaultdict(list))

for game in root.findall("game"):
    manu_raw = game.findtext("manufacturer") or ""
    manu = pick_manufacturer(manu_raw)
    if not manu:
        continue

    genre_raw = game.findtext("genre")
    genre = clean_genre(genre_raw)

    buckets[manu][genre].append(game)

# -------------------------------
# Write XML files
# -------------------------------
for manu, genres in buckets.items():
    manu_dir = OUT_DIR / manu
    manu_dir.mkdir(exist_ok=True)

    for genre, games in genres.items():
        menu = ET.Element("menu")
        for g in games:
            menu.append(g)

        genre_name = safe_filename(genre)
        out_file = manu_dir / f"{genre_name}.xml"

        ET.ElementTree(menu).write(
            out_file,
            encoding="utf-8",
            xml_declaration=True
        )

# -------------------------------
# Summary
# -------------------------------
print("\n=== Split Complete ===\n")

for manu in PRIORITY:
    if manu in buckets:
        total = sum(len(v) for v in buckets[manu].values())
        print(f"{manu:20}: {len(buckets[manu])} genres, {total} games")

print(f"\nOutput folder: {OUT_DIR}")


"""
Naomi vertical games
"""

import xml.etree.ElementTree as ET
from pathlib import Path

# -------------------------------
# Paths
# -------------------------------
BASE = Path(r"C:\Users\PC\Desktop\HS2026\files")
INPUT_XML = BASE / "mame.xml"
OUTPUT_XML = BASE / "Naomi_Vertical.xml"

# -------------------------------
# Load MAME XML
# -------------------------------
tree = ET.parse(INPUT_XML)
root = tree.getroot()

# -------------------------------
# Filter Naomi vertical games
# -------------------------------
naomi_games = []
parent_count = 0

for machine in root.findall("machine"):
    # Only Naomi games
    sourcefile = machine.get("sourcefile") or ""
    if sourcefile.lower() != "naomi.cpp":
        continue

    # Only vertical
    display = machine.find("display")
    rotate = display.get("rotate", "0") if display is not None else "0"
    if rotate not in ("90", "270"):
        continue

    # Build HyperSpin <game>
    game = ET.Element("game", name=machine.get("name") or "", index="", image="")

    ET.SubElement(game, "description").text = machine.findtext("description") or machine.get("name") or ""
    ET.SubElement(game, "cloneof").text = machine.get("cloneof") or ""
    ET.SubElement(game, "crc").text = ""
    ET.SubElement(game, "manufacturer").text = machine.findtext("manufacturer") or ""
    ET.SubElement(game, "year").text = machine.findtext("year") or ""
    ET.SubElement(game, "genre").text = machine.findtext("genre") or ""
    ET.SubElement(game, "rating").text = ""
    ET.SubElement(game, "enabled").text = "Yes"

    naomi_games.append(game)

    # Count parents only
    if not (machine.get("cloneof") or "").strip():
        parent_count += 1

# -------------------------------
# Pretty-print helper
# -------------------------------
def indent(elem, level=0):
    i = "\n" + level*"    "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "    "
        for child in elem:
            indent(child, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# -------------------------------
# Build menu XML
# -------------------------------
menu = ET.Element("menu")
for g in naomi_games:
    menu.append(g)

indent(menu)

# -------------------------------
# Save XML
# -------------------------------
ET.ElementTree(menu).write(
    OUTPUT_XML,
    encoding="utf-8",
    xml_declaration=True
)

# -------------------------------
# Print summary
# -------------------------------
print(f"Total Naomi vertical games: {len(naomi_games)}")
print(f"Number of parent games: {parent_count}")
print(f"Output file: {OUTPUT_XML}")

"""
Naomi games to remove:
    
quizqgd
shors2k1
shorse
shorsep
shorsepr
"""

import xml.etree.ElementTree as ET
from pathlib import Path

# -------------------------------
# Paths
# -------------------------------
BASE = Path(r"C:\Users\PC\Desktop\HS2026\files")
INPUT_XML = BASE / "Naomi_Vertical.xml"

# -------------------------------
# List of games to remove
# -------------------------------
REMOVE_GAMES = {"quizqgd", "shors2k1", "shorse", "shorsep", "shorsepr"}

# -------------------------------
# Load XML
# -------------------------------
tree = ET.parse(INPUT_XML)
root = tree.getroot()

# -------------------------------
# Helper to pretty-print XML
# -------------------------------
def indent(elem, level=0):
    i = "\n" + level * "    "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "    "
        for child in elem:
            indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# -------------------------------
# Build new menu
# -------------------------------
new_root = ET.Element("menu")
kept_count = 0
removed_count = 0

for game in root.findall("game"):
    name = game.get("name") or ""
    if name in REMOVE_GAMES:
        removed_count += 1
        continue
    new_root.append(game)
    kept_count += 1

indent(new_root)

# -------------------------------
# OVERWRITE original XML
# -------------------------------
ET.ElementTree(new_root).write(
    INPUT_XML,
    encoding="utf-8",
    xml_declaration=True
)

print(f"XML overwritten: {INPUT_XML}")
print(f"Total games kept: {kept_count}")
print(f"Total games removed: {removed_count}")
