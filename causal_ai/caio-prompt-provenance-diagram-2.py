#!/usr/bin/env python3
"""
CAIO Diagram: The Silent Degradation Gauge
Topic: prompt-provenance
Type: Gauge / semicircle meter
Output: caio-prompt-provenance-diagram-2.png
"""

import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
MUSTARD = HexColor('#C4952A')
BRICK = HexColor('#A04A2A')
TAUPE = HexColor('#8A7B6B')
WHITE = HexColor('#FFFFFF')

pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work2/caio-prompt-provenance-diagram-2.png'
OUTPUT_PDF = '/tmp/_p2.pdf'


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(W / 2, H - 70, "The Silent Degradation Gauge")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, H - 100, "Left unmonitored, an AI system's error rate climbs while the dashboard stays green")

    cx, cy = W / 2, 430
    R_out = 380
    R_in = 250

    # three colored zones across the 180-degree arc (left=180 to right=0)
    zones = [
        (180, 120, EMERALD, "MONITORED"),     # 0-33%
        (120, 60, MUSTARD, "DRIFTING"),       # 33-66%
        (60, 0, BURGUNDY, "DEGRADED"),        # 66-100%
    ]
    for start, end, col, _ in zones:
        extent = end - start  # negative
        c.setFillColor(col)
        # outer wedge
        c.wedge(cx - R_out, cy - R_out, cx + R_out, cy + R_out, start, extent, stroke=0, fill=1)
    # cut inner to make a band
    c.setFillColor(WHITE)
    c.circle(cx, cy, R_in, stroke=0, fill=1)
    # mask bottom half of the inner cut (keep semicircle clean)
    c.setFillColor(WHITE)
    c.rect(cx - R_out - 5, cy - R_out - 5, 2 * (R_out + 5), R_out + 5, stroke=0, fill=1)

    # zone labels along the band
    band_r = (R_out + R_in) / 2
    for start, end, col, name in zones:
        mid = math.radians((start + end) / 2)
        lx = cx + band_r * math.cos(mid)
        ly = cy + band_r * math.sin(mid)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 18)
        c.drawCentredString(lx, ly - 6, name)

    # needle pointing into DEGRADED zone (~ +35% error after 6 months unmonitored)
    needle_ang = math.radians(35)  # within burgundy zone
    nx = cx + (R_in - 15) * math.cos(needle_ang)
    ny = cy + (R_in - 15) * math.sin(needle_ang)
    c.setStrokeColor(NAVY)
    c.setLineWidth(6)
    c.line(cx, cy, nx, ny)
    c.setFillColor(NAVY)
    c.circle(cx, cy, 18, stroke=0, fill=1)

    # center readout (raised above the needle path)
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Bold', 58)
    c.drawCentredString(cx, cy + 120, "+35%")
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 18)
    c.drawCentredString(cx, cy + 92, "error rate after 6+ months")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 15)
    c.drawCentredString(cx, cy + 68, "with no monitoring or provenance")

    # endpoint markers
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Medium', 15)
    c.drawRightString(cx - R_out + 10, cy - 28, "Day one")
    c.drawString(cx + R_out - 10, cy - 28, "Unattended")

    # bottom callouts (two verified data points)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 17)
    c.drawCentredString(cx - 330, 200, "+35%")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13.5)
    c.drawCentredString(cx - 330, 175, "error-rate rise on models left")
    c.drawCentredString(cx - 330, 156, "unchanged for six months or more")

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 17)
    c.drawCentredString(cx + 330, 200, "~15%")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13.5)
    c.drawCentredString(cx + 330, 175, "accuracy drop overnight when a")
    c.drawCentredString(cx + 330, 156, "provider updates a model silently")


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
