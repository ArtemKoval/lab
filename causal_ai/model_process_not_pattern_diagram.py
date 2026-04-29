#!/usr/bin/env python3
"""
CAIO Diagram: The Data Generating Process Hierarchy
Topic: process-not-pattern
Type: Concentric Rings (5 nested layers, innermost = DGP)
Output: caio-process-not-pattern-diagram-1.png
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
TAUPE = HexColor('#8A7B6B')
MOSS = HexColor('#4A5A3A')

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
OUTPUT_PNG = '/home/claude/caio/caio-process-not-pattern-diagram-1.png'
OUTPUT_PDF = '/tmp/_diagram1_temp.pdf'


def draw_diagram(c):
    """Concentric rings showing the DGP hierarchy from innermost (mechanism) to outermost (data)."""
    # White background for clean Substack embedding
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 70, "The Data Generating Process Hierarchy")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W / 2, H - 100, "Many-to-one relationships from mechanism to dataset")

    # Center the rings — place center slightly left to leave room for callouts on right
    cx, cy = 580, 540

    # Five concentric rings, from outermost (largest) to innermost (smallest)
    # Outer = Dataset (most surface), Inner = DGP (deepest mechanism)
    # Ring radii (outer edge of each layer)
    radii = [430, 360, 290, 215, 130]
    fills = [TAUPE, AMETHYST, SAPPHIRE, EMERALD, NAVY]
    labels_inside = [
        ("Dataset", "what we hand to the model"),
        ("Empirical distribution", "the finite sample's structure"),
        ("Observational joint distribution", "of measured variables"),
        ("Full joint distribution", "observed plus latent"),
        ("Data generating process", "the actual mechanism"),
    ]

    # Draw rings outermost first
    for r, color in zip(radii, fills):
        c.setFillColor(color)
        c.setStrokeColor(HexColor('#FFFFFF'))
        c.setLineWidth(3)
        c.circle(cx, cy, r, stroke=1, fill=1)

    # Inner labels — placed at the top of each ring band, in Ivory text
    # Each label sits in the band between this ring and the next inner ring
    band_centers = []
    for i in range(len(radii)):
        outer = radii[i]
        inner = radii[i + 1] if i + 1 < len(radii) else 0
        band_centers.append((outer + inner) / 2)

    # For ring labels, place them along the top of each band
    label_positions = [
        (cx, cy + (radii[0] + radii[1]) / 2 - 5),  # outermost band — Dataset
        (cx, cy + (radii[1] + radii[2]) / 2 - 5),  # Empirical
        (cx, cy + (radii[2] + radii[3]) / 2 - 5),  # Observational
        (cx, cy + (radii[3] + radii[4]) / 2 - 5),  # Full joint
        (cx, cy - 5),  # innermost — DGP at center
    ]

    for i, ((title, _), (lx, ly)) in enumerate(zip(labels_inside, label_positions)):
        c.setFillColor(IVORY)
        if i == 4:
            # Innermost: bigger title, centered
            c.setFont('Poppins-Bold', 16)
            c.drawCentredString(lx, ly + 8, "Data generating")
            c.drawCentredString(lx, ly - 12, "process")
        else:
            c.setFont('Poppins-Bold', 14)
            c.drawCentredString(lx, ly, title)

    # Right-side callout column — explain the many-to-one relationship
    callout_x = 1100
    callout_top_y = 950
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 18)
    c.drawString(callout_x, callout_top_y, "Many-to-one as you")
    c.drawString(callout_x, callout_top_y - 26, "move down the stack")

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13)
    callout_lines = [
        "",
        "Many datasets share one",
        "empirical distribution.",
        "",
        "Many empirical distributions",
        "share one observational joint.",
        "",
        "Many observational joints",
        "share one full joint.",
        "",
        "Many generating processes",
        "share one full joint.",
        "",
        "",
    ]
    y_start = callout_top_y - 70
    for i, line in enumerate(callout_lines):
        c.drawString(callout_x, y_start - i * 22, line)

    # Bottom callout — the strategic implication
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Bold', 14)
    c.drawString(callout_x, 360, "Statistical AI optimizes")
    c.drawString(callout_x, 340, "the top of the stack.")
    c.setFillColor(EMERALD)
    c.drawString(callout_x, 305, "Causal AI reasons")
    c.drawString(callout_x, 285, "about the bottom.")

    # Connector arrows from rings to callout (using dashes, no arrowheads — design rule: no arrows)
    # Use thin Taupe dashed indicator lines
    c.setStrokeColor(TAUPE)
    c.setLineWidth(1.5)
    c.setDash(3, 3)
    # Line from outermost band to "Many datasets" callout
    c.line(cx + radii[0] - 30, cy + (radii[0] + radii[1]) /
           2, callout_x - 20, y_start - 22)
    # Line from innermost ring up to bottom callout
    c.line(cx + 80, cy - 100, callout_x - 20, 350)
    c.setDash()  # reset dash

    # Footer attribution — small, bottom-right
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawRightString(
        W - 60, 50, "After Ness, Causal AI, Manning 2025 — adapted for enterprise context")


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()

    import subprocess
    subprocess.run([
        'pdftoppm', '-png', '-r', '150',
        '-singlefile', OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')
    ], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
