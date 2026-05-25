#!/usr/bin/env python3
"""
CAIO Diagram: Automated MLOps Pipeline (Circular Reconstruction)
Topic: mlops-pipeline-circular
Type: Circular flow (process wheel) with deployment sub-cycle expansion
Output: caio-mlops-pipeline-diagram-1.png
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
TAUPE = HexColor('#8A7B6B')
OCHRE = HexColor('#C49A2A')
MUSTARD = HexColor('#C4952A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')
UMBER = HexColor('#6B4226')
MOSS = HexColor('#4A5A3A')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-mlops-pipeline-diagram-1.png'
OUTPUT_PDF = '/tmp/_mlops_pipeline.pdf'

# --- Layout constants ---
MAIN_CX, MAIN_CY = 540, 560
MAIN_ORBIT_R = 285
MAIN_NODE_R = 78

SUB_CX, SUB_CY = 1240, 560
SUB_ORBIT_R = 155
SUB_NODE_R = 62


def draw_arc_arrow(c, cx, cy, orbit_r, theta_start_deg, theta_end_deg,
                   color, line_width=2.5, arrow_size=14):
    """Draw an arc from start to end along orbit, with an arrowhead at the end.
    Clockwise = decreasing angle (extent negative)."""
    extent = theta_end_deg - theta_start_deg

    # Arc stroke
    c.setStrokeColor(color)
    c.setLineWidth(line_width)
    p = c.beginPath()
    p.arc(cx - orbit_r, cy - orbit_r, cx + orbit_r, cy + orbit_r,
          theta_start_deg, extent)
    c.drawPath(p, stroke=1, fill=0)

    # Arrowhead at end angle
    theta_end = math.radians(theta_end_deg)
    end_x = cx + orbit_r * math.cos(theta_end)
    end_y = cy + orbit_r * math.sin(theta_end)

    # Tangent at endpoint (clockwise traversal uses opposite-sign tangent)
    if extent < 0:
        tangent_x = math.sin(theta_end)
        tangent_y = -math.cos(theta_end)
    else:
        tangent_x = -math.sin(theta_end)
        tangent_y = math.cos(theta_end)

    base_x = end_x - arrow_size * tangent_x
    base_y = end_y - arrow_size * tangent_y
    perp_x = -tangent_y
    perp_y = tangent_x
    hw = arrow_size * 0.55
    left_x = base_x + hw * perp_x
    left_y = base_y + hw * perp_y
    right_x = base_x - hw * perp_x
    right_y = base_y - hw * perp_y

    c.setFillColor(color)
    p2 = c.beginPath()
    p2.moveTo(end_x, end_y)
    p2.lineTo(left_x, left_y)
    p2.lineTo(right_x, right_y)
    p2.close()
    c.drawPath(p2, stroke=0, fill=1)


def draw_circular_node(c, x, y, r, fill_color, text_color, number, label_lines,
                       border_color=None, number_size=24, label_size=13):
    """Draw a numbered circular node with wrapped label inside."""
    c.setFillColor(fill_color)
    c.setStrokeColor(border_color if border_color else IVORY)
    c.setLineWidth(2.5)
    c.circle(x, y, r, stroke=1, fill=1)

    # Number above center
    c.setFillColor(text_color)
    c.setFont('Poppins-Bold', number_size)
    c.drawCentredString(x, y + 12, str(number))

    # Label below number
    c.setFont('Poppins-Medium', label_size)
    line_height = label_size + 2
    if len(label_lines) == 1:
        c.drawCentredString(x, y - 18, label_lines[0])
    else:
        start_y = y - 14
        for i, line in enumerate(label_lines):
            c.drawCentredString(x, start_y - i * line_height, line)


def draw_sub_node(c, x, y, r, fill_color, text_color, label_lines,
                  border_color=None, label_size=12):
    """Draw a smaller labeled node for the sub-cluster (no number)."""
    c.setFillColor(fill_color)
    c.setStrokeColor(border_color if border_color else IVORY)
    c.setLineWidth(2.5)
    c.circle(x, y, r, stroke=1, fill=1)

    c.setFillColor(text_color)
    c.setFont('Poppins-Medium', label_size)
    line_height = label_size + 2
    if len(label_lines) == 1:
        c.drawCentredString(x, y - 4, label_lines[0])
    else:
        total = (len(label_lines) - 1) * line_height
        start_y = y + total / 2 - 4
        for i, line in enumerate(label_lines):
            c.drawCentredString(x, start_y - i * line_height, line)


def draw_main_wheel(c):
    """Six pipeline stages arranged clockwise, with directional arc connectors
    and a dashed feedback-loop closure from deployment back to data collection."""
    # Subtle orbit guide
    c.setStrokeColor(TAUPE)
    c.setLineWidth(0.7)
    c.setDash(1, 5)
    c.circle(MAIN_CX, MAIN_CY, MAIN_ORBIT_R, stroke=1, fill=0)
    c.setDash()

    # Six stages — clockwise flow ending at deployment on the right (0 deg)
    # Pattern: start at i=0 at 300 deg, decrease by 60 deg each step
    stages = [
        (1, ["Data", "collection"], SAPPHIRE, 300),
        (2, ["Data", "versioning"], EMERALD, 240),
        (3, ["Model", "training"], AMETHYST, 180),
        (4, ["Model", "evaluation"], BURGUNDY, 120),
        (5, ["Model", "validation"], UMBER, 60),
        (6, ["Model", "deployment"], NAVY, 0),
    ]

    # Compute positions
    positions = []
    for num, lines, color, ang in stages:
        rad = math.radians(ang)
        x = MAIN_CX + MAIN_ORBIT_R * math.cos(rad)
        y = MAIN_CY + MAIN_ORBIT_R * math.sin(rad)
        positions.append((x, y, ang, num, lines, color))

    # Angular clearance to keep arcs from running into node circles
    delta_deg = math.degrees(math.atan(MAIN_NODE_R / MAIN_ORBIT_R)) + 3

    # Forward arc connectors between adjacent stages (clockwise)
    for i in range(len(stages) - 1):
        ang_from = positions[i][2]
        ang_to = positions[i + 1][2]
        start_ang = ang_from - delta_deg
        end_ang = ang_to + delta_deg
        draw_arc_arrow(c, MAIN_CX, MAIN_CY, MAIN_ORBIT_R,
                       start_ang, end_ang, GRAPHITE,
                       line_width=2.8, arrow_size=15)

    # Feedback-loop closure (deployment -> data collection), dashed
    ang_from = 0
    ang_to = -60  # = 300 deg mod 360
    start_ang = ang_from - delta_deg
    end_ang = ang_to + delta_deg
    c.setDash(7, 5)
    draw_arc_arrow(c, MAIN_CX, MAIN_CY, MAIN_ORBIT_R,
                   start_ang, end_ang, TAUPE,
                   line_width=2.2, arrow_size=12)
    c.setDash()

    # Draw nodes on top
    for x, y, ang, num, lines, color in positions:
        draw_circular_node(c, x, y, MAIN_NODE_R, color, IVORY, num, lines,
                           number_size=24, label_size=13)

    # Center label inside the wheel
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(MAIN_CX, MAIN_CY + 10, "Automated")
    c.drawCentredString(MAIN_CX, MAIN_CY - 18, "Pipeline")

    # Small feedback label near the dashed closure arc
    # Place near midpoint between deployment (0 deg) and data collection (300 deg)
    fb_ang_deg = -30  # midpoint
    fb_rad = math.radians(fb_ang_deg)
    fb_x = MAIN_CX + (MAIN_ORBIT_R + 38) * math.cos(fb_rad)
    fb_y = MAIN_CY + (MAIN_ORBIT_R + 38) * math.sin(fb_rad)
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Italic', 11) if False else c.setFont('Poppins', 11)
    c.drawCentredString(fb_x, fb_y, "feedback")
    c.drawCentredString(fb_x, fb_y - 13, "loop")


def draw_sub_cluster(c):
    """Deployment expansion: 4-node circular flow showing Trigger -> CI/CD ->
    Container Registry -> Kubernetes Deploy with feedback closure."""
    # Subtle orbit guide
    c.setStrokeColor(TAUPE)
    c.setLineWidth(0.7)
    c.setDash(1, 5)
    c.circle(SUB_CX, SUB_CY, SUB_ORBIT_R, stroke=1, fill=0)
    c.setDash()

    # Four sub-stages — clockwise from top
    # Trigger uses Mustard (light) with Navy text + Navy border
    sub_stages = [
        (["Trigger"], MUSTARD, NAVY, NAVY, 90),
        (["CI/CD"], TEAL, IVORY, None, 0),
        (["Container", "Registry"], MOSS, IVORY, None, -90),
        (["Kubernetes", "Deploy"], SAPPHIRE, IVORY, None, -180),
    ]

    positions = []
    for lines, fill, text_color, border, ang in sub_stages:
        rad = math.radians(ang)
        x = SUB_CX + SUB_ORBIT_R * math.cos(rad)
        y = SUB_CY + SUB_ORBIT_R * math.sin(rad)
        positions.append((x, y, ang, lines, fill, text_color, border))

    delta_deg = math.degrees(math.atan(SUB_NODE_R / SUB_ORBIT_R)) + 4

    # Forward connectors (Trigger -> CI/CD -> Container Registry -> K8s Deploy)
    for i in range(3):
        ang_from = positions[i][2]
        ang_to = positions[i + 1][2]
        start_ang = ang_from - delta_deg
        end_ang = ang_to + delta_deg
        draw_arc_arrow(c, SUB_CX, SUB_CY, SUB_ORBIT_R,
                       start_ang, end_ang, GRAPHITE,
                       line_width=2.4, arrow_size=12)

    # Feedback closure (K8s Deploy -> Trigger), dashed
    ang_from = -180
    ang_to = -270  # = 90 deg mod 360
    start_ang = ang_from - delta_deg
    end_ang = ang_to + delta_deg
    c.setDash(6, 4)
    draw_arc_arrow(c, SUB_CX, SUB_CY, SUB_ORBIT_R,
                   start_ang, end_ang, TAUPE,
                   line_width=2, arrow_size=11)
    c.setDash()

    # Draw nodes
    for x, y, ang, lines, fill, text_color, border in positions:
        draw_sub_node(c, x, y, SUB_NODE_R, fill, text_color, lines,
                      border_color=border, label_size=12)

    # Center label
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(SUB_CX, SUB_CY + 6, "Deploy")
    c.drawCentredString(SUB_CX, SUB_CY - 14, "cycle")


def draw_connector_between(c):
    """Dashed connector showing the deployment node expansion into the sub-cycle."""
    # Right edge of deployment node (at angle 0 on main wheel)
    deploy_x = MAIN_CX + MAIN_ORBIT_R + MAIN_NODE_R
    deploy_y = MAIN_CY
    # Left edge of K8s Deploy node (at angle 180 / -180 on sub-cluster)
    k8s_x = SUB_CX - SUB_ORBIT_R - SUB_NODE_R
    k8s_y = SUB_CY

    # Small breathing room
    start_x = deploy_x + 6
    end_x = k8s_x - 6

    # Dashed line, Navy
    c.setStrokeColor(NAVY)
    c.setLineWidth(2.2)
    c.setDash(8, 6)
    c.line(start_x, deploy_y, end_x, k8s_y)
    c.setDash()

    # Arrowhead at end (pointing right toward sub-cluster)
    c.setFillColor(NAVY)
    p = c.beginPath()
    p.moveTo(end_x + 10, k8s_y)
    p.lineTo(end_x - 4, k8s_y + 8)
    p.lineTo(end_x - 4, k8s_y - 8)
    p.close()
    c.drawPath(p, stroke=0, fill=1)

    # Label above connector
    mid_x = (start_x + end_x) / 2
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 13)
    c.drawCentredString(mid_x, k8s_y + 14, "expanded view")


def draw_diagram(c):
    # Background — white for standalone Substack embedding
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 75, "Automated MLOps Pipeline")

    # Subtitle
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W / 2, H - 108,
        "Continuous delivery from data preparation through Kubernetes deployment"
    )

    # Section captions above each cluster
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Medium', 14)
    c.drawCentredString(MAIN_CX, MAIN_CY + MAIN_ORBIT_R + MAIN_NODE_R + 32,
                        "PIPELINE STAGES")
    c.drawCentredString(SUB_CX, SUB_CY + SUB_ORBIT_R + SUB_NODE_R + 28,
                        "DEPLOYMENT EXPANSION")

    # Connector between clusters (drawn first so nodes can sit over it cleanly)
    draw_connector_between(c)

    # Main wheel and sub-cluster
    draw_main_wheel(c)
    draw_sub_cluster(c)

    # Footer attribution
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(W / 2, 38, "Art Koval  —  Chief AI Officer Insights")


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
