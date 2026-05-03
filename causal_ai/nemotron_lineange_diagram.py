#!/usr/bin/env python3
"""
CAIO Diagram: The Nemotron Distillation Lineage
Topic: nemotron-distillation-lineage
Type: Hub-and-Spoke radial mindmap (three lineage branches)
Output: caio-nemotron-distillation-lineage-diagram-1.png
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
TAUPE = HexColor('#8A7B6B')
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')
MUSTARD = HexColor('#C4952A')
BRICK = HexColor('#A04A2A')
TERRACOTTA = HexColor('#C4613A')
BRONZE = HexColor('#8C6E3A')
UMBER = HexColor('#6B4226')
MOSS = HexColor('#4A5A3A')

# --- Fonts ---
pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Italic', '/usr/share/fonts/truetype/google-fonts/Poppins-Italic.ttf'))

# --- Canvas ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio/caio-nemotron-distillation-lineage-diagram-1.png'
OUTPUT_PDF = '/tmp/_diagram1_temp.pdf'


def draw_diagram(c):
    # White background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 70, "The Nemotron Distillation Lineage")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W / 2, H - 100, "Three teacher-student trees rooted in one synthetic-data engine")

    # Central hub: synthetic-data engine (Nemotron-4 340B)
    cx, cy = W / 2, 580
    hub_r = 110

    c.setFillColor(NAVY)
    c.circle(cx, cy, hub_r, stroke=0, fill=1)
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 18)
    c.drawCentredString(cx, cy + 22, "Nemotron-4")
    c.drawCentredString(cx, cy, "340B")
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(cx, cy - 22, "synthetic data engine")
    c.drawCentredString(cx, cy - 38, "(June 2024)")

    # Three branch hubs: Dense, Llama-Nemotron, Hybrid Mamba
    branch_r = 70
    branch_orbit = 320
    branches = [
        (150, SAPPHIRE, "DENSE", "lineage"),
        (30, EMERALD, "LLAMA-", "NEMOTRON"),
        (270, BURGUNDY, "HYBRID", "MAMBA"),
    ]

    branch_positions = []
    for angle_deg, color, name, sub in branches:
        ang = math.radians(angle_deg)
        bx = cx + branch_orbit * math.cos(ang)
        by = cy + branch_orbit * math.sin(ang)
        branch_positions.append((bx, by, color, name, sub))

        # Connector from hub to branch
        c.setStrokeColor(TAUPE)
        c.setLineWidth(3)
        dx, dy = bx - cx, by - cy
        d = math.sqrt(dx * dx + dy * dy)
        ux, uy = dx / d, dy / d
        c.line(cx + ux * hub_r, cy + uy * hub_r,
               bx - ux * branch_r, by - uy * branch_r)

        # Branch circle
        c.setFillColor(color)
        c.circle(bx, by, branch_r, stroke=0, fill=1)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 15)
        c.drawCentredString(bx, by + 8, name)
        c.drawCentredString(bx, by - 10, sub)

    # Leaf nodes (children) for each branch
    leaf_r = 50
    leaf_distance = 200

    # DENSE branch leaves: Nemotron-4 15B → Minitron 8B/4B → Nemotron-Mini-4B
    bx, by, color, _, _ = branch_positions[0]
    dense_leaves = [
        # offset from branch center, label
        (-180, 100, "Nemotron-4", "15B base"),
        (-260, -10, "Minitron", "8B / 4B"),
        (-180, -120, "Nemotron-Mini", "4B Instruct"),
    ]
    for ox, oy, l1, l2 in dense_leaves:
        lx = bx + ox
        ly = by + oy
        # Connector
        c.setStrokeColor(TAUPE)
        c.setLineWidth(1.5)
        # From edge of branch
        dx, dy = lx - bx, ly - by
        d = math.sqrt(dx * dx + dy * dy)
        ux, uy = dx / d, dy / d
        c.line(bx + ux * branch_r, by + uy * branch_r,
               lx - ux * leaf_r, ly - uy * leaf_r)
        # Leaf
        c.setFillColor(IVORY)
        c.circle(lx, ly, leaf_r, stroke=0, fill=1)
        c.setStrokeColor(color)
        c.setLineWidth(2.5)
        c.circle(lx, ly, leaf_r, stroke=1, fill=0)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 11)
        c.drawCentredString(lx, ly + 4, l1)
        c.setFont('Poppins-Light', 10)
        c.drawCentredString(lx, ly - 10, l2)

    # LLAMA-NEMOTRON branch leaves
    bx, by, color, _, _ = branch_positions[1]
    llama_leaves = [
        (180, 100, "LN-Super", "49B"),
        (260, -10, "LN-Ultra", "253B"),
        (180, -120, "LN-Nano", "8B"),
    ]
    for ox, oy, l1, l2 in llama_leaves:
        lx = bx + ox
        ly = by + oy
        c.setStrokeColor(TAUPE)
        c.setLineWidth(1.5)
        dx, dy = lx - bx, ly - by
        d = math.sqrt(dx * dx + dy * dy)
        ux, uy = dx / d, dy / d
        c.line(bx + ux * branch_r, by + uy * branch_r,
               lx - ux * leaf_r, ly - uy * leaf_r)
        c.setFillColor(IVORY)
        c.circle(lx, ly, leaf_r, stroke=0, fill=1)
        c.setStrokeColor(color)
        c.setLineWidth(2.5)
        c.circle(lx, ly, leaf_r, stroke=1, fill=0)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 12)
        c.drawCentredString(lx, ly + 4, l1)
        c.setFont('Poppins-Light', 11)
        c.drawCentredString(lx, ly - 12, l2)

    # HYBRID MAMBA branch leaves — pull center leaf up to clear bottom caption
    bx, by, color, _, _ = branch_positions[2]
    hybrid_leaves = [
        (-200, 40, "Nemotron-H", "47B / 56B"),
        (0, -75, "Nano 2", "9B-v2"),
        (200, 40, "Nemotron 3", "Nano/Super/Ultra"),
    ]
    for ox, oy, l1, l2 in hybrid_leaves:
        lx = bx + ox
        ly = by + oy
        c.setStrokeColor(TAUPE)
        c.setLineWidth(1.5)
        dx, dy = lx - bx, ly - by
        d = math.sqrt(dx * dx + dy * dy)
        ux, uy = dx / d, dy / d
        c.line(bx + ux * branch_r, by + uy * branch_r,
               lx - ux * leaf_r, ly - uy * leaf_r)
        c.setFillColor(IVORY)
        c.circle(lx, ly, leaf_r, stroke=0, fill=1)
        c.setStrokeColor(color)
        c.setLineWidth(2.5)
        c.circle(lx, ly, leaf_r, stroke=1, fill=0)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 11)
        c.drawCentredString(lx, ly + 4, l1)
        c.setFont('Poppins-Light', 10)
        c.drawCentredString(lx, ly - 10, l2)

    # Caption strip at bottom
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Italic', 13)
    c.drawCentredString(W / 2, 80,
                        "Each leaf is a deployable student distilled or pruned from a larger teacher under a permissive license.")
    c.drawCentredString(W / 2, 60,
                        "Lineage selection — not model selection — is the operating discipline.")


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
