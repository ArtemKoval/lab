#!/usr/bin/env python3
"""
CAIO Diagram: What Actually Blocks Agents at Scale
Topic: instruction-architecture
Type: Polar area (coxcomb) — survey-data comparison, area-proportional radius
Output: caio-instruction-architecture-diagram-3.png
"""

import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# --- Palette (CAIO standard) ---
NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')
MUSTARD = HexColor('#C4952A')
UMBER = HexColor('#6B4226')
WHITE = HexColor('#FFFFFF')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas Setup ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-instruction-architecture-diagram-3.png'
OUTPUT_PDF = '/tmp/_diagram3_temp.pdf'

# Data: DataHub State of Context Management Report 2026 — obstacles to scaling AI agents
DATA = [
    ('Security & privacy', 51, BURGUNDY),
    ('Tool integration', 43, SAPPHIRE),
    ('Data fragmentation', 41, EMERALD),
    ('Evaluation & visibility', 37, AMETHYST),
    ('Governance & compliance', 34, UMBER),
    ('Context window', 31, TEAL),
]


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, 1130, 'What Actually Blocks Agents at Scale')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, 1094, 'Top obstacles to scaling AI agents in the enterprise  —  DataHub, 2026')

    cx, cy = 800, 520
    max_r = 330
    max_v = max(v for _, v, _ in DATA)
    n = len(DATA)
    ext = 360.0 / n  # 60

    # light reference grid rings (Graphite, subtle) at value gridlines
    c.setStrokeColor(HexColor('#C9C9C9'))
    c.setLineWidth(1)
    for frac in (0.5, 0.75, 1.0):
        c.circle(cx, cy, max_r * math.sqrt(frac), stroke=1, fill=0)

    bbox_full = max_r
    for i, (name, val, col) in enumerate(DATA):
        r = max_r * math.sqrt(val / max_v)  # area-proportional
        start = 90 - i * ext
        c.setFillColor(col)
        c.setStrokeColor(WHITE)
        c.setLineWidth(3)
        c.wedge(cx - r, cy - r, cx + r, cy + r, start, -ext, stroke=1, fill=1)

        mid = 90 - i * ext - ext / 2.0
        rad = math.radians(mid)

        # percentage inside the wedge (Ivory on dark fill)
        rp = r - 40
        px = cx + rp * math.cos(rad)
        py = cy + rp * math.sin(rad)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 24)
        c.drawCentredString(px, py - 8, f'{val}%')

        # category name outside the wedge (Navy on white)
        rl = max_r + 58
        lx = cx + rl * math.cos(rad)
        ly = cy + rl * math.sin(rad)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 16)
        c.drawCentredString(lx, ly - 6, name)

    # Punchline caption
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, 92,
                        'Context window limits — raw model capacity — rank last. The bottleneck is governance and context, not the model.')


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    import subprocess
    subprocess.run(['pdftoppm', '-png', '-r', '150', '-singlefile',
                    OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
