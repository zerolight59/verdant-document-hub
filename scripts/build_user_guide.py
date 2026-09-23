"""Build the visual user guide from real, checked-in application screenshots.
Install scripts/requirements-docs.txt, then run python scripts/build_user_guide.py.
Refresh screenshots with frontend/tests/capture-guide.mjs against a demo installation.
"""
from html import escape
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "user-guide-assets"
OUTPUT = ROOT / "output" / "pdf" / "Verdant-User-Guide.pdf"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
W, H = 1200, 850
FONT, BOLD = "Helvetica", "Helvetica-Bold"
fonts = Path("C:/Windows/Fonts")
if (fonts / "arial.ttf").exists():
    for name, filename in (("Guide", "arial.ttf"), ("GuideBold", "arialbd.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))
    pdfmetrics.registerFontFamily("Guide", normal="Guide", bold="GuideBold",
                                 italic="Guide", boldItalic="GuideBold")
    FONT, BOLD = "Guide", "GuideBold"
INK, GREEN, MUTED, BG, LINE = "#203C2E", "#246249", "#63776A", "#F5F8F4", "#DDE7DE"
PAGES = 20
C = canvas.Canvas(str(OUTPUT), pagesize=(W, H))
C.setTitle("Verdant - Visual User Guide")
C.setAuthor("Verdant Document Hub")
C.setSubject("Page-by-page actions, roles, document viewing, review workflow and demo walkthrough")
page_number = 0


def box(x, y, width, height, fill="#FFFFFF", border=LINE, radius=10):
    C.setFillColor(HexColor(fill))
    C.setStrokeColor(HexColor(border))
    C.roundRect(x, H-y-height, width, height, radius, fill=1, stroke=1)


def text(value, x, y, width, size=14, color=INK, bold=False):
    style = ParagraphStyle("guide", fontName=BOLD if bold else FONT, fontSize=size,
                           leading=size*1.4, textColor=HexColor(color))
    paragraph = Paragraph(value, style)
    _, height = paragraph.wrap(width, H)
    if y+height > 790:
        raise ValueError(f"Text outside content area on page {page_number}: {value[:60]}")
    paragraph.drawOn(C, x, H-y-height)
    return height


def page(section, title, subtitle):
    global page_number
    page_number += 1
    C.setFillColor(HexColor(BG))
    C.rect(0, 0, W, H, fill=1, stroke=0)
    text("verdant.", 36, 25, 190, 24, GREEN, True)
    text(section.upper(), 815, 31, 349, 10, MUTED, True)
    text(title, 36, 78, 1128, 31, INK, True)
    text(subtitle, 36, 126, 1115, 13, MUTED)
    C.setStrokeColor(HexColor(LINE))
    C.line(36, 34, 1164, 34)
    C.setFont(FONT, 9)
    C.setFillColor(HexColor(MUTED))
    C.drawString(36, 18, "VERDANT / VISUAL USER GUIDE / SEPTEMBER 2026 / FICTIONAL DEMO DATA")
    C.drawRightString(1164, 18, f"{page_number:02d} / {PAGES}")
    C.bookmarkPage(f"page{page_number}")
    C.addOutlineEntry(title, f"page{page_number}", level=0)


def image(name, x=36, y=179, width=820, height=None):
    height = height or width*1000/1440
    box(x-1, y-1, width+2, height+2, radius=5)
    C.drawImage(str(ASSETS / (name+".png")), x, H-y-height, width=width, height=height,
                preserveAspectRatio=True, anchor="c", mask="auto")


def steps(items, x=884, y=185, width=280):
    for number, (title, body) in enumerate(items, 1):
        box(x, y+1, 26, 26, GREEN, GREEN, 13)
        text(str(number), x+8, y+3, 20, 12, "#FFFFFF", True)
        th = text(title, x+38, y, width-38, 17, INK, True)
        bh = text(body, x+38, y+th+8, width-38, 13, MUTED)
        y += th+bh+34
    return y


def tip(value):
    box(884, 676, 280, 89, "#EAF2E8")
    text(value, 898, 688, 252, 11, GREEN)


def screen(section, title, subtitle, name, items, note):
    page(section, title, subtitle)
    image(name)
    steps(items)
    tip(note)
    C.showPage()


# 01
page("Start here", "Your documents. Your next step. One workspace.",
     "A visual handbook for employees, project owners, reviewers and read-only visitors.")
image("home", 36, 180, 744)
box(808, 180, 356, 222, GREEN, GREEN)
text("Two connected spaces", 832, 202, 306, 22, "#FFFFFF", True)
text("<b>Project documents</b><br/>Required files, named responsibilities, versions and reviews."
     "<br/><br/><b>Research library</b><br/>Shared knowledge, classifications, references and endorsements.",
     832, 251, 300, 14, "#FFFFFF")
text("Find the page you need", 808, 432, 350, 20, GREEN, True)
index = [("Sign in, Home, My actions and projects", "02-05"), ("People and required documents", "06-07"),
         ("Read, upload, review and compare", "08-11"), ("Research and project references", "12-14"),
         ("Sharing, search, activity and Office files", "15-18"), ("Demo walkthrough and local setup", "19-20")]
for i, (title, number) in enumerate(index):
    text(title, 808, 474+i*36, 280, 13)
    text(number, 1107, 474+i*36, 57, 13, GREEN, True)
text("How to use this guide: follow the numbered instructions beside each actual application screen. "
     "Some examples show an unsaved form. Sample engineering values are invented and must not be used for real work.",
     36, 720, 730, 12, MUTED)
C.showPage()

# 02
page("Sign in", "Choose the right role for your demonstration",
     "Open http://localhost:3000. Use an employee ID or username, then enter the password.")
image("login", 36, 180, 740)
text("Demo accounts", 808, 182, 350, 22, GREEN, True)
text("All sample accounts use <b>verdant-demo</b>.<br/>These credentials are for a local demo only.",
     808, 223, 345, 13)
accounts = [
    ("EMP-1042", "Ananya / project owner"),
    ("EMP-1071", "Mira / responsible employee"),
    ("EMP-1088", "Vikram / assigned reviewer"),
    ("VIS-1100", "Leela / document-only visitor"),
    ("DEMO-1201", "Rohan / additional engineer"),
    ("DEMO-1202", "Sara / project observer"),
]
for i, (code, role) in enumerate(accounts):
    box(808, 285+i*66, 356, 57)
    text(code, 823, 295+i*66, 327, 14, GREEN, True)
    text(role, 823, 317+i*66, 327, 11, MUTED)
text("<b>Sign out before changing roles.</b> Use separate browser profiles or private windows for a live "
     "author/reviewer demonstration. Different tabs in the same browser profile share one session.",
     36, 723, 740, 12)
C.showPage()

# 03
screen("Home + My actions", "Start with your own workspace",
       "Home is the landing page after login. My actions focuses on the work assigned specifically to you.",
       "home", [
           ("See your memberships", "Project cards show only the projects you own or belong to. Select a card to open it."),
           ("Check your next action", "Choose <b>My actions</b> or a row under <b>Needs your attention</b>. The matching document opens directly."),
           ("Use the workspace shortcuts", "The summary cards lead to My projects, My actions and the shared research library."),
       ], "The workspace refreshes about every 30 seconds while visible, except while a form or action is open.")

# 04
screen("My actions", "Know exactly what is waiting for you",
       "Choose My actions in the sidebar. The list is based on individual document assignments.",
       "my-actions", [
           ("Missing or Draft", "As the responsible employee, upload the first file or open an existing draft and submit it when ready."),
           ("Changes requested", "Read the review feedback. Correct the file, upload a new version with a change summary, then submit it again."),
           ("Submitted or Under review", "As the assigned reviewer, open the document, start review if needed, then approve or send written feedback."),
       ], "A viewer or observer may have no actions at all. A task leaves this list when it no longer needs that employee's action.")

screen("My projects", "Create a document workspace",
       "Select My projects in the sidebar. Choose Create project to open the form shown here.",
       "create-project", [
           ("Name the project", "Use a recognizable name and a short description. Example: <b>Project Y - pilot assembly</b>."),
           ("Choose a starting lifecycle", "Select a company template if useful. Leave it blank to create your own stages later."),
           ("Create, then configure", "Choose <b>Create project</b>. The creator is its owner. Next open <b>People &amp; stages</b>."),
       ], "A Verdant project organizes documentation. It is not a schedule, budget or project-planning board.")

# 05
screen("Project / People & stages", "Build the team and lifecycle",
       "Only the project owner can add members, stages and document requirements.",
       "people-stages", [
           ("Add employees", "Choose <b>Add member</b>, select an employee and save. Membership gives visibility into the project."),
           ("Add lifecycle stages", "Choose <b>Add stage</b>. Use your project's real phases, such as Design, Validation and Release."),
           ("Assign work separately", "Membership is not permission to upload every file. Each required document gets its own responsible employee and reviewer."),
       ], "The owner may view and manage the project but cannot perform another employee's assigned upload or review.")

# 06
screen("Project / Required document", "Define one document slot",
       "Choose Required document from the project header. The example form is filled but not saved.",
       "requirement-form", [
           ("Describe the required file", "Enter a clear title and document type or part. Put different part drawings in separate document slots."),
           ("Choose stage and people", "Select the lifecycle stage, responsible employee and one different reviewer. Both employees must belong to the project."),
           ("Save the requirement", "Add an optional due date and description, then save. The slot starts as <b>Missing</b> until the first upload."),
       ], "Use Change assignments on a document to update people. Assignments cannot change while its review is pending or underway.")

# 07
screen("Project / Documents", "Read without leaving the application",
       "Choose Documents, then select a file in the stage-grouped list on the left.",
       "project-workspace", [
           ("Find the right document", "Filter by title or lifecycle stage. Each row shows its current status, responsible employee and version."),
           ("Read in the main panel", "PDFs open inside Verdant. Use previous/next page and zoom controls above the page. Images and content previews use the same panel."),
           ("Check the context", "Read the responsible employee, reviewer, version note and feedback. A missing upload shows an empty reader."),
       ], "PDFs retain page layout. DOCX/PPTX show text; XLSX/CSV show tables. Export to PDF when exact Office formatting matters.")

# 08
screen("Responsible employee / Upload", "Upload a version, then submit it",
       "Example: Mira opens Atlas > Battery enclosure drawing, which has Changes requested.",
       "upload-version", [
           ("Read the feedback first", "Understand what the reviewer asked for. Update your file outside Verdant; the app stores and previews files, not an in-browser editor."),
           ("Upload the corrected file", "Choose <b>Upload new version</b>, select the file, explain what changed, then choose <b>Upload</b>. Earlier files remain available."),
           ("Submit the draft", "The new version is a <b>Draft</b>. Read it, then choose <b>Submit for review</b>. It appears in the assigned reviewer's My actions."),
       ], "Only the responsible employee can upload or submit. Uploads are blocked while a submitted version is awaiting review.")

# 09
screen("Assigned reviewer / Review", "Make feedback clear and actionable",
       "Start from My actions. On a Submitted document, select Start review before making a decision.",
       "review-feedback", [
           ("Inspect the latest file", "Check its content and version note. Use comparison or history when earlier versions exist."),
           ("Approve or request changes", "<b>Approve</b> records acceptance of this version. <b>Request changes</b> opens the feedback form shown here."),
           ("Explain the correction", "Written feedback is required for changes requests. Choose <b>Send feedback</b>. The responsible employee then uploads a new version."),
       ], "Owners and administrators cannot bypass the assigned reviewer. A research endorsement is different from a project review.")

# 10
screen("Document history", "Keep the evidence, compare revisions",
       "Older versions and their review comments stay attached to the same document.",
       "version-comparison", [
           ("Choose a version", "Use the version selector above the reader. An earlier version shows its own feedback and a historical-version notice."),
           ("Compare side by side", "Choose <b>Compare versions side by side</b>. The selected version and another retained version each have reading controls."),
           ("Return to the current file", "Close comparison and select the latest version before submitting or reviewing. Historical selection hides current review actions."),
       ], "Comparison is visual; it does not automatically highlight edits or calculate a redline. Read the author's change summary too.")

# 11
screen("Research library / Browse", "Explore the company's knowledge",
       "Research is a shared file library, not the controlled project review pipeline.",
       "research-library", [
           ("Browse classifications", "Choose a folder on the far left. A parent includes documents from its subcategories. All research removes the category filter."),
           ("Switch between files", "Select a title in the middle column. The reader and document details update on the right."),
           ("Look for useful context", "Read the description, uploader, endorsement badges and references. An endorsement is a trust signal, not a publishing gate."),
       ], "Use the classification's filter for a local search, or the top search bar to search across accessible project and research metadata.")

# 12
screen("Research library / Contribute", "Publish research and connect it",
       "Any signed-in employee can contribute research files without submitting them for a project review.",
       "research-links", [
           ("Classify and upload", "Use <b>+</b> beside Classifications to add a category or subcategory. Choose <b>Upload document</b>, enter a title and classification, then upload."),
           ("Connect the reference", "<b>+ Link project</b> connects the file to an accessible project. <b>+ Add reference</b> connects related research documents."),
           ("Keep one source", "Use <b>New version</b> for a revision of the same research document. Click a linked title to navigate. Do not duplicate a file just to reference it."),
       ], "Senior approvers can Endorse research. Only authorized users can remove a link or archive a document; the server checks permission.")

# 13
screen("Project / Research links", "See the research behind the project",
       "Open a project's Research links tab to browse references used by that team.",
       "project-references", [
           ("Link an existing reference", "Choose <b>Link research</b>, select a company research document and save."),
           ("Open the source", "Select the linked document title. Verdant opens that document in the research library with its current version."),
           ("Return via its project link", "In the research document, select the project reference to go back. Removing a link does not delete the research file."),
       ], "Project names are visible in the research library only to employees who can access those projects.")

# 14
screen("Shared with me", "Share a document, not the whole project",
       "The screen shown is Leela's read-only visitor account.",
       "visitor-inbox", [
           ("Owner: share the file", "Open the project document, choose <b>Share</b>, select an existing employee or visitor account and save."),
           ("Visitor: open Shared with me", "Select the shared title in the sidebar's Shared with me area. Its latest version opens in the reader."),
           ("Keep access narrow", "A document-only visitor does not gain access to the project dashboard, its other documents or its assigned work."),
       ], "Sharing is to existing accounts, not a public anonymous URL. Only the project owner can manage document sharing.")

# 15
screen("Global search", "Go straight to the document you need",
       "The search bar stays available at the top of the workspace.",
       "search", [
           ("Use recognizable terms", "Search a title, description, document type or research classification. Try <b>thermal</b> in the demo."),
           ("Read the result context", "Results identify the project or research category so similar file names are easier to distinguish."),
           ("Open the matching result", "Select a result to open that exact project, research or shared document in the appropriate workspace."),
       ], "Search currently matches metadata. Full-file text search and semantic/topic search with embeddings are not implemented.")

# 16
screen("Project / Activity", "Understand what happened and who acted",
       "The Activity tab shows the project's uploads, submissions, decisions, membership and reference changes.",
       "activity-log", [
           ("Read the timeline", "Entries include the action, actor and time. Review decision entries include written comments."),
           ("Use it alongside history", "Activity explains the sequence. The document's version selector opens the actual files and version-specific feedback."),
           ("Archive carefully", "Owners can archive project requirements; research uploaders/admins can archive research. A confirmation explains that stored history remains."),
       ], "Archive hides a document; it is not a permanent file deletion. There is no self-service restore screen yet. The seeded history is fictional demo activity.")

# 17
screen("File reader / Office content", "View more than PDFs",
       "Example: the fictional material comparison workbook opens as a table inside the research library.",
       "office-preview", [
           ("Choose a supported file", "PDF, PNG/JPEG/GIF/WebP, TXT/Markdown, CSV, DOCX, XLSX and PPTX can be viewed inside Verdant."),
           ("Read the preview note", "Office previews show readable content, not original Office layout. Tables are bounded; the note states the row, column and sheet limits."),
           ("Use PDF for exact appearance", "Export charts, complex formatting or legacy files to PDF before uploading when the precise layout is important."),
       ], "Previewing does not edit the source file or execute spreadsheet formulas. To change content, edit it externally and upload a new version.")

page("Live demonstration", "A useful 10-minute walkthrough",
     "The showcase is already populated. These steps demonstrate real actions, not mocked screens.")
cards = [
    ("1 / Owner - show the big picture", "EMP-1042", "Home shows Project X, Atlas and Nova. Open Atlas, show its stages, document states and Research links.", "0-2 min"),
    ("2 / Author - respond to feedback", "EMP-1071", "My actions > Battery enclosure drawing. Read the feedback. Upload demo-files/battery-enclosure-v3.pdf with a change summary, then Submit for review.", "2-5 min"),
    ("3 / Reviewer - close the loop", "EMP-1088", "My actions > Battery enclosure drawing. Start review, inspect the new file and Compare versions. Approve with a short review note.", "5-7 min"),
    ("4 / Visitor - read safely", "VIS-1100", "Shared with me > Material selection report. Read the multi-page PDF. No project management or upload actions are available.", "7-8 min"),
    ("5 / Research - connect knowledge", "EMP-1071", "Browse DEMO research > Materials > Metals & alloys. Open the workbook, follow a related reference, and use a project link to return.", "8-10 min"),
]
for i, (title, account, body, timing) in enumerate(cards):
    top = 176+i*114
    box(36, top, 1128, 101)
    text(title, 55, top+13, 400, 17, GREEN, True)
    text(account+" / "+timing, 55, top+46, 380, 12, MUTED)
    text(body, 468, top+18, 671, 14)
text("Use a separate browser profile for each role, or sign out between accounts. Rerunning Add-DemoData.ps1 "
     "does not reset this walkthrough after you complete it. For a clean rehearsal use a separate fresh demo database.",
     36, 759, 1128, 11, MUTED)
C.showPage()

# 18
page("Local setup + quick reference", "Keep the demo ready to run",
     "The product branch is product-architecture-postgresql. Docker is not required.")
box(36, 178, 545, 280)
text("First installation", 58, 198, 500, 22, GREEN, True)
text("Install Git, Python 3.12+, Node.js 22.13+ and PostgreSQL 16+. Clone the branch and run these "
     "commands from the project folder:", 58, 239, 495, 14)
box(58, 322, 501, 112, GREEN, GREEN)
text("powershell -ExecutionPolicy Bypass<br/>"
     "-File .\\Install-Verdant.ps1 -DemoData<br/><br/>"
     "powershell -ExecutionPolicy Bypass -File .\\Start-Verdant.ps1",
     73, 339, 470, 12, "#FFFFFF")
box(605, 178, 559, 280)
text("Existing demo installation", 627, 198, 513, 22, GREEN, True)
text("Update the code and dependencies, then run <b>Add-DemoData.ps1</b>. It applies migrations "
     "and adds the showcase once. It does not replace employee passwords, existing documents or demo progress.",
     627, 239, 507, 14)
text("Open <b>http://localhost:3000</b>.<br/>Use <b>Stop-Verdant.ps1</b> to stop the app and "
     "<b>Start-Verdant.ps1</b> after restarting Windows.", 627, 357, 507, 14)
box(36, 482, 1128, 262)
text("If something is not available", 58, 503, 1060, 22, GREEN, True)
rows = [
    ("No upload/review button", "Check the named responsible employee or reviewer; ownership alone does not grant that action."),
    ("A new upload is blocked", "Wait for the current submitted/active review to finish. After changes are requested, upload a new version."),
    ("Office layout looks different", "Office files show readable content. Use PDF for exact formatting; CAD/legacy/unsafe formats need conversion."),
    ("A project or link is missing", "Ask its owner for membership or a document-only share. Company research visibility does not grant project access."),
    ("Sign-in or setup fails", "Confirm PostgreSQL and both app services are running. Follow LOCAL-RUN.md and docs/LOCAL_INSTALLATION_WINDOWS.md."),
]
for i, (problem, solution) in enumerate(rows):
    text(problem, 58, 549+i*36, 251, 11, GREEN, True)
    text(solution, 325, 549+i*36, 811, 11)
text("Use only fictional data in demos. Before company deployment, replace demo credentials and arrange HTTPS, "
     "backups, restricted database access and a security review.", 36, 762, 1128, 11, MUTED)
C.showPage()
assert page_number == PAGES
C.save()
print(OUTPUT)
