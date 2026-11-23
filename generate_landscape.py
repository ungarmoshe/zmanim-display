#!/usr/bin/env python3
"""Landscape companion to generate.py. Same Hebcal data and calculation methods."""
import os
import sys
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import generate as g


def font(size, bold=False, he=False):
    base = g.NOTO + ('NotoSansHebrew-Bold.ttf' if bold else 'NotoSansHebrew-Regular.ttf') if he else g.DEJAVU + ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')
    return ImageFont.truetype(base, size)


def main():
    out = sys.argv[2] if len(sys.argv) > 2 else 'zmanim-landscape.jpg'
    now = datetime.fromisoformat(os.environ['ZMANIM_NOW']).astimezone(g.TZ) if os.environ.get('ZMANIM_NOW') else datetime.now(g.TZ)
    today = now.strftime('%Y-%m-%d')
    tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')
    z = g.get(f'/zmanim?cfg=json&zip={g.ZIP}&date={today}')
    sh = g.get(f'/shabbat?cfg=json&zip={g.ZIP}&M=on')
    hd = g.get(f'/converter?cfg=json&date={today}&g2h=1')
    ht = g.get(f'/converter?cfg=json&date={tomorrow}&g2h=1')
    im = Image.new('RGB', (1920, 1200), g.BG)
    d = ImageDraw.Draw(im)
    def text(x, y, value, f, color=g.INK, rtl=False, right=False):
        if right:
            x -= d.textlength(value, font=f, direction='rtl' if rtl else None)
        d.text((x, y), value, font=f, fill=color, direction='rtl' if rtl else None)
    text(1848, 32, 'זמני היום', font(68, True, True), right=True, rtl=True)
    text(72, 44, now.strftime('%A, %b %-d, %Y'), font(38, True))
    text(72, 100, z['location']['title'], font(30), g.INK2)
    text(1848, 130, hd['hebrew'] + ' · אחרי השקיעה ' + ht['hebrew'], font(32), g.TEAL, rtl=True, right=True)
    d.line((72, 208, 1848, 208), fill=g.HAIR, width=2)
    for idx, (key, he, en, method) in enumerate(g.ZMANIM):
        # Hebrew reading order: morning column on the right, afternoon on the left.
        x = 1000 if idx < 5 else 72
        y = 244 + (idx % 5) * 113
        text(x + 848, y, he, font(42, True, True), rtl=True, right=True)
        text(x, y - 1, g.fmt_time(z['times'][key]), font(46, True), g.TEAL)
        text(x + 848, y + 57, en, font(26), g.INK2, right=True)
        if method:
            text(x, y + 60, method, font(25), g.INK2, rtl=True)
        d.line((x, y + 99, x + 848, y + 99), fill=g.HAIR, width=1)
    d.line((960, 248, 960, 795), fill=g.HAIR, width=2)
    d.rounded_rectangle((72, 850, 1848, 1070), radius=16, fill='#20242b')
    items = sh.get('items', [])
    candle = next((i for i in items if i['category'] == 'candles'), None)
    hav = next((i for i in items if i['category'] == 'havdalah'), None)
    parsha = next((i for i in items if i['category'] == 'parashat'), None)
    groups = [(1272, 'הדלקת נרות', candle, '18 דקות לפני השקיעה'), (672, 'צאת שבת', hav, '8.5°'), (104, 'פרשת השבוע', parsha, None)]
    for x, label, item, method in groups:
        text(x + 496, 868, label, font(32, True, True), right=True, rtl=True)
        if item:
            val = item.get('hebrew', '') if label == 'פרשת השבוע' else g.fmt_time(item['date'])
            text(x + 496, 922, val, font(40, True, label == 'פרשת השבוע'), g.TEAL, right=True, rtl=label == 'פרשת השבוע')
            if method:
                text(x + 496, 984, g.fmt_day(item['date']), font(23), g.INK2, right=True)
                text(x + 496, 1020, method, font(23), g.INK2, right=True, rtl=True)
    text(72, 1093, 'Calculation methods unconfirmed. Check the printed date before use.', font(25), g.INK2)
    text(72, 1140, 'Source: Hebcal.com', font(24), g.INK2)
    text(1848, 1140, 'Generated ' + now.strftime('%b %-d, %Y, %-I:%M:%S %p') + ' ET', font(24), g.INK2, right=True)
    im.save(out, 'JPEG', quality=90)
    print(out, '1920x1200')


if __name__ == '__main__':
    main()
