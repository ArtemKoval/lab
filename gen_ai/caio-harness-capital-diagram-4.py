#!/usr/bin/env python3
"""
CAIO Diagram: Motion Is Not Delivery
Topic: harness-capital
Type: Radial spokes (magnitude as distance from center)
Output: caio-harness-capital-diagram-4.png
"""

import os
import math
import subprocess
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
TAUPE = HexColor('#8A7B6B')
MOSS = HexColor('#4A5A3A')
WHITE = HexColor('#FFFFFF')

# --- Font Registration ---
FONT_DIR = '/usr/share/fonts/truetype/google-fonts'
pdfmetrics.registerFont(TTFont('Poppins', f'{FONT_DIR}/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', f'{FONT_DIR}/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', f'{FONT_DIR}/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', f'{FONT_DIR}/Poppins-Light.ttf'))

# --- Canvas Setup ---
W, H = 1600, 1200
BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PNG = os.path.join(BASE, 'caio-harness-capital-diagram-4.png')
OUTPUT_PDF = os.path.join(BASE, '_diagram4_temp.pdf')


def polar(cx, cy, r, deg):
    rad = math.radians(deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title + subtitle
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 34)
    c.drawCentredString(W / 2, H - 84, 'Motion Is Not Delivery')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 17)
    c.drawCentredString(W / 2, H - 118,
                        'High-AI-adoption teams, 2025 — individual output soared, company delivery did not')

    cx, cy = W / 2, 552
    rmin, rmax, vmax = 116, 408, 154
    metrics = [
        ('PR size', 154, 30, AMETHYST),
        ('PRs merged', 98, 78, SAPPHIRE),
        ('review time', 91, 128, BURGUNDY),
        ('tasks done', 21, 232, TEAL),
        ('bugs / dev', 9, 286, UMBER),
        ('company delivery', 0, 332, MOSS),
    ]

    # faint guide rings
    c.setStrokeColor(TAUPE)
    c.setLineWidth(1)
    for fr in (rmin, (rmin + rmax) / 2, rmax):
        c.circle(cx, cy, fr, stroke=1, fill=0)

    for name, val, ang, col in metrics:
        rr = rmin + (val / vmax) * (rmax - rmin)
        sx, sy = polar(cx, cy, rmin, ang)
        ex, ey = polar(cx, cy, rr, ang)
        c.setStrokeColor(col)
        c.setLineWidth(9)
        c.line(sx, sy, ex, ey)
        c.setFillColor(col)
        c.circle(ex, ey, 19, stroke=0, fill=1)
        # label outside the dot (push small values a little further so they clear the hub cluster)
        off = 78 if val < 25 else 64
        lx, ly = polar(cx, cy, rr + off, ang)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 25)
        plus = '+' if val > 0 else ''
        c.drawCentredString(lx, ly + 6, f'{plus}{val}%')
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins-Medium', 18)
        c.drawCentredString(lx, ly - 19, name)

    # center note
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(cx, cy + 8, 'same')
    c.drawCentredString(cx, cy - 18, 'delivery')

    # bottom attribution + takeaway
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 19)
    c.drawCentredString(W / 2, 132,
                        'Output exploded. Company-level delivery stayed flat — the signature of running in a circle.')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, 102,
                        'Telemetry from 10,000+ developers across 1,255 teams — Faros AI, 2025.')


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    subprocess.run(['pdftoppm', '-png', '-r', '150', '-singlefile',
                    OUTPUT_PDF, OUTPUT_PNG[:-4]], check=True)
    os.remove(OUTPUT_PDF)
    print(f'Rendered: {OUTPUT_PNG}')


if __name__ == '__main__':
    main()
