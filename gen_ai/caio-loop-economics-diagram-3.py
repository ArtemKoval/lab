#!/usr/bin/env python3
"""Diagram 3 - Rent and own win on opposite axes. A six-axis radar with two
overlaid polygons: the rented inner loop (speed, falling cost, availability) and
the owned outer loop (differentiation, durability, defensibility). White
background, 1600x1200, no footer. Self-rasterizing."""

import os
import math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = "/usr/share/fonts/truetype/google-fonts"
pdfmetrics.registerFont(TTFont("Poppins", f"{FONT_DIR}/Poppins-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Bold", f"{FONT_DIR}/Poppins-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Medium", f"{FONT_DIR}/Poppins-Medium.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Light", f"{FONT_DIR}/Poppins-Light.ttf"))

NAVY = HexColor("#1E2A4A")
SAPPHIRE = HexColor("#1A3A6B")
GRAPHITE = HexColor("#3A3A3A")
IVORY = HexColor("#F0EAD6")
MUSTARD = HexColor("#C4952A")
GRID = HexColor("#CCCCCC")

W, H = 1600, 1200
CX, CY = 800, 558
RMAX = 330

# (label lines, angle_deg, rent_value, own_value) - clockwise from top
AXES = [
    (["Speed to", "capability"], 90, 0.95, 0.32),
    (["Falling", "unit cost"], 30, 0.92, 0.28),
    (["Immediate", "availability"], 330, 0.95, 0.40),
    (["Differentiation"], 270, 0.22, 0.90),
    (["Durability"], 210, 0.18, 0.95),
    (["Defensibility"], 150, 0.18, 0.92),
]


def poly_points(values):
    pts = []
    for (_, ang, _, _), v in zip(AXES, values):
        a = math.radians(ang)
        pts.append((CX + RMAX * v * math.cos(a), CY + RMAX * v * math.sin(a)))
    return pts


def draw_poly(c, values, rgb, alpha, stroke_color):
    pts = poly_points(values)
    c.setFillColor(Color(rgb[0], rgb[1], rgb[2], alpha))
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))  # reset alpha to opaque white
    # stroke outline
    c.setStrokeColor(stroke_color)
    c.setLineWidth(3.5)
    p2 = c.beginPath()
    p2.moveTo(*pts[0])
    for pt in pts[1:]:
        p2.lineTo(*pt)
    p2.close()
    c.drawPath(p2, fill=0, stroke=1)
    # vertex dots
    c.setFillColor(stroke_color)
    for pt in pts:
        c.circle(pt[0], pt[1], 5, fill=1, stroke=0)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(here, "_d3_tmp.pdf")
    png_path = os.path.join(here, "caio-loop-economics-diagram-3.png")

    c = canvas.Canvas(pdf_path, pagesize=(W, H))
    c.setFillColor(HexColor("#FFFFFF"))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Title and caption
    c.setFillColor(NAVY)
    c.setFont("Poppins-Bold", 48)
    c.drawCentredString(CX, 1118, "Rent and own win on opposite axes")
    c.setFillColor(GRAPHITE)
    c.setFont("Poppins-Light", 25)
    c.drawCentredString(CX, 1072, "Renting buys speed and price. Owning buys difference and durability.")

    # Gridline rings (stroke only)
    c.setStrokeColor(GRID)
    c.setLineWidth(1.4)
    for frac in (0.2, 0.4, 0.6, 0.8, 1.0):
        c.circle(CX, CY, RMAX * frac, fill=0)

    # Radial spokes
    for _, ang, _, _ in AXES:
        a = math.radians(ang)
        c.setStrokeColor(GRID)
        c.setLineWidth(1.4)
        c.line(CX, CY, CX + RMAX * math.cos(a), CY + RMAX * math.sin(a))

    # Polygons: draw owned (larger lower half) consideration - draw rent first
    draw_poly(c, [a[2] for a in AXES], (0.769, 0.584, 0.165), 0.42, MUSTARD)
    draw_poly(c, [a[3] for a in AXES], (0.102, 0.227, 0.420), 0.46, SAPPHIRE)

    # Axis labels
    for lines, ang, _, _ in AXES:
        a = math.radians(ang)
        lr = RMAX + 34
        lx, ly = CX + lr * math.cos(a), CY + lr * math.sin(a)
        cosv = math.cos(a)
        c.setFillColor(NAVY)
        c.setFont("Poppins-Medium", 23)
        n = len(lines)
        for i, ln in enumerate(lines):
            yoff = (n - 1) * 13 - i * 26
            yy = ly + yoff - 8
            if cosv > 0.3:
                c.drawString(lx, yy, ln)
            elif cosv < -0.3:
                c.drawRightString(lx, yy, ln)
            else:
                c.drawCentredString(lx, yy, ln)

    # Legend (horizontal, centered, above bottom strip)
    ly = 86
    sw = 30
    item1_sw = CX - 282
    item2_sw = CX + 60
    # rent swatch
    c.setFillColor(Color(0.769, 0.584, 0.165, 0.6))
    c.rect(item1_sw, ly, sw, sw, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setStrokeColor(MUSTARD)
    c.setLineWidth(2.5)
    c.rect(item1_sw, ly, sw, sw, fill=0, stroke=1)
    c.setFillColor(NAVY)
    c.setFont("Poppins-Bold", 23)
    c.drawString(item1_sw + 42, ly + 7, "Rented inner loop")
    # own swatch
    c.setFillColor(Color(0.102, 0.227, 0.420, 0.72))
    c.rect(item2_sw, ly, sw, sw, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont("Poppins-Bold", 23)
    c.drawString(item2_sw + 42, ly + 7, "Owned outer loop")

    # Bottom caption strip
    c.setFillColor(GRAPHITE)
    c.setFont("Poppins-Medium", 22)
    c.drawCentredString(CX, 42, "Everyone can rent the top half. Only you can build the bottom half.")

    c.showPage()
    c.save()

    os.system(f'/usr/bin/pdftoppm -png -r 150 -singlefile "{pdf_path}" "{png_path[:-4]}"')
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    print("wrote", png_path)


if __name__ == "__main__":
    main()
