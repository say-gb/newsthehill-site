from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FONTS = Path('/usr/share/fonts/opentype/noto')
BOLD = FONTS / 'NotoSansCJK-Bold.ttc'
REGULAR = FONTS / 'NotoSansCJK-Regular.ttc'


def font(size, regular=False):
    path = REGULAR if regular and REGULAR.exists() else BOLD
    for index in range(10):
        face = ImageFont.truetype(str(path), size, index=index)
        if face.getname()[0] == 'Noto Sans CJK KR':
            return face
    raise RuntimeError(f'Korean face missing: {path}')


card = Image.new('RGB', (320, 400), '#faf6ee')
draw = ImageDraw.Draw(card)
draw.rectangle((0, 0, 319, 399), outline='#c9a96a', width=2)


def centered(text, top, face, fill, spacing=0):
    boxes = [draw.textbbox((0, 0), char, font=face) for char in text]
    if not spacing:
        boxes = [draw.textbbox((0, 0), text, font=face)]
    parts = list(text) if spacing else [text]
    width = sum(box[2] - box[0] for box in boxes) + spacing * (len(parts) - 1)
    x = (320 - width) / 2
    for part, box in zip(parts, boxes):
        position = (x - box[0], top - box[1])
        left, upper, right, lower = draw.textbbox(position, part, font=face)
        assert 18 <= left <= right <= 302 and 18 <= upper <= lower <= 382
        draw.text(position, part, font=face, fill=fill)
        x += box[2] - box[0] + spacing


centered('최경집 교수의', 48, font(30), '#283043')
title = '현장 마케팅 노트'
title_font = font(38)
bbox = draw.textbbox((0, 0), title, font=title_font)
if bbox[2] - bbox[0] <= 284:
    centered(title, 124, title_font, '#283043')
else:
    centered('현장', 112, title_font, '#283043')
    centered('마케팅 노트', 164, title_font, '#283043')
draw.line((135, 235, 185, 235), fill='#c9a96a', width=2)
centered('매주 연재 · 뉴스더힐 칼럼', 265, font(22, regular=True), '#666666')
centered('NEWS THE HILL', 350, font(18), '#a88a4f', spacing=2)

output = ROOT / 'static/banners/rec-column-160x200.png'
card.save(output, optimize=True)
print(f'{output.relative_to(ROOT)}: {card.width}x{card.height} px, {output.stat().st_size:,} bytes')
