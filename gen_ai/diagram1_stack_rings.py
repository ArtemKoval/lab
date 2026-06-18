"""Diagram 1 — concentric rings: where value moves in the enterprise AI stack.
Renders a 768x576 pt PDF; rasterize at 150 dpi for a 1600x1200 px PNG.
"""
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

FP = '/usr/share/fonts/truetype/google-fonts/'
pdfmetrics.registerFont(TTFont('Poppins', FP + 'Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', FP + 'Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', FP + 'Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', FP + 'Poppins-Light.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Italic', FP + 'Poppins-Italic.ttf'))

NAVY = HexColor('#1E2A4A'); SAPPHIRE = HexColor('#244F9C'); GRAPHITE = HexColor('#3A3F4B')
IVORY = HexColor('#F0EAD6'); OCHRE = HexColor('#C8862B'); EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A'); AMETHYST = HexColor('#5E4B8B'); TEAL = HexColor('#1E7A7A')
MUSTARD = HexColor('#D6A92E'); UMBER = HexColor('#5C4326'); TAUPE = HexColor('#8A7E6D')
BRICK = HexColor('#A04A2A'); WHITE = HexColor('#FFFFFF')

W, H = 768, 576
c = canvas.Canvas('diagram1_stack_rings.pdf', pagesize=(W, H))
c.setFillColor(WHITE); c.rect(0, 0, W, H, fill=1, stroke=0)

def ctext(x, y, s, font, size, color):
    c.setFont(font, size); c.setFillColor(color); c.drawCentredString(x, y, s)

def ltext(x, y, s, font, size, color):
    c.setFont(font, size); c.setFillColor(color); c.drawString(x, y, s)

# Title
ctext(W / 2, H - 44, 'Where value moves in the enterprise AI stack', 'Poppins-Bold', 21, NAVY)
ctext(W / 2, H - 67, 'Capability sits at the core. Durable value compounds outward.', 'Poppins-Italic', 12, GRAPHITE)

# Concentric rings (drawn largest disc first, smallest on top)
cx, cy = 248, 258
rings = [
    (210, EMERALD,   'Context'),
    (168, AMETHYST,  'Governance'),
    (126, TEAL,      'Orchestration'),
    (84,  SAPPHIRE,  'Routing'),
    (46,  GRAPHITE,  'Model'),
]
for r, col, _ in rings:
    c.setFillColor(col); c.setStrokeColor(WHITE); c.setLineWidth(2)
    c.circle(cx, cy, r, fill=1, stroke=1)

# Center label only (full room — avoids inner-band overflow)
ctext(cx, cy + 4, 'Model', 'Poppins-Bold', 14, IVORY)
ctext(cx, cy - 12, 'commodity', 'Poppins-Italic', 9.5, IVORY)

# Legend (right) maps colors to layers, ordered core outward
lx, sw = 478, 494
rows = [
    (GRAPHITE,  'Model',         'rent | churns | obsolete within a year'),
    (SAPPHIRE,  'Routing',       'which model, which size, when to escalate'),
    (TEAL,      'Orchestration', 'how agents coordinate and stay coherent'),
    (AMETHYST,  'Governance',    'classifiers, policy, audit trail, retention'),
    (EMERALD,   'Context',       'retrieval, domain knowledge, evaluation'),
]
ctext(620, 432, 'From the core outward', 'Poppins-Medium', 12.5, NAVY)
y = 398
for col, name, desc in rows:
    c.setFillColor(col); c.circle(sw + 8, y + 1, 10, fill=1, stroke=0)
    ltext(lx + 38, y + 4, name, 'Poppins-Bold', 13, NAVY)
    ltext(lx + 38, y - 11, desc, 'Poppins', 9.3, GRAPHITE)
    y -= 50

# Inner = rent, outer = own annotations
ctext(620, 150, 'Value and durability increase from the core outward.', 'Poppins-Italic', 10, GRAPHITE)

# Footer
ctext(W / 2, 26, 'Routing | orchestration | governance | context — the layer that survives a model swap.',
      'Poppins-Italic', 10.5, GRAPHITE)

c.showPage(); c.save()
print('wrote diagram1_stack_rings.pdf')
