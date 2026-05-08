#!/usr/bin/env python3
"""
CAIO Diagram: The Identification Toolkit
Topic: caio-causal-identification
Type: Polar Area (Coxcomb) — equal-angle sectors with variable radius encoding query coverage
Output: caio-causal-identification-diagram-2.png
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

pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-causal-identification-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 70, 'The Identification Toolkit')

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, H - 100, 'Six identification strategies — sector area encodes query reach within their target domain')

    # 6 strategies, each a sector with proportional area
    # Position the chart center
    cx, cy = 540, 540
    
    # Each strategy: (label, query_strength_value, layer, color, short_descriptor)
    # values are conceptual reach scores 1-10
    strategies = [
        ('Do-calculus',          10, 'Layer 2',  SAPPHIRE,  'Complete for graphical ID'),
        ('Backdoor adjustment',   9, 'Layer 2',  EMERALD,   'When confounders observed'),
        ('Front-door adjustment', 5, 'Layer 2',  AMETHYST,  'When mediator observed'),
        ('Counterfactual graphs', 7, 'Layer 3',  BURGUNDY,  'IDC* algorithm'),
        ('SWIGs',                 6, 'Layer 3',  UMBER,     'Single-world assumption'),
        ('Partial identification',8, 'Layers 2-3', TEAL,    'Bounds when ID fails'),
    ]

    n = len(strategies)
    angle_per = 360 / n
    max_r = 280
    max_value = 10

    # Background concentric guide rings (Taupe, light)
    c.setStrokeColor(TAUPE)
    c.setLineWidth(1)
    for ring_frac in [0.33, 0.66, 1.0]:
        rg = max_r * ring_frac
        # Draw dashed circle
        c.setDash(3, 4)
        c.circle(cx, cy, rg, stroke=1, fill=0)
    c.setDash()  # Reset to solid

    # Draw sectors
    for i, (label, value, layer, color, descriptor) in enumerate(strategies):
        # Area-proportional radius: r ∝ sqrt(value)
        r = max_r * math.sqrt(value / max_value)
        start_ang = 90 - (i + 1) * angle_per  # Start from 12 o'clock, go clockwise
        # ReportLab wedge: positive extent = counter-clockwise; we want clockwise so use positive extent
        # Actually we want sectors going around clockwise. Let's compute:
        # Sector i covers angular range [90 - i*angle_per - angle_per, 90 - i*angle_per]
        c.setFillColor(color)
        c.setStrokeColor(WHITE)
        c.setLineWidth(3)
        c.wedge(cx - r, cy - r, cx + r, cy + r, start_ang, angle_per, stroke=1, fill=1)

    # Labels for each sector — placed outside the largest possible radius for that sector
    label_radius = max_r + 90
    for i, (label, value, layer, color, descriptor) in enumerate(strategies):
        mid_angle_deg = 90 - (i + 0.5) * angle_per
        mid_angle_rad = math.radians(mid_angle_deg)
        lx = cx + label_radius * math.cos(mid_angle_rad)
        ly = cy + label_radius * math.sin(mid_angle_rad)

        # Two-line label: strategy name (bold), then layer
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 14)
        c.drawCentredString(lx, ly + 8, label)
        c.setFillColor(color)
        c.setFont('Poppins-Medium', 11)
        c.drawCentredString(lx, ly - 10, layer)

    # Center label - the overarching concept
    c.setFillColor(WHITE)
    c.circle(cx, cy, 50, stroke=0, fill=1)
    c.setStrokeColor(NAVY)
    c.setLineWidth(2)
    c.circle(cx, cy, 50, stroke=1, fill=0)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 13)
    c.drawCentredString(cx, cy + 6, 'Causal')
    c.drawCentredString(cx, cy - 10, 'Identification')

    # Right-side panel: strategy details
    panel_x = 1050
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 18)
    c.drawString(panel_x, cy + 280, 'When to reach for each')

    descriptors = [
        ('Do-calculus',           SAPPHIRE,  'Complete graphical-ID algorithm.',     'Use when graph + level-1 data is all you have.'),
        ('Backdoor adjustment',   EMERALD,   'Block confounding paths via observed', 'covariates. The default level-2 estimator.'),
        ('Front-door adjustment', AMETHYST,  'Use a mediator when confounders',      'are unobserved. Specialized but powerful.'),
        ('Counterfactual graphs', BURGUNDY,  'Identify level-3 queries via IDC*',    'over collapsed parallel-world graphs.'),
        ('SWIGs',                 UMBER,     'Node-splitting for level-3 ID',        'under the single-world assumption.'),
        ('Partial identification',TEAL,      'When full ID fails — derive bounds',   'on the query. Often actionable.'),
    ]
    
    y = cy + 240
    line_h = 70
    for name, color, line1, line2 in descriptors:
        c.setFillColor(color)
        c.circle(panel_x + 10, y - 4, 8, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 13)
        c.drawString(panel_x + 28, y, name)
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins', 11)
        c.drawString(panel_x + 28, y - 16, line1)
        c.drawString(panel_x + 28, y - 30, line2)
        y -= line_h

    # Bottom anchor text
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(W / 2, 140, 'Identification asks one question — can the answer be derived at all')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 14)
    c.drawCentredString(W / 2, 115, 'Output is yes, no, or partial. All three carry information that should reach the project sponsor')
    c.drawCentredString(W / 2, 95, 'before estimation begins.')


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
