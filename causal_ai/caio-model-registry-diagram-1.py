#!/usr/bin/env python3
"""
CAIO Diagram: The Model Registry
Topic: model-registry
Type: Hub-and-spoke with split central registry (Staging / Production halves)
       and orbital input satellites feeding a published endpoint.
Output: caio-model-registry-diagram-1.png
"""

import math
import subprocess
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# --- Palette (CAIO standard) ---
NAVY      = HexColor('#1E2A4A')
SAPPHIRE  = HexColor('#1A3A6B')
GRAPHITE  = HexColor('#3A3A3A')
IVORY     = HexColor('#F0EAD6')
OCHRE     = HexColor('#C49A2A')
EMERALD   = HexColor('#1A5C3A')
BURGUNDY  = HexColor('#6B1C2A')
AMETHYST  = HexColor('#5A2D6A')
TEAL      = HexColor('#1A7A7A')
MUSTARD   = HexColor('#C4952A')
BRICK     = HexColor('#A04A2A')
TERRACOTTA= HexColor('#C4613A')
BRONZE    = HexColor('#8C6E3A')
UMBER     = HexColor('#6B4226')
MOSS      = HexColor('#4A5A3A')
TAUPE     = HexColor('#8A7B6B')
WHITE     = HexColor('#FFFFFF')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins',        '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold',   '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light',  '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas Setup ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-model-registry-diagram-1.png'
OUTPUT_PDF = '/tmp/_model_registry_temp.pdf'


def draw_arrow(c, x_from, y_from, x_to, y_to,
               line_color, arrow_color, line_width=2.5, arrow_size=12):
    """Draw a line with a triangular arrowhead at (x_to, y_to)."""
    dx, dy = x_to - x_from, y_to - y_from
    mag = math.sqrt(dx * dx + dy * dy)
    if mag == 0:
        return
    ux, uy = dx / mag, dy / mag
    # Pull line endpoint back so the arrowhead sits cleanly at the target
    x_line_end = x_to - ux * (arrow_size * 0.55)
    y_line_end = y_to - uy * (arrow_size * 0.55)
    c.setStrokeColor(line_color)
    c.setLineWidth(line_width)
    c.line(x_from, y_from, x_line_end, y_line_end)
    # Triangular arrowhead
    perp_x, perp_y = -uy, ux
    tip_x, tip_y = x_to, y_to
    base1_x = tip_x - ux * arrow_size + perp_x * arrow_size * 0.42
    base1_y = tip_y - uy * arrow_size + perp_y * arrow_size * 0.42
    base2_x = tip_x - ux * arrow_size - perp_x * arrow_size * 0.42
    base2_y = tip_y - uy * arrow_size - perp_y * arrow_size * 0.42
    p = c.beginPath()
    p.moveTo(tip_x, tip_y)
    p.lineTo(base1_x, base1_y)
    p.lineTo(base2_x, base2_y)
    p.close()
    c.setFillColor(arrow_color)
    c.drawPath(p, stroke=0, fill=1)


def draw_diagram(c):
    # Background — white for standalone Substack-style diagrams
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # --- Title block ---
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 36)
    c.drawCentredString(W / 2, H - 78, 'The Model Registry')

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 17)
    c.drawCentredString(W / 2, H - 112,
                        'Where ML artifacts converge, get promoted, and become production endpoints')

    # --- Layout constants ---
    cx, cy        = 720, 540          # Hub center (slight left of canvas center to make room for endpoint)
    hub_r         = 200               # Central hub radius
    inner_r       = 68                # White inner cutout radius
    sat_r         = 85                # Input satellite radius
    sat_dist      = 425               # Distance from hub center to satellite center
    endpoint_x    = 1360
    endpoint_y    = cy
    endpoint_r    = 82

    # Input satellite definitions: (angle_deg, fill_color, label, sublabel)
    satellites = [
        (135, BURGUNDY, 'Metadata',   'Lineage — owners — tags'),    # NW
        (45,  AMETHYST, 'Parameters', 'Hyperparameters — config'),   # NE
        (225, UMBER,    'ML Model',   'Trained weights'),            # SW
        (315, MOSS,     'Artifacts',  'Datasets — code — plots'),    # SE
    ]

    # Pre-compute satellite positions
    sat_positions = []
    for ang_deg, color, label, sublabel in satellites:
        ang_rad = math.radians(ang_deg)
        sx = cx + sat_dist * math.cos(ang_rad)
        sy = cy + sat_dist * math.sin(ang_rad)
        sat_positions.append((sx, sy, ang_rad, color, label, sublabel))

    # --- Connectors (drawn first so circles render on top) ---
    # Input connectors: from each satellite edge to the hub edge, arrow pointing INTO hub
    for sx, sy, ang_rad, color, label, sublabel in sat_positions:
        # Satellite edge in the direction of the hub
        sat_edge_x = sx + sat_r * math.cos(ang_rad + math.pi)
        sat_edge_y = sy + sat_r * math.sin(ang_rad + math.pi)
        # Hub edge in the direction of the satellite
        hub_edge_x = cx + hub_r * math.cos(ang_rad)
        hub_edge_y = cy + hub_r * math.sin(ang_rad)
        draw_arrow(c, sat_edge_x, sat_edge_y, hub_edge_x, hub_edge_y,
                   line_color=TAUPE, arrow_color=TAUPE,
                   line_width=2.5, arrow_size=13)

    # Output connector: hub right edge -> endpoint left edge, Navy and thicker
    draw_arrow(c, cx + hub_r, cy, endpoint_x - endpoint_r, endpoint_y,
               line_color=NAVY, arrow_color=NAVY,
               line_width=4, arrow_size=18)

    # Small caption above the output arrow
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Medium', 11)
    arrow_mid_x = (cx + hub_r + endpoint_x - endpoint_r) / 2
    c.drawCentredString(arrow_mid_x, cy + 14, 'PUBLISHES')

    # --- Central registry hub: top half Staging (Sapphire), bottom Production (Emerald) ---
    c.setFillColor(SAPPHIRE)
    c.wedge(cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r,
            0, 180, stroke=0, fill=1)
    c.setFillColor(EMERALD)
    c.wedge(cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r,
            180, 180, stroke=0, fill=1)

    # Thin divider between halves
    c.setStrokeColor(IVORY)
    c.setLineWidth(2)
    c.line(cx - hub_r + 4, cy, cx + hub_r - 4, cy)

    # STAGING label (top half)
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 26)
    c.drawCentredString(cx, cy + hub_r * 0.55, 'STAGING')
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(cx, cy + hub_r * 0.55 - 22, 'pre-promotion candidates')

    # PRODUCTION label (bottom half)
    c.setFont('Poppins-Bold', 26)
    c.drawCentredString(cx, cy - hub_r * 0.55 + 6, 'PRODUCTION')
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(cx, cy - hub_r * 0.55 - 18, 'serving live traffic')

    # White inner cutout with "MODEL REGISTRY" core label
    c.setFillColor(WHITE)
    c.setStrokeColor(NAVY)
    c.setLineWidth(2.5)
    c.circle(cx, cy, inner_r, stroke=1, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 14)
    c.drawCentredString(cx, cy + 5, 'MODEL')
    c.drawCentredString(cx, cy - 13, 'REGISTRY')

    # --- Input satellites ---
    for sx, sy, ang_rad, color, label, sublabel in sat_positions:
        c.setFillColor(color)
        c.setStrokeColor(NAVY)
        c.setLineWidth(1.5)
        c.circle(sx, sy, sat_r, stroke=1, fill=1)

        # Label inside satellite (Ivory on dark jewel fill)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 19)
        c.drawCentredString(sx, sy + 2, label)

        # Sublabel placed OUTSIDE the satellite (Navy on white canvas)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Light', 13)
        if sy > cy:
            # Upper-half satellite: sublabel above
            c.drawCentredString(sx, sy + sat_r + 22, sublabel)
        else:
            # Lower-half satellite: sublabel below
            c.drawCentredString(sx, sy - sat_r - 26, sublabel)

    # --- Endpoint satellite (Navy fill, terminal node) ---
    c.setFillColor(NAVY)
    c.setStrokeColor(NAVY)
    c.setLineWidth(2)
    c.circle(endpoint_x, endpoint_y, endpoint_r, stroke=1, fill=1)

    # Endpoint path text — /model in Mustard (passes AA at large size on Navy), version in Ivory
    c.setFillColor(MUSTARD)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(endpoint_x, endpoint_y + 8, '/model')
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 18)
    c.drawCentredString(endpoint_x, endpoint_y - 20, 'v1.2.3')

    # Endpoint outer labels — placed BELOW the circle so primary label sits closest
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(endpoint_x, endpoint_y - endpoint_r - 22, 'Model Endpoint')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(endpoint_x, endpoint_y - endpoint_r - 40, 'consumed by applications')

    # --- Footer caption ---
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(W / 2, 60,
                        'Artifacts feed the registry — Staging promotes to Production — Endpoint exposes the served version')


def main():
    # Render to intermediate PDF
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()

    # Rasterize PDF -> PNG at 150 DPI
    subprocess.run([
        'pdftoppm', '-png', '-r', '150',
        '-singlefile', OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')
    ], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
