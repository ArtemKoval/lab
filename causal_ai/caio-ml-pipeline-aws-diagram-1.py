#!/usr/bin/env python3
"""
CAIO Diagram: Production ML Lifecycle on AWS
Topic: ml-pipeline-aws
Type: Circular flow (process wheel) + hub-and-spoke AWS service satellites
Output: caio-ml-pipeline-aws-diagram-1.png

Six-stage ML lifecycle arranged as a closed loop, with each supporting
infrastructure satellite mapped to its AWS-native service. The dashed
return connector from SageMaker Model Monitor closes the loop into the
next iteration of problem definition.
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
MUSTARD = HexColor('#C4952A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')
TAUPE = HexColor('#8A7B6B')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-ml-pipeline-aws-diagram-1.png'
OUTPUT_PDF = '/tmp/_aws_diagram_1.pdf'

# --- Layout constants ---
CX, CY = 800, 590
INNER_R = 235
NODE_R = 65
HUB_R = 95
OUTER_R = 425
SAT_R = 60


def draw_arrow_head(c, end_x, end_y, tangent_rad, size, color):
    tip_x = end_x + size * math.cos(tangent_rad)
    tip_y = end_y + size * math.sin(tangent_rad)
    back_x = end_x - size * 0.35 * math.cos(tangent_rad)
    back_y = end_y - size * 0.35 * math.sin(tangent_rad)
    w1x = back_x + size * 0.55 * math.cos(tangent_rad + math.pi / 2)
    w1y = back_y + size * 0.55 * math.sin(tangent_rad + math.pi / 2)
    w2x = back_x + size * 0.55 * math.cos(tangent_rad - math.pi / 2)
    w2y = back_y + size * 0.55 * math.sin(tangent_rad - math.pi / 2)
    c.setFillColor(color)
    p = c.beginPath()
    p.moveTo(tip_x, tip_y)
    p.lineTo(w1x, w1y)
    p.lineTo(w2x, w2y)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def draw_diagram(c):
    # White background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 65, "Production ML Lifecycle on AWS")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, H - 95, "Six-stage closed loop with AWS-native supporting services")

    # Pipeline stages (clockwise from 12 o'clock)
    # (display_label, step_number, fill_color, category)
    pipeline = [
        ("Problem\nDefinition",   "1", BURGUNDY, "human"),
        ("Model\nDesign",         "2", BURGUNDY, "human"),
        ("Data\nPreparation",     "3", SAPPHIRE, "pipeline"),
        ("Model\nTraining",       "4", SAPPHIRE, "pipeline"),
        ("Model\nEvaluation",     "5", SAPPHIRE, "pipeline"),
        ("Model\nDeployment",     "6", SAPPHIRE, "pipeline"),
    ]

    n = len(pipeline)
    positions = []
    for i in range(n):
        angle_deg = 90 - i * (360 / n)
        angle_rad = math.radians(angle_deg)
        x = CX + INNER_R * math.cos(angle_rad)
        y = CY + INNER_R * math.sin(angle_rad)
        positions.append((x, y, angle_rad, angle_deg))

    # AWS-flavored satellites
    # (label, fill, text_color, navy_border, target_node_idx, sat_angle_deg, dashed, flow_label)
    satellites = [
        ("SageMaker\nModel Monitor", AMETHYST, IVORY, False, 0,   90, True,  "logging"),
        ("Amazon S3\n+ Redshift",    MUSTARD,  NAVY,  True,  2,  -15, False, "data"),
        ("SageMaker\nFeature Store", MUSTARD,  NAVY,  True,  2,  -50, False, "features"),
        ("SageMaker\nExperiments",   EMERALD,  IVORY, False, 3,  -90, False, "metrics"),
        ("SageMaker\nModel Registry",MUSTARD,  NAVY,  True,  4, -150, False, "model"),
        ("SageMaker\nEndpoints",     AMETHYST, IVORY, False, 5,  150, False, "endpoint"),
    ]

    # 1. Pipeline arcs
    c.setStrokeColor(TAUPE)
    c.setLineWidth(3)
    for i in range(n):
        start_deg = 90 - i * 60
        gap_deg = math.degrees(math.atan2(NODE_R * 1.15, INNER_R))
        arc_start = start_deg - gap_deg
        arc_extent = -(60 - 2 * gap_deg)
        p = c.beginPath()
        p.arc(CX - INNER_R, CY - INNER_R, CX + INNER_R, CY + INNER_R, arc_start, arc_extent)
        c.drawPath(p, stroke=1, fill=0)
        end_rad = math.radians(arc_start + arc_extent)
        end_x = CX + INNER_R * math.cos(end_rad)
        end_y = CY + INNER_R * math.sin(end_rad)
        draw_arrow_head(c, end_x, end_y, end_rad - math.pi / 2, 13, TAUPE)

    # 2. Satellite connectors with flow labels
    for sat_label, sat_color, sat_text, has_border, node_idx, sat_angle_deg, dashed, flow_label in satellites:
        nx, ny, _, _ = positions[node_idx]
        sar = math.radians(sat_angle_deg)
        sx = CX + OUTER_R * math.cos(sar)
        sy = CY + OUTER_R * math.sin(sar)
        dx, dy = sx - nx, sy - ny
        dist = math.hypot(dx, dy)
        ux, uy = dx / dist, dy / dist
        s_start = (nx + NODE_R * ux, ny + NODE_R * uy)
        s_end   = (sx - SAT_R * ux, sy - SAT_R * uy)

        c.setStrokeColor(TAUPE)
        c.setLineWidth(2.2)
        if dashed:
            c.setDash(6, 5)
        c.line(s_start[0], s_start[1], s_end[0], s_end[1])
        if dashed:
            c.setDash()

        # Flow label at midpoint with white pad to mask line behind text
        mid_x = (s_start[0] + s_end[0]) / 2
        mid_y = (s_start[1] + s_end[1]) / 2
        c.setFont('Poppins', 11)
        lw = c.stringWidth(flow_label, 'Poppins', 11)
        c.setFillColor(HexColor('#FFFFFF'))
        c.rect(mid_x - lw / 2 - 5, mid_y - 6, lw + 10, 14, stroke=0, fill=1)
        c.setFillColor(GRAPHITE)
        c.drawCentredString(mid_x, mid_y - 2, flow_label)

    # 3. Central hub
    c.setFillColor(NAVY)
    c.setStrokeColor(IVORY)
    c.setLineWidth(4)
    c.circle(CX, CY, HUB_R, stroke=1, fill=1)
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 18)
    c.drawCentredString(CX, CY + 16, "AWS")
    c.drawCentredString(CX, CY - 6, "ML")
    c.drawCentredString(CX, CY - 26, "Lifecycle")

    # 4. Pipeline nodes
    for (label, num, color, cat), (x, y, _, _) in zip(pipeline, positions):
        c.setFillColor(color)
        c.circle(x, y, NODE_R, stroke=0, fill=1)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 13)
        c.drawCentredString(x, y + 28, num)
        c.setFont('Poppins-Bold', 13)
        lines = label.split('\n')
        line_h = 15
        for j, ln in enumerate(lines):
            off = (len(lines) - 1) * line_h / 2 - j * line_h
            c.drawCentredString(x, y + off - 8, ln)

    # 5. Satellites
    for sat_label, sat_color, sat_text, has_border, node_idx, sat_angle_deg, _, _ in satellites:
        sar = math.radians(sat_angle_deg)
        sx = CX + OUTER_R * math.cos(sar)
        sy = CY + OUTER_R * math.sin(sar)
        c.setFillColor(sat_color)
        if has_border:
            c.setStrokeColor(NAVY)
            c.setLineWidth(2.5)
            c.circle(sx, sy, SAT_R, stroke=1, fill=1)
        else:
            c.circle(sx, sy, SAT_R, stroke=0, fill=1)
        c.setFillColor(sat_text)
        c.setFont('Poppins-Bold', 11)
        lines = sat_label.split('\n')
        line_h = 13
        for j, ln in enumerate(lines):
            off = (len(lines) - 1) * line_h / 2 - j * line_h
            c.drawCentredString(sx, sy + off - 3, ln)

    # 6. Feedback annotation along the dashed loop
    fb_x = CX + 95
    fb_y = CY + INNER_R + NODE_R + 70
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawString(fb_x, fb_y, "continuous feedback loop")

    # 7. Bottom legend
    legend_y = 80
    legend_items = [
        ("Human-centric step",       BURGUNDY, IVORY, False),
        ("Pipeline component",       SAPPHIRE, IVORY, False),
        ("Data & model storage",     MUSTARD,  NAVY,  True),
        ("Lineage & traceability",   EMERALD,  IVORY, False),
        ("Customer-facing",          AMETHYST, IVORY, False),
    ]
    c.setFont('Poppins-Medium', 14)
    widths = [c.stringWidth(lbl, 'Poppins-Medium', 14) + 36 for lbl, *_ in legend_items]
    spacing = 28
    total_w = sum(widths) + spacing * (len(legend_items) - 1)
    cur_x = (W - total_w) / 2
    for (label, color, text_color, border), w in zip(legend_items, widths):
        sx = cur_x + 12
        c.setFillColor(color)
        if border:
            c.setStrokeColor(NAVY)
            c.setLineWidth(1.5)
            c.circle(sx, legend_y, 10, stroke=1, fill=1)
        else:
            c.circle(sx, legend_y, 10, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 14)
        c.drawString(sx + 18, legend_y - 5, label)
        cur_x += w + spacing


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    subprocess.run(['pdftoppm', '-png', '-r', '150', '-singlefile', OUTPUT_PDF,
                    OUTPUT_PNG.replace('.png', '')], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
