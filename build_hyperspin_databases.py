"""
FULL MAME / HYPERSPIN DATABASE PIPELINE
FINAL – COMPLETE – STABLE – NAOMI INCLUDED
"""

# =================================================
# IMPORTS
# =================================================
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import re
import shutil

# =================================================
# PATHS
# =================================================
BASE = Path(r"PATH HERE")

MAME_EXE = BASE / "mame.exe"

DB = BASE / "databases"
DB.mkdir(exist_ok=True)

MAME_XML = BASE / "mame.xml" 
HS_XML = BASE / "Mame 0.284.xml"
ALL_GAMES_XML = BASE / "Mame 0.284 All games.xml"

VERTICAL_XML = DB / "Mame 0.284 Vertical.xml"
NAOMI_XML = DB / "Naomi_Vertical.xml"

GENRES_VERTICAL = DB / "genres - vertical"
MANU_VERTICAL = DB / "manufacturer - vertical"
MANU_SHMUPS = DB / "manufacturer - shmups"
MANU_GENRES = DB / "manufacturer - vertical by genres"
GENRES_NAOMI = DB / "genres - naomi"

for d in (
    GENRES_VERTICAL,
    MANU_VERTICAL,
    MANU_SHMUPS,
    MANU_GENRES,
    GENRES_NAOMI,
):
    d.mkdir(exist_ok=True)

# =================================================
# CONSTANTS
# =================================================
PRIORITY = [
    "AMCOE","Atari","Bally","BFM","Capcom","Cave","Data East","Gaelco",
    "IGS","IGT","Irem","Jaleco","Kaneko","Konami","Midway","Namco",
    "Nichibutsu","Nintendo","Novotech","Psikyo","Sega",
    "Seibu Kaihatsu","SNK","Taito"
]

REMOVE_NAOMI = {"quizqgd","shors2k1","shorse","shorsep","shorsepr"}

# Exclusion list for specific unwanted games
REMOVE_GAMES = {"kbh", "kbm", "kbm2nd", "kbm3rd", "cmpmx10", "jammin"}

# =================================================
# HELPERS
# =================================================
def clean_filename(text):
    return re.sub(r'[\\/:*?"<>|]', '', (text or "").strip()) or "Unknown"

def normalize(text):
    return re.sub(r"\s*\(.*?\)", "", (text or "").strip())

def pick_manufacturer(raw):
    for part in re.split(r"\s*/\s*|\s*&\s*|\s*\+\s*", raw or ""):
        p = normalize(part)
        if p in PRIORITY:
            return p
    return None

def indent(elem, level=0):
    i = "\n" + level * "    "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "    "
        for c in elem:
            indent(c, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    elif level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i

# =================================================
# 1) GENERATE MAME.XML
# =================================================
print(f"Generating mame.xml in {BASE}...")
with open(MAME_XML, "w", encoding="utf-8") as f:
    subprocess.run(
        [MAME_EXE, "-listxml"],
        stdout=f,
        stderr=subprocess.DEVNULL,
        check=True
    )

mame_root = ET.parse(MAME_XML).getroot()

# =================================================
# 2) ADD DODONPACHI SAIDAI-OU-JOU (STANDALONE PARENT)
# =================================================
print("Checking DoDonPachi SaiDaiOuJou...")

hs_tree = ET.parse(HS_XML)
hs_root = hs_tree.getroot()

# 1. Find all instances of ddpsdoj
existing_ddp = hs_root.findall(".//game[@name='ddpsdoj']")

if not existing_ddp:
    print("→ Adding ddpsdoj (Parent)...")
    g = ET.Element("game", name="ddpsdoj", index="", image="")
    ET.SubElement(g, "description").text = "DoDonPachi SaiDaiOuJou (2012/ 4/20)"
    ET.SubElement(g, "cloneof").text = ""  # Correct: Parent has no cloneof
    ET.SubElement(g, "crc").text = ""
    ET.SubElement(g, "manufacturer").text = "Cave"
    ET.SubElement(g, "year").text = "2012"
    ET.SubElement(g, "genre").text = "Shoot-&apos;Em-Up"
    ET.SubElement(g, "rating").text = ""
    ET.SubElement(g, "enabled").text = "Yes"
    hs_root.append(g)
    
    indent(hs_root)
    hs_tree.write(HS_XML, encoding="utf-8", xml_declaration=True)
    print("✔ SaiDaiOuJou added.")

elif len(existing_ddp) > 1:
    print(f"→ Found {len(existing_ddp)} copies of ddpsdoj. Cleaning duplicates...")
    # Keep the first one, remove the rest
    first_found = False
    for game in hs_root.findall("game"):
        if game.get("name") == "ddpsdoj":
            if not first_found:
                first_found = True
                continue
            hs_root.remove(game)
            
    indent(hs_root)
    hs_tree.write(HS_XML, encoding="utf-8", xml_declaration=True)
    print("✔ Duplicates removed, kept one parent entry.")

else:
    print("✔ SaiDaiOuJou parent already correctly present.")

# =================================================
# 3) NAOMI VERTICAL GAMES
# =================================================
print("Building Naomi vertical database...")
menu = ET.Element("menu")
for m in mame_root.findall("machine"):
    source = m.get("sourcefile", "").lower()
    if not source.endswith("naomi.cpp"):
        continue
    d = m.find("display")
    if d is None or d.get("rotate") not in ("90", "270"):
        continue
    g = ET.Element("game", name=m.get("name"), index="", image="")
    for t in ("description", "manufacturer", "year"):
        ET.SubElement(g, t).text = m.findtext(t) or ""
    ET.SubElement(g, "genre").text = m.findtext("genre") or ""
    ET.SubElement(g, "cloneof").text = m.get("cloneof") or ""
    ET.SubElement(g, "crc").text = ""
    ET.SubElement(g, "rating").text = ""
    ET.SubElement(g, "enabled").text = "Yes"
    menu.append(g)
indent(menu)
ET.ElementTree(menu).write(NAOMI_XML, encoding="utf-8", xml_declaration=True)

# =================================================
# 4) REMOVE BAD NAOMI GAMES
# =================================================
root = ET.parse(NAOMI_XML).getroot()
menu = ET.Element("menu")
for g in root.findall("game"):
    if g.get("name") not in REMOVE_NAOMI:
        menu.append(g)
indent(menu)
ET.ElementTree(menu).write(NAOMI_XML, encoding="utf-8", xml_declaration=True)

# =================================================
# 5) COMPLETE NAOMI GENRES FROM ALL GAMES DB
# =================================================
lookup = {
    g.get("name"): g.findtext("genre")
    for g in ET.parse(ALL_GAMES_XML).getroot().findall("game")
}
root = ET.parse(NAOMI_XML).getroot()
menu = ET.Element("menu")
for g in root.findall("game"):
    name = g.get("name")
    genre = g.find("genre")
    if (genre is None or not (genre.text or "").strip()) and name in lookup:
        if genre is None:
            genre = ET.SubElement(g, "genre")
        genre.text = lookup[name]
    menu.append(g)
indent(menu)
ET.ElementTree(menu).write(NAOMI_XML, encoding="utf-8", xml_declaration=True)

# =================================================
# 5a) SPLIT NAOMI BY GENRE
# =================================================
root = ET.parse(NAOMI_XML).getroot()
by_genre = defaultdict(list)
for g in root.findall("game"):
    by_genre[clean_filename(g.findtext("genre"))].append(g)
for genre, games in by_genre.items():
    m = ET.Element("menu")
    for g in games:
        m.append(g)
    ET.ElementTree(m).write(GENRES_NAOMI / f"{genre}.xml", encoding="utf-8", xml_declaration=True)

# =================================================
# 6) MERGE NAOMI INTO MAIN HS DB + SORT
# =================================================
print("Merging Naomi into main HyperSpin DB...")
hs_root = ET.parse(HS_XML).getroot()
naomi_root = ET.parse(NAOMI_XML).getroot()
existing = {g.get("name") for g in hs_root.findall("game")}
for g in naomi_root.findall("game"):
    if g.get("name") not in existing:
        hs_root.append(g)
games = sorted(hs_root.findall("game"), key=lambda g: g.get("name", "").lower())
new_root = ET.Element("menu")
for g in games:
    new_root.append(g)
indent(new_root)
ET.ElementTree(new_root).write(HS_XML, encoding="utf-8", xml_declaration=True)

# =================================================
# 7) KEEP VERTICAL GAMES ONLY & FILTER BLACKLIST
# =================================================
print("Filtering vertical games and applying blacklist...")

# Define the manual parents that aren't in the official MAME XML
MANUAL_PARENTS = {"ddpsdoj"}

vertical = set()
for m in mame_root.findall("machine"):
    d = m.find("display")
    if d is not None and d.get("rotate") in ("90","270"):
        vertical.add(m.get("name"))

hs_root = ET.parse(HS_XML).getroot()
menu = ET.Element("menu")

for g in hs_root.findall("game"):
    name = g.get("name")
    parent = (g.findtext("cloneof") or "").strip() or name
    
    # NEW LOGIC: Keep if (it's officially vertical OR it's a manual parent) 
    # AND it's not in the blacklist
    if (parent in vertical or name in MANUAL_PARENTS) and name not in REMOVE_GAMES:
        menu.append(g)

ET.ElementTree(menu).write(VERTICAL_XML, encoding="utf-8", xml_declaration=True)
print(f"✔ Vertical filtering complete. '{VERTICAL_XML.name}' updated.")

# =================================================
# 8) SPLIT VERTICAL BY GENRE
# =================================================
root = ET.parse(VERTICAL_XML).getroot()
by_genre = defaultdict(list)
for g in root.findall("game"):
    by_genre[clean_filename(g.findtext("genre"))].append(g)
for genre, games in by_genre.items():
    m = ET.Element("menu")
    for g in games:
        m.append(g)
    ET.ElementTree(m).write(GENRES_VERTICAL / f"{genre}.xml", encoding="utf-8", xml_declaration=True)

# =================================================
# 9) SPLIT VERTICAL BY MANUFACTURER
# =================================================
for manu in PRIORITY:
    games = [g for g in root.findall("game") if pick_manufacturer(g.findtext("manufacturer")) == manu]
    if games:
        m = ET.Element("menu")
        for g in games:
            m.append(g)
        ET.ElementTree(m).write(MANU_VERTICAL / f"{manu}.xml", encoding="utf-8", xml_declaration=True)

# =================================================
# 10) SPLIT SHMUPS BY MANUFACTURER
# =================================================
shmups_path = GENRES_VERTICAL / "Shoot-'Em-Up.xml"
if shmups_path.exists():
    shmups = ET.parse(shmups_path).getroot()
    for manu in PRIORITY:
        games = [g for g in shmups.findall("game") if pick_manufacturer(g.findtext("manufacturer")) == manu]
        if games:
            m = ET.Element("menu")
            for g in games:
                m.append(g)
            ET.ElementTree(m).write(MANU_SHMUPS / f"{manu}.xml", encoding="utf-8", xml_declaration=True)

# =================================================
# 11) SPLIT MANUFACTURER → GENRE
# =================================================
bucket = defaultdict(lambda: defaultdict(list))
for g in root.findall("game"):
    manu = pick_manufacturer(g.findtext("manufacturer"))
    if manu:
        bucket[manu][g.findtext("genre") or "Unknown"].append(g)
for manu, genres in bucket.items():
    d = MANU_GENRES / manu
    d.mkdir(exist_ok=True)
    for genre, games in genres.items():
        m = ET.Element("menu")
        for g in games:
            m.append(g)
        ET.ElementTree(m).write(d / f"{clean_filename(genre)}.xml", encoding="utf-8", xml_declaration=True)

# =================================================
# 13) FIX GENRE STRINGS EVERYWHERE
# =================================================
replacements = {
    "<genre>Shoot-'Em-Up</genre>": "<genre>Shoot-&apos;Em-Up</genre>",
    "<genre>Beat-'Em-Up</genre>": "<genre>Beat-&apos;Em-Up</genre>",
}
for xml in DB.rglob("*.xml"):
    text = xml.read_text(encoding="utf-8")
    for old, new in replacements.items():
        text = text.replace(old, new)
    xml.write_text(text, encoding="utf-8")

# =================================================
# 14) FINAL ORGANIZATION (!Final)
# =================================================
print("Organizing final files into !Final...")
FINAL_DIR = DB / "!Final"
FINAL_DIR.mkdir(exist_ok=True)

MAME_DIR = FINAL_DIR / "MAME"
MAME_DIR.mkdir(exist_ok=True)
shutil.copy2(VERTICAL_XML, MAME_DIR / "MAME.xml")
if GENRES_VERTICAL.exists():
    for f in GENRES_VERTICAL.glob("*.xml"):
        shutil.copy2(f, MAME_DIR / f.name)

NAOMI_DIR = FINAL_DIR / "Sega Naomi"
NAOMI_DIR.mkdir(exist_ok=True)
shutil.copy2(NAOMI_XML, NAOMI_DIR / "Sega Naomi.xml")
if GENRES_NAOMI.exists():
    for f in GENRES_NAOMI.glob("*.xml"):
        shutil.copy2(f, NAOMI_DIR / f.name)

SHMUP_FINAL_FOLDER = FINAL_DIR / "Shoot-'Em-Up"
SHMUP_FINAL_FOLDER.mkdir(exist_ok=True)
shmup_main = GENRES_VERTICAL / "Shoot-'Em-Up.xml"
if shmup_main.exists():
    shutil.copy2(shmup_main, SHMUP_FINAL_FOLDER / "Shoot-'Em-Up.xml")
if MANU_SHMUPS.exists():
    for f in MANU_SHMUPS.glob("*.xml"):
        shutil.copy2(f, SHMUP_FINAL_FOLDER / f.name)

if MANU_VERTICAL.exists():
    for xml_file in MANU_VERTICAL.glob("*.xml"):
        folder_name = xml_file.stem 
        target_folder = FINAL_DIR / folder_name
        target_folder.mkdir(exist_ok=True)
        shutil.copy2(xml_file, target_folder / xml_file.name)

if MANU_GENRES.exists():
    for item in MANU_GENRES.iterdir():
        if item.is_dir():
            shutil.copytree(item, FINAL_DIR / item.name, dirs_exist_ok=True)

# =================================================
# 15) GENERATE MAMEclrmame.xml FOR CLRMAMEPRO
# =================================================
print("Generating MAMEclrmame.xml for ClrMamePro...")
CLRMAME_XML = BASE / "MAMEclrmame.xml"
FINAL_MAME_DB = MAME_DIR / "MAME.xml"

if FINAL_MAME_DB.exists() and MAME_XML.exists():
    filtered_tree = ET.parse(FINAL_MAME_DB)
    allowed_names = {g.get("name") for g in filtered_tree.findall("game")}
    full_mame_tree = ET.parse(MAME_XML)
    full_mame_root = full_mame_tree.getroot()
    new_mame_root = ET.Element("mame")
    for attr_name, attr_value in full_mame_root.attrib.items():
        new_mame_root.set(attr_name, attr_value)
    for machine in full_mame_root.findall("machine"):
        if machine.get("name") in allowed_names:
            new_mame_root.append(machine)
    indent(new_mame_root)
    ET.ElementTree(new_mame_root).write(CLRMAME_XML, encoding="utf-8", xml_declaration=True)
    print(f"✔ ClrMamePro XML created: {CLRMAME_XML}")

print("\n✔ ALL STEPS COMPLETE")
