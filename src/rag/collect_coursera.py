"""
Collecte du contenu INTEGRAL du cours Gamification (Coursera).
Strategie : on ne connait pas le type de chaque item, donc on essaie
les deux endpoints (video transcript + supplement) pour chacun.
"""
import requests
import os
import re
import time

COURSE_SLUG = "gamification"
COURSE_ID = "69Bku0KoEeWZtA4u62x6lQ"
BASE_URL = "https://api.coursera.org"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
OUTPUT_DIR = os.path.join(DATA_DIR, f"coursera_{COURSE_SLUG}")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def clean_html(html_text):
    """Retire les balises HTML pour ne garder que le texte brut."""
    text = re.sub(r"<[^>]+>", "", html_text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    return text.strip()


def safe_filename(name):
    """Transforme un nom en nom de fichier valide."""
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')[:80]


def try_get_transcript(item_id):
    """
    Essaie de recuperer la transcription video d'un item.
    Utilise 'subtitles' (pas subtitlesTxt) car c'est le champ qui contient les URLs.
    Telecharge le fichier de sous-titres en .txt via subtitleAssetProxy.
    """
    try:
        url = (
            f"{BASE_URL}/api/onDemandLectureVideos.v1/"
            f"{COURSE_ID}~{item_id}"
            f"?includes=video&fields=onDemandVideos.v1(subtitles,subtitlesTxt)"
        )
        rv = requests.get(url, timeout=10)
        if rv.status_code != 200:
            return None, False

        vdata = rv.json()
        videos = vdata.get("linked", {}).get("onDemandVideos.v1", [])
        if not videos:
            return None, False

        video = videos[0]

        # Methode 1 : subtitlesTxt (texte brut direct)
        subtitles_txt = video.get("subtitlesTxt", {})
        if subtitles_txt:
            sub_url = subtitles_txt.get("en") or subtitles_txt.get("fr")
            if not sub_url and subtitles_txt:
                sub_url = list(subtitles_txt.values())[0]
            if sub_url:
                if sub_url.startswith("/"):
                    sub_url = BASE_URL + sub_url
                resp = requests.get(sub_url, timeout=10)
                if resp.status_code == 200 and resp.text.strip():
                    return resp.text, True

        # Methode 2 : subtitles (URLs vers subtitleAssetProxy)
        subtitles = video.get("subtitles", {})
        if subtitles:
            sub_path = subtitles.get("en") or subtitles.get("fr")
            if not sub_path and subtitles:
                sub_path = list(subtitles.values())[0]
            if sub_path:
                full_url = BASE_URL + sub_path
                if "fileExtension" not in full_url:
                    full_url += "&fileExtension=txt"
                resp = requests.get(full_url, timeout=10)
                if resp.status_code == 200 and resp.text.strip():
                    return resp.text, True

        return None, False
    except Exception:
        return None, False


def try_get_supplement(item_id):
    """Essaie de recuperer le contenu supplement d'un item."""
    try:
        url = (
            f"{BASE_URL}/api/onDemandSupplements.v1/"
            f"{COURSE_ID}~{item_id}"
            f"?includes=asset&fields=openCourseAssets.v1(typeName),"
            f"openCourseAssets.v1(definition)"
        )
        rs = requests.get(url, timeout=10)
        if rs.status_code != 200:
            return None, False

        sdata = rs.json()
        assets = sdata.get("linked", {}).get("openCourseAssets.v1", [])
        if not assets:
            return None, False

        definition = assets[0].get("definition", {})
        html_content = definition.get("value", "") or definition.get("dtdId", "")
        text_content = clean_html(html_content)
        if not text_content:
            return None, False

        return text_content, True
    except Exception:
        return None, False


# ============================================================
# 1. Recuperer la structure du cours
# ============================================================
print("[1/3] Recuperation de la structure du cours...")
r = requests.get(
    f"{BASE_URL}/api/onDemandCourseMaterials.v2"
    f"?q=slug&slug={COURSE_SLUG}"
    f"&fields=moduleIds,lessonIds"
    f"&includes=modules,lessons,items"
)
r.raise_for_status()
data = r.json()
modules = data["linked"]["onDemandCourseMaterialModules.v1"]
lessons = data["linked"]["onDemandCourseMaterialLessons.v1"]
items = data["linked"]["onDemandCourseMaterialItems.v2"]
print(f"   {len(modules)} modules, {len(lessons)} lecons, {len(items)} items")

# ============================================================
# 2. Pour chaque item, essayer transcript puis supplement
# ============================================================
print(f"\n[2/3] Telechargement du contenu ({len(items)} items)...\n")
video_count = 0
supp_count = 0
skip_count = 0

for idx, item in enumerate(items, 1):
    item_id = item["id"]
    item_name = item.get("name", item_id)
    prefix = f"   [{idx}/{len(items)}]"

    # Essai 1 : transcription video
    transcript, ok = try_get_transcript(item_id)
    if ok and transcript:
        fname = f"transcript_{safe_filename(item_name)}.txt"
        path = os.path.join(OUTPUT_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {item_name}\n\n{transcript}")
        video_count += 1
        print(f"{prefix} [VIDEO] {item_name} ({len(transcript)} chars)")
        time.sleep(0.3)
        continue

    # Essai 2 : supplement / lecture
    content, ok = try_get_supplement(item_id)
    if ok and content:
        fname = f"supplement_{safe_filename(item_name)}.txt"
        path = os.path.join(OUTPUT_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {item_name}\n\n{content}")
        supp_count += 1
        print(f"{prefix} [SUPPL] {item_name} ({len(content)} chars)")
        time.sleep(0.3)
        continue

    # Ni video ni supplement (quiz, peer review, etc.)
    skip_count += 1
    print(f"{prefix} [SKIP]  {item_name}")

# ============================================================
# 3. Resume
# ============================================================
print(f"\n[3/3] Resume :")
print(f"   Transcriptions video : {video_count}")
print(f"   Supplements          : {supp_count}")
print(f"   Ignores (quiz, etc.) : {skip_count}")
print(f"   Total fichiers data/ : {len(os.listdir(OUTPUT_DIR))}")
print(f"\nTermine !")
