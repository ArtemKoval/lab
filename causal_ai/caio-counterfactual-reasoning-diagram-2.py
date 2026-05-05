#!/usr/bin/env python3
"""
CAIO Diagram: The Four Uplift Segments
Topic: counterfactual-reasoning
Type: Segmented wheel (4 quadrants)
Output: caio-counterfactual-reasoning-diagram-2.png
"""

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
TAUPE = HexColor('#8A7B6B')
UMBER = HexColor('#6B4226')
MOSS = HexColor('#4A5A3A')
WHITE = HexColor('#FFFFFF')

# --- Font Registration ---
pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas Setup ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-counterfactual-reasoning-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'


def draw_diagram(c):
    # White background
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # --- Title ---
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 60, 'The Four Uplift Segments')

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W / 2, H - 90, 'Every targeted population contains four hidden groups — only one is worth targeting')

    # --- Wheel ---
    cx, cy = W / 2, H / 2 - 60
    outer_r = 380
    inner_r = 110
    label_r = 270  # Where to place segment titles
    desc_r = 340   # Where to place 1-line descriptors

    # Four segments — start at 45° (so segments are NE, NW, SW, SE quadrants)
    # Order: persuadables (top-right, EMERALD), sure things (top-left, SAPPHIRE),
    #        lost causes (bottom-left, BURGUNDY), sleeping dogs (bottom-right, AMETHYST)
    segments = [
        {
            'name': 'PERSUADABLES',
            'tagline': 'Behavior changes\nbecause of action',
            'note': 'Target this group',
            'fill': EMERALD,
            'label_color': IVORY,
            'start_ang': 45,
        },
        {
            'name': 'SURE THINGS',
            'tagline': 'Outcome happens\nregardless',
            'note': 'Wastes spend',
            'fill': SAPPHIRE,
            'label_color': IVORY,
            'start_ang': 135,
        },
        {
            'name': 'LOST CAUSES',
            'tagline': 'Will not respond\nregardless',
            'note': 'Wastes spend',
            'fill': BURGUNDY,
            'label_color': IVORY,
            'start_ang': 225,
        },
        {
            'name': 'SLEEPING DOGS',
            'tagline': 'Loyal until provoked\nby the action',
            'note': 'Negative lift',
            'fill': AMETHYST,
            'label_color': IVORY,
            'start_ang': 315,
        },
    ]

    # Draw segments as wedges
    for seg in segments:
        c.setFillColor(seg['fill'])
        c.setStrokeColor(WHITE)
        c.setLineWidth(4)
        # ReportLab wedge: bounding box of outer circle, start angle, extent
        c.wedge(cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
                seg['start_ang'], 90, stroke=1, fill=1)

    # Draw inner cutout (white) to create donut effect
    c.setFillColor(WHITE)
    c.setStrokeColor(WHITE)
    c.circle(cx, cy, inner_r, stroke=1, fill=1)

    # Central label inside cutout
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 18)
    c.drawCentredString(cx, cy + 22, 'CAMPAIGN')
    c.drawCentredString(cx, cy + 0, 'TARGETS')
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(cx, cy - 22, 'Four hidden groups')
    c.drawCentredString(cx, cy - 36, 'in every list')

    # Place segment labels at sector midpoints
    for seg in segments:
        mid_ang_deg = seg['start_ang'] + 45
        mid_ang = math.radians(mid_ang_deg)
        # Title placement
        lx = cx + label_r * math.cos(mid_ang)
        ly = cy + label_r * math.sin(mid_ang)

        c.setFillColor(seg['label_color'])
        c.setFont('Poppins-Bold', 22)
        c.drawCentredString(lx, ly + 30, seg['name'])

        # Tagline below title
        c.setFont('Poppins', 13)
        tagline_lines = seg['tagline'].split('\n')
        for j, tl in enumerate(tagline_lines):
            c.drawCentredString(lx, ly + 4 - j * 16, tl)

        # Note (action implication) — smaller, italicized feel via Poppins-Light
        c.setFont('Poppins-Bold', 14)
        c.drawCentredString(lx, ly - 38, seg['note'])

    # --- Footer attribution ---
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(
        W / 2, 40, 'Source: Uplift modeling literature (Lo 2002; Radcliffe & Surry 2007) | Art Koval / Chief AI Officer Insights')


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    subprocess.run([
        'pdftoppm', '-png', '-r', '150',
        '-singlefile', OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')
    ], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
