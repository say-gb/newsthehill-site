"""뉴스더힐 카드 렌더러 (코덱스 카드뉴스 스타일).
사용: python3 tools/cards/render.py <카드.html> <출력.jpg>
- 카드 HTML은 tools/cards/ 안에 두고 base.css를 링크한다(sample-*.html 복사해서 글자만 바꾼다).
- 1200x675로 그려 2배 렌더 후 1600x900 JPG로 저장.
"""
import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image
src, out = os.path.abspath(sys.argv[1]), sys.argv[2]
png = out + '.png'
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1200, 'height': 675}, device_scale_factor=2)
    pg.goto('file://' + src); pg.wait_for_timeout(700); pg.screenshot(path=png); b.close()
Image.open(png).convert('RGB').resize((1600, 900), Image.LANCZOS).save(out, quality=90)
os.remove(png)
