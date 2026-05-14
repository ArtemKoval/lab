#!/usr/bin/env python3
"""
CAIO Carousel: The Platform That Compounds
Topic: caio-ml-platform-business-case
13 slides, 1080x1080, Ivory (#F0EAD6) background, Navy footer bar
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
UMBER = HexColor('#6B4226')
MOSS = HexColor('#4A5A3A')
TAUPE = HexColor('#8A7B6B')
TERRACOTTA = HexColor('#C4613A')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas Setup ---
W, H = 1080, 1080
OUTPUT_PDF = '/home/claude/caio-ml-platform-business-case-carousel.pdf'

# Zone constants
FOOTER_TOP = 62           # nothing below y=70 except footer
CONTENT_BOTTOM = 80       # minimum y for content
TOP_ACCENT_TOP = H        # top accent stripe
TOP_ACCENT_BOTTOM = H - 8
TITLE_Y = H - 105
SUBTITLE_Y = H - 145
CONTENT_TOP_DEFAULT = H - 175


# ============================================================
# Helpers
# ============================================================
def draw_background(c):
    c.setFillColor(IVORY)
    c.rect(0, 0, W, H, stroke=0, fill=1)


def draw_top_accent(c, color=NAVY, height=8):
    c.setFillColor(color)
    c.rect(0, H - height, W, height, stroke=0, fill=1)


def draw_footer(c, slide_num, total=13):
    # Navy footer bar
    c.setFillColor(NAVY)
    c.rect(0, 0, W, 60, stroke=0, fill=1)
    # Small mustard accent line above
    c.setFillColor(OCHRE)
    c.rect(0, 60, W, 2, stroke=0, fill=1)
    # Footer text
    c.setFillColor(IVORY)
    c.setFont('Poppins-Light', 14)
    c.drawString(40, 22, "Art Koval")
    c.drawRightString(W - 40, 22, f"{slide_num} / {total}")


def draw_title(c, title, color=NAVY, y=TITLE_Y, size=34, font='Poppins-Bold'):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawCentredString(W / 2, y, title)


def draw_subtitle(c, subtitle, color=GRAPHITE, y=SUBTITLE_Y, size=16, font='Poppins-Light'):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawCentredString(W / 2, y, subtitle)


def stat_ring(c, cx, cy, r, big_text, descriptor, source_line=None):
    """Draw a stat callout ring (Navy circle + Mustard number inside + Navy descriptor below)."""
    c.setFillColor(NAVY)
    c.setStrokeColor(NAVY)
    c.circle(cx, cy, r, stroke=0, fill=1)
    c.setFillColor(MUSTARD)
    c.setFont('Poppins-Bold', 50)
    c.drawCentredString(cx, cy - 14, big_text)
    # Descriptor below ring
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 14)
    lines = descriptor.split('|')
    for i, line in enumerate(lines):
        c.drawCentredString(cx, cy - r - 28 - i * 18, line.strip())
    if source_line:
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins-Light', 10)
        c.drawCentredString(cx, cy - r - 28 - len(lines) * 18, source_line)


def donut(c, cx, cy, outer_r, inner_r, segments):
    """segments = [(value_pct, color), ...]
       Draws a donut: arc wedges from 12 o'clock CCW, then cuts out inner."""
    start_ang = 90  # 12 o'clock
    total_pct = sum(s[0] for s in segments)
    for val, color in segments:
        extent = -(val / total_pct) * 360  # negative for CW
        c.setFillColor(color)
        c.setStrokeColor(IVORY)
        c.setLineWidth(2)
        c.wedge(cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
                start_ang, extent, stroke=1, fill=1)
        start_ang += extent
    # Cut center to make donut
    c.setFillColor(IVORY)
    c.setStrokeColor(IVORY)
    c.circle(cx, cy, inner_r, stroke=0, fill=1)


def label_below_circle(c, cx, cy, r, lines, color=NAVY, size=14):
    """Place lines of text centered below a circle."""
    c.setFillColor(color)
    c.setFont('Poppins-Medium', size)
    for i, line in enumerate(lines):
        c.drawCentredString(cx, cy - r - 24 - i * (size + 4), line)


# ============================================================
# Slide 1: Cover with three stat rings
# ============================================================
def slide_1(c):
    draw_background(c)
    draw_top_accent(c, NAVY, height=12)

    # Title - larger for cover
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 50)
    c.drawCentredString(W / 2, H - 130, "The Platform That")
    c.setFont('Poppins-Bold', 50)
    c.setFillColor(BURGUNDY)
    c.drawCentredString(W / 2, H - 190, "Compounds")

    # Subtitle
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 19)
    c.drawCentredString(W / 2, H - 245, "Why an internal ML/AI platform is the")
    c.drawCentredString(W / 2, H - 270, "CAIO's highest-leverage investment")

    # Three stat rings - row in lower-middle area
    r = 95
    cy = 500
    spacing = 280
    stat_ring(c, W / 2 - spacing, cy, r, "95%",
              "No measurable | AI ROI",
              "MIT NANDA, 2025")
    stat_ring(c, W / 2, cy, r, "67%",
              "Partner-led | success rate",
              "MIT NANDA, 2025")
    stat_ring(c, W / 2 + spacing, cy, r, "48%",
              "Of AI projects | reach production",
              "Gartner, 2025")

    # Bottom credit / book reference
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 16)
    c.drawCentredString(W / 2, 175, "The CAIO case for")
    c.setFont('Poppins-Bold', 18)
    c.setFillColor(BURGUNDY)
    c.drawCentredString(W / 2, 148, "ML Platform Engineering")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(W / 2, 125, "Internal developer platforms, custom SLMs, agentic workflows")

    draw_footer(c, 1)


# ============================================================
# Slide 2: Hero donut - the 95% / 5% divide
# ============================================================
def slide_2(c):
    draw_background(c)
    draw_top_accent(c, BURGUNDY)

    draw_title(c, "The GenAI Divide")
    draw_subtitle(c, "$30 to $40 billion spent. Only 5% extracted measurable value.")

    cx, cy = W / 2, 510
    outer_r, inner_r = 230, 145

    # 95% Burgundy (no return), 5% Emerald (real value)
    donut(c, cx, cy, outer_r, inner_r, [(95, BURGUNDY), (5, EMERALD)])

    # Central KPI
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 38)
    c.drawCentredString(cx, cy + 8, "$30-40B")
    c.setFont('Poppins-Medium', 16)
    c.drawCentredString(cx, cy - 22, "GenAI spent")

    # Segment callouts
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Bold', 22)
    c.drawString(80, 360, "95%")
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 14)
    c.drawString(150, 364, "no measurable P&L impact")

    c.setFillColor(EMERALD)
    c.setFont('Poppins-Bold', 22)
    c.drawString(80, 320, "5%")
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 14)
    c.drawString(150, 324, "extracting real value")

    # Diagnosis box (text only on Ivory)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 18)
    c.drawCentredString(W / 2, 230, "Failure mode is not model quality.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 15)
    c.drawCentredString(W / 2, 200, "It is the absence of a platform layer that integrates,")
    c.drawCentredString(W / 2, 180, "learns, and persists across model generations.")

    # Source
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 90, "MIT NANDA, State of AI in Business 2025 — 300+ deployments, 52 interviews, 153 leadership surveys")

    draw_footer(c, 2)


# ============================================================
# Slide 3: Segmented wheel - six capability domains
# ============================================================
def slide_3(c):
    draw_background(c)
    draw_top_accent(c, NAVY)

    draw_title(c, "Six Platform Capability Domains")
    draw_subtitle(c, "One integrated stack. Every model passes through; the platform survives every model.")

    cx, cy = W / 2, 470
    outer_r = 290
    inner_r = 105

    sectors = [
        ("Pipelines", "Kubeflow", SAPPHIRE),
        ("Tracking", "MLflow", EMERALD),
        ("Features", "Feast", AMETHYST),
        ("Serving", "BentoML", BURGUNDY),
        ("Monitoring", "Evidently", UMBER),
        ("LLM Obs", "Langfuse", MOSS),
    ]
    n = len(sectors)
    angle_per = 360 / n
    start_offset = 90 + angle_per / 2

    for i, (name, sub, color) in enumerate(sectors):
        start_ang = start_offset - (i + 1) * angle_per
        c.setFillColor(color)
        c.setStrokeColor(IVORY)
        c.setLineWidth(3)
        c.wedge(cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
                start_ang, angle_per, stroke=1, fill=1)

    # Cut center
    c.setFillColor(IVORY)
    c.setStrokeColor(IVORY)
    c.circle(cx, cy, inner_r + 8, stroke=0, fill=1)

    # Hub
    c.setFillColor(NAVY)
    c.setStrokeColor(IVORY)
    c.setLineWidth(3)
    c.circle(cx, cy, inner_r, stroke=1, fill=1)

    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 17)
    c.drawCentredString(cx, cy + 12, "ML / AI")
    c.drawCentredString(cx, cy - 8, "Platform")
    c.setFillColor(OCHRE)
    c.setFont('Poppins-Medium', 11)
    c.drawCentredString(cx, cy - 30, "on Kubernetes")

    # Sector labels
    label_r = (outer_r + inner_r) / 2
    for i, (name, sub, color) in enumerate(sectors):
        mid_ang_deg = start_offset - (i + 0.5) * angle_per
        rad = math.radians(mid_ang_deg)
        lx = cx + label_r * math.cos(rad)
        ly = cy + label_r * math.sin(rad)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 16)
        c.drawCentredString(lx, ly + 8, name)
        c.setFont('Poppins-Medium', 12)
        c.drawCentredString(lx, ly - 12, sub)

    # Caption
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 15)
    c.drawCentredString(W / 2, 130, "The integration between these six domains is the asset.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(W / 2, 105, "Substitutes exist in each slot. The durable value lies in the seams.")

    draw_footer(c, 3)


# ============================================================
# Slide 4: Dual donut comparison - change failure rate
# ============================================================
def slide_4(c):
    draw_background(c)
    draw_top_accent(c, NAVY)

    draw_title(c, "Why the Platform Layer Earns Its Cost")
    draw_subtitle(c, "Change failure rate: a leading indicator of platform discipline")

    # Two donuts side by side
    cy = 540
    outer_r, inner_r = 145, 90
    left_cx = 300
    right_cx = 780

    # Left: Without IDP — 75% over 15% failure, 25% under
    donut(c, left_cx, cy, outer_r, inner_r, [(75, BURGUNDY), (25, TAUPE)])
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 38)
    c.drawCentredString(left_cx, cy + 4, "25%")
    c.setFont('Poppins-Medium', 12)
    c.drawCentredString(left_cx, cy - 20, "sub-15% failure")

    # Right: With IDP — 89% under 15%, 11% over
    donut(c, right_cx, cy, outer_r, inner_r, [(89, EMERALD), (11, TAUPE)])
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 38)
    c.drawCentredString(right_cx, cy + 4, "89%")
    c.setFont('Poppins-Medium', 12)
    c.drawCentredString(right_cx, cy - 20, "sub-15% failure")

    # Labels above donuts
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(left_cx, cy + outer_r + 40, "Without IDP")
    c.drawCentredString(right_cx, cy + outer_r + 40, "With IDP")

    # Labels below
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13)
    c.drawCentredString(left_cx, cy - outer_r - 38, "Fragmented tools and bespoke")
    c.drawCentredString(left_cx, cy - outer_r - 56, "integrations break under change")
    c.drawCentredString(right_cx, cy - outer_r - 38, "Standardized rails carry change")
    c.drawCentredString(right_cx, cy - outer_r - 56, "without breaking what surrounds them")

    # Bottom callout
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 17)
    c.drawCentredString(W / 2, 250, "Mature platform organizations also see")
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Bold', 17)
    c.drawCentredString(W / 2, 225, "3.5x higher deployment frequency and 4x shorter lead times.")

    # Sources
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 105, "DevOps Benchmarking Study 2023; EITT Platform Engineering Report 2026")
    c.drawCentredString(W / 2, 88, "Sub-15% failure rate is the DORA benchmark for elite performers")

    draw_footer(c, 4)


# ============================================================
# Slide 5: Hub-and-spoke - AWS integration points
# ============================================================
def slide_5(c):
    draw_background(c)
    draw_top_accent(c, NAVY)

    draw_title(c, "AWS as Configuration, Not Architecture")
    draw_subtitle(c, "Kubernetes operators collapse the managed-vs-self-hosted trade-off")

    cx, cy = W / 2, 530
    hub_r = 90
    spoke_r = 235
    node_r = 65

    # Spokes (6 surrounding nodes)
    spokes = [
        ("ACK", "SageMaker", "as kubectl", SAPPHIRE),
        ("Karpenter", "GPU nodes", "in <90 sec", EMERALD),
        ("EKS Auto", "Managed", "infrastructure", AMETHYST),
        ("EFS / FSx", "Shared", "datasets", BURGUNDY),
        ("KServe", "Scalable", "inference", UMBER),
        ("Managed", "Prometheus", "Grafana", MOSS),
    ]
    n = len(spokes)
    for i, (name, line1, line2, color) in enumerate(spokes):
        ang = math.radians(90 - i * (360 / n))
        sx = cx + spoke_r * math.cos(ang)
        sy = cy + spoke_r * math.sin(ang)
        # Connector line
        c.setStrokeColor(TAUPE)
        c.setLineWidth(2)
        # Compute the connector endpoints so they don't pass through node/hub
        # Vector from hub to spoke
        dx, dy = sx - cx, sy - cy
        dist = math.hypot(dx, dy)
        ux, uy = dx / dist, dy / dist
        c.line(cx + hub_r * ux, cy + hub_r * uy, sx - node_r * ux, sy - node_r * uy)
        # Spoke node
        c.setFillColor(color)
        c.setStrokeColor(IVORY)
        c.setLineWidth(2)
        c.circle(sx, sy, node_r, stroke=1, fill=1)
        # Text inside
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 15)
        c.drawCentredString(sx, sy + 13, name)
        c.setFont('Poppins', 11)
        c.drawCentredString(sx, sy - 2, line1)
        c.drawCentredString(sx, sy - 16, line2)

    # Hub
    c.setFillColor(NAVY)
    c.setStrokeColor(IVORY)
    c.setLineWidth(3)
    c.circle(cx, cy, hub_r, stroke=1, fill=1)
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 18)
    c.drawCentredString(cx, cy + 14, "EKS")
    c.setFont('Poppins-Medium', 13)
    c.drawCentredString(cx, cy - 4, "Kubeflow")
    c.setFillColor(OCHRE)
    c.setFont('Poppins-Bold', 12)
    c.drawCentredString(cx, cy - 28, "control plane")

    # Bottom caption
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 15)
    c.drawCentredString(W / 2, 140, "Every AWS service becomes a Kubernetes custom resource.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(W / 2, 115, "The control plane stays portable. The compute stays optimal.")
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 90, "AWS Controllers for Kubernetes (ACK); AWS EKS best-practices documentation 2025")

    draw_footer(c, 5)


# ============================================================
# Slide 6: Radar overlay - three approaches
# ============================================================
def slide_6(c):
    draw_background(c)
    draw_top_accent(c, NAVY)

    draw_title(c, "Three Approaches, One Winner")
    draw_subtitle(c, "Platform-led IDP dominates the cost-effectiveness curve at scale")

    cx, cy = W / 2, 500
    max_r = 230

    axes = [
        ("Time to", "production"),
        ("Failure", "resilience"),
        ("Cost", "predictability"),
        ("Vendor", "portability"),
        ("Governance", "maturity"),
        ("LLM", "extensibility"),
    ]
    series = [
        ("DIY notebook-to-prod", BURGUNDY, [20, 18, 30, 75, 25, 20]),
        ("Managed-platform-only", SAPPHIRE, [72, 68, 55, 28, 75, 62]),
        ("Platform-led IDP", EMERALD, [85, 88, 82, 78, 85, 86]),
    ]

    n_axes = len(axes)
    axis_angles = [math.radians(90 - i * (360 / n_axes)) for i in range(n_axes)]

    # Gridlines
    c.setStrokeColor(TAUPE)
    c.setLineWidth(0.8)
    for level in [0.25, 0.5, 0.75, 1.0]:
        r = max_r * level
        pts = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in axis_angles]
        p = c.beginPath()
        p.moveTo(pts[0][0], pts[0][1])
        for x, y in pts[1:]:
            p.lineTo(x, y)
        p.close()
        c.drawPath(p, stroke=1, fill=0)

    # Spokes
    for a in axis_angles:
        c.line(cx, cy, cx + max_r * math.cos(a), cy + max_r * math.sin(a))

    # Plot series
    for name, color, values in series:
        pts = []
        for i, val in enumerate(values):
            r = max_r * (val / 100.0)
            x = cx + r * math.cos(axis_angles[i])
            y = cy + r * math.sin(axis_angles[i])
            pts.append((x, y))
        c.saveState()
        c.setFillColor(color)
        c.setStrokeColor(color)
        c.setLineWidth(2.5)
        c.setFillAlpha(0.32)
        p = c.beginPath()
        p.moveTo(pts[0][0], pts[0][1])
        for x, y in pts[1:]:
            p.lineTo(x, y)
        p.close()
        c.drawPath(p, stroke=1, fill=1)
        c.restoreState()
        c.setFillColor(color)
        for x, y in pts:
            c.circle(x, y, 3.5, stroke=0, fill=1)

    # Axis labels
    label_r = max_r + 45
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 12)
    for i, (l1, l2) in enumerate(axes):
        a = axis_angles[i]
        lx = cx + label_r * math.cos(a)
        ly = cy + label_r * math.sin(a)
        c.drawCentredString(lx, ly + 6, l1)
        c.drawCentredString(lx, ly - 8, l2)

    # Legend (bottom, three rows compact)
    legend_y = 170
    c.setFont('Poppins-Medium', 13)
    spacing = 340
    legend_x_start = 100
    for i, (name, color, _) in enumerate(series):
        lx = legend_x_start + i * spacing
        c.setFillColor(color)
        c.circle(lx, legend_y, 8, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.drawString(lx + 16, legend_y - 4, name)

    # Footer note
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 105, "Higher = better. Vendor portability rewards an architecture that survives a cloud or service swap.")
    c.drawCentredString(W / 2, 88, "Sources: MIT NANDA 2025, Cortex/Forrester TEI 2024, AWS EKS docs 2025")

    draw_footer(c, 6)


# ============================================================
# Slide 7: Progress rings - business outcomes
# ============================================================
def slide_7(c):
    draw_background(c)
    draw_top_accent(c, NAVY)

    draw_title(c, "What the Platform Layer Delivers")
    draw_subtitle(c, "Quantified outcomes from internal developer platform adoption")

    # Progress rings on the left side
    cx, cy = 320, 510
    ring_w = 20
    base_r = 180
    gap = 30

    metrics = [
        (89, EMERALD, "89%",
         "sub-15% change failure rate", "vs. 75% without IDP",
         "DevOps Benchmarking 2023"),
        (100, SAPPHIRE, "3.5x",   # 3.5x rendered as a near-full ring
         "deployment frequency", "vs. non-platform orgs",
         "EITT Platform Engineering 2026"),
        (25, BURGUNDY, "25%",
         "reduction in deployment time", "for new software",
         "Forrester TEI of Cortex IDP 2024"),
        (20, AMETHYST, "20%",
         "engineering productivity gain", "across the team",
         "Forrester TEI of Cortex IDP 2024"),
    ]

    for i, (raw_pct, color, big, lbl1, lbl2, src) in enumerate(metrics):
        r = base_r - i * gap
        # Background ring (Taupe outline)
        c.setStrokeColor(TAUPE)
        c.setLineWidth(ring_w)
        c.circle(cx, cy, r, stroke=1, fill=0)
        # Progress arc (jewel)
        pct = min(raw_pct, 100)
        extent = -(pct / 100.0) * 320
        c.setStrokeColor(color)
        c.setLineWidth(ring_w)
        p = c.beginPath()
        p.arc(cx - r, cy - r, cx + r, cy + r, 90 + 20, extent)
        c.drawPath(p, stroke=1, fill=0)

    # Caption below rings
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 13)
    c.drawCentredString(cx, cy - base_r - 40, "Each ring is a verified outcome")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(cx, cy - base_r - 60, "Higher arc = stronger gain on that dimension")

    # Right side: metric breakdown legend
    lx = 640
    ly0 = cy + 170
    line_h = 95

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 17)
    c.drawString(lx, ly0 + 40, "Outcomes that compound")

    for i, (raw_pct, color, big, lbl1, lbl2, src) in enumerate(metrics):
        y = ly0 - i * line_h
        # Color swatch
        c.setFillColor(color)
        c.circle(lx + 14, y - 14, 12, stroke=0, fill=1)
        # Big stat
        c.setFillColor(color)
        c.setFont('Poppins-Bold', 24)
        c.drawString(lx + 38, y - 8, big)
        # Label
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 12)
        c.drawString(lx + 120, y - 4, lbl1)
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins-Light', 10)
        c.drawString(lx + 120, y - 22, lbl2)
        c.setFont('Poppins-Light', 9)
        c.drawString(lx + 120, y - 38, src)

    # Footer
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 85, "Each model deployed pays into the same platform asset.")

    draw_footer(c, 7)


# ============================================================
# Slide 8 (NEW): Segmented wheel - Why custom SLMs win
# ============================================================
def slide_slm_why(c):
    draw_background(c)
    draw_top_accent(c, NAVY)

    draw_title(c, "Distill the Giants. Deploy the Specialists.")
    draw_subtitle(c, "Custom SLMs turn the platform into a compounding economic moat")

    # Segmented wheel — 6 sectors of business benefits
    cx, cy = W / 2, 555
    outer_r = 270
    inner_r = 95

    sectors = [
        # (title, stat_line, fill_color)
        ("Inference cost",  "up to 30x cheaper", EMERALD),
        ("Latency",         "10-50 ms response", SAPPHIRE),
        ("Data privacy",    "on-prem / air-gapped", BURGUNDY),
        ("Domain accuracy", "96% F1 on niche tasks", AMETHYST),
        ("Independence",    "no vendor lock-in", UMBER),
        ("Compounding",     "improves with telemetry", MOSS),
    ]

    n = len(sectors)
    angle_per = 360 / n
    # Start at top (12 o'clock) and go clockwise
    start_ang_top = 90  # 12 o'clock in ReportLab degrees (CCW from 3 o'clock)

    for i, (title, stat, fill) in enumerate(sectors):
        # Sector start angle (clockwise progression)
        seg_start = start_ang_top - i * angle_per
        extent = -angle_per  # negative = clockwise sweep

        # Draw wedge
        c.setFillColor(fill)
        c.setStrokeColor(IVORY)
        c.setLineWidth(3)
        c.wedge(cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
                seg_start, extent, stroke=1, fill=1)

        # Label position — midpoint of sector at ~70% of outer radius
        mid_ang_deg = seg_start + extent / 2
        mid_ang_rad = math.radians(mid_ang_deg)
        label_r = (inner_r + outer_r) / 2 + 5  # midway between inner and outer ring
        lx = cx + label_r * math.cos(mid_ang_rad)
        ly = cy + label_r * math.sin(mid_ang_rad)

        # Title (bold) above stat
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 15)
        c.drawCentredString(lx, ly + 8, title)
        c.setFont('Poppins-Light', 12)
        c.drawCentredString(lx, ly - 10, stat)

    # Cut out center to make donut
    c.setFillColor(IVORY)
    c.setStrokeColor(NAVY)
    c.setLineWidth(2)
    c.circle(cx, cy, inner_r, stroke=1, fill=1)

    # Central label
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(cx, cy + 10, "Custom")
    c.drawCentredString(cx, cy - 18, "SLMs")

    # Bottom caption
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 17)
    c.drawCentredString(W / 2, 215, "85-95% of frontier performance at 1-3% of inference cost.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(W / 2, 192, "Specialised models beat zero-shot GPT-4 on most classification tasks.")
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 170, "TensorZero 2025; Snorkel AI; n1n.ai SLM-vs-LLM analysis 2026")

    # Bottom line
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 14)
    c.drawCentredString(W / 2, 90, "The model is the workload. The platform is the moat.")

    draw_footer(c, 8)


# ============================================================
# Slide 9 (NEW): Circular flow - The distillation pipeline + hardware
# ============================================================
def slide_slm_pipeline(c):
    draw_background(c)
    draw_top_accent(c, NAVY)

    draw_title(c, "From Open Source to Production SLM", size=32)
    draw_subtitle(c, "Five steps, ballpark costs, commodity hardware")

    # ---- Left side: circular flow of 5 process nodes ----
    cx, cy = 340, 555
    orbit_r = 195
    node_r = 75

    # Light orbit ring in Taupe — shows the cycle
    c.setStrokeColor(TAUPE)
    c.setLineWidth(2)
    c.circle(cx, cy, orbit_r, stroke=1, fill=0)

    steps = [
        # (number, title, sub_line, color)
        ("1", "Select base",   "Llama / Gemma / Qwen", SAPPHIRE),
        ("2", "Curate corpus", "teacher distillation", EMERALD),
        ("3", "Fine-tune",     "LoRA + prune",         BURGUNDY),
        ("4", "Quantize",      "4-bit / 8-bit",        AMETHYST),
        ("5", "Serve",         "KServe + monitor",     UMBER),
    ]

    n = len(steps)
    for i, (num, title, sub, fill) in enumerate(steps):
        # Start at top, go clockwise
        ang_deg = 90 - i * (360 / n)
        ang_rad = math.radians(ang_deg)
        nx = cx + orbit_r * math.cos(ang_rad)
        ny = cy + orbit_r * math.sin(ang_rad)

        # Node circle
        c.setFillColor(fill)
        c.setStrokeColor(IVORY)
        c.setLineWidth(2)
        c.circle(nx, ny, node_r, stroke=1, fill=1)

        # Number (big, top of node)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 20)
        c.drawCentredString(nx, ny + 22, num)
        # Title (medium, middle)
        c.setFont('Poppins-Bold', 12)
        c.drawCentredString(nx, ny + 2, title)
        # Sub (small, below title)
        c.setFont('Poppins-Light', 9)
        c.drawCentredString(nx, ny - 18, sub)

    # Center hub label
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(cx, cy + 14, "Distillation")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(cx, cy - 6, "pipeline")
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Bold', 13)
    c.drawCentredString(cx, cy - 28, "$500-$5K")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 10)
    c.drawCentredString(cx, cy - 42, "per fine-tune")

    # ---- Right side: hardware tiers panel ----
    panel_x = 700
    panel_top = 760

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 18)
    c.drawString(panel_x, panel_top, "Inference hardware")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 12)
    c.drawString(panel_x, panel_top - 22, "Sized by model parameter count")

    # Four hardware tiers as bullet-dot rows
    tiers = [
        # (color, model_label, hardware_label, vram_label)
        (EMERALD,  "7B SLM",      "RTX 4090  (~$1.6K)",     "16-24 GB VRAM"),
        (SAPPHIRE, "13B SLM",     "RTX 5090  (~$2K)",       "24-32 GB, 4-bit"),
        (AMETHYST, "30B SLM",     "RTX 5090 / dual GPU",    "32-48 GB, 4-bit"),
        (BURGUNDY, "70B+ SLM",    "2x A100 80GB  (~$30K)",  "or H100 / H200"),
    ]

    tier_y = panel_top - 70
    row_h = 80
    bullet_r = 14

    for i, (color, model, hw, vram) in enumerate(tiers):
        y = tier_y - i * row_h
        # Bullet circle
        c.setFillColor(color)
        c.setStrokeColor(IVORY)
        c.setLineWidth(2)
        c.circle(panel_x + bullet_r, y, bullet_r, stroke=1, fill=1)

        # Model label
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 14)
        c.drawString(panel_x + bullet_r * 2 + 14, y + 8, model)
        # Hardware
        c.setFont('Poppins-Medium', 12)
        c.drawString(panel_x + bullet_r * 2 + 14, y - 8, hw)
        # VRAM detail
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins-Light', 10)
        c.drawString(panel_x + bullet_r * 2 + 14, y - 24, vram)

    # Bottom caption — break-even
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(W / 2, 158, "Break-even vs API: ~2M tokens / day.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(W / 2, 135, "Payoff window: 3-6 months. Compliance-grade deployments shorter.")
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 113, "Dev.to SLM analysis 2026; SitePoint TCO 2026; Galileo training-cost benchmarks")

    # Anchor line
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 13)
    c.drawCentredString(W / 2, 88, "One distilled model per critical workflow. Each one improves the next.")

    draw_footer(c, 9)


# ============================================================
# Slide 10 (NEW): Stat callout rings - Agent business case
# ============================================================
def slide_agents_why(c):
    draw_background(c)
    draw_top_accent(c, NAVY)

    draw_title(c, "The Agent Wave Already Pays Back", size=32)
    draw_subtitle(c, "Why the platform thesis upgrades into autonomous workflows")

    # 6 stat callout rings in 2 rows of 3
    r = 78
    col_x = [195, 540, 885]
    row_y_top = 690
    row_y_bot = 405

    stats_top = [
        # (big_stat, desc_line_1, desc_line_2, source)
        ("40%",  "of enterprise apps",  "embed task-specific agents by end-2026", "Gartner, 2025"),
        ("5.8x", "ROI on AI investment", "within 14 months of production",       "McKinsey, 2025"),
        ("66%",  "of agent users",      "report measurable productivity gains",  "PwC AI Predictions, 2025"),
    ]
    stats_bot = [
        ("88%",   "of organizations",  "plan budget increases for agentic AI",  "PwC, 2025"),
        ("62%",   "of agent deployments", "expect ROI above 100%",              "PwC, 2025"),
        ("$450B", "agentic AI revenue", "by 2035 - up from 2% in 2025",         "Gartner forecast, 2025"),
    ]

    def draw_callout(cx, cy, big, l1, l2, source):
        # Navy ring
        c.setFillColor(NAVY)
        c.setStrokeColor(NAVY)
        c.circle(cx, cy, r, stroke=0, fill=1)
        # Big number in Mustard
        c.setFillColor(MUSTARD)
        c.setFont('Poppins-Bold', 38)
        c.drawCentredString(cx, cy - 12, big)
        # Descriptor lines in Navy below ring
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 12)
        c.drawCentredString(cx, cy - r - 18, l1)
        c.drawCentredString(cx, cy - r - 32, l2)
        # Source in Graphite
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins-Light', 10)
        c.drawCentredString(cx, cy - r - 48, source)

    for i, (big, l1, l2, src) in enumerate(stats_top):
        draw_callout(col_x[i], row_y_top, big, l1, l2, src)
    for i, (big, l1, l2, src) in enumerate(stats_bot):
        draw_callout(col_x[i], row_y_bot, big, l1, l2, src)

    # Bottom anchor line
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(W / 2, 230, "Agents convert platform capability into autonomous workflows.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(W / 2, 208, "Gartner predicts a 33-fold rise in agentic enterprise apps by 2028.")

    # Closing line
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Bold', 14)
    c.drawCentredString(W / 2, 165, "The IDP is the launch pad. Every agent ships on rails the platform already built.")

    draw_footer(c, 10)


# ============================================================
# Slide 11 (NEW): Hub-and-spoke - Agent runtime on the IDP
# ============================================================
def slide_agents_runtime(c):
    draw_background(c)
    draw_top_accent(c, NAVY)

    draw_title(c, "Agents Run on the Same Substrate", size=34)
    draw_subtitle(c, "No second stack. The IDP absorbs agentic AI as another workload.")

    # Hub-and-spoke
    cx, cy = W / 2, 560
    hub_r = 95
    spoke_r = 270
    node_r = 70

    # 6 spokes at 60-degree intervals, starting from top
    spokes = [
        # (angle_deg from 3 o'clock CCW, title, subtitle, color)
        (90,  "LangChain",   "CrewAI / AutoGen",   SAPPHIRE),   # top
        (30,  "MCP",         "tools and skills",   EMERALD),    # top-right
        (-30, "KServe",      "model serving",      AMETHYST),   # bottom-right
        (-90, "Evidently",   "agent observability", BURGUNDY),  # bottom
        (210, "Kubeflow",    "Argo workflows",     UMBER),      # bottom-left
        (150, "kagent / A2A","cloud-native runtime", MOSS),     # top-left
    ]

    # Draw connector lines first (under nodes)
    c.setStrokeColor(TAUPE)
    c.setLineWidth(2)
    for ang_deg, _, _, _ in spokes:
        ang_rad = math.radians(ang_deg)
        x1 = cx + hub_r * math.cos(ang_rad)
        y1 = cy + hub_r * math.sin(ang_rad)
        x2 = cx + (spoke_r - node_r) * math.cos(ang_rad)
        y2 = cy + (spoke_r - node_r) * math.sin(ang_rad)
        c.line(x1, y1, x2, y2)

    # Central hub
    c.setFillColor(NAVY)
    c.setStrokeColor(OCHRE)
    c.setLineWidth(3)
    c.circle(cx, cy, hub_r, stroke=1, fill=1)
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 17)
    c.drawCentredString(cx, cy + 14, "Agent")
    c.drawCentredString(cx, cy - 6, "Runtime")
    c.setFillColor(OCHRE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(cx, cy - 28, "on K8s + Kubeflow")

    # Spoke nodes
    for ang_deg, title, sub, fill in spokes:
        ang_rad = math.radians(ang_deg)
        nx = cx + spoke_r * math.cos(ang_rad)
        ny = cy + spoke_r * math.sin(ang_rad)
        # Node circle
        c.setFillColor(fill)
        c.setStrokeColor(IVORY)
        c.setLineWidth(2)
        c.circle(nx, ny, node_r, stroke=1, fill=1)
        # Title (bold) inside, top half
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 13)
        c.drawCentredString(nx, ny + 6, title)
        # Subtitle inside, bottom half
        c.setFont('Poppins-Light', 10)
        c.drawCentredString(nx, ny - 12, sub)

    # Bottom anchor: business benefit line
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 15)
    c.drawCentredString(W / 2, 195, "Every chapter of the agent playbook lands on infrastructure you already operate.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(W / 2, 173, "Same Kubernetes. Same registry. Same observability. Same governance.")
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 152, "Anthropic, OpenAI, and LangChain all run their agent infrastructure on Kubernetes.")
    c.setFont('Poppins-Light', 10)
    c.drawCentredString(W / 2, 132, "Mirantis K8s agent architecture 2026; kagent open-source agent runtime")

    # Closing strategic line
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Bold', 14)
    c.drawCentredString(W / 2, 92, "Zero second-stack tax. Agents inherit the moat.")

    draw_footer(c, 11)


# ============================================================
# Slide 12: Target/bullseye - three platform decisions
# ============================================================
def slide_8(c):
    draw_background(c)
    draw_top_accent(c, NAVY)

    draw_title(c, "Three Platform Decisions for CAIOs")
    draw_subtitle(c, "These choices determine the return on every downstream AI investment")

    cx, cy = W / 2 - 200, 480
    # Three concentric rings, center = highest priority
    rings = [
        # (radius, color, title, line)
        (250, BURGUNDY, "Component absorption rate", "Each project contributes one durable component"),
        (175, SAPPHIRE, "Abstraction boundary", "Platform owns infra; product owns models"),
        (100, EMERALD, "Treat infrastructure as a product", "Dedicated team, roadmap, internal customers"),
    ]

    for r, color, title, line in rings:
        c.setFillColor(color)
        c.setStrokeColor(IVORY)
        c.setLineWidth(4)
        c.circle(cx, cy, r, stroke=1, fill=1)

    # Center label
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 15)
    c.drawCentredString(cx, cy + 8, "Decision 1")
    c.setFont('Poppins-Medium', 11)
    c.drawCentredString(cx, cy - 10, "Product treatment")
    c.drawCentredString(cx, cy - 26, "of the platform")

    # Ring labels at side
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 13)
    # Decision 2 label - in the middle ring band, above center
    c.drawCentredString(cx, cy + 130, "Decision 2")
    c.setFont('Poppins-Medium', 11)
    c.drawCentredString(cx, cy + 113, "Abstraction boundary")

    # Decision 3 label - in the outer ring band, above center
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 13)
    c.drawCentredString(cx, cy + 207, "Decision 3")
    c.setFont('Poppins-Medium', 11)
    c.drawCentredString(cx, cy + 190, "Component absorption rate")

    # Right side: full description of each decision
    lx = W - 460
    ly0 = cy + 200
    line_h = 130

    items = [
        (EMERALD, "Decision 1",
         "Treat infrastructure as a product.",
         "Dedicated platform team, published roadmap,",
         "uptime commitments, internal customer interviews."),
        (SAPPHIRE, "Decision 2",
         "Place the abstraction boundary cleanly.",
         "Platform owns clusters, pipelines, registries.",
         "Product teams own models and business logic."),
        (BURGUNDY, "Decision 3",
         "Absorb new components into the platform.",
         "Each successful project contributes one",
         "durable rail that the next project reuses."),
    ]
    for i, (color, label, l1, l2, l3) in enumerate(items):
        y = ly0 - i * line_h
        c.setFillColor(color)
        c.circle(lx + 12, y - 12, 12, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 14)
        c.drawString(lx + 38, y - 6, label)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 12)
        c.drawString(lx + 38, y - 26, l1)
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins', 11)
        c.drawString(lx + 38, y - 44, l2)
        c.drawString(lx + 38, y - 60, l3)

    # Bottom caption
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 90, "Made deliberately, these three decisions place a program in the 5%. Made by accident, they place it in the 95%.")

    draw_footer(c, 12)


# ============================================================
# Slide 9: Closing - key takeaway + sources
# ============================================================
def slide_9(c):
    draw_background(c)
    draw_top_accent(c, NAVY)

    draw_title(c, "The Platform Compounds")

    # Single circle with key takeaway
    cx, cy = W / 2, 660
    r = 165
    c.setFillColor(NAVY)
    c.setStrokeColor(OCHRE)
    c.setLineWidth(4)
    c.circle(cx, cy, r, stroke=1, fill=1)

    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 24)
    c.drawCentredString(cx, cy + 42, "Models change.")
    c.drawCentredString(cx, cy + 14, "Foundations reset.")
    c.setFillColor(OCHRE)
    c.setFont('Poppins-Bold', 26)
    c.drawCentredString(cx, cy - 18, "The platform")
    c.drawCentredString(cx, cy - 48, "compounds.")

    # CTA
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 18)
    c.drawCentredString(W / 2, 440, "Read the full article on Substack")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(W / 2, 418, "Link in the post — strategic detail and the AWS-specific case for platform-led")

    # Sources block
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 13)
    c.drawCentredString(W / 2, 360, "Sources")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 10)
    src_lines = [
        "MIT NANDA, State of AI in Business 2025 (July 2025)",
        "RAND Corporation 2025; Gartner AI Production 2025",
        "DevOps Benchmarking Study 2023; EITT Platform Engineering Report 2026",
        "Forrester TEI of Cortex IDP, March 2024",
        "AWS EKS best-practices 2025; AWS Controllers for Kubernetes",
        "TensorZero Distillation Benchmarks 2025; Stanford AI Index 2025",
        "Gartner Agentic AI Forecast 2025; McKinsey AI ROI Study 2025; PwC 2025",
        "Deloitte State of AI in Enterprise 2026; Mirantis K8s Agent Arch 2026",
    ]
    for i, line in enumerate(src_lines):
        c.drawCentredString(W / 2, 340 - i * 16, line)

    draw_footer(c, 13)


# ============================================================
# Main render
# ============================================================
def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    slides = [
        slide_1, slide_2, slide_3, slide_4, slide_5, slide_6, slide_7,
        slide_slm_why,         # slide 8: Why custom SLMs
        slide_slm_pipeline,    # slide 9: Distillation pipeline + hardware
        slide_agents_why,      # NEW slide 10: Agent business case
        slide_agents_runtime,  # NEW slide 11: Agent runtime architecture
        slide_8,               # now slide 12: three platform decisions
        slide_9,               # now slide 13: closing
    ]
    for fn in slides:
        fn(c)
        c.showPage()
    c.save()
    print(f"Rendered: {OUTPUT_PDF}")


if __name__ == '__main__':
    main()
