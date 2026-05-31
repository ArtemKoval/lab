#!/usr/bin/env python3
"""
CAIO Diagram: What a Misread Intent Costs
Topic: intent-classification
Type: Gauge / semicircle meter (speedometer dial with needle and graduated ticks)
Output: caio-intent-classification-diagram-4.png
"""

import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# --- Palette (CAIO standard) ---
NAVY     = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY    = HexColor('#F0EAD6')
OCHRE    = HexColor('#C49A2A')
MUSTARD  = HexColor('#C4952A')
EMERALD  = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL     = HexColor('#1A7A7A')
WHITE    = HexColor('#FFFFFF')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Italic', '/usr/share/fonts/truetype/google-fonts/Poppins-Italic.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-intent-classification-diagram-4.png'
OUTPUT_PDF = '/tmp/_diagram4.pdf'

CX, CY = 800, 560      # gauge pivot
R_OUT, R_IN = 380, 250  # band radii
NEEDLE_ANG = 24         # degrees: swung toward the expensive (right) end


def draw_diagram(c):
    # Background — white for standalone diagram
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title + subtitle
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(CX, H - 78, "What a Misread Intent Costs")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 17)
    c.drawCentredString(CX, H - 112,
                        "Median cost per resolved contact, self-service against assisted  ·  Gartner, 2024")

    # --- Gauge band: three cost zones across the top semicircle ---
    # angles measured CCW from east (0). right=0-60 expensive, mid=60-120, left=120-180 cheap
    c.setFillColor(BURGUNDY); c.wedge(CX - R_OUT, CY - R_OUT, CX + R_OUT, CY + R_OUT, 0,   60, stroke=0, fill=1)
    c.setFillColor(MUSTARD);  c.wedge(CX - R_OUT, CY - R_OUT, CX + R_OUT, CY + R_OUT, 60,  60, stroke=0, fill=1)
    c.setFillColor(EMERALD);  c.wedge(CX - R_OUT, CY - R_OUT, CX + R_OUT, CY + R_OUT, 120, 60, stroke=0, fill=1)
    # carve inner white half-disk to leave the band
    c.setFillColor(WHITE)
    c.wedge(CX - R_IN, CY - R_IN, CX + R_IN, CY + R_IN, 0, 180, stroke=0, fill=1)

    # zone captions inside the band (Ivory on dark fills, Navy on mustard)
    band_mid = (R_IN + R_OUT) / 2
    for ang, txt, col in [(150, "self-service", IVORY), (90, "transition", NAVY), (30, "assisted", IVORY)]:
        rad = math.radians(ang)
        lx, ly = CX + band_mid * math.cos(rad), CY + band_mid * math.sin(rad)
        c.setFillColor(col); c.setFont('Poppins-Medium', 17)
        c.drawCentredString(lx, ly - 6, txt)

    # --- Graduated speedometer ticks outside the band ---
    c.setStrokeColor(GRAPHITE)
    ang = 0.0
    while ang <= 180.0001:
        rad = math.radians(ang)
        major = abs((ang % 45)) < 0.01 or abs((ang % 45) - 45) < 0.01
        t0 = R_OUT + 10
        t1 = R_OUT + (32 if major else 20)
        c.setLineWidth(4 if major else 2)
        c.line(CX + t0 * math.cos(rad), CY + t0 * math.sin(rad),
               CX + t1 * math.cos(rad), CY + t1 * math.sin(rad))
        ang += 11.25

    # --- Needle (tapered, swung right into the burgundy zone) ---
    a = math.radians(NEEDLE_ANG)
    L, b, tail = 322, 16, 48
    perp = a + math.pi / 2
    tipx, tipy = CX + L * math.cos(a), CY + L * math.sin(a)
    blx, bly = CX + b * math.cos(perp), CY + b * math.sin(perp)
    brx, bry = CX - b * math.cos(perp), CY - b * math.sin(perp)
    tx, ty = CX - tail * math.cos(a), CY - tail * math.sin(a)
    c.setFillColor(NAVY)
    p = c.beginPath()
    p.moveTo(tipx, tipy); p.lineTo(blx, bly); p.lineTo(tx, ty); p.lineTo(brx, bry); p.close()
    c.drawPath(p, stroke=0, fill=1)
    # hub
    c.setFillColor(NAVY); c.circle(CX, CY, 30, stroke=0, fill=1)
    c.setStrokeColor(OCHRE); c.setLineWidth(3); c.circle(CX, CY, 30, stroke=1, fill=0)
    c.setFillColor(WHITE); c.circle(CX, CY, 9, stroke=0, fill=1)

    # --- End value anchors (below the gauge baseline) ---
    lx = CX - band_mid
    c.setFillColor(EMERALD); c.setFont('Poppins-Bold', 46)
    c.drawCentredString(lx, CY - 78, "$1.84")
    c.setFillColor(GRAPHITE); c.setFont('Poppins-Light', 19)
    c.drawCentredString(lx, CY - 108, "self-service contact")

    rx = CX + band_mid
    c.setFillColor(BURGUNDY); c.setFont('Poppins-Bold', 46)
    c.drawCentredString(rx, CY - 78, "$13.50")
    c.setFillColor(GRAPHITE); c.setFont('Poppins-Light', 19)
    c.drawCentredString(rx, CY - 108, "assisted contact")

    # --- Center spread callout ---
    c.setFillColor(NAVY); c.setFont('Poppins-Bold', 44)
    c.drawCentredString(CX, CY - 192, "roughly 7 to 1")
    c.setFillColor(GRAPHITE); c.setFont('Poppins-Light', 20)
    c.drawCentredString(CX, CY - 228,
                        "A wrong route does not just fail — it pays the expensive channel to clean up the cheap one.")
    c.setFillColor(BURGUNDY); c.setFont('Poppins-Italic', 18)
    c.drawCentredString(CX, CY - 262, "Every misread intent swings the needle toward $13.50.")


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
