#!/usr/bin/env python3
"""Diagram 1 - A Moving Frontier (Archimedean spiral, non-stationary LLM leadership)."""
import math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = "/usr/share/fonts/truetype/google-fonts/"
for name, fn in [("Poppins", "Poppins-Regular.ttf"), ("Poppins-Bold", "Poppins-Bold.ttf"),
                 ("Poppins-Medium", "Poppins-Medium.ttf"), ("Poppins-Light", "Poppins-Light.ttf"),
                 ("Poppins-Italic", "Poppins-Italic.ttf")]:
    pdfmetrics.registerFont(TTFont(name, FONT_DIR + fn))

NAVY = HexColor("#1E2A4A"); SAPPHIRE = HexColor("#1A3A6B"); GRAPHITE = HexColor("#3A3A3A")
IVORY = HexColor("#F0EAD6"); OCHRE = HexColor("#C49A2A"); EMERALD = HexColor("#1A5C3A")
BURGUNDY = HexColor("#6B1C2A"); AMETHYST = HexColor("#5A2D6A"); TEAL = HexColor("#1A7A7A")

W, H = 1600, 1200
c = canvas.Canvas("caio-ai-optionality-diagram-1.pdf", pagesize=(W, H))
c.setFillColor(HexColor("#FFFFFF")); c.rect(0, 0, W, H, fill=1, stroke=0)

CX, CY = 800, 575
R0, RMAX, TURNS = 58, 345, 2.5
total_theta = TURNS * 2 * math.pi
b = (RMAX - R0) / total_theta

# --- spiral curve ---
pts = []
steps = 600
for i in range(steps + 1):
    th = total_theta * i / steps
    r = R0 + b * th
    pts.append((CX + r * math.cos(th), CY + r * math.sin(th)))
c.setStrokeColor(GRAPHITE); c.setLineWidth(2.0)
p = c.beginPath(); p.moveTo(*pts[0])
for pt in pts[1:]:
    p.lineTo(*pt)
c.drawPath(p, stroke=1, fill=0)

def label_halo(cv, x, y, text, font, size, align, fill):
    cv.setFont(font, size)
    tw = cv.stringWidth(text, font, size)
    asc, desc = size * 0.74, size * 0.26
    x0 = x if align == "left" else (x - tw if align == "right" else x - tw / 2)
    cv.setFillColor(HexColor("#FFFFFF"))
    cv.roundRect(x0 - 5, y - desc - 2, tw + 10, asc + desc + 4, 4, fill=1, stroke=0)
    cv.setFillColor(fill)
    if align == "left":
        cv.drawString(x, y, text)
    elif align == "right":
        cv.drawRightString(x, y, text)
    else:
        cv.drawCentredString(x, y, text)

# --- nodes along the spiral ---
nodes = [
    ("1", "Capability leapfrogs", SAPPHIRE),
    ("2", "Price resets", EMERALD),
    ("3", "New model launches", AMETHYST),
    ("4", "Benchmark reshuffles", TEAL),
    ("5", "Leadership changes hands", BURGUNDY),
]
fracs = [0.17, 0.35, 0.53, 0.72, 0.93]
NODE_R = 37
for (num, label, col), f in zip(nodes, fracs):
    th = total_theta * f
    r = R0 + b * th
    nx, ny = CX + r * math.cos(th), CY + r * math.sin(th)
    # node disc
    c.setFillColor(col); c.setStrokeColor(HexColor("#FFFFFF")); c.setLineWidth(3)
    c.circle(nx, ny, NODE_R, fill=1, stroke=1)
    # number inside
    c.setFillColor(IVORY); c.setFont("Poppins-Bold", 26)
    c.drawCentredString(nx, ny - 9, num)
    # outward label, quadrant-aware, with halo
    cos_v, sin_v = math.cos(th), math.sin(th)
    gap = NODE_R + 14
    lx, ly = nx + cos_v * gap, ny + sin_v * gap - 6
    if cos_v > 0.3:
        label_halo(c, lx, ly, label, "Poppins-Medium", 21, "left", GRAPHITE)
    elif cos_v < -0.3:
        label_halo(c, lx, ly, label, "Poppins-Medium", 21, "right", GRAPHITE)
    else:
        yoff = 0 if sin_v >= 0 else 16
        label_halo(c, nx + cos_v * gap, ny + sin_v * (gap + 4) - yoff, label, "Poppins-Medium", 21, "center", GRAPHITE)

# --- center text ---
c.setFillColor(NAVY); c.setFont("Poppins-Bold", 18)
c.drawCentredString(CX, CY + 6, "Never sits")
c.drawCentredString(CX, CY - 16, "still")

# --- title + subtitle ---
c.setFillColor(NAVY); c.setFont("Poppins-Bold", 46)
c.drawCentredString(CX, H - 95, "A Moving Frontier")
c.setFillColor(GRAPHITE); c.setFont("Poppins-Light", 23)
c.drawCentredString(CX, H - 132, "Enterprise LLM leadership keeps changing hands \u2014 optionality is the hedge.")

c.showPage(); c.save()

# rasterize PDF to PNG (same toolchain as the carousel)
import subprocess
subprocess.run(["pdftoppm", "-png", "-r", "150", "-singlefile",
                "caio-ai-optionality-diagram-1.pdf", "caio-ai-optionality-diagram-1"],
               check=True)
print("diagram-1 rendered: caio-ai-optionality-diagram-1.png")
