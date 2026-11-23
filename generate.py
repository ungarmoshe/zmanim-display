#!/usr/bin/env python3
"""Generate the daily zmanim display image (dark card, matching the user's reference display).

Fetches Hebcal zmanim/shabbat/hebrew-date for a US ZIP and renders a JPEG.
All dates/times are computed in the location timezone (America/New_York), never the host clock.
"""
import json
import sys
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

ZIP = sys.argv[1] if len(sys.argv) > 1 else "11205"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/downloads/zmanim-image/zmanim.jpg"
TZ = ZoneInfo("America/New_York")
HEBCAL = "https://www.hebcal.com"

W = 1000
BG = "#16181d"
INK = "#ededed"
INK2 = "#b7b9bd"
INK3 = "#7d8085"
TEAL = "#8fc8b8"
HAIR = "#2a2e35"

NOTO = "/usr/share/fonts/truetype/noto/"
DEJAVU = "/usr/share/fonts/truetype/dejavu/"

ZMANIM = [
    ("alotHaShachar", "עלות השחר", "Alos", "16.1°"),
    ("misheyakir", "משיכיר", "Talis & Tefillin", "11.5°"),
    ("sunrise", "הנץ החמה", "Netz", None),
    ("sofZmanShmaMGA", "סוף זמן ק״ש", "Shma (M.A.)", "מג״א · יום מ־72 דק׳"),
    ("sofZmanTfillaMGA", "סוף זמן תפילה", "Tefila (M.A.)", "מג״א · יום מ־72 דק׳"),
    ("chatzot", "חצות", "Chatzos", None),
    ("minchaGedola", "מנחה גדולה", "Mincha Gedola", None),
    ("minchaKetana", "מנחה קטנה", "Mincha Ketana", None),
    ("sunset", "שקיעה", "Shkia", None),
    ("tzeit72min", "צאת ר״ת", "Tzeis", "72 דק׳ קבועות"),
]

def _truetype_with_fallback(size, *paths):
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    raise OSError(f"none of the font paths exist: {paths}")


F_TITLE = ImageFont.truetype(NOTO + "NotoSansHebrew-Bold.ttf", 58)
F_SUB = ImageFont.truetype(DEJAVU + "DejaVuSans.ttf", 30)
F_SUB_HE = ImageFont.truetype(NOTO + "NotoSansHebrew-Regular.ttf", 30)
F_STATUS_HE = ImageFont.truetype(DEJAVU + "DejaVuSans.ttf", 34)
F_STATUS_EN = ImageFont.truetype(DEJAVU + "DejaVuSans-Bold.ttf", 34)
F_ROW_HE = _truetype_with_fallback(40, NOTO + "NotoSansHebrew-SemiBold.ttf", NOTO + "NotoSansHebrew-Bold.ttf", NOTO + "NotoSansHebrew-Regular.ttf")
F_ROW_EN = ImageFont.truetype(DEJAVU + "DejaVuSans.ttf", 26)
F_METHOD = ImageFont.truetype(DEJAVU + "DejaVuSans.ttf", 26)
F_TIME = ImageFont.truetype(DEJAVU + "DejaVuSans-Bold.ttf", 44)
F_SECTION = ImageFont.truetype(NOTO + "NotoSansHebrew-Bold.ttf", 40)
F_FOOTER = ImageFont.truetype(DEJAVU + "DejaVuSans.ttf", 22)
F_FOOTER_HE = ImageFont.truetype(NOTO + "NotoSansHebrew-Regular.ttf", 24)

X0, X1 = 56, W - 56


def get(path):
    req = urllib.request.Request(HEBCAL + path, headers={"User-Agent": "zmanim-display/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def fmt_time(iso):
    return datetime.fromisoformat(iso).astimezone(TZ).strftime("%-I:%M %p")


def fmt_day(iso):
    return datetime.fromisoformat(iso).astimezone(TZ).strftime("%A, %B %-d")


def seg_width(d, segments):
    return sum(d.textlength(t, font=f) for t, f, _d, _c in segments)


def draw_segments(d, x, y, segments):
    for text, font, direction, fill in segments:
        d.text((x, y), text, font=font, fill=fill, direction=direction)
        x += d.textlength(text, font=font)
    return x


def main():
    import os
    now = (datetime.fromisoformat(os.environ["ZMANIM_NOW"]).astimezone(TZ)
           if os.environ.get("ZMANIM_NOW") else datetime.now(TZ))
    today = now.strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    zmanim = get(f"/zmanim?cfg=json&zip={ZIP}&date={today}")
    shabbat = get(f"/shabbat?cfg=json&zip={ZIP}&M=on")
    heb_today = get(f"/converter?cfg=json&date={today}&g2h=1")
    heb_tomorrow = get(f"/converter?cfg=json&date={tomorrow}&g2h=1")

    times = zmanim["times"]
    city = zmanim["location"]["title"]
    # Hebrew date labeled as belonging to the listed civil day's zmanim:
    # the day starts as heb_today and turns to heb_tomorrow at shkiah.
    hebrew_date = f'{heb_today["hebrew"]} · אחרי השקיעה {heb_tomorrow["hebrew"]}'

    items = shabbat.get("items", [])
    candles = next((i for i in items if i["category"] == "candles"), None)
    havdalah = next((i for i in items if i["category"] == "havdalah"), None)
    parsha = next((i for i in items if i["category"] == "parashat"), None)

    rows = [(he, en, m, times[k]) for k, he, en, m in ZMANIM if k in times]

    shabbos_rows = []
    if candles:
        shabbos_rows.append(("הדלקת נרות", [("18 דקות לפני השקיעה", F_METHOD, "rtl", INK3)], fmt_day(candles["date"]), fmt_time(candles["date"])))
    if havdalah:
        shabbos_rows.append(("צאת שבת", [("8.5°", F_METHOD, "rtl", INK3)], fmt_day(havdalah["date"]), fmt_time(havdalah["date"])))
    if parsha:
        shabbos_rows.append(("פרשת השבוע", None, None, parsha["hebrew"]))

    # Layout pass: compute total height before drawing.
    H_CONTENT = 56 + 92 + 46 + 58  # title, sub, hebrew date
    sections = 1 + (1 if shabbos_rows else 0)
    H_CONTENT += sections * (24 + 62)
    total_rows = len(rows) + len(shabbos_rows)
    H_CONTENT += total_rows * (48 + 34 + 26)
    H = H_CONTENT + 90  # footer room

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    y = 56

    d.text((X0, y), "זמני היום", font=F_TITLE, fill=INK, direction="rtl")
    y += 92
    d.text((X0, y), f"Zmanim for {now.strftime('%a, %b %-d, %Y')} · {city}", font=F_SUB, fill=INK2)
    y += 46
    d.text((X0, y), hebrew_date, font=F_SUB, fill=TEAL, direction="rtl")
    y += 58

    def section(title):
        nonlocal y
        y += 24
        d.text((X0, y), title, font=F_SECTION, fill=INK, direction="rtl")
        y += 62

    def row(he, detail_segments, value, value_is_hebrew=False):
        nonlocal y
        d.text((X0, y), he, font=F_ROW_HE, fill=INK, direction="rtl")
        if value_is_hebrew:
            w = d.textlength(value, font=F_ROW_HE)
            d.text((X1 - w, y), value, font=F_ROW_HE, fill=TEAL, direction="rtl")
        else:
            d.text((X1 - d.textlength(value, font=F_TIME), y - 2), value, font=F_TIME, fill=TEAL)
        y += 48
        if detail_segments:
            draw_segments(d, X0, y, detail_segments)
            y += 34
        else:
            y += 10
        d.line((X0, y, X1, y), fill=HAIR, width=1)
        y += 26

    section("זמני היום")
    for he, en, method, iso in rows:
        detail = [(en, F_ROW_EN, None, INK3)]
        if method:
            detail += [("  ·  ", F_ROW_EN, None, INK3), (method, F_METHOD, "rtl", INK3)]
        row(he, detail, fmt_time(iso))

    if shabbos_rows:
        section("שבת")
        for he, method_segs, day, value in shabbos_rows:
            detail = []
            if day:
                detail.append((day, F_ROW_EN, None, INK3))
            if method_segs:
                detail.append(("  ·  ", F_ROW_EN, None, INK3))
                detail += method_segs
            row(he, detail or None, value, value_is_hebrew=he == "פרשת השבוע")

    y = H - 52
    d.text((X0, y), "מתעדכן אוטומטית כל יום", font=F_FOOTER_HE, fill=INK3, direction="rtl")
    footer_en = f"Generated {now.strftime('%b %-d, %-I:%M %p')} ET · Source: Hebcal.com"
    d.text((X1 - d.textlength(footer_en, font=F_FOOTER), y + 4), footer_en, font=F_FOOTER, fill=INK3)

    img.save(OUT, "JPEG", quality=88)
    print(OUT, f"{W}x{H}")


if __name__ == "__main__":
    main()
