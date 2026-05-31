from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Circle, RoundedRect
from reportlab.graphics.shapes import Group
from reportlab.graphics import renderPDF
from reportlab.platypus import Image as RLImage
import io

# ─── Color Palette ────────────────────────────────────────────────────────────
NAVY      = colors.HexColor("#0D1B2A")
TEAL      = colors.HexColor("#1A6B72")
TEAL_LITE = colors.HexColor("#2E9EA8")
ACCENT    = colors.HexColor("#E8A838")
LIGHT_BG  = colors.HexColor("#F4F8FB")
CARD_BG   = colors.HexColor("#EAF4F6")
WHITE     = colors.white
GRAY      = colors.HexColor("#6B7C93")
GRAY_LITE = colors.HexColor("#D8E3EC")
TEXT      = colors.HexColor("#1C2B3A")
RED_SOFT  = colors.HexColor("#C0392B")
GREEN_SOFT= colors.HexColor("#27AE60")
ORANGE    = colors.HexColor("#E67E22")

PAGE_W, PAGE_H = A4

# ─── Styles ──────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def make_style(name, parent='Normal', **kw):
    s = ParagraphStyle(name, parent=styles[parent], **kw)
    return s

H1 = make_style('H1', fontSize=22, textColor=NAVY, spaceAfter=6, spaceBefore=18,
                fontName='Helvetica-Bold', leading=28)
H2 = make_style('H2', fontSize=15, textColor=TEAL, spaceAfter=4, spaceBefore=14,
                fontName='Helvetica-Bold', leading=20)
H3 = make_style('H3', fontSize=11, textColor=NAVY, spaceAfter=3, spaceBefore=8,
                fontName='Helvetica-Bold', leading=15)
BODY = make_style('BODY', fontSize=9.5, textColor=TEXT, spaceAfter=5, leading=15,
                  fontName='Helvetica', alignment=TA_JUSTIFY)
BODY_SML = make_style('BODY_SML', fontSize=8.5, textColor=TEXT, spaceAfter=3, leading=12,
                       fontName='Helvetica')
CAPTION = make_style('CAPTION', fontSize=8, textColor=GRAY, spaceAfter=8, leading=11,
                     fontName='Helvetica-Oblique', alignment=TA_CENTER)
CODE = make_style('CODE', fontSize=8, fontName='Courier', textColor=colors.HexColor("#1E3A5F"),
                  backColor=colors.HexColor("#EEF3F8"), spaceAfter=6, leading=12,
                  leftIndent=8, rightIndent=8)
LABEL = make_style('LABEL', fontSize=8, textColor=WHITE, fontName='Helvetica-Bold',
                   alignment=TA_CENTER, leading=10)
TOC_ITEM = make_style('TOC', fontSize=10, textColor=NAVY, spaceAfter=3, leading=14,
                      fontName='Helvetica')
BULLET = make_style('BULLET', fontSize=9.5, textColor=TEXT, spaceAfter=3, leading=14,
                    leftIndent=14, fontName='Helvetica', bulletIndent=4)

# ─── Helpers ──────────────────────────────────────────────────────────────────
def spacer(h=0.3): return Spacer(1, h*cm)
def hr(color=GRAY_LITE, thickness=0.5): return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=6)

def section_title(text):
    return [H1_underline(text), spacer(0.2)]

def H1_underline(text):
    return Paragraph(text, H1)

def badge(text, bg=TEAL, fg=WHITE, size=8):
    return Paragraph(f'<font color="white"><b>{text}</b></font>', 
                     make_style('badge_'+text, fontSize=size, backColor=bg,
                                textColor=fg, fontName='Helvetica-Bold', alignment=TA_CENTER,
                                leading=12, borderPadding=(2,6,2,6)))

# ─── Flowable: Colored Box ────────────────────────────────────────────────────
class ColorBox(Flowable):
    def __init__(self, w, h, fill, stroke=None, radius=4):
        self.bw, self.bh, self.fill = w, h, fill
        self.stroke = stroke
        self.radius = radius
    def wrap(self, *args): return self.bw, self.bh
    def draw(self):
        c = self.canv
        c.setFillColor(self.fill)
        if self.stroke:
            c.setStrokeColor(self.stroke)
            c.setLineWidth(0.5)
        else:
            c.setStrokeColor(self.fill)
        c.roundRect(0, 0, self.bw, self.bh, self.radius, fill=1, stroke=1 if self.stroke else 0)

# ─── Flowable: Info Card ──────────────────────────────────────────────────────
class InfoCard(Flowable):
    def __init__(self, title, items, width=None, title_color=TEAL, icon_char="■"):
        super().__init__()
        self.title = title
        self.items = items
        self.cw = width or 16*cm
        self.tc = title_color
        self.icon = icon_char

    def wrap(self, *args):
        self.h = 1.1*cm + len(self.items)*0.65*cm + 0.3*cm
        return self.cw, self.h

    def draw(self):
        c = self.canv
        # Card background
        c.setFillColor(CARD_BG)
        c.setStrokeColor(TEAL_LITE)
        c.setLineWidth(0.8)
        c.roundRect(0, 0, self.cw, self.h, 6, fill=1, stroke=1)
        # Title bar
        c.setFillColor(self.tc)
        c.roundRect(0, self.h - 1.0*cm, self.cw, 1.0*cm, 6, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 10)
        c.drawString(0.4*cm, self.h - 0.7*cm, self.title)
        # Items
        y = self.h - 1.4*cm
        for item in self.items:
            c.setFillColor(ACCENT)
            c.setFont('Helvetica-Bold', 9)
            c.drawString(0.4*cm, y, self.icon)
            c.setFillColor(TEXT)
            c.setFont('Helvetica', 8.5)
            c.drawString(0.9*cm, y, item)
            y -= 0.65*cm

# ─── Flowable: Architecture Diagram ──────────────────────────────────────────
class ArchDiagram(Flowable):
    def __init__(self, width=16*cm, height=9*cm):
        self.dw, self.dh = width, height

    def wrap(self, *args): return self.dw, self.dh

    def draw(self):
        c = self.canv
        w, h = self.dw, self.dh

        def box(x, y, bw, bh, label, sub=None, fill=TEAL, text_color=WHITE, radius=5):
            c.setFillColor(fill)
            c.setStrokeColor(NAVY)
            c.setLineWidth(0.6)
            c.roundRect(x, y, bw, bh, radius, fill=1, stroke=1)
            c.setFillColor(text_color)
            c.setFont('Helvetica-Bold', 8.5)
            ty = y + bh/2 + (3 if sub else 0)
            c.drawCentredString(x + bw/2, ty, label)
            if sub:
                c.setFont('Helvetica', 7)
                c.setFillColor(colors.HexColor("#cce9ed") if fill == TEAL else GRAY)
                c.drawCentredString(x + bw/2, y + bh/2 - 7, sub)

        def arrow(x1, y1, x2, y2):
            c.setStrokeColor(TEAL_LITE)
            c.setLineWidth(1.2)
            c.line(x1, y1, x2, y2)
            # arrowhead
            import math
            dx, dy = x2-x1, y2-y1
            length = math.sqrt(dx*dx + dy*dy)
            if length == 0: return
            ux, uy = dx/length, dy/length
            px, py = -uy, ux
            size = 5
            c.setFillColor(TEAL_LITE)
            c.setStrokeColor(TEAL_LITE)
            pts = [x2, y2, x2 - size*ux + size*0.5*px, y2 - size*uy + size*0.5*py,
                   x2 - size*ux - size*0.5*px, y2 - size*uy - size*0.5*py]
            p = c.beginPath()
            p.moveTo(pts[0], pts[1])
            p.lineTo(pts[2], pts[3])
            p.lineTo(pts[4], pts[5])
            p.close()
            c.drawPath(p, fill=1, stroke=0)

        bw, bh = 2.5*cm, 1.0*cm
        # Background
        c.setFillColor(LIGHT_BG)
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=0)

        # Title
        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 9)
        c.drawCentredString(w/2, h - 0.4*cm, "High-Level System Architecture")

        # Nodes
        nodes = {
            'user':    (0.3*cm,  h*0.55, "User", "Operator"),
            'ui':      (3.2*cm,  h*0.55, "Flet UI", "app.py"),
            'camera':  (6.1*cm,  h*0.72, "OpenCV", "Webcam"),
            'preview': (6.1*cm,  h*0.30, "Preview", "Base64 JPEG"),
            'model':   (9.0*cm,  h*0.55, "YOLO Model", "best.pt / CPU"),
            'excel':   (12.0*cm, h*0.72, "Excel", "acne_history.xlsx"),
            'images':  (12.0*cm, h*0.30, "Images", "Annotated JPGs"),
        }

        fills = {
            'user': ACCENT, 'ui': NAVY, 'camera': TEAL,
            'preview': colors.HexColor("#2E6DA4"), 'model': colors.HexColor("#7B3F9E"),
            'excel': GREEN_SOFT, 'images': colors.HexColor("#C0392B")
        }

        coords = {}
        for key, (x, y, label, sub) in nodes.items():
            box(x, y - bh/2, bw, bh, label, sub, fill=fills[key])
            coords[key] = (x + bw/2, y)

        def mid_r(key): return (coords[key][0] + bw/2 - bw/2 + bw, coords[key][1])
        def mid_l(key): return (coords[key][0] - bw/2, coords[key][1])
        def mid_t(key): return (coords[key][0], coords[key][1] + bh/2)
        def mid_b(key): return (coords[key][0], coords[key][1] - bh/2)

        arrow(*mid_r('user'), *mid_l('ui'))
        arrow(*mid_r('ui'),   *(coords['camera'][0] - bw/2, coords['camera'][1]))
        arrow(*mid_r('ui'),   *(coords['preview'][0] - bw/2, coords['preview'][1]))
        arrow(*mid_r('ui'),   *(coords['model'][0] - bw/2, coords['model'][1]))
        arrow(*(coords['camera'][0] + bw/2, coords['camera'][1]), *(coords['excel'][0] - bw/2, coords['excel'][1]))
        arrow(*(coords['model'][0] + bw/2, coords['model'][1]), *(coords['excel'][0] - bw/2, coords['excel'][1]))
        arrow(*(coords['model'][0] + bw/2, coords['model'][1]), *(coords['images'][0] - bw/2, coords['images'][1]))

        # Legend
        c.setFont('Helvetica', 7)
        lx, ly = 0.3*cm, 0.25*cm
        for color, label in [(ACCENT, "User"), (NAVY, "UI"), (TEAL, "Camera"), (colors.HexColor("#7B3F9E"), "Model"), (GREEN_SOFT, "Excel"), (colors.HexColor("#C0392B"), "Storage")]:
            c.setFillColor(color)
            c.rect(lx, ly, 0.25*cm, 0.25*cm, fill=1, stroke=0)
            c.setFillColor(GRAY)
            c.drawString(lx + 0.35*cm, ly + 0.04*cm, label)
            lx += 2.5*cm


# ─── Flowable: App Flow Diagram ───────────────────────────────────────────────
class AppFlowDiagram(Flowable):
    def __init__(self, width=16*cm, height=14*cm):
        self.dw, self.dh = width, height

    def wrap(self, *args): return self.dw, self.dh

    def draw(self):
        c = self.canv
        w, h = self.dw, self.dh

        c.setFillColor(LIGHT_BG)
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 9)
        c.drawCentredString(w/2, h - 0.4*cm, "Application Flow Diagram")

        bw, bh = 3.8*cm, 0.65*cm
        cx = w / 2

        steps = [
            ("Start app.py", NAVY),
            ("Build Flet UI", TEAL),
            ("Load Excel History", TEAL),
            ("Background Model Load", colors.HexColor("#7B3F9E")),
            ("Warmup YOLO (320×320)", colors.HexColor("#7B3F9E")),
            ("Status: System Ready", GREEN_SOFT),
            ("User: Open Camera", ACCENT),
            ("Stream Webcam Frames", TEAL),
            ("User: Capture & Analyze", ACCENT),
            ("Stop Camera / Release", TEAL),
            ("YOLO Predict on Frame", colors.HexColor("#7B3F9E")),
            ("Draw Bounding Boxes", colors.HexColor("#7B3F9E")),
            ("Append to Excel History", GREEN_SOFT),
            ("Show Result + Count", NAVY),
            ("Save Annotated Image", colors.HexColor("#C0392B")),
        ]

        step_h = (h - 1.0*cm) / (len(steps) + 1)
        y = h - 1.1*cm

        def draw_box(label, fill, y_pos):
            x = cx - bw/2
            c.setFillColor(fill)
            c.setStrokeColor(colors.HexColor("#0D1B2A"))
            c.setLineWidth(0.5)
            c.roundRect(x, y_pos, bw, bh, 4, fill=1, stroke=1)
            c.setFillColor(WHITE)
            c.setFont('Helvetica-Bold', 7.5)
            c.drawCentredString(cx, y_pos + bh*0.35, label)

        positions = []
        for i, (label, fill) in enumerate(steps):
            y = h - 1.1*cm - i * step_h
            draw_box(label, fill, y)
            positions.append((cx, y, bh))
            # Arrow
            if i < len(steps) - 1:
                ay = y - 0.05*cm
                c.setStrokeColor(TEAL_LITE)
                c.setLineWidth(1.0)
                c.line(cx, ay, cx, ay - (step_h - bh) + 0.05*cm)
                # arrowhead
                tip_y = ay - (step_h - bh) + 0.05*cm
                c.setFillColor(TEAL_LITE)
                p = c.beginPath()
                p.moveTo(cx, tip_y)
                p.lineTo(cx - 0.15*cm, tip_y + 0.25*cm)
                p.lineTo(cx + 0.15*cm, tip_y + 0.25*cm)
                p.close()
                c.drawPath(p, fill=1, stroke=0)

        # Side label for streaming loop
        c.setFillColor(ORANGE)
        c.setFont('Helvetica-Oblique', 7)
        lx = cx + bw/2 + 0.15*cm
        c.drawString(lx, h - 1.1*cm - 6*step_h + bh/2 - 0.1*cm, "↺ Loop 24 FPS")


# ─── Flowable: Model Loading Diagram ─────────────────────────────────────────
class ModelLoadDiagram(Flowable):
    def __init__(self, width=16*cm, height=8*cm):
        self.dw, self.dh = width, height

    def wrap(self, *args): return self.dw, self.dh

    def draw(self):
        c = self.canv
        w, h = self.dw, self.dh

        c.setFillColor(LIGHT_BG)
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 9)
        c.drawCentredString(w/2, h - 0.4*cm, "Model Loading Flow")

        bw, bh = 3.5*cm, 0.6*cm
        x_left = 1.2*cm
        x_mid  = w/2 - bw/2
        x_ok   = w - x_left - bw
        x_err  = x_left

        def box(x, y, label, fill, width=None):
            bww = width or bw
            c.setFillColor(fill)
            c.setStrokeColor(NAVY)
            c.setLineWidth(0.5)
            c.roundRect(x, y, bww, bh, 4, fill=1, stroke=1)
            c.setFillColor(WHITE)
            c.setFont('Helvetica-Bold', 7.5)
            c.drawCentredString(x + bww/2, y + bh*0.35, label)

        def arrow_v(x, y1, y2):
            c.setStrokeColor(TEAL_LITE)
            c.setLineWidth(1.0)
            c.line(x, y1, x, y2)
            c.setFillColor(TEAL_LITE)
            p = c.beginPath()
            p.moveTo(x, y2)
            p.lineTo(x - 0.12*cm, y2 + 0.2*cm)
            p.lineTo(x + 0.12*cm, y2 + 0.2*cm)
            p.close()
            c.drawPath(p, fill=1, stroke=0)

        def arrow_h(y, x1, x2, label=""):
            c.setStrokeColor(ORANGE)
            c.setLineWidth(0.8)
            c.setDash([2, 2])
            c.line(x1, y, x2, y)
            c.setDash()
            if label:
                c.setFillColor(ORANGE)
                c.setFont('Helvetica', 6.5)
                c.drawString(min(x1,x2) + 0.1*cm, y + 0.05*cm, label)

        cx = w/2
        steps = [
            ("Background Thread", NAVY),
            ("Import torch + YOLO", TEAL),
            ("Limit CPU Threads", TEAL),
            ("Load YOLO(best.pt)", colors.HexColor("#7B3F9E")),
            ("Move to CPU  •  Fuse  •  eval()", colors.HexColor("#7B3F9E")),
            ("Warmup Predict", TEAL),
            ("Status: System Ready", GREEN_SOFT),
        ]

        gap = (h - 1.0*cm) / (len(steps) + 0.5)
        y = h - 1.1*cm
        for i, (label, fill) in enumerate(steps):
            box(x_mid, y, label, fill, width=bw + 1.0*cm)
            if i < len(steps) - 1:
                arrow_v(cx, y, y - gap + bh)
            y -= gap

        # Decision diamond for best.pt
        dy = h - 1.1*cm - 2.5*gap
        pts_x = cx
        pts_y = dy + bh/2
        size = 0.35*cm
        # Draw diamond around step 3
        c.setFillColor(colors.HexColor("#F39C12"))
        c.setStrokeColor(NAVY)
        c.setLineWidth(0.5)
        p = c.beginPath()
        p.moveTo(pts_x - 5.2*cm, pts_y)
        p.lineTo(pts_x - 5.2*cm + size, pts_y + size)
        p.lineTo(pts_x - 5.2*cm + 2*size, pts_y)
        p.lineTo(pts_x - 5.2*cm + size, pts_y - size)
        p.close()
        c.drawPath(p, fill=1, stroke=1)
        c.setFillColor(TEXT)
        c.setFont('Helvetica-Bold', 6)
        c.drawCentredString(pts_x - 5.2*cm + size, pts_y - 0.05*cm, "?")

        c.setFillColor(GRAY)
        c.setFont('Helvetica', 7)
        c.drawString(0.3*cm, pts_y + 0.1*cm, "best.pt")
        c.drawString(0.3*cm, pts_y - 0.1*cm, "exists?")

        # Error path
        box(0.3*cm, pts_y - 1.2*cm, "Error State", RED_SOFT, width=2.8*cm)
        arrow_h(pts_y, pts_x - 4.8*cm, 0.3*cm + 2.8*cm, "No")


# ─── Flowable: Camera Pipeline ────────────────────────────────────────────────
class CamPipelineDiagram(Flowable):
    def __init__(self, width=16*cm, height=4.5*cm):
        self.dw, self.dh = width, height

    def wrap(self, *args): return self.dw, self.dh

    def draw(self):
        c = self.canv
        w, h = self.dw, self.dh
        c.setFillColor(LIGHT_BG)
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 9)
        c.drawCentredString(w/2, h - 0.4*cm, "Camera Feed Pipeline")

        stages = [
            ("Webcam", TEAL),
            ("VideoCapture", TEAL),
            ("BGR Frame", NAVY),
            ("frame_lock", GRAY),
            ("Resize", NAVY),
            ("JPEG Encode", colors.HexColor("#7B3F9E")),
            ("Base64", colors.HexColor("#7B3F9E")),
            ("Flet Image", ACCENT),
        ]
        bw = (w - 1.0*cm) / len(stages) - 0.2*cm
        bh = 0.75*cm
        y = h/2 - bh/2

        for i, (label, fill) in enumerate(stages):
            x = 0.5*cm + i * (bw + 0.2*cm)
            c.setFillColor(fill)
            c.setStrokeColor(NAVY)
            c.setLineWidth(0.5)
            c.roundRect(x, y, bw, bh, 3, fill=1, stroke=1)
            c.setFillColor(WHITE)
            c.setFont('Helvetica-Bold', 6.5)
            c.drawCentredString(x + bw/2, y + bh*0.32, label)
            if i < len(stages) - 1:
                ax = x + bw + 0.02*cm
                ay = y + bh/2
                c.setStrokeColor(TEAL_LITE)
                c.setLineWidth(0.8)
                c.line(ax, ay, ax + 0.14*cm, ay)
                c.setFillColor(TEAL_LITE)
                p = c.beginPath()
                p.moveTo(ax + 0.18*cm, ay)
                p.lineTo(ax + 0.05*cm, ay + 0.12*cm)
                p.lineTo(ax + 0.05*cm, ay - 0.12*cm)
                p.close()
                c.drawPath(p, fill=1, stroke=0)


# ─── Flowable: Sequence Diagram ───────────────────────────────────────────────
class SeqDiagram(Flowable):
    def __init__(self, width=16*cm, height=11*cm):
        self.dw, self.dh = width, height

    def wrap(self, *args): return self.dw, self.dh

    def draw(self):
        c = self.canv
        w, h = self.dw, self.dh
        c.setFillColor(LIGHT_BG)
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 9)
        c.drawCentredString(w/2, h - 0.4*cm, "Capture & Analysis Sequence Diagram")

        actors = ["User", "Flet UI", "Camera Thread", "YOLO CPU Model", "Excel History"]
        n = len(actors)
        bw_a = 2.5*cm
        bh_a = 0.6*cm
        xs = [0.5*cm + i * (w - 1.0*cm) / (n - 1) for i in range(n)]
        fills_a = [ACCENT, NAVY, TEAL, colors.HexColor("#7B3F9E"), GREEN_SOFT]

        top_y = h - 1.1*cm
        bottom_y = 0.5*cm

        # Actor boxes
        for i, (actor, x, fill) in enumerate(zip(actors, xs, fills_a)):
            c.setFillColor(fill)
            c.setStrokeColor(NAVY)
            c.setLineWidth(0.5)
            c.roundRect(x - bw_a/2, top_y, bw_a, bh_a, 3, fill=1, stroke=1)
            c.setFillColor(WHITE)
            c.setFont('Helvetica-Bold', 7)
            c.drawCentredString(x, top_y + bh_a*0.38, actor)
            # Lifeline
            c.setStrokeColor(GRAY_LITE)
            c.setLineWidth(0.5)
            c.setDash([3, 3])
            c.line(x, top_y, x, bottom_y)
            c.setDash()

        def msg(x1, x2, y, label, color=TEAL, dashed=False):
            c.setStrokeColor(color)
            c.setLineWidth(0.8)
            if dashed:
                c.setDash([3, 2])
            else:
                c.setDash()
            c.line(x1, y, x2, y)
            c.setDash()
            # arrowhead
            if x2 > x1:
                c.setFillColor(color)
                p = c.beginPath()
                p.moveTo(x2, y)
                p.lineTo(x2 - 0.2*cm, y + 0.1*cm)
                p.lineTo(x2 - 0.2*cm, y - 0.1*cm)
                p.close()
                c.drawPath(p, fill=1, stroke=0)
            else:
                c.setFillColor(color)
                p = c.beginPath()
                p.moveTo(x2, y)
                p.lineTo(x2 + 0.2*cm, y + 0.1*cm)
                p.lineTo(x2 + 0.2*cm, y - 0.1*cm)
                p.close()
                c.drawPath(p, fill=1, stroke=0)
            c.setFillColor(TEXT)
            c.setFont('Helvetica', 6.5)
            mx = (x1 + x2)/2
            c.drawCentredString(mx, y + 0.12*cm, label)

        messages = [
            (xs[0], xs[1], top_y - 0.9*cm,  "Click Open Camera", ACCENT),
            (xs[1], xs[2], top_y - 1.5*cm,  "Start preview thread", TEAL),
            (xs[2], xs[1], top_y - 2.1*cm,  "Update live frame preview", TEAL, True),
            (xs[0], xs[1], top_y - 2.7*cm,  "Click Capture & Analyze", ACCENT),
            (xs[1], xs[2], top_y - 3.3*cm,  "Stop preview / release camera", TEAL),
            (xs[1], xs[3], top_y - 3.9*cm,  "Predict latest frame", colors.HexColor("#7B3F9E")),
            (xs[3], xs[1], top_y - 4.5*cm,  "Boxes + annotated image", colors.HexColor("#7B3F9E"), True),
            (xs[1], xs[4], top_y - 5.1*cm,  "Append record", GREEN_SOFT),
            (xs[1], xs[0], top_y - 5.7*cm,  "Show acne count + annotated image", NAVY, True),
        ]

        for m in messages:
            msg(*m)


# ─── Page Header / Footer ─────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    # Header bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 1.5*cm, PAGE_W, 1.5*cm, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, PAGE_H - 1.55*cm, PAGE_W, 0.07*cm, fill=1, stroke=0)

    canvas.setFillColor(WHITE)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawString(1.5*cm, PAGE_H - 1.0*cm, "Acne Detection Kiosk")
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(GRAY_LITE)
    canvas.drawRightString(PAGE_W - 1.5*cm, PAGE_H - 1.0*cm, "Technical Project Documentation")

    # Footer
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, 1.1*cm, fill=1, stroke=0)
    canvas.setFillColor(GRAY_LITE)
    canvas.setFont('Helvetica', 7.5)
    canvas.drawString(1.5*cm, 0.4*cm, "CONFIDENTIAL · Acne Detection Kiosk · Technical Documentation")
    canvas.setFillColor(ACCENT)
    canvas.setFont('Helvetica-Bold', 8)
    canvas.drawRightString(PAGE_W - 1.5*cm, 0.4*cm, f"Page {doc.page}")
    canvas.restoreState()

def on_first_page(canvas, doc):
    canvas.saveState()
    # Cover background
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Accent stripe
    canvas.setFillColor(TEAL)
    canvas.rect(0, PAGE_H * 0.38, PAGE_W, PAGE_H * 0.30, fill=1, stroke=0)

    # Bottom accent
    canvas.setFillColor(ACCENT)
    canvas.rect(0, 0, PAGE_W, 1.2*cm, fill=1, stroke=0)

    # Decorative dots
    for i in range(6):
        for j in range(4):
            canvas.setFillColor(colors.HexColor("#1A3A5C"))
            canvas.circle(1.5*cm + i*2*cm, PAGE_H*0.92 - j*1.5*cm, 0.15*cm, fill=1, stroke=0)

    # Main title
    canvas.setFillColor(WHITE)
    canvas.setFont('Helvetica-Bold', 32)
    canvas.drawCentredString(PAGE_W/2, PAGE_H*0.60, "Acne Detection")
    canvas.setFont('Helvetica-Bold', 32)
    canvas.drawCentredString(PAGE_W/2, PAGE_H*0.54, "Kiosk")

    canvas.setFillColor(ACCENT)
    canvas.setFont('Helvetica', 14)
    canvas.drawCentredString(PAGE_W/2, PAGE_H*0.48, "Technical Project Documentation")

    # Divider
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1.5)
    canvas.line(PAGE_W*0.25, PAGE_H*0.445, PAGE_W*0.75, PAGE_H*0.445)

    # Subtitle block
    canvas.setFillColor(LIGHT_BG)
    canvas.setFont('Helvetica', 10)
    canvas.drawCentredString(PAGE_W/2, PAGE_H*0.415, "CPU-based YOLO Acne Detection · Flet Desktop UI · Excel Patient History")

    # Info block
    info = [
        ("Document Type", "Technical Architecture & API Reference"),
        ("Version",        "1.0"),
        ("Date",           "May 2026"),
        ("Framework",      "Flet + Ultralytics YOLO"),
        ("Platform",       "Windows Desktop"),
    ]
    by = PAGE_H * 0.30
    for label, value in info:
        canvas.setFillColor(TEAL_LITE)
        canvas.setFont('Helvetica-Bold', 8.5)
        canvas.drawString(PAGE_W*0.20, by, label + ":")
        canvas.setFillColor(WHITE)
        canvas.setFont('Helvetica', 8.5)
        canvas.drawString(PAGE_W*0.45, by, value)
        by -= 0.55*cm

    # Footer
    canvas.setFillColor(ACCENT)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawCentredString(PAGE_W/2, 0.45*cm, "CONFIDENTIAL · FOR INTERNAL USE ONLY")
    canvas.restoreState()


# ─── Build Story ─────────────────────────────────────────────────────────────
def build_pdf(path):
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2.0*cm, bottomMargin=1.8*cm,
        title="Acne Detection Kiosk – Technical Documentation",
        author="Project Team",
    )

    story = []

    # ── COVER (blank placeholder page) ──
    story.append(Spacer(1, PAGE_H))  # cover handled by on_first_page

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 1: EXECUTIVE SUMMARY
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("1.  Executive Summary"), hr(TEAL, 1.5), spacer(0.2)]

    story.append(Paragraph(
        "The <b>Acne Detection Kiosk</b> is a standalone desktop application designed to assist medical "
        "and cosmetic practitioners in objectively quantifying facial acne. The system captures a live "
        "webcam frame, runs a custom-trained <b>Ultralytics YOLO</b> deep-learning model entirely on "
        "<b>CPU</b>, counts detected acne instances, and persists results in an Excel-based patient "
        "history log — all without requiring cloud connectivity or specialist hardware.", BODY))

    story.append(Paragraph(
        "Two UI implementations exist in the repository: a modern <b>Flet</b> application "
        "(<code>app.py</code>) used in production, and a legacy <b>CustomTkinter</b> implementation "
        "(<code>main.py</code>) retained for reference. The core detection pipeline — model loading, "
        "inference, annotation, and history storage — is shared conceptually between both.", BODY))

    kpis = [
        ["Metric", "Value"],
        ["Inference Device", "CPU (no GPU required)"],
        ["Model Input Size", "320 × 320 px"],
        ["Live Preview Frame Rate", "≈ 24 FPS"],
        ["Confidence Threshold", "0.25"],
        ["History Format", "Excel (.xlsx)"],
        ["History Records Shown", "Last 15 visits"],
        ["Target Platform", "Windows Desktop"],
    ]
    t = Table(kpis, colWidths=[6*cm, 9.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('GRID',       (0,0), (-1,-1), 0.4, GRAY_LITE),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('ROUNDEDCORNERS', [4]),
    ]))
    story += [spacer(), t, spacer()]

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 2: TECHNOLOGY STACK
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("2.  Technology Stack"), hr(TEAL, 1.5), spacer(0.2)]

    story.append(Paragraph(
        "The application is built using open-source Python libraries, deliberately selected to keep "
        "dependencies minimal and deployment straightforward on Windows machines without GPU acceleration.", BODY))

    tech = [
        ["Area", "Library / Tool", "Version", "Purpose"],
        ["Desktop UI",       "Flet",                 "Latest", "Primary user interface"],
        ["Legacy UI",        "CustomTkinter",         "Latest", "Retained reference implementation"],
        ["Computer Vision",  "OpenCV (cv2)",          "4.x",    "Webcam capture, frame encoding"],
        ["Model Runtime",    "PyTorch",               "2.x",    "CPU inference backend"],
        ["Detection",        "Ultralytics YOLO",      "8.x",    "Loads and runs best.pt"],
        ["Numerics",         "NumPy",                 "Latest", "Warmup image and array ops"],
        ["History Storage",  "openpyxl",              "Latest", "Read/write acne_history.xlsx"],
        ["Packaging",        "PyInstaller",           "Latest", "Build Windows executable"],
    ]
    t2 = Table(tech, colWidths=[3.5*cm, 3.8*cm, 2.2*cm, 6.0*cm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), TEAL),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',   (0,0), (-1,-1), 8.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('GRID',       (0,0), (-1,-1), 0.4, GRAY_LITE),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story += [spacer(), t2, spacer()]

    story.append(Paragraph(
        "<b>Why openpyxl over pandas?</b>  The history log is a small, append-only workbook. "
        "openpyxl avoids the heavyweight pandas/numpy import chain, keeping cold-start time low "
        "on kiosk hardware — pandas is only justified when analytical operations are needed at scale.", BODY))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 3: PROJECT STRUCTURE
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("3.  Project Structure"), hr(TEAL, 1.5), spacer(0.2)]

    files = [
        ["File / Directory", "Role"],
        ["app.py",              "Primary Flet desktop application (production)"],
        ["main.py",             "Legacy CustomTkinter application (reference)"],
        ["best.pt",             "Trained YOLO acne detection model weights"],
        ["requirements.txt",    "pip dependency list"],
        ["Pipfile",             "Pipenv dependency list"],
        ["AcneKiosk.spec",      "PyInstaller build config (currently targets main.py)"],
        ["icon.ico",            "App icon for packaged builds"],
        ["acne_history.xlsx",   "Sample / seed patient history workbook"],
        ["LICENSE",             "Project license file"],
        ["README.md",           "Project documentation"],
    ]
    t3 = Table(files, colWidths=[4.5*cm, 11.0*cm])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME',   (0,1), (-1,-1), 'Courier'),
        ('FONTSIZE',   (0,0), (-1,-1), 8.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('GRID',       (0,0), (-1,-1), 0.4, GRAY_LITE),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story += [spacer(), t3, spacer()]

    story.append(Paragraph(
        "<b>Important:</b> The file <code>AcneKiosk.spec</code> currently references <code>main.py</code> "
        "as its entry point. Before distributing the Flet build, the spec must be updated to target "
        "<code>app.py</code> and include any Flet-specific data files.", BODY))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 4: SYSTEM ARCHITECTURE
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("4.  High-Level System Architecture"), hr(TEAL, 1.5), spacer(0.2)]

    story.append(Paragraph(
        "The diagram below illustrates the major subsystems and the direction of data flow at runtime. "
        "The Flet UI acts as the central orchestrator: it manages the camera thread, triggers model "
        "inference, and coordinates output to both the Excel history log and the annotated image store.", BODY))

    story += [spacer(0.3), ArchDiagram(width=15.5*cm, height=9*cm), spacer(0.1),
              Paragraph("Figure 1 – High-level system architecture and data-flow overview.", CAPTION), spacer(0.4)]

    story.append(Paragraph(
        "All user interactions flow through the Flet UI layer. The camera and model operate in "
        "background threads so the main UI thread remains responsive. The Excel and image-storage "
        "operations execute synchronously after detection completes, keeping the write order "
        "deterministic and race-condition-free.", BODY))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 5: APPLICATION FLOW
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("5.  Application Flow"), hr(TEAL, 1.5), spacer(0.2)]

    story.append(Paragraph(
        "From launch to result, the application progresses through four broad phases: "
        "<b>Initialization</b>, <b>Camera Preview</b>, <b>Capture &amp; Detection</b>, and "
        "<b>Result Storage</b>. The diagram below maps the complete step-by-step control flow.", BODY))

    story += [spacer(0.3), AppFlowDiagram(width=15.5*cm, height=14*cm), spacer(0.1),
              Paragraph("Figure 2 – Full application control flow from startup to result storage.", CAPTION), spacer(0.2)]

    story.append(Paragraph(
        "The live camera streaming loop runs at approximately <b>24 FPS</b> in a background Flet thread. "
        "Detection is deliberately <i>not</i> performed on every live frame — inference only occurs after "
        "the user clicks <b>Capture &amp; Analyze</b>, which stops the preview and runs the model "
        "on the most recently captured frame. This design keeps CPU load manageable on kiosk hardware.", BODY))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 6: MODEL LOADING
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("6.  Model Loading Flow"), hr(TEAL, 1.5), spacer(0.2)]

    story.append(Paragraph(
        "Model loading is deferred to a background thread to prevent the UI from blocking on startup. "
        "The sequence below details every step, including the error path when <code>best.pt</code> is missing.", BODY))

    story += [spacer(0.3), ModelLoadDiagram(width=15.5*cm, height=8*cm), spacer(0.1),
              Paragraph("Figure 3 – Model loading sequence with error-handling branch.", CAPTION), spacer(0.2)]

    load_steps = [
        ["Step", "Action", "Rationale"],
        ["1", "Import torch + YOLO",           "Deferred import keeps startup fast"],
        ["2", "Limit CPU thread count",        "Prevents CPU oversubscription on kiosk hardware"],
        ["3", "Check best.pt existence",       "Fail fast with clear status message if missing"],
        ["4", "YOLO(best.pt)",                 "Deserializes weights and builds PyTorch model graph"],
        ["5", "Move to CPU",                   "Explicit device assignment; no GPU assumed"],
        ["6", "model.fuse()",                  "Merges Conv+BN layers → faster forward pass"],
        ["7", "model.eval()",                  "Disables dropout/BatchNorm training behaviour"],
        ["8", "Warmup predict (320×320 blank)","Forces JIT compilation before first real frame"],
        ["9", "Status → System Ready",         "UI unlocks Capture button for operator"],
    ]
    t4 = Table(load_steps, colWidths=[1.0*cm, 4.5*cm, 10.0*cm])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), TEAL),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
        ('FONTNAME',   (0,1), (1,-1), 'Courier'),
        ('FONTSIZE',   (0,0), (-1,-1), 8.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('GRID',       (0,0), (-1,-1), 0.4, GRAY_LITE),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('ALIGN',      (0,0), (0,-1), 'CENTER'),
    ]))
    story += [spacer(), t4]

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 7: CAMERA PIPELINE
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("7.  Camera Feed Pipeline"), hr(TEAL, 1.5), spacer(0.2)]

    story.append(Paragraph(
        "OpenCV provides the low-level webcam interface. Each raw BGR frame is processed through "
        "a lightweight encoding chain before being displayed in the Flet UI as a base64-encoded "
        "JPEG string. The chain is designed for minimal latency on CPU-only machines.", BODY))

    story += [spacer(0.3), CamPipelineDiagram(width=15.5*cm, height=4.5*cm), spacer(0.1),
              Paragraph("Figure 4 – Camera feed pipeline: raw webcam frames to Flet Image widget.", CAPTION), spacer(0.3)]

    cam_detail = [
        ["Stage", "Details"],
        ["VideoCapture(0, CAP_DSHOW)", "Opens default webcam using DirectShow backend (Windows-optimised)"],
        ["MJPG encoding request",      "Requests MJPEG from camera hardware for higher throughput"],
        ["CAMERA_SIZE (960×540)",       "Requested capture resolution — camera may negotiate lower"],
        ["frame_lock (threading.Lock)", "Thread-safe storage of the latest frame for capture access"],
        ["Resize to PREVIEW_SIZE",      "Preserves aspect ratio; reduces encoding cost for preview"],
        ["JPEG encode (cv2)",           "Compresses frame to JPEG bytes; quality balances size/speed"],
        ["Base64 encode",               "Converts bytes to ASCII string consumable by Flet Image.src"],
        ["Flet Image.src update",       "Triggers Flet re-render; shows updated frame in UI"],
    ]
    t5 = Table(cam_detail, colWidths=[5.5*cm, 10.0*cm])
    t5.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
        ('FONTNAME',   (0,1), (0,-1), 'Courier'),
        ('FONTSIZE',   (0,0), (-1,-1), 8.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('GRID',       (0,0), (-1,-1), 0.4, GRAY_LITE),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story += [t5]

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 8: DETECTION ALGORITHM
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("8.  Detection Algorithm"), hr(TEAL, 1.5), spacer(0.2)]

    story.append(Paragraph(
        "<b>YOLO (You Only Look Once)</b> is a single-stage object detection architecture that predicts "
        "bounding boxes and class probabilities in a single forward pass through a convolutional neural "
        "network, without a separate region-proposal step. This makes it significantly faster than "
        "two-stage detectors (e.g. Faster R-CNN) at the cost of slightly lower accuracy on very small "
        "or densely overlapping objects.", BODY))

    story.append(Paragraph(
        "In this application the model is specialized for <b>acne spot detection</b>. Each detected "
        "spot produces a bounding box, a confidence score, and a class index. The app uses "
        "<code>len(results.boxes)</code> as the acne count and calls <code>results.plot()</code> "
        "to render annotated bounding boxes onto the captured frame.", BODY))

    story.append(Paragraph("<b>Inference configuration used at runtime:</b>", H3))
    code_txt = (
        "results = model.predict(\n"
        "    frame,\n"
        "    conf=0.25,       # minimum confidence to accept a detection\n"
        "    imgsz=320,       # inference image size (width = height)\n"
        "    device='cpu',    # CPU-only — no GPU required\n"
        "    verbose=False,   # suppress per-frame logging\n"
        ")[0]"
    )
    story.append(Paragraph(code_txt.replace('\n','<br/>').replace(' ', '&nbsp;'), CODE))
    story.append(spacer(0.2))

    yolo_steps = [
        ["Step", "Description"],
        ["1 – Capture",      "BGR frame read from webcam via OpenCV VideoCapture"],
        ["2 – Preprocess",   "Ultralytics internally letterboxes and normalises to 320×320"],
        ["3 – Forward pass", "Single CNN forward pass on CPU under torch.inference_mode()"],
        ["4 – Post-process", "NMS applied; bounding boxes, scores, and classes extracted"],
        ["5 – Count",        "len(results.boxes) is the acne count for the visit record"],
        ["6 – Annotate",     "results.plot() renders coloured boxes onto a copy of the frame"],
    ]
    t6 = Table(yolo_steps, colWidths=[3.5*cm, 12.0*cm])
    t6.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#7B3F9E")),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',   (0,0), (-1,-1), 8.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('GRID',       (0,0), (-1,-1), 0.4, GRAY_LITE),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story += [t6]

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 9: CAPTURE & ANALYSIS SEQUENCE
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("9.  Capture & Analysis Sequence"), hr(TEAL, 1.5), spacer(0.2)]

    story.append(Paragraph(
        "The sequence diagram below shows the actor-level message exchanges during a full "
        "capture-and-analysis session, from the operator clicking <b>Open Camera</b> through "
        "to the final result display.", BODY))

    story += [spacer(0.3), SeqDiagram(width=15.5*cm, height=11*cm), spacer(0.1),
              Paragraph("Figure 5 – UML-style sequence diagram for the capture and analysis workflow.", CAPTION), spacer(0.2)]

    story.append(Paragraph(
        "Key design decisions visible in this sequence: the camera thread is <i>stopped and the "
        "device released</i> before inference begins, ensuring no resource contention; and Excel "
        "history writing occurs immediately after inference so that a partial visit is never lost "
        "if the user closes the app before saving the annotated image.", BODY))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 10: HISTORY & OUTPUT STORAGE
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("10.  History & Output Storage"), hr(TEAL, 1.5), spacer(0.2)]

    story.append(Paragraph(
        "All persistent output is written to the current user's Desktop to keep the kiosk "
        "self-contained without requiring installer-time path configuration. Two artefacts are produced "
        "per session:", BODY))

    output_data = [
        ["Output", "Location", "Description"],
        ["History workbook", "~/Desktop/acne_history.xlsx", "Stores date, patient name, and acne count"],
        ["Annotated images", "~/Desktop/Acne_Annotated_Images/", "Saved .jpg detection results per session"],
    ]
    t7 = Table(output_data, colWidths=[3.5*cm, 6.5*cm, 5.5*cm])
    t7.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), TEAL),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',   (0,0), (-1,-1), 8.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('GRID',       (0,0), (-1,-1), 0.4, GRAY_LITE),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story += [spacer(), t7, spacer(0.3)]

    story.append(Paragraph("<b>Excel Row Schema:</b>", H3))
    excel_schema = [
        ["Column", "Example Value", "Source"],
        ["Date",    "2026-05-27 19:30", "Current system time at capture"],
        ["Patient", "Unknown (default) or entered name", "Patient name text field"],
        ["Count",   "12", "len(results.boxes) from YOLO output"],
    ]
    t8 = Table(excel_schema, colWidths=[2.5*cm, 6.0*cm, 7.0*cm])
    t8.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',   (0,0), (-1,-1), 8.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('GRID',       (0,0), (-1,-1), 0.4, GRAY_LITE),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story += [t8]

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 11: PERFORMANCE OPTIMIZATIONS
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("11.  CPU Performance Optimizations"), hr(TEAL, 1.5), spacer(0.2)]

    story.append(Paragraph(
        "Because the kiosk targets commodity Windows laptops without discrete GPUs, every "
        "component is tuned for CPU efficiency. The optimizations below collectively reduce "
        "inference latency, memory pressure, and background CPU overhead:", BODY))
    story.append(spacer(0.2))

    perf_items = [
        ("Model", [
            "device='cpu' explicit in every model.predict() call",
            "model.fuse() combines Conv+BatchNorm layers, reducing op count",
            "model.eval() disables dropout and training-only behaviour",
            "torch.inference_mode() context eliminates autograd overhead",
        ]),
        ("Threading", [
            "PyTorch internal thread count capped to avoid CPU oversubscription",
            "cv2.setNumThreads(1) limits OpenCV's internal parallel decode threads",
            "cv2.ocl.setUseOpenCL(False) disables OpenCL path for predictable latency",
        ]),
        ("Camera", [
            "MJPG encoding requested from camera hardware — reduces USB bandwidth",
            "Preview frames resized before encoding — smaller JPEG payload",
            "Frame interval set to 1/24 s — smooth but not wasteful",
        ]),
        ("Inference", [
            "imgsz=320 — smallest YOLO input that still detects acne adequately",
            "Detection runs only on demand (Capture click), not continuously",
            "openpyxl used instead of pandas — avoids importing the full pandas stack",
        ]),
    ]

    for cat, items in perf_items:
        story.append(InfoCard(cat, items, width=15.5*cm))
        story.append(spacer(0.25))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 12: KEY CONSTANTS
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("12.  Important Constants"), hr(TEAL, 1.5), spacer(0.2)]

    story.append(Paragraph(
        "The following constants are declared near the top of <code>app.py</code>. Adjusting them "
        "directly changes the trade-off between quality and CPU performance without code refactoring:", BODY))

    consts = [
        ["Constant", "Default", "Purpose", "Adjustment Guidance"],
        ["PREVIEW_SIZE",       "(850, 500)", "Maximum displayed preview dimensions (px)",
         "Increase for larger monitors; decreasing saves encoding cost"],
        ["CAMERA_SIZE",        "(960, 540)", "Requested webcam capture resolution",
         "Higher values can improve capture quality at higher CPU/bandwidth cost"],
        ["MODEL_IMAGE_SIZE",   "320",        "YOLO inference resolution (square)",
         "Increase to 640 for better small-object detection; slows CPU inference"],
        ["STREAM_INTERVAL_SEC","1 / 24",     "Preview frame interval in seconds",
         "Lower = smoother but more CPU; raise to 1/12 on underpowered machines"],
    ]
    t9 = Table(consts, colWidths=[4.0*cm, 2.5*cm, 4.5*cm, 4.5*cm])
    t9.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
        ('FONTNAME',   (0,1), (0,-1), 'Courier'),
        ('FONTNAME',   (0,1), (1,-1), 'Courier'),
        ('FONTSIZE',   (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('GRID',       (0,0), (-1,-1), 0.4, GRAY_LITE),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story += [spacer(), t9]

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 13: TROUBLESHOOTING
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("13.  Troubleshooting Guide"), hr(TEAL, 1.5), spacer(0.2)]

    issues = [
        ("Camera preview does not appear", [
            "Enable Windows Camera privacy permission (Settings → Privacy → Camera).",
            "Close all other applications using the webcam (Teams, Zoom, OBS, etc.).",
            "Verify OpenCV can read the camera: python -c \"import cv2; cap=cv2.VideoCapture(0, cv2.CAP_DSHOW); print(cap.isOpened())\"",
        ], RED_SOFT),
        ("Model does not load", [
            "Confirm best.pt exists in the project root directory.",
            "Confirm ultralytics, torch, and torchvision are installed: pip install -r requirements.txt",
            "Check the status label in the UI; an error message identifies the specific failure.",
        ], colors.HexColor("#C0392B")),
        ("Capture & Analyze does nothing", [
            "Wait for status label to display 'System Ready' before attempting capture.",
            "Click Open Camera first — the camera must be streaming before capture.",
            "Confirm the camera feed is active (live preview should be visible).",
        ], ORANGE),
        ("Slow CPU inference", [
            "Keep MODEL_IMAGE_SIZE = 320 — do not increase unless detection quality is unacceptable.",
            "Close CPU-heavy background applications (browser with many tabs, antivirus scans, etc.).",
            "Consider retraining with a smaller YOLO variant (e.g. YOLOv8n instead of YOLOv8s/m).",
        ], TEAL),
        ("Import errors on startup", [
            "Install all dependencies: pip install -r requirements.txt",
            "If using Pipenv: pipenv install && pipenv run python app.py",
            "Ensure Python 3.11 is active — other versions may have compatibility issues.",
        ], GRAY),
    ]

    for title, steps, color in issues:
        story.append(Paragraph(f'<b>{title}</b>', H3))
        for s in steps:
            story.append(Paragraph(f'• {s}', BULLET))
        story.append(spacer(0.2))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 14: FUTURE IMPROVEMENTS
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("14.  Future Improvements"), hr(TEAL, 1.5), spacer(0.2)]

    story.append(Paragraph(
        "The following enhancements have been identified for future development cycles, "
        "prioritised by user impact and implementation effort:", BODY))
    story.append(spacer(0.2))

    improvements = [
        ["Priority", "Feature", "Category", "Notes"],
        ["High",   "Camera selector for multi-camera systems",          "UX",         "Use cv2.VideoCapture index enumeration"],
        ["High",   "Update AcneKiosk.spec to target app.py",           "Build",      "Required before distributing Flet build"],
        ["Medium", "Confidence threshold slider in UI",                 "UX",         "Expose conf= parameter to operator"],
        ["Medium", "Export visit reports as PDF",                       "Output",     "Use reportlab or weasyprint"],
        ["Medium", "Optional continuous detection mode (low FPS cap)",  "Feature",    "Throttle to 2–4 FPS to manage CPU"],
        ["Medium", "Validation on patient name field",                  "Robustness", "Sanitise before using as filename"],
        ["Low",    "Model metadata documentation",                      "Docs",       "Training dataset, class labels, mAP metrics"],
        ["Low",    "Automated tests for Excel and frame helpers",       "Quality",    "pytest with mocked cv2 and openpyxl"],
    ]
    t10 = Table(improvements, colWidths=[1.8*cm, 5.5*cm, 2.5*cm, 5.7*cm])

    def pri_color(val):
        return {
            "High": colors.HexColor("#C0392B"),
            "Medium": ORANGE,
            "Low": GREEN_SOFT,
        }.get(val, GRAY)

    t10_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), TEAL),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',   (0,0), (-1,-1), 8.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('GRID',       (0,0), (-1,-1), 0.4, GRAY_LITE),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('ALIGN',      (0,0), (0,-1), 'CENTER'),
    ])
    for i, row in enumerate(improvements[1:], start=1):
        color = pri_color(row[0])
        t10_style.add('TEXTCOLOR', (0,i), (0,i), color)
        t10_style.add('FONTNAME',  (0,i), (0,i), 'Helvetica-Bold')
    t10.setStyle(t10_style)
    story += [t10]

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 15: PACKAGING & DEPLOYMENT
    # ─────────────────────────────────────────────────────────────────────────
    story += [PageBreak(), *section_title("15.  Packaging & Deployment"), hr(TEAL, 1.5), spacer(0.2)]

    story.append(Paragraph(
        "The project includes a <code>AcneKiosk.spec</code> PyInstaller specification for building "
        "a standalone Windows executable. The model file <code>best.pt</code> is already listed in "
        "the spec's data files, ensuring it is bundled into the distribution.", BODY))

    story.append(Paragraph("<b>Current spec entry point issue:</b>", H3))
    story.append(Paragraph(
        "The spec currently references <code>main.py</code> (CustomTkinter). Before releasing the "
        "Flet build, update the Analysis block:", BODY))

    code2 = (
        "# AcneKiosk.spec — update this line:\n"
        "a = Analysis(\n"
        "    ['app.py'],     # ← was 'main.py'\n"
        "    ...\n"
        ")"
    )
    story.append(Paragraph(code2.replace('\n','<br/>').replace(' ', '&nbsp;'), CODE))
    story.append(spacer(0.2))

    story.append(Paragraph("<b>Runtime Requirements Summary:</b>", H3))
    runtime = [
        ["Requirement", "Detail"],
        ["Python version",  "3.11 recommended (other 3.x may work)"],
        ["Operating system","Windows (webcam uses CAP_DSHOW; Desktop path is Windows-style)"],
        ["GPU",             "Not required — all inference runs on CPU"],
        ["Model file",      "best.pt must be present in project root or bundled by PyInstaller"],
        ["Camera",          "Default webcam (index 0); Windows camera permission must be enabled"],
        ["Disk (output)",   "Write access to current user's Desktop"],
    ]
    t11 = Table(runtime, colWidths=[4.0*cm, 11.5*cm])
    t11.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',   (0,0), (-1,-1), 8.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('GRID',       (0,0), (-1,-1), 0.4, GRAY_LITE),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story += [t11]

    # ─────────────────────────────────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_page)
    print("Done:", path)


if __name__ == "__main__":
    build_pdf("Acne_Detection_Kiosk_Documentation.pdf")