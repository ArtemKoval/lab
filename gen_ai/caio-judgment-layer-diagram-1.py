#!/usr/bin/env python3
"""Standalone diagram 1 for CAIO judgment-layer package.
Archimedean spiral: bare keyword unfurling into a fully directed scene
specification. White background, no footer. Renders itself to a
1600x1200 PNG via a temporary PDF and pdftoppm supersampling.
"""
import math
import os
import subprocess
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

FONT_DIR = "/usr/share/fonts/truetype/google-fonts"
pdfmetrics.registerFont(TTFont("Poppins", f"{FONT_DIR}/Poppins-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Bold", f"{FONT_DIR}/Poppins-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Medium", f"{FONT_DIR}/Poppins-Medium.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Light", f"{FONT_DIR}/Poppins-Light.ttf"))

NAVY = HexColor("#1E2A4A")
SAPPHIRE = HexColor("#1A3A6B")
GRAPHITE = HexColor("#3A3A3A")
IVORY = HexColor("#F0EAD6")
EMERALD = HexColor("#1A5C3A")
TAUPE = HexColor("#8A7B6B")
WHITE = HexColor("#FFFFFF")

W, H = 1600, 1200

NODES = [
    ("1", ["Keyword"], TAUPE),
    ("2", ["Subject &", "action"], SAPPHIRE),
    ("3", ["Scene &", "lighting"], SAPPHIRE),
    ("4", ["Visual", "style"], SAPPHIRE),
    ("5", ["Camera &", "pacing"], SAPPHIRE),
    ("6", ["Audio", "direction"], SAPPHIRE),
    ("7", ["Reference", "anchor"], EMERALD),
]


def spiral_r(theta_deg):
    return 60 + 0.72 * (theta_deg - 90)


def compute_positions(cx, cy):
    pts = []
    for i, (num, lines, col) in enumerate(NODES):
        theta = 90 + i * 100
        r = spiral_r(theta)
        x = cx + r * math.cos(math.radians(theta))
        y = cy + r * math.sin(math.radians(theta))
        pts.append((x, y, num, lines, col, theta))
    return pts


def draw_label(c, x, y, lines, theta, node_r):
    """Quadrant-aware outward radial label, stacked lines."""
    co = math.cos(math.radians(theta))
    si = math.sin(math.radians(theta))
    pad = node_r + 16
    lx = x + pad * co
    ly = y + pad * si
    c.setFont("Poppins-Medium", 30)
    c.setFillColor(GRAPHITE)
    line_h = 34
    block_h = line_h * (len(lines) - 1)
    start_y = ly + block_h / 2.0 - 22
    for j, ln in enumerate(lines):
        yy = start_y - j * line_h
        if co > 0.3:
            c.drawString(lx, yy, ln)
        elif co < -0.3:
            c.drawRightString(lx, yy, ln)
        else:
            c.drawCentredString(lx, yy, ln)


def render_pdf(path):
    c = canvas.Canvas(path, pagesize=(W, H))
    # white background
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    cx0, cy0 = 800, 600
    raw = compute_positions(cx0, cy0)
    xs = [p[0] for p in raw]
    ys = [p[1] for p in raw]
    bx = (min(xs) + max(xs)) / 2.0
    by = (min(ys) + max(ys)) / 2.0
    # center node cloud at (800, 560): leaves room for title top, caption bottom
    dx = 800 - bx
    dy = 560 - by
    cx, cy = cx0 + dx, cy0 + dy

    # --- continuous spiral underlay (drawn first, behind nodes) ---
    c.setStrokeColor(TAUPE)
    c.setLineWidth(4)
    prev = None
    t = 64.0
    while t <= 716.0:
        r = spiral_r(t)
        if r >= 0:
            x = cx + r * math.cos(math.radians(t))
            y = cy + r * math.sin(math.radians(t))
            if prev is not None:
                c.line(prev[0], prev[1], x, y)
            prev = (x, y)
        t += 2.5

    pos = compute_positions(cx, cy)
    node_r = 46
    for (x, y, num, lines, col, theta) in pos:
        # node disc
        c.setFillColor(col)
        c.circle(x, y, node_r, fill=1, stroke=0)
        # thin ivory keyline for separation from spiral
        c.setStrokeColor(WHITE)
        c.setLineWidth(3)
        c.circle(x, y, node_r, fill=0, stroke=1)
        # ivory step number centered
        c.setFillColor(IVORY)
        c.setFont("Poppins-Bold", 40)
        c.drawCentredString(x, y - 14, num)
        draw_label(c, x, y, lines, theta, node_r)

    # --- title block (top) ---
    c.setFillColor(NAVY)
    c.setFont("Poppins-Bold", 46)
    c.drawCentredString(W / 2, H - 92, "From keyword to directed scene")
    c.setFillColor(GRAPHITE)
    c.setFont("Poppins-Light", 27)
    c.drawCentredString(
        W / 2, H - 132,
        "Specification depth, not model choice, is what lifts a clip from generic to on-brand"
    )

    # --- start / end annotations ---
    c.setFont("Poppins-Medium", 24)
    c.setFillColor(TAUPE)
    c.drawCentredString(W / 2, 118, "Bare prompt: the model fills every gap with its average")
    c.setFillColor(EMERALD)
    c.drawCentredString(W / 2, 84, "Directed prompt: every variable fixed on purpose")

    c.showPage()
    c.save()


def rasterize(pdf_path, png_path):
    stem = png_path[:-4]
    subprocess.run(
        ["pdftoppm", "-png", "-r", "150", "-singlefile", pdf_path, stem],
        check=True,
    )
    img = Image.open(png_path).convert("RGB")
    img = img.resize((W, H), Image.LANCZOS)
    img.save(png_path)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    pdf = os.path.join(here, "_tmp_diagram1.pdf")
    png = os.path.join(here, "caio-judgment-layer-diagram-1.png")
    render_pdf(pdf)
    rasterize(pdf, png)
    os.remove(pdf)
    print("wrote", png)
