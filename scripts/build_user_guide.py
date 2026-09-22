"""Build the visual user guide from the checked-in sample screenshots.

Run: python -m pip install -r scripts/requirements-docs.txt
     python scripts/build_user_guide.py
"""
from pathlib import Path
from html import escape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "user-guide-assets"
OUTPUT = ROOT / "output" / "pdf" / "Verdant-User-Guide.pdf"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
FONT, BOLD = "Helvetica", "Helvetica-Bold"
font_dir = Path("C:/Windows/Fonts")
if (font_dir / "arial.ttf").exists():
    pdfmetrics.registerFont(TTFont("Guide", str(font_dir / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("GuideBold", str(font_dir / "arialbd.ttf")))
    pdfmetrics.registerFontFamily("Guide", normal="Guide", bold="GuideBold", italic="Guide", boldItalic="GuideBold")
    FONT, BOLD = "Guide", "GuideBold"

W, H = 1024, 720
GREEN, INK, MUTED = "#174D38", "#183329", "#52675D"
BG, BORDER, LIME, LIGHT = "#F5F7F2", "#D8E3DA", "#DDF1B6", "#EAF2E8"
C = canvas.Canvas(str(OUTPUT), pagesize=(W, H))
C.setTitle("Verdant - A visual guide to your document workspace")
C.setAuthor("Verdant Document Hub")
C.setSubject("Project documents, roles, reviews, research, sharing, and local setup")
page_number = 0

def rect(x, top, width, height, fill, stroke=None, radius=12):
    C.setFillColor(HexColor(fill))
    C.setStrokeColor(HexColor(stroke or fill))
    C.roundRect(x, H-top-height, width, height, radius, fill=1, stroke=bool(stroke))

def text(value, x, top, width, size=14, color=INK, bold=False, leading=None):
    style = ParagraphStyle("t", fontName=BOLD if bold else FONT, fontSize=size,
                           leading=leading or size*1.4, textColor=HexColor(color))
    paragraph = Paragraph(value, style)
    _, height = paragraph.wrap(width, H)
    if top + height > 662:
        raise ValueError(f"Text exceeds content area: {value[:65]} at {top}+{height}")
    paragraph.drawOn(C, x, H-top-height)
    return height

def line(x1, top1, x2, top2, color=BORDER, width=1):
    C.setStrokeColor(HexColor(color)); C.setLineWidth(width)
    C.line(x1, H-top1, x2, H-top2)

def arrow(x1, top1, x2, top2, color=GREEN):
    import math
    line(x1, top1, x2, top2, color, 2)
    angle = math.atan2(top2-top1, x2-x1)
    for delta in (-0.5, 0.5):
        line(x2, top2, x2-9*math.cos(angle+delta), top2-9*math.sin(angle+delta), color, 2)

def pill(label, x, top, width, fill=LIGHT, color=GREEN):
    rect(x, top, width, 27, fill, radius=13)
    text(label, x+12, top+5, width-20, 11, color, True)

def card(x, top, width, height, title, body, fill="#FFFFFF", title_size=18):
    rect(x, top, width, height, fill, BORDER)
    th = text(title, x+20, top+19, width-40, title_size, GREEN, True)
    text(body, x+20, top+29+th, width-40, 13)

def base(section, title, subtitle):
    global page_number
    page_number += 1
    C.setFillColor(HexColor(BG)); C.rect(0, 0, W, H, fill=1, stroke=0)
    rect(40, 27, 26, 26, GREEN, radius=7)
    line(47, 46, 59, 34, LIME, 2)
    text("VERDANT", 77, 29, 160, 15, GREEN, True)
    text(section.upper(), 730, 31, 254, 10, MUTED)
    text(title, 40, 83, 944, 31, INK, True)
    text(subtitle, 40, 130, 936, 13, MUTED)
    line(40, 676, 984, 676)
    C.setFont(FONT, 9); C.setFillColor(HexColor(MUTED))
    C.drawString(40, 24, "VERDANT  /  USER GUIDE  /  September 2026  /  Sample data shown")
    C.drawRightString(984, 24, f"{page_number:02d} / 08")

def screenshot(name, x, top, width, height):
    rect(x-1, top-1, width+2, height+2, "#FFFFFF", BORDER, 5)
    C.drawImage(str(ASSETS/name), x, H-top-height, width=width, height=height,
                preserveAspectRatio=True, anchor="c", mask="auto")

def step(number, title, body, x, top, width=278):
    rect(x, top, 30, 30, GREEN, radius=15)
    text(str(number), x+10, top+5, 22, 13, "#FFFFFF", True)
    height=text(title, x+43, top, width-43, 17, INK, True)
    return text(body, x+43, top+height+9, width-43, 13, MUTED)

# 01
base("Start here", "Company knowledge, in one place.",
     "Find documents, understand their status, and know who is responsible for the next step.")
pill("TWO CONNECTED AREAS", 40, 185, 191)
card(40, 231, 456, 226, "Project documents",
     "Required files for a specific project.<br/><br/>The owner defines stages and document requirements, "
     "assigns people, and controls access. Uploads move through a review workflow.")
card(516, 231, 468, 226, "Research library",
     "A shared reference library for the company.<br/><br/>Employees choose or create classifications, "
     "upload files, and browse knowledge. A reference can be linked to a project without requiring a project review.")
rect(40, 484, 944, 143, GREEN)
text("Which area should I use?", 64, 502, 880, 21, "#FFFFFF", True)
text("<b>A required technical drawing for Project X?</b> Use its project document requirement.<br/>"
     "<b>A general study about a material?</b> Upload it to the research library.<br/>"
     "<b>Useful in both places?</b> Keep the research reference and link it to the project.",
     64, 543, 866, 14, "#FFFFFF")
C.showPage()

# 02
base("Navigate", "Your project workspace",
     "The project screen brings required documents, responsibilities, and progress together.")
screenshot("project-workspace.png", 40, 180, 648, 450)
step(1, "Choose the project", "Use the project selector. You see projects that your account can access.", 711, 184, 275)
step(2, "Read the overview", "Approved, awaiting action, and readiness summarize the required document statuses.", 711, 292, 275)
step(3, "Find the document", "Each stage lists its requirements, latest file version, responsible employee, and reviewer.", 711, 410, 275)
step(4, "Use its actions", "View opens the file. New version uploads a revision. Access is available to project owners.", 711, 540, 275)
C.showPage()

# 03
base("Owner setup", "Plan the documents before uploading files",
     "A requirement is a named place for one document and its versions. Stages organize when it is needed.")
labels=[
("01", "Create the project", "Choose New project, add a name and description, and select a lifecycle template."),
("02", "Set up the stages", "Start from template stages and use Add stage for the project's own lifecycle."),
("03", "Add the people", "Use Manage members to add employees and choose their project access level."),
("04", "Define requirements", "Use Add required document. Choose a stage, document type, responsible person, and reviewer.")]
for i, (number, title, body) in enumerate(labels):
    x=40+i*240
    card(x, 185, 224, 213, title, body, title_size=17)
    pill(number, x+16, 409, 48)
    if i < 3: arrow(x+226, 290, x+238, 290)
text("Different people, different responsibilities", 40, 468, 940, 23, INK, True)
for x, title, body in [
    (40, "Owner / administrator", "Sets up requirements, people, and document access."),
    (360, "Responsible employee", "Uploads the file, revises it, and submits it for review."),
    (680, "Assigned reviewer", "Checks the latest submission and approves or requests changes.")]:
    card(x, 513, 304, 128, title, body, title_size=16)
C.showPage()

# 04
base("Review flow", "One document. Multiple versions. One reviewer.",
     "Uploading saves a draft. Submitting sends that version into its assigned review workflow.")
states=[
("Missing", "No file uploaded.", "#EEF1EC"),
("Draft", "Latest upload is ready\nto submit.", "#EDF0FF"),
("Submitted", "Waiting for the\nassigned reviewer.", "#FFF1DA"),
("Under review", "The reviewer is\nchecking the file.", "#FFF1DA"),
("Approved", "This version has\nbeen accepted.", "#DDF1B6")]
for i,(title,body,fill) in enumerate(states):
    x=40+i*191
    rect(x, 197, 178, 104, fill, BORDER)
    text(title, x+14, 214, 152, 17, INK, True)
    text(body.replace("\n","<br/>"), x+14, 248, 152, 12)
    if i < 4: arrow(x+180, 248, x+189, 248)
text("Upload", 144, 172, 100, 10, MUTED)
text("Submit", 337, 172, 100, 10, MUTED)
rect(385, 375, 229, 112, "#FFFFFF", BORDER)
text("Upload the revised file", 403, 391, 195, 17, GREEN, True)
text("New version returns to Draft.<br/>Submit it again for review.", 403, 428, 195, 12)
rect(653, 375, 258, 112, "#FFF0E5", BORDER)
text("Changes requested", 671, 391, 222, 17, "#8C4728", True)
text("The responsible employee<br/>updates the document.", 671, 428, 222, 12)
arrow(703, 305, 703, 367, "#99663B")
arrow(646, 431, 620, 431, "#99663B")
line(499, 374, 499, 338, GREEN, 2)
line(499, 338, 315, 338, GREEN, 2)
arrow(315, 338, 315, 306)
rect(40, 530, 944, 111, GREEN)
text("What to click", 61, 545, 900, 19, "#FFFFFF", True)
text("<b>Uploader:</b> New version, choose the file, then Submit.<br/>"
     "<b>Reviewer:</b> View, then Approve or Request changes. These buttons start the review and save the decision.<br/>"
     "The current screen saves preset review comments. It does not provide a custom feedback editor or email alerts.",
     61, 580, 900, 12, "#FFFFFF", leading=17)
C.showPage()

# 05
base("Research", "Build the company's shared reference library",
     "Research documents are available to signed-in employees and do not use the project review pipeline.")
screenshot("research-library.png", 40, 180, 648, 450)
step(1, "Classify the knowledge", "Choose Classification. A parent classification lets you build nested topics.", 711, 184, 275)
step(2, "Upload the reference", "Choose Upload file. Select a classification, add the title and description, and choose a file.", 711, 297, 275)
step(3, "Read and reuse it", "Use View to open the file. Link it to the currently selected project when relevant.", 711, 428, 275)
step(4, "Recognize useful work", "An administrator can Endorse a reference. This is a badge, not a publication gate.", 711, 541, 275)
C.showPage()

# 06
base("Access and traceability", "Share the right file. See what happened.",
     "Project membership, document-only access, and the activity log serve different needs.")
screenshot("visitor-inbox.png", 40, 181, 456, 317)
screenshot("activity-log.png", 528, 181, 456, 317)
card(40, 519, 456, 132, "Shared with me",
     "A visitor can open explicitly shared files without seeing the full project. Owners use the document's Access button to grant access.", title_size=19)
card(528, 519, 456, 132, "Project activity",
     "Open Activity to see recorded project actions, the employee involved, and the time. The log supports traceability of uploads and reviews.", title_size=19)
C.showPage()

# 07
base("Everyday use", "A practical routine for each role",
     "Keep the document name stable; use versions when the same document changes.")
card(40, 182, 456, 174, "As the responsible employee",
     "1. Open your project and find the requirement.<br/>"
     "2. Use New version to upload the file.<br/>"
     "3. Check the preview, then Submit.<br/>"
     "4. If changes are requested, revise and submit a new version.")
card(516, 182, 468, 174, "As the reviewer",
     "1. Open the project and locate a submitted document.<br/>"
     "2. Use View to examine the latest file.<br/>"
     "3. Choose Approve or Request changes.<br/>"
     "4. Check Activity to confirm the recorded decision.")
card(40, 376, 456, 147, "Find a document quickly",
     "Use the top search bar with a title, type, or description. Open the result's project or research area, then use View.")
card(516, 376, 468, 147, "Keep requirements clear",
     "Use separate requirements for different parts, such as 'Technical drawing - front assembly'. Revised files belong to that requirement's version history.")
rect(40, 545, 944, 106, LIGHT, BORDER)
text("Know this version", 60, 560, 900, 18, GREEN, True)
text("Search uses document metadata, not full document contents or semantic topics. PDF and common image files are best for in-browser viewing; Office files are not automatically converted. Historical versions are stored; side-by-side change comparison is not provided.", 60, 595, 900, 12)
C.showPage()

# 08
base("Get started locally", "Open Verdant on your own computer",
     "For a local demonstration, use the product branch and its Windows setup helpers. Docker is not required.")
step(1, "Prepare the computer", "Install Git, Python 3.12+, Node.js 22.13+, and PostgreSQL 16+. Start PostgreSQL and keep its administrator password available.", 40, 180, 576)
step(2, "Clone and install", "Clone the product-architecture-postgresql branch. In its folder, run the installer with -DemoData to create sample accounts in an empty database.", 40, 281, 576)
rect(84, 381, 520, 104, GREEN)
text("powershell -ExecutionPolicy Bypass<br/>"
     "-File .\\Install-Verdant.ps1 -DemoData<br/><br/>"
     "powershell -ExecutionPolicy Bypass<br/>"
     "-File .\\Start-Verdant.ps1", 100, 392, 490, 11, "#FFFFFF", leading=15)
step(3, "Sign in and explore", "Open http://localhost:3000. Start with the owner account, then try the responsible employee, reviewer, and visitor accounts.", 40, 517, 576)
rect(648, 182, 336, 357, "#FFFFFF", BORDER)
text("Sample accounts", 670, 203, 290, 23, GREEN, True)
text("All use password: <b>verdant-demo</b>", 670, 245, 284, 12)
for top, code, role in [(288,"EMP-1042","Owner / administrator"),(347,"EMP-1071","Responsible employee"),(406,"EMP-1088","Assigned reviewer"),(465,"VIS-1100","Document-only visitor")]:
    text(code, 670, top, 280, 17, INK, True)
    text(role, 670, top+25, 280, 12, MUTED)
text("Run each PowerShell command above as one line. Use Stop-Verdant.ps1 to stop the app, and Start-Verdant.ps1 after restarting Windows. Full installation steps: LOCAL-RUN.md in the repository.", 648, 560, 332, 11)
C.linkURL("https://github.com/zerolight59/verdant-document-hub/tree/product-architecture-postgresql", (40,28,430,50), relative=0)
C.showPage()
C.save()
print(OUTPUT)
