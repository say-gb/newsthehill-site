#!/usr/bin/env python3
"""뉴스더힐 자체 인포카드(기사 대표 이미지) 생성기.
사진을 쓸 수 없는 정부 보도자료 기사용. 저작권은 뉴스더힐.
사용: python3 scripts/make_info_card.py spec.json static/img/news-XXXX-card.jpg

spec.json 예:
{"kicker": "식품 회수", "title": ["구리 성림방앗간 들기름", "벤조피렌 기준 초과"],
 "rows": [["검출량", "4.8㎍/kg", "기준 2.0㎍/kg"], ["소비기한", "2027.04.05.", "표시 제품"]],
 "source": "자료: 식품의약품안전처"}
rows: [라벨, 큰 값, 보조 설명(선택)] 최대 4줄
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
NAVY, GOLD, IVORY, WHITE = (40, 48, 67), (201, 162, 75), (246, 240, 228), (255, 255, 255)
SANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-{}.ttc"
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"

def font(path, size):
    # Noto CJK ttc: 한국어(KR) 서체 인덱스를 찾는다
    for i in range(10):
        try:
            f = ImageFont.truetype(path, size, index=i)
        except OSError:
            break
        if "KR" in " ".join(f.getname()):
            return f
    return ImageFont.truetype(path, size)

def main(spec_path, out):
    s = json.load(open(spec_path, encoding="utf-8"))
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    # 왼쪽 금색 띠, 상단 라벨
    d.rectangle([0, 0, 14, H], fill=GOLD)
    f_k = font(SANS.format("Bold"), 30)
    d.text((70, 52), "NEWS THE HILL  ·  " + s.get("kicker", "식품·유통"), font=f_k, fill=GOLD)
    # 제목(최대 2줄)
    f_t = font(SERIF, 62)
    y = 110
    for line in s["title"][:2]:
        d.text((70, y), line, font=f_t, fill=WHITE)
        y += 82
    y += 22
    d.line([70, y, W - 70, y], fill=(90, 100, 122), width=2)
    y += 26
    # 핵심 수치 줄
    rows = s.get("rows", [])[:4]
    f_l = font(SANS.format("Medium"), 30)
    f_v = font(SANS.format("Bold"), 46)
    f_n = font(SANS.format("Regular"), 26)
    gap = (H - 80 - y) // max(len(rows), 1)
    for r in rows:
        label, val = r[0], r[1]
        note = r[2] if len(r) > 2 else ""
        d.text((70, y + 10), label, font=f_l, fill=IVORY)
        d.text((330, y), val, font=f_v, fill=GOLD)
        if note:
            vw = d.textlength(val, font=f_v)
            d.text((330 + vw + 24, y + 16), note, font=f_n, fill=(200, 205, 215))
        y += gap
    # 하단 출처
    f_s = font(SANS.format("Regular"), 24)
    src = s.get("source", "") + "  ·  그래픽=뉴스더힐"
    d.text((70, H - 56), src, font=f_s, fill=(170, 178, 192))
    im.save(out, quality=88)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
