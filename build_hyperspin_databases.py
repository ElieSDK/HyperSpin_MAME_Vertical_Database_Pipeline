"""
FULL MAME / HYPERSPIN DATABASE PIPELINE
FINAL – COMPLETE – STABLE – DYNAMIC INJECTION
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
BASE = Path(r"PATH")

MAME_EXE = BASE / "mame.exe"
DDP_INJECT_XML = BASE / "ddpsdoj.xml" # The file you mentioned

DB = BASE / "databases"
DB.mkdir(exist_ok=True)

MAME_XML = BASE / "mame.xml" 
HS_XML = BASE / "Mame 0.284.xml"
ALL_GAMES_XML = BASE / "Mame 0.284 All games.xml"

VERTICAL_XML = DB / "Mame 0.284 Vertical.xml"
NAOMI_XML = DB / "Naomi_Vertical.xml"

# Directory setup
DIRS = [
    DB / "genres - vertical",
    DB / "manufacturer - vertical",
    DB / "manufacturer - shmups",
    DB / "manufacturer - vertical by genres",
    DB / "genres - naomi"
]
for d in DIRS: d.mkdir(exist_ok=True)

# =================================================
# CONSTANTS & CONFIG
# =================================================
PRIORITY = [
    "AMCOE","Atari","Bally","BFM","Capcom","Cave","Data East","Gaelco",
    "IGS","IGT","Irem","Jaleco","Kaneko","Konami","Midway","Namco",
    "Nichibutsu","Nintendo","Novotech","Psikyo","Sega",
    "Seibu Kaihatsu","SNK","Taito"
]

REMOVE_NAOMI = {"quizqgd","shors2k1","shorse","shorsep","shorsepr"}
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
# 1) GENERATE & PATCH MAME.XML
# =================================================
print(f"Generating mame.xml...")
with open(MAME_XML, "w", encoding="utf-8") as f:
    subprocess.run([MAME_EXE, "-listxml"], stdout=f, stderr=subprocess.DEVNULL, check=True)

mame_tree = ET.parse(MAME_XML)
mame_root = mame_tree.getroot()

# INJECTION STEP: Add ddpsdoj from its own XML file into the main MAME tree
if DDP_INJECT_XML.exists():
    print(f"Patching {DDP_INJECT_XML.name} into MAME database...")
    ddp_element = ET.parse(DDP_INJECT_XML).getroot() # This is the <machine> tag
    
    # Check if already there to avoid duplicates
    if mame_root.find(f".//machine[@name='{ddp_element.get('name')}']") is None:
        mame_root.append(ddp_element)
        # Re-save the MAME XML so later steps see it as a "real" MAME game
        indent(mame_root)
        mame_tree.write(MAME_XML, encoding="utf-8", xml_declaration=True)
        print("✔ ddpsdoj injected successfully.")
    else:
        print("✔ ddpsdoj already exists in MAME tree.")

# =================================================
# 2) BUILD NAOMI VERTICAL DATABASE
# =================================================
print("Building Naomi vertical database...")
naomi_menu = ET.Element("menu")
for m in mame_root.findall("machine"):
    source = m.get("sourcefile", "").lower()
    if not source.endswith("naomi.cpp"):
        continue
    disp = m.find("display")
    if disp is None or disp.get("rotate") not in ("90", "270"):
        continue
    
    # Filter bad Naomi games
    if m.get("name") in REMOVE_NAOMI:
        continue

    g = ET.Element("game", name=m.get("name"), index="", image="")
    for t in ("description", "manufacturer", "year"):
        ET.SubElement(g, t).text = m.findtext(t) or ""
    ET.SubElement(g, "genre").text = "" # Will fill from lookup later
    ET.SubElement(g, "cloneof").text = m.get("cloneof") or ""
    ET.SubElement(g, "crc").text = ""
    ET.SubElement(g, "rating").text = ""
    ET.SubElement(g, "enabled").text = "Yes"
    naomi_menu.append(g)

# Lookup Naomi genres from 'All Games' XML
lookup = {g.get("name"): g.findtext("genre") for g in ET.parse(ALL_GAMES_XML).getroot().findall("game")}
for g in naomi_menu.findall("game"):
    if g.get("name") in lookup:
        g.find("genre").text = lookup[g.get("name")]

indent(naomi_menu)
ET.ElementTree(naomi_menu).write(NAOMI_XML, encoding="utf-8", xml_declaration=True)

# Split Naomi by genre
by_genre = defaultdict(list)
for g in naomi_menu.findall("game"):
    by_genre[clean_filename(g.findtext("genre"))].append(g)
for genre, games in by_genre.items():
    m = ET.Element("menu")
    for g in games: m.append(g)
    ET.ElementTree(m).write(DB / "genres - naomi" / f"{genre}.xml", encoding="utf-8", xml_declaration=True)

# =================================================
# 3) MERGE NAOMI INTO MAIN HS DB & SORT
# =================================================
print("Merging Naomi into main HyperSpin DB...")
hs_tree = ET.parse(HS_XML)
hs_root = hs_tree.getroot()

# Since we injected ddpsdoj into MAME, we check if it's missing from HS and add it generically
# Note: SaiDaiOuJou is NOT Naomi, so it will be handled by the Vertical filter below.
# This loop handles the Sega Naomi merge.
existing = {g.get("name") for g in hs_root.findall("game")}
for g in naomi_menu.findall("game"):
    if g.get("name") not in existing:
        hs_root.append(g)

# Sort everything alphabetically
sorted_games = sorted(hs_root.findall("game"), key=lambda g: g.get("name", "").lower())
new_hs_root = ET.Element("menu")
for g in sorted_games: new_hs_root.append(g)
indent(new_hs_root)
ET.ElementTree(new_hs_root).write(HS_XML, encoding="utf-8", xml_declaration=True)

# =================================================
# 4) FILTER VERTICAL (INCLUDES INJECTED DDPSDOJ)
# =================================================
print("Creating Vertical Database...")
# Build a set of vertical machine names from the MAME XML
vertical_names = set()
for m in mame_root.findall("machine"):
    d = m.find("display")
    if d is not None and d.get("rotate") in ("90", "270"):
        vertical_names.add(m.get("name"))

# Filter HS_XML based on the vertical list
final_vertical_menu = ET.Element("menu")
for g in new_hs_root.findall("game"):
    name = g.get("name")
    parent = (g.findtext("cloneof") or "").strip() or name
    
    # ddpsdoj is now in 'vertical_names' because we injected its display/rotate info!
    if (parent in vertical_names or name in vertical_names) and name not in REMOVE_GAMES:
        final_vertical_menu.append(g)

indent(final_vertical_menu)
ET.ElementTree(final_vertical_menu).write(VERTICAL_XML, encoding="utf-8", xml_declaration=True)

# =================================================
# 5) SPLITS (GENRE / MANUFACTURER)
# =================================================
root = final_vertical_menu
# Vertical by Genre
by_genre = defaultdict(list)
for g in root.findall("game"):
    by_genre[clean_filename(g.findtext("genre"))].append(g)
for genre, games in by_genre.items():
    m = ET.Element("menu")
    for g in games: m.append(g)
    ET.ElementTree(m).write(DB / "genres - vertical" / f"{genre}.xml", encoding="utf-8", xml_declaration=True)

# Vertical by Manufacturer
for manu in PRIORITY:
    games = [g for g in root.findall("game") if pick_manufacturer(g.findtext("manufacturer")) == manu]
    if games:
        m = ET.Element("menu")
        for g in games: m.append(g)
        ET.ElementTree(m).write(DB / "manufacturer - vertical" / f"{manu}.xml", encoding="utf-8", xml_declaration=True)

# Shmups by Manufacturer
shmup_file = DB / "genres - vertical" / "Shoot-'Em-Up.xml"
if shmup_file.exists():
    shmups = ET.parse(shmup_file).getroot()
    for manu in PRIORITY:
        games = [g for g in shmups.findall("game") if pick_manufacturer(g.findtext("manufacturer")) == manu]
        if games:
            m = ET.Element("menu")
            for g in games: m.append(g)
            ET.ElementTree(m).write(DB / "manufacturer - shmups" / f"{manu}.xml", encoding="utf-8", xml_declaration=True)

# Manufacturer -> Genre subfolders
bucket = defaultdict(lambda: defaultdict(list))
for g in root.findall("game"):
    manu = pick_manufacturer(g.findtext("manufacturer"))
    if manu:
        bucket[manu][g.findtext("genre") or "Unknown"].append(g)
for manu, genres in bucket.items():
    d = DB / "manufacturer - vertical by genres" / manu
    d.mkdir(exist_ok=True)
    for genre, games in genres.items():
        m = ET.Element("menu")
        for g in games: m.append(g)
        ET.ElementTree(m).write(d / f"{clean_filename(genre)}.xml", encoding="utf-8", xml_declaration=True)

# =================================================
# 6) FINAL CLEANUP & ORGANIZATION
# =================================================
# Fix &apos;
replacements = {"<genre>Shoot-'Em-Up</genre>": "<genre>Shoot-&apos;Em-Up</genre>", 
                "<genre>Beat-'Em-Up</genre>": "<genre>Beat-&apos;Em-Up</genre>"}
for xml in DB.rglob("*.xml"):
    text = xml.read_text(encoding="utf-8")
    for old, new in replacements.items(): text = text.replace(old, new)
    xml.write_text(text, encoding="utf-8")

# Final move to !Final
FINAL_DIR = DB / "!Final"
FINAL_DIR.mkdir(exist_ok=True)

# Move MAME Vertical
m_dir = FINAL_DIR / "MAME"
m_dir.mkdir(exist_ok=True)
shutil.copy2(VERTICAL_XML, m_dir / "MAME.xml")
for f in (DB / "genres - vertical").glob("*.xml"): shutil.copy2(f, m_dir / f.name)

# Move Naomi
n_dir = FINAL_DIR / "Sega Naomi"
n_dir.mkdir(exist_ok=True)
shutil.copy2(NAOMI_XML, n_dir / "Sega Naomi.xml")
for f in (DB / "genres - naomi").glob("*.xml"): shutil.copy2(f, n_dir / f.name)

# Move Shmups folder
s_dir = FINAL_DIR / "Shoot-'Em-Up"
s_dir.mkdir(exist_ok=True)
if shmup_file.exists(): shutil.copy2(shmup_file, s_dir / "Shoot-'Em-Up.xml")
for f in (DB / "manufacturer - shmups").glob("*.xml"): shutil.copy2(f, s_dir / f.name)

# Move Manufacturer folders
for xml_file in (DB / "manufacturer - vertical").glob("*.xml"):
    target = FINAL_DIR / xml_file.stem
    target.mkdir(exist_ok=True)
    shutil.copy2(xml_file, target / xml_file.name)
if (DB / "manufacturer - vertical by genres").exists():
    shutil.copytree(DB / "manufacturer - vertical by genres", FINAL_DIR, dirs_exist_ok=True)

# =================================================
# 7) CLRMAMEPRO XML (Includes injected ddpsdoj)
# =================================================
print("Generating MAMEclrmame.xml...")
CLRMAME_XML = BASE / "MAMEclrmame.xml"
allowed_names = {g.get("name") for g in final_vertical_menu.findall("game")}
new_mame_root = ET.Element("mame", mame_root.attrib)
for machine in mame_root.findall("machine"):
    if machine.get("name") in allowed_names:
        new_mame_root.append(machine)
indent(new_mame_root)
ET.ElementTree(new_mame_root).write(CLRMAME_XML, encoding="utf-8", xml_declaration=True)

print("\n✔ ALL STEPS COMPLETE")
