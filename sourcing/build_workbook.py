"""Build the Crowsons Distribution wholesale supplier workbook.

Usage: python3 build_workbook.py  ->  writes Crowsons_Wholesale_Suppliers.xlsx
"""
import os
import sys
from urllib.parse import quote_plus

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from suppliers_data import SUPPLIERS  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Crowsons_Wholesale_Suppliers.xlsx")

FONT = "Arial"
NAVY = "1F3864"
HDR_FILL = PatternFill("solid", fgColor=NAVY)
TRACK_FILL = PatternFill("solid", fgColor="FFF2CC")   # yellow = cells for the user to fill in
SECTION_FILL = PatternFill("solid", fgColor="D9E1F2")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
LINK_FONT = Font(name=FONT, size=10, color="0563C1", underline="single")
BODY = Font(name=FONT, size=10)
BOLD = Font(name=FONT, size=10, bold=True)
HDR_FONT = Font(name=FONT, size=10, bold=True, color="FFFFFF")
TITLE = Font(name=FONT, size=16, bold=True, color=NAVY)
H2 = Font(name=FONT, size=12, bold=True, color=NAVY)

STATUSES = ["Not contacted", "Contacted", "Follow-up sent", "Replied", "Application submitted",
            "Account approved", "Price list received", "First order placed", "Rejected", "Not suitable"]
METHODS = ["Email", "LinkedIn", "Phone", "Website form", "WhatsApp", "Trade show", "In person"]


def linkedin_company(name):
    base = name.split("(")[0].strip()
    return "https://www.linkedin.com/search/results/companies/?keywords=" + quote_plus(base)


def linkedin_people(name):
    base = name.split("(")[0].strip()
    return ("https://www.linkedin.com/search/results/people/?keywords="
            + quote_plus(f'{base} sales OR "account manager" OR "business development"'))


def header_row(ws, row, headers, widths, fills=None):
    for i, (h, w) in enumerate(zip(headers, widths), start=1):
        c = ws.cell(row=row, column=i, value=h)
        c.font = HDR_FONT
        c.fill = (fills or {}).get(i, HDR_FILL)
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        c.border = BORDER
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[row].height = 32


def set_link(cell, url, text=None):
    if not url:
        return
    cell.value = text or url
    cell.hyperlink = url
    cell.font = LINK_FONT


# --------------------------------------------------------------------------- data prep
rows = sorted(SUPPLIERS, key=lambda s: (-s["pri"], s["cat"], s["name"]))

wb = Workbook()

# =========================================================================== Start Here
ws0 = wb.active
ws0.title = "Start Here"
ws0.sheet_view.showGridLines = False
ws0.column_dimensions["A"].width = 3
ws0.column_dimensions["B"].width = 30
ws0.column_dimensions["C"].width = 95
r = 2
ws0.cell(row=r, column=2, value="Crowsons Distribution - Wholesale Supplier Sourcing List").font = TITLE
r += 1
ws0.cell(row=r, column=2, value="UK & EU suppliers for Amazon UK wholesale: fragrance, health & beauty, healthcare, toys, pet, baby, FMCG. Researched Oct 2026.").font = BODY
r += 2
ws0.cell(row=r, column=2, value="How to use this workbook").font = H2
r += 1
steps = [
    ("1. Suppliers", "The master list. Sorted by Priority (5 = best fit for Amazon). Use the filter arrows to filter by category, country or priority."),
    ("2. Yellow columns", "Your outreach tracker - fill these in as you go. Status, Method and Account Approved have drop-down lists. 'Suggested Follow-up' fills in automatically (5 working days after Date Contacted) and turns red when overdue."),
    ("3. LinkedIn Outreach", "One-click LinkedIn searches for each company page and its sales / account-manager staff, plus a tracker. Message templates are on the Templates tab."),
    ("4. Templates", "Copy-paste first-contact email, follow-up, LinkedIn connection note, LinkedIn message and invoice / ungating request."),
    ("5. Dashboard", "Live counts of suppliers by category and outreach status (updates automatically from the Suppliers tab)."),
    ("6. Find More Suppliers", "Directories, registries and trade shows to keep growing the list."),
    ("7. Due Diligence", "Checklist to confirm a supplier is legitimate BEFORE you send money."),
]
for k, v in steps:
    ws0.cell(row=r, column=2, value=k).font = BOLD
    c = ws0.cell(row=r, column=3, value=v); c.font = BODY; c.alignment = WRAP
    r += 1
r += 1
ws0.cell(row=r, column=2, value="Priority score (1-5)").font = H2
r += 1
for k, v in [
    ("5", "Established, branded stock, sells to online / Amazon sellers or provides invoices suitable for ungating. Contact first."),
    ("4", "Established and branded, but may have higher MOQs, selective accounts or a narrower range."),
    ("3", "Credible, worth contacting - confirm terms, online-selling policy and invoice details."),
    ("2", "Lower fit (EU-only focus, pro-only brands, limited info) or larger-scale target for later."),
    ("1", "Low confidence, known red flag, or not suitable for Amazon - kept so you know to avoid / verify."),
]:
    ws0.cell(row=r, column=2, value=k).font = BOLD
    c = ws0.cell(row=r, column=3, value=v); c.font = BODY; c.alignment = WRAP
    r += 1
r += 1
ws0.cell(row=r, column=2, value="Data confidence").font = H2
r += 1
for k, v in [
    ("Official / company website", "Details came from the supplier's own site or an official register (Companies House, MHRA)."),
    ("Directory / press", "Details came from trade press or business directories - confirm on the company website before relying on them."),
    ("Marketplace / unverified", "Self-published profile only. Verify company registration (Companies House / KvK / VIES VAT) before engaging."),
    ("Blank cells", "Information was not publicly available. MOQ is usually only given once a trade account is approved - ask in your first email."),
]:
    ws0.cell(row=r, column=2, value=k).font = BOLD
    c = ws0.cell(row=r, column=3, value=v); c.font = BODY; c.alignment = WRAP
    r += 1
r += 1
ws0.cell(row=r, column=2, value="Key Amazon UK considerations").font = H2
r += 1
for k, v in [
    ("Brand / category gating", "Fragrance, beauty, toys (Q4), baby and health have gated brands/categories. Amazon wants invoices from a real wholesaler/distributor (not a retailer) dated within 180 days, showing supplier name, address, phone, website, your business name/address, and 10+ units."),
    ("Hazmat (fragrance)", "Perfume / aftershave is flammable dangerous goods. You need a Safety Data Sheet (SDS) per product for Amazon's hazmat review - ask suppliers if they provide them."),
    ("No testers / unboxed", "Amazon does not allow testers or unboxed fragrance. Ask for sealed retail stock only."),
    ("Online-selling policies", "Some suppliers (e.g. CLF, We.pet, Faire brands) forbid Amazon resale - ask before applying so you don't waste time."),
    ("EU suppliers after Brexit", "Buying from the EU into the UK means import VAT, possible duty and customs paperwork. Ask EU suppliers for DDP (delivered duty paid) or use a freight forwarder. Toys/cosmetics need UK compliance (UKCA/CE, UK Responsible Person for cosmetics)."),
    ("Medicines", "GSL medicines need care on Amazon (category approval). Licensed pharma wholesalers may only supply pharmacies."),
]:
    ws0.cell(row=r, column=2, value=k).font = BOLD
    c = ws0.cell(row=r, column=3, value=v); c.font = BODY; c.alignment = WRAP
    ws0.row_dimensions[r].height = 42
    r += 1
r += 1
ws0.cell(row=r, column=2, value="About LinkedIn outreach").font = H2
r += 1
c = ws0.cell(row=r, column=3, value=(
    "Messages must be sent from your own LinkedIn account. Automation tools break LinkedIn's terms and risk a ban, "
    "so this workbook gives you one-click searches + templates to make manual outreach fast. "
    "Tip: send ~15-25 connection requests per day, personalise the first line, and follow up after 4-5 working days."))
c.font = BODY; c.alignment = WRAP
ws0.row_dimensions[r].height = 45

# =========================================================================== Suppliers
ws = wb.create_sheet("Suppliers")
cols = [
    ("ID", 6), ("Priority (1-5)", 9), ("Category", 16), ("Company", 30), ("Website", 30), ("Country", 13),
    ("City / Region", 20), ("Address", 34), ("Phone", 18), ("Email", 28), ("Supplier Type", 20),
    ("Key Brands / Products", 38), ("Segment", 20), ("MOQ / Min. Order", 22), ("Account Requirements", 28),
    ("Ships to UK?", 18), ("Legitimacy Evidence", 34), ("Amazon Fit Notes", 36), ("Notes / Red Flags", 36),
    ("Data Confidence", 22), ("Source", 22), ("LinkedIn Company Search", 18),
    # tracker
    ("Status", 18), ("Date Contacted", 13), ("Method", 13), ("Contact Name", 18), ("Response / Notes", 30),
    ("Suggested Follow-up", 13), ("Account Approved?", 12), ("Next Step", 26),
]
TRACK_START = 23
fills = {i: PatternFill("solid", fgColor="BF8F00") for i in range(TRACK_START, len(cols) + 1)}
header_row(ws, 1, [c[0] for c in cols], [c[1] for c in cols], fills)

for i, s in enumerate(rows, start=1):
    r = i + 1
    vals = [i, s["pri"], s["cat"], s["name"], None, s["country"], s["city"], s["addr"], s["phone"], s["email"],
            s["stype"], s["brands"], s["segment"], s["moq"], s["req"], s["uk"], s["legit"], s["amazon"],
            s["notes"], s["verified"], None, None,
            "Not contacted", None, None, None, None,
            f'=IF(X{r}="","",WORKDAY(X{r},5))', None, None]
    for col, v in enumerate(vals, start=1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = BODY
        c.alignment = WRAP
        c.border = BORDER
        if col >= TRACK_START:
            c.fill = TRACK_FILL
    set_link(ws.cell(row=r, column=5), s["web"])
    if not s["web"]:
        ws.cell(row=r, column=5, value="Not confirmed - search company name")
    set_link(ws.cell(row=r, column=21), s["src"], "Source link")
    set_link(ws.cell(row=r, column=22), linkedin_company(s["name"]), "Search LinkedIn")
    ws.cell(row=r, column=2).alignment = Alignment(horizontal="center", vertical="top")
    ws.cell(row=r, column=24).number_format = "dd/mm/yyyy"
    ws.cell(row=r, column=28).number_format = "dd/mm/yyyy"

last = len(rows) + 1
ws.freeze_panes = "E2"
ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{last}"

dv_status = DataValidation(type="list", formula1='"' + ",".join(STATUSES) + '"', allow_blank=True)
dv_method = DataValidation(type="list", formula1='"' + ",".join(METHODS) + '"', allow_blank=True)
dv_yes = DataValidation(type="list", formula1='"Yes,No,Pending"', allow_blank=True)
dv_date = DataValidation(type="date", operator="greaterThan", formula1="DATE(2020,1,1)", allow_blank=True)
for dv, col in [(dv_status, "W"), (dv_method, "Y"), (dv_yes, "AC"), (dv_date, "X")]:
    ws.add_data_validation(dv)
    dv.add(f"{col}2:{col}{last}")

# priority colour scale
ws.conditional_formatting.add(f"B2:B{last}", CellIsRule(operator="equal", formula=["5"], fill=PatternFill("solid", fgColor="63BE7B")))
ws.conditional_formatting.add(f"B2:B{last}", CellIsRule(operator="equal", formula=["4"], fill=PatternFill("solid", fgColor="B1D580")))
ws.conditional_formatting.add(f"B2:B{last}", CellIsRule(operator="equal", formula=["1"], fill=PatternFill("solid", fgColor="F8696B")))
# overdue follow-up
ws.conditional_formatting.add(
    f"AB2:AB{last}",
    FormulaRule(formula=[f'AND(AB2<>"",AB2<=TODAY(),OR(W2="Contacted",W2="Follow-up sent"))'],
                fill=PatternFill("solid", fgColor="F8696B"), font=Font(name=FONT, bold=True, color="FFFFFF")))
# red-flag notes
ws.conditional_formatting.add(
    f"S2:S{last}",
    FormulaRule(formula=['OR(ISNUMBER(SEARCH("RED FLAG",S2)),ISNUMBER(SEARCH("NOT SUITABLE",R2)))'],
                fill=PatternFill("solid", fgColor="FCE4D6")))

# =========================================================================== LinkedIn Outreach
wl = wb.create_sheet("LinkedIn Outreach")
lcols = [("ID", 6), ("Company", 32), ("Category", 16), ("Country", 12), ("Company Page Search", 18),
         ("Find Sales / Account Managers", 22), ("Person Name", 20), ("Job Title", 20), ("Profile URL", 28),
         ("Connection Sent", 12), ("Accepted?", 10), ("Message Sent", 12), ("Reply?", 10), ("Notes", 34)]
header_row(wl, 1, [c[0] for c in lcols], [c[1] for c in lcols],
           {i: PatternFill("solid", fgColor="BF8F00") for i in range(7, len(lcols) + 1)})
for i, s in enumerate(rows, start=1):
    r = i + 1
    for col, v in enumerate([f"=Suppliers!A{r}", f"=Suppliers!D{r}", f"=Suppliers!C{r}", f"=Suppliers!F{r}"], start=1):
        c = wl.cell(row=r, column=col, value=v); c.font = Font(name=FONT, size=10, color="008000"); c.border = BORDER; c.alignment = WRAP
    set_link(wl.cell(row=r, column=5), linkedin_company(s["name"]), "Company page")
    set_link(wl.cell(row=r, column=6), linkedin_people(s["name"]), "Find people")
    for col in (5, 6):
        wl.cell(row=r, column=col).border = BORDER
    for col in range(7, len(lcols) + 1):
        c = wl.cell(row=r, column=col); c.fill = TRACK_FILL; c.border = BORDER; c.font = BODY; c.alignment = WRAP
    for col in (10, 12):
        wl.cell(row=r, column=col).number_format = "dd/mm/yyyy"
llast = len(rows) + 1
wl.freeze_panes = "C2"
wl.auto_filter.ref = f"A1:{get_column_letter(len(lcols))}{llast}"
dv_yn = DataValidation(type="list", formula1='"Yes,No,Pending"', allow_blank=True)
wl.add_data_validation(dv_yn)
dv_yn.add(f"K2:K{llast}")
dv_yn.add(f"M2:M{llast}")

# =========================================================================== Templates
wt = wb.create_sheet("Templates")
wt.sheet_view.showGridLines = False
wt.column_dimensions["A"].width = 3
wt.column_dimensions["B"].width = 28
wt.column_dimensions["C"].width = 100
wt.cell(row=2, column=2, value="Outreach templates - replace [brackets] before sending").font = TITLE
templates = [
    ("Email 1 - First contact", "Subject: Trade account enquiry - Crowsons Distribution (UK online retailer)",
     "Hi [Name / Sales Team],\n\n"
     "I'm [Your Name], founder of Crowsons Distribution, a UK-registered online retailer (Company No. [xxxx], VAT No. [xxxx]). "
     "We sell branded [fragrance / health & beauty / toys] to UK customers through our online channels, including Amazon UK.\n\n"
     "We're looking for reliable, long-term suppliers and would like to open a trade account with [Company]. Could you please let me know:\n"
     "  1. Your trade account application process and requirements\n"
     "  2. Minimum order quantity / minimum order value\n"
     "  3. Current price list or stock list\n"
     "  4. Payment terms and delivery options to the UK\n"
     "  5. Whether you're happy to supply retailers who sell online / on marketplaces\n\n"
     "We place repeat orders on lines that sell well, and we're happy to start with a test order.\n\n"
     "Kind regards,\n[Your Name]\nCrowsons Distribution\n[Phone] | [Email] | [Website]"),
    ("Email 2 - Follow-up (5 working days)", "Subject: Re: Trade account enquiry - Crowsons Distribution",
     "Hi [Name],\n\nJust following up on my email from [day] about opening a trade account. "
     "We're keen to place an initial order in the next few weeks - is there a price list or application form you could share?\n\n"
     "If there's a better person to speak to, I'd be grateful if you could point me in the right direction.\n\n"
     "Thanks,\n[Your Name]"),
    ("LinkedIn connection note (max 300 chars)", "",
     "Hi [First name], I run Crowsons Distribution, a UK online retailer of branded [fragrance/beauty/toys]. "
     "I'm looking to open trade accounts with established distributors like [Company] and would love to connect."),
    ("LinkedIn message (after they accept)", "",
     "Thanks for connecting, [First name]!\n\n"
     "We're a UK-registered online retailer (Amazon UK + own channels) growing our range of branded [category]. "
     "I'd love to explore opening a trade account with [Company]. Who's the best person to speak to about new accounts, "
     "and is there a price list or application form you could share?\n\nHappy to jump on a quick call if easier."),
    ("Invoice / Amazon ungating request", "Subject: Invoice requirements for our order",
     "Hi [Name],\n\nThanks for processing our order. For our records, could you please make sure the invoice shows:\n"
     "  - Your company name, full address, phone number and website\n"
     "  - Our company name and address: [Crowsons Distribution, address]\n"
     "  - Invoice date, product names/descriptions and quantities (in units)\n"
     "  - Prices are optional and can be hidden if you prefer\n\n"
     "If available, could you also send the Safety Data Sheets (SDS) for the fragrance lines?\n\n"
     "Many thanks,\n[Your Name]"),
]
r = 4
for title, subj, body in templates:
    wt.cell(row=r, column=2, value=title).font = H2
    if subj:
        c = wt.cell(row=r, column=3, value=subj); c.font = BOLD
        r += 1
    c = wt.cell(row=r, column=3, value=body); c.font = BODY; c.alignment = WRAP
    c.fill = PatternFill("solid", fgColor="F2F2F2")
    wt.row_dimensions[r].height = max(45, 15 * (body.count("\n") + 2 + len(body) // 110))
    r += 2

# =========================================================================== Dashboard
wd = wb.create_sheet("Dashboard")
wd.sheet_view.showGridLines = False
wd.column_dimensions["A"].width = 3
wd.column_dimensions["B"].width = 28
for col in "CDEFG":
    wd.column_dimensions[col].width = 14
wd.cell(row=2, column=2, value="Outreach dashboard").font = TITLE
wd.cell(row=3, column=2, value="All figures are formulas linked to the Suppliers tab.").font = BODY

rng = f"Suppliers!$C$2:$C${last}"
st = f"Suppliers!$W$2:$W${last}"
pr = f"Suppliers!$B$2:$B${last}"
ap = f"Suppliers!$AC$2:$AC${last}"
hdr = ["Category", "Suppliers", "Priority 4-5", "Contacted+", "Approved"]
for i, h in enumerate(hdr):
    c = wd.cell(row=5, column=2 + i, value=h); c.font = HDR_FONT; c.fill = HDR_FILL; c.border = BORDER
cats = sorted({s["cat"] for s in rows})
r = 6
for cat in cats:
    wd.cell(row=r, column=2, value=cat).font = BODY
    wd.cell(row=r, column=3, value=f'=COUNTIF({rng},B{r})')
    wd.cell(row=r, column=4, value=f'=COUNTIFS({rng},B{r},{pr},">=4")')
    wd.cell(row=r, column=5, value=f'=COUNTIFS({rng},B{r},{st},"<>Not contacted")')
    wd.cell(row=r, column=6, value=f'=COUNTIFS({rng},B{r},{ap},"Yes")')
    for col in range(2, 7):
        wd.cell(row=r, column=col).border = BORDER
        wd.cell(row=r, column=col).font = BODY
    r += 1
wd.cell(row=r, column=2, value="Total").font = BOLD
for col in range(3, 7):
    L = get_column_letter(col)
    c = wd.cell(row=r, column=col, value=f"=SUM({L}6:{L}{r - 1})"); c.font = BOLD; c.border = BORDER
wd.cell(row=r, column=2).border = BORDER

r += 3
for i, h in enumerate(["Outreach status", "Count", "% of list"]):
    c = wd.cell(row=r, column=2 + i, value=h); c.font = HDR_FONT; c.fill = HDR_FILL; c.border = BORDER
r += 1
first_status = r
for s_ in STATUSES:
    wd.cell(row=r, column=2, value=s_).font = BODY
    wd.cell(row=r, column=3, value=f'=COUNTIF({st},B{r})').font = BODY
    c = wd.cell(row=r, column=4, value=f'=IF(COUNTA({rng})=0,0,C{r}/COUNTA({rng}))'); c.number_format = "0.0%"; c.font = BODY
    for col in range(2, 5):
        wd.cell(row=r, column=col).border = BORDER
    r += 1
r += 1
wd.cell(row=r, column=2, value="Follow-ups overdue").font = BOLD
wd.cell(row=r, column=3, value=(
    f'=SUMPRODUCT((Suppliers!$AB$2:$AB${last}<>"")*(Suppliers!$AB$2:$AB${last}<=TODAY())*'
    f'((Suppliers!$W$2:$W${last}="Contacted")+(Suppliers!$W$2:$W${last}="Follow-up sent")))')).font = BOLD

# =========================================================================== Find More Suppliers
wf = wb.create_sheet("Find More Suppliers")
fcols = [("Resource", 32), ("Type", 18), ("Use it for", 60), ("Link", 45)]
header_row(wf, 1, [c[0] for c in fcols], [c[1] for c in fcols])
resources = [
    ("Companies House", "UK registry", "Verify any UK supplier: status, address, directors, SIC 46450 = perfume & cosmetics wholesale", "https://find-and-update.company-information.service.gov.uk/"),
    ("EU VIES VAT checker", "EU registry", "Confirm an EU supplier's VAT number is real and active", "https://ec.europa.eu/taxation_customs/vies/"),
    ("KvK (Netherlands)", "EU registry", "Verify Dutch companies (many EU beauty wholesalers are Dutch)", "https://www.kvk.nl/en/"),
    ("MHRA licence register", "UK regulator", "Check a health/pharma wholesaler holds a wholesale dealer licence", "https://cms.mhra.gov.uk/mhra/wholesale-dealer-licences"),
    ("Better Retailing Supplier Directory", "UK directory", "UK wholesalers incl. toys, health & beauty, grocery", "https://supplier-directory.betterretailing.com/"),
    ("Unitas Wholesale - find a wholesaler", "UK directory", "Independent UK cash & carry / delivered wholesalers", "https://unitaswholesale.co.uk/"),
    ("Pet Business World trade directory", "UK directory", "Pet wholesalers & distributors", "https://www.petbusinessworld.co.uk/trade-directory/"),
    ("great.gov.uk Find a Supplier", "UK gov directory", "UK companies listing their export / supply capability", "https://www.great.gov.uk/international/buy-from-the-uk/find-a-supplier/"),
    ("Europages", "EU directory", "Search EU wholesalers by product & country", "https://www.europages.co.uk/"),
    ("Kompass", "Global directory", "Company search by NACE code (e.g. 46.45 perfume & cosmetics wholesale)", "https://www.kompass.com/"),
    ("CosmeticIndex - EU distributors", "Beauty directory", "Cosmetic distributors & wholesalers across Europe", "https://www.cosmeticindex.com/~cosmetic-distributors-wholesalers_Europe"),
    ("Qogita blog - UK & EU H&B suppliers", "Guide", "Lists of health & beauty wholesalers (marketing content, but useful leads)", "https://www.qogita.com/blog/top-10-wholesale-health-beauty-suppliers-in-the-uk-eu/"),
    ("London Toy Fair (January)", "Trade show", "Meet UK toy distributors - exhibitor list is a ready-made supplier list", "https://www.toyfair.co.uk/"),
    ("Spielwarenmesse Nuremberg (Jan/Feb)", "Trade show", "World's biggest toy fair - EU toy distributors", "https://www.spielwarenmesse.de/"),
    ("Cosmoprof Worldwide Bologna (March)", "Trade show", "Beauty & fragrance brands and distributors", "https://www.cosmoprof.com/"),
    ("Esxence Milan", "Trade show", "Niche / artistic perfumery brands and distributors", "https://www.esxence.com/"),
    ("Spring Fair Birmingham (Feb)", "Trade show", "UK gifts, toys, beauty & home wholesale", "https://www.springfair.com/"),
    ("Brand 'Where to buy' / 'Trade' pages", "Method", "Go to a brand's UK site and look for 'Stockists', 'Trade' or 'Distributors' to find authorised wholesalers", ""),
    ("LinkedIn search: 'distributor' + brand", "Method", "e.g. search 'Lattafa distributor UK' or 'Hasbro distributor' and filter by Companies / People", "https://www.linkedin.com/search/results/companies/?keywords=fragrance%20distributor"),
]
for i, (a, b, c_, d) in enumerate(resources, start=2):
    for col, v in enumerate([a, b, c_], start=1):
        cell = wf.cell(row=i, column=col, value=v); cell.font = BODY; cell.alignment = WRAP; cell.border = BORDER
    set_link(wf.cell(row=i, column=4), d)
    wf.cell(row=i, column=4).border = BORDER
wf.freeze_panes = "A2"

# =========================================================================== Due Diligence
wq = wb.create_sheet("Due Diligence")
qcols = [("Check", 44), ("Why it matters", 60), ("How", 50)]
header_row(wq, 1, [c[0] for c in qcols], [c[1] for c in qcols])
checks = [
    ("Company is registered & active", "Fake wholesalers often use made-up company names", "Companies House (UK), KvK (NL), VIES VAT check (EU)"),
    ("Physical address matches registry", "A real warehouse/office is a good sign; residential or virtual offices are a warning", "Google Maps Street View + registry address"),
    ("Business email domain (not Gmail/Hotmail)", "Free email addresses are common with scam suppliers", "Ask for a contact on the company domain"),
    ("VAT number on invoices", "Needed for Amazon ungating and your VAT reclaim", "Check the VAT number on HMRC / VIES"),
    ("Brand authorisation (for gated brands)", "Authorised-distributor invoices are the most accepted for Amazon ungating", "Ask: 'Are you an authorised distributor for [brand]? Can you share a letter?'"),
    ("Prices are realistic", "Prices far below other wholesalers suggest counterfeit or grey stock", "Compare to 2-3 other suppliers and the Amazon Buy Box"),
    ("Reviews & reputation", "Past complaints reveal problems", "Trustpilot, Google reviews, UK Business Forums, Amazon seller forums, council / Trading Standards news"),
    ("Safe payment for first order", "Bank transfer to a new supplier is hard to recover", "Start small; use credit card / trade credit where possible; never pay a personal account"),
    ("Product compliance", "Non-compliant stock gets removed from Amazon", "Fragrance: SDS + UK Responsible Person on pack. Toys: UKCA/CE marks. Cosmetics: CPNP / SCPN registered"),
    ("Online / marketplace selling allowed", "Some suppliers cancel accounts that sell on Amazon", "Ask in your first email"),
    ("Sealed retail stock (no testers)", "Testers / unboxed fragrance cannot be sold as new on Amazon", "Confirm in writing before ordering"),
]
for i, row in enumerate(checks, start=2):
    for col, v in enumerate(row, start=1):
        c = wq.cell(row=i, column=col, value=v); c.font = BODY; c.alignment = WRAP; c.border = BORDER

wb.save(OUT)
print("saved", OUT, "suppliers:", len(rows))
