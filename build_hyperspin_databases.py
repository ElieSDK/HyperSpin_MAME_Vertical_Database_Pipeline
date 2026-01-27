"""
FULL MAME / HYPERSPIN DATABASE PIPELINE
FINAL – COMPLETE – STABLE
"""

# =================================================
# IMPORTS
# =================================================
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import re

# =================================================
# PATHS
# =================================================
BASE = Path(r"C:\Users\PC\Desktop\HS2026\files")

MAME_EXE = BASE / "mame.exe"

DB = BASE / "databases"
DB.mkdir(exist_ok=True)

MAME_XML = DB / "mame.xml"
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
    "Nichibutsu","Nintendo","Novotech","Psikyo","Sammy","Sega",
    "Seibu Kaihatsu","SNK","Taito","Williams"
]

REMOVE_NAOMI = {"quizqgd","shors2k1","shorse","shorsep","shorsepr"}

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
    i = "\n" + level*"    "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "    "
        for c in elem:
            indent(c, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    elif level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i

# =================================================
# 1) GENERATE MAME.XML
# =================================================
print("Generating mame.xml...")
with open(MAME_XML, "w", encoding="utf-8") as f:
    subprocess.run(
        [MAME_EXE, "-listxml"],
        stdout=f,
        stderr=subprocess.DEVNULL,
        check=True
    )

mame_root = ET.parse(MAME_XML).getroot()

# =================================================
# 2) ADD DODONPACHI SAIDAI-OU-JOU TO HYPERSPIN DB
# =================================================
print("Adding DoDonPachi SaiDaiOuJou...")

target = "DoDonPachi Dai-Ou-Jou Tamashii (V201, China)"

new_entry = """<game name="ddpsdoj" index="" image="">
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

lines = HS_XML.read_text(encoding="utf-8").splitlines(keepends=True)
out, wait, inserted = [], False, False

for line in lines:
    out.append(line)
    if target in line:
        wait = True
    if wait and "</game>" in line:
        out.append(new_entry + "\n")
        inserted = True
        wait = False

if inserted:
    HS_XML.write_text("".join(out), encoding="utf-8")

# =================================================
# 3) KEEP VERTICAL GAMES ONLY
# =================================================
vertical = set()
for m in mame_root.findall("machine"):
    d = m.find("display")
    if d is not None and d.get("rotate") in ("90", "270"):
        vertical.add(m.get("name"))

hs_root = ET.parse(HS_XML).getroot()
menu = ET.Element("menu")

for g in hs_root.findall("game"):
    parent = (g.findtext("cloneof") or "").strip() or g.get("name")
    if parent in vertical:
        menu.append(g)

ET.ElementTree(menu).write(VERTICAL_XML, encoding="utf-8", xml_declaration=True)

# =================================================
# 4) SPLIT VERTICAL BY GENRE
# =================================================
root = ET.parse(VERTICAL_XML).getroot()
by_genre = defaultdict(list)

for g in root.findall("game"):
    by_genre[clean_filename(g.findtext("genre"))].append(g)

for genre, games in by_genre.items():
    m = ET.Element("menu")
    for g in games:
        m.append(g)
    ET.ElementTree(m).write(GENRES_VERTICAL / f"{genre}.xml",
                            encoding="utf-8", xml_declaration=True)

# =================================================
# 5) SPLIT VERTICAL BY MANUFACTURER
# =================================================
for manu in PRIORITY:
    games = [g for g in root.findall("game")
             if pick_manufacturer(g.findtext("manufacturer")) == manu]
    if games:
        m = ET.Element("menu")
        for g in games:
            m.append(g)
        ET.ElementTree(m).write(MANU_VERTICAL / f"{manu} Games.xml",
                                encoding="utf-8", xml_declaration=True)

# =================================================
# 6) SPLIT SHMUPS BY MANUFACTURER
# =================================================
shmups = ET.parse(GENRES_VERTICAL / "Shoot-'Em-Up.xml").getroot()

for manu in PRIORITY:
    games = [g for g in shmups.findall("game")
             if pick_manufacturer(g.findtext("manufacturer")) == manu]
    if games:
        m = ET.Element("menu")
        for g in games:
            m.append(g)
        ET.ElementTree(m).write(MANU_SHMUPS / f"{manu} Games.xml",
                                encoding="utf-8", xml_declaration=True)

# =================================================
# 7) SPLIT MANUFACTURER → GENRE
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
        ET.ElementTree(m).write(d / f"{clean_filename(genre)}.xml",
                                encoding="utf-8", xml_declaration=True)

# =================================================
# 8) NAOMI VERTICAL GAMES
# =================================================
menu = ET.Element("menu")

for m in mame_root.findall("machine"):
    if m.get("sourcefile","").lower() != "naomi.cpp":
        continue
    d = m.find("display")
    if d is None or d.get("rotate") not in ("90","270"):
        continue

    g = ET.Element("game", name=m.get("name"), index="", image="")
    for t in ("description","manufacturer","year","genre"):
        ET.SubElement(g, t).text = m.findtext(t) or ""
    ET.SubElement(g, "cloneof").text = m.get("cloneof") or ""
    ET.SubElement(g, "crc").text = ""
    ET.SubElement(g, "rating").text = ""
    ET.SubElement(g, "enabled").text = "Yes"
    menu.append(g)

indent(menu)
ET.ElementTree(menu).write(NAOMI_XML, encoding="utf-8", xml_declaration=True)

# =================================================
# 9) REMOVE BAD NAOMI GAMES
# =================================================
root = ET.parse(NAOMI_XML).getroot()
menu = ET.Element("menu")

for g in root.findall("game"):
    if g.get("name") not in REMOVE_NAOMI:
        menu.append(g)

indent(menu)
ET.ElementTree(menu).write(NAOMI_XML, encoding="utf-8", xml_declaration=True)

# =================================================
# 10) COMPLETE NAOMI GENRES FROM ALL GAMES DB
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
# 11) SPLIT NAOMI BY GENRE
# =================================================
root = ET.parse(NAOMI_XML).getroot()
by_genre = defaultdict(list)

for g in root.findall("game"):
    by_genre[clean_filename(g.findtext("genre"))].append(g)

for genre, games in by_genre.items():
    m = ET.Element("menu")
    for g in games:
        m.append(g)
    ET.ElementTree(m).write(GENRES_NAOMI / f"{genre}.xml",
                            encoding="utf-8", xml_declaration=True)

# =================================================
# 12) MOVE mame.xml BACK TO BASE
# =================================================
final_mame = BASE / "mame.xml"
MAME_XML.replace(final_mame)

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

print("\n✔ ALL STEPS COMPLETE")
print("✔ Databases:", DB)
print("✔ mame.xml:", final_mame)
