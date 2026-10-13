"""Build the Crowsons Distribution wholesale supplier workbook.

Usage: python3 build_workbook.py  ->  writes Crowsons_Wholesale_Suppliers.xlsx
"""
import os
import sys
from urllib.parse import quote_plus

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from suppliers_data import SUPPLIERS  # noqa: E402
from suppliers_eu2 import SUPPLIERS_EU2  # noqa: E402
from suppliers_eu3 import SUPPLIERS_EU3  # noqa: E402
from suppliers_eu4 import SUPPLIERS_EU4  # noqa: E402
from suppliers_eu5 import SUPPLIERS_EU5  # noqa: E402
from supplier_updates import REMOVE, UPDATES  # noqa: E402
import scam_check as SC  # noqa: E402
import re  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Crowsons_Wholesale_Suppliers.xlsx")

FONT = "Arial"
NAVY = "1F3864"
HDR_FILL = PatternFill("solid", fgColor=NAVY)
TRACK_HDR_FILL = PatternFill("solid", fgColor="BF8F00")
TRACK_FILL = PatternFill("solid", fgColor="FFF2CC")   # yellow = cells for the user to fill in
NEW_FILL = PatternFill("solid", fgColor="E2EFDA")     # green tint = added in the latest round
BAND_FILLS = [PatternFill("solid", fgColor="DDEBF7"), PatternFill("solid", fgColor="FCE4D6")]  # alternate per country
PAN_EU = "Pan-European / Online"
LATEST_ROUND = "Round 5"
# Rough country price level for buying stock (based on EU price-level indices and local
# manufacturing costs). Low-cost countries usually give the cheapest unit prices on their
# own home-made brands; "Higher" countries are often still best for big branded distributors.
COST_TIER = {
    "Bulgaria": "Low-cost", "Romania": "Low-cost", "Poland": "Low-cost", "Hungary": "Low-cost",
    "Czech Republic": "Low-cost", "Lithuania": "Low-cost", "Latvia": "Low-cost", "Estonia": "Low-cost",
    "Slovakia": "Low-cost", "Croatia": "Low-cost", "Slovenia": "Low-cost", "Portugal": "Low-cost",
    "Greece": "Low-cost",
    "Spain": "Mid", "Italy": "Mid", "Cyprus": "Mid", "Malta": "Mid",
    "Germany": "Higher", "France": "Higher", "Netherlands": "Higher", "Belgium": "Higher",
    "Austria": "Higher", "Ireland": "Higher", "Luxembourg": "Higher", "Denmark": "Higher",
    "Sweden": "Higher", "Finland": "Higher",
    "UK": "UK (no import)", "Switzerland": "Higher (non-EU)", PAN_EU: "Varies",
}
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
LINK_FONT = Font(name=FONT, size=10, color="0563C1", underline="single")
BODY = Font(name=FONT, size=10)
BOLD = Font(name=FONT, size=10, bold=True)
INPUT_FONT = Font(name=FONT, size=10, color="0000FF")
LINKED_FONT = Font(name=FONT, size=10, color="008000")
HDR_FONT = Font(name=FONT, size=10, bold=True, color="FFFFFF")
TITLE = Font(name=FONT, size=16, bold=True, color=NAVY)
H2 = Font(name=FONT, size=12, bold=True, color=NAVY)

STATUSES = ["Not contacted", "Contacted", "Follow-up sent", "Replied", "Application submitted",
            "Account approved", "Price list received", "First order placed", "Rejected", "Not suitable"]
METHODS = ["Email", "LinkedIn", "Phone", "Website form", "WhatsApp", "Trade show", "In person"]

# Align round-1 category names with the Amazon niches used in round 2.
CAT_RENAME = {"Pet": "Pet Supplies", "Baby": "Baby Products", "Toys": "Toys & Games",
              "Healthcare / Medical": "Health & Personal Care",
              "Health & Beauty": "Beauty"}
CAT_OVERRIDE = {  # round-1 "Health & Beauty" entries split into the two niches
    "CLF Distribution": "Health & Personal Care",
    "Harrisons Direct (Albert Harrison & Co Ltd)": "Health & Personal Care",
    "Lexon (UK) Ltd": "Health & Personal Care",
    "W Pharma Europe": "Health & Personal Care",
    "Europe Pharma Group B.V.": "Health & Personal Care",
    "Kinetic Natural Product Distributor (Kinetic Enterprises Ltd)": "Health & Personal Care",
    "PB Wholesale (Protein Bargain Wholesale)": "Health & Personal Care",
    "Suma Wholefoods": "Health & Personal Care",
    "DK Wholesale": "General Wholesale / FMCG",
    "West Coast Supply Group": "General Wholesale / FMCG",
}


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
    cell.hyperlink = url.replace(" ", "%20")  # some registry URLs contain spaces
    cell.font = LINK_FONT


def para(ws, r, key, text, height=None):
    ws.cell(row=r, column=2, value=key).font = BOLD
    ws.cell(row=r, column=2).alignment = WRAP
    c = ws.cell(row=r, column=3, value=text)
    c.font = BODY
    c.alignment = WRAP
    if height:
        ws.row_dimensions[r].height = height


# --------------------------------------------------------------------------- data prep
STRONG_EVIDENCE = [
    (r"stock exchange|euronext|nasdaq|NewConnect|frankfurt-listed|\(listed\)|\bplc\b", "listed company"),
    (r"CzechTrade|trade\.gov\.pl|government|ICEX|AICEP|ASEPRI", "government export agency / trade body listing"),
    (r"KRS|IČO|IČ |CIF|NIF|EIK|CUI|CVR|SIREN|LEI|Companies House|KvK|HRB|registry|register|NIP", "company register entry"),
    (r"exhibitor|Interzoo|Ambiente|Spielwarenmesse|Heimtextil|Zoomark|Kind \+ Jugend|ISPO|Cosmoprof|Toy Fair|FIBO|IFA|Paperworld|Creativeworld|Kids' Time", "major trade-fair exhibitor"),
    (r"MHRA|WDA|HPRA|wholesale (dealer )?licen", "regulator licence"),
    (r"subsidiar|group|acquired|owned by|since 19|since 20|founded|established|years", "established brand / group"),
]


def scam_status(s):
    """Legitimacy check result shown in the 'Scam Check' column."""
    n = s["name"]
    if n in SC.CAUTION:
        return "CAUTION - " + SC.CAUTION[n]
    if n in SC.PASS:
        return "PASS (checked) - " + SC.PASS[n]
    if n in SC.WELL_KNOWN:
        return "PASS - well-known company: " + SC.WELL_KNOWN[n]
    txt = " ".join(str(s.get(k, "")) for k in ("legit", "verified", "regid", "stype"))
    for pat, label in STRONG_EVIDENCE:
        if re.search(pat, txt, re.I):
            return "PASS - " + label
    return "CHECK - limited public info: verify registration & bank details before paying"


def normalise(s, rnd):
    s = dict(s)
    s.update(UPDATES.get(s["name"], {}))
    s["cat"] = CAT_OVERRIDE.get(s["name"], CAT_RENAME.get(s["cat"], s["cat"]))
    s.setdefault("amzsell", "Unknown")
    s.setdefault("dropship", "Unknown")
    s.setdefault("regid", "")
    # One primary country per supplier so each country's suppliers sit together.
    parts = [p.strip() for p in s["country"].split("/")]
    if parts[0] in ("EU", "Global (UK site)"):
        s["country"], s["also"] = PAN_EU, ", ".join(p for p in parts if p not in ("EU", "Global (UK site)"))
    else:
        s["country"], s["also"] = parts[0], ", ".join(p for p in parts[1:] if p != "EU")
    s["region"] = "UK" if s["country"] == "UK" else ("Pan-EU" if s["country"] == PAN_EU else "EU / Europe")
    s["round"] = rnd
    s["cost"] = COST_TIER.get(s["country"], "Varies")
    s["scam"] = scam_status(s)
    if s["name"] in SC.PRIORITY_CAP:
        s["pri"] = min(s["pri"], SC.PRIORITY_CAP[s["name"]])
    return s


rows = ([normalise(s, "Round 1") for s in SUPPLIERS] + [normalise(s, "Round 2") for s in SUPPLIERS_EU2]
        + [normalise(s, "Round 3") for s in SUPPLIERS_EU3] + [normalise(s, "Round 4") for s in SUPPLIERS_EU4]
        + [normalise(s, "Round 5") for s in SUPPLIERS_EU5])
rows = [s for s in rows if s["name"] not in REMOVE]
REMOVED = [s for s in rows if s["name"] in SC.FAIL]
rows = [s for s in rows if s["name"] not in SC.FAIL]
# Country A-Z (pan-European platforms last), then Category A-Z, then best priority first.
rows.sort(key=lambda s: (s["country"] == PAN_EU, s["country"], s["cat"], -s["pri"], s["name"].lower()))
COUNTRIES = []
for s_ in rows:
    if s_["country"] not in COUNTRIES:
        COUNTRIES.append(s_["country"])
CATS = sorted({s["cat"] for s in rows})
N = len(rows)
LAST = N + 1

wb = Workbook()

# =========================================================================== Start Here
ws0 = wb.active
ws0.title = "Start Here"
ws0.sheet_view.showGridLines = False
ws0.column_dimensions["A"].width = 3
ws0.column_dimensions["B"].width = 30
ws0.column_dimensions["C"].width = 100
ws0.cell(row=2, column=2, value="Crowsons Distribution - Wholesale Supplier Sourcing List").font = TITLE
ws0.cell(row=3, column=2, value=(
    f"{N} UK & EU suppliers for Amazon UK wholesale across {len(CATS)} niches. Researched Oct 2026.")).font = BODY
r = 5
ws0.cell(row=r, column=2, value="What's new in this version").font = H2
r += 1
for k, v in [
    ("Sorted Country > Category > Priority", "The Suppliers tab is sorted by Country A-Z, then Category A-Z within each country, then Priority (best first). Country is the first column and each country is shaded in alternating bands, so you can work through one country - and one niche - at a time. Pan-European / online platforms are at the bottom."),
    ("Anti-scam check (latest)", "Every wholesaler, trader and marketplace was checked against company registers (Companies House, KvK, KRS, ARES, SIREN...), insolvency notices, regulator fines and independent reviews. 24 suppliers failed (liquidation, dissolved, administration, fines, or no evidence the business exists) and were moved to the 'Removed - Failed Check' tab. Every remaining supplier has a 'Scam Check' result: PASS (green), CHECK (yellow - limited public info, verify before paying) or CAUTION (orange - specific risk noted). The Contact First tab now only lists PASS suppliers."),
    ("Quality check", "Every supplier was re-checked: missing phone numbers, emails, addresses and registry IDs were filled in for ~30 suppliers; 3 suppliers with no verifiable contact or registration were removed; websites we could not confirm are now a click-to-search link; and a new 'Contact First' tab lists the best EU suppliers with a direct phone/email, cheapest countries first."),
    ("Round 5: cheapest-country sourcing", "Round 5 targets the EU countries where stock is cheapest to buy - mainly Poland, Czech Republic, Bulgaria, Romania, the Baltics, Portugal and Greece - and their home-grown manufacturers. Most Round 5 suppliers are verified through a government export agency (CzechTrade, Poland's trade.gov.pl, Bulgarian/Lithuanian registries) or a major trade fair, which is the best protection against fake 'wholesalers'. Round 5 rows are shaded green in the Company column."),
    ("Country Price Level column + Best-Value Countries tab", "Each supplier now shows whether its country is Low-cost, Mid or Higher for buying stock. The new Best-Value Countries tab lists, for every niche, the cheapest EU countries to source from, why, and how many suppliers you already have there."),
    ("Round 4: quality-filtered EU brands", "Round 4 added EU-only suppliers that passed a strict quality bar: identifiable company + proof of establishment (trade-fair exhibitor, official registry, years trading or recognised brand) + a usable contact route. Weak / directory-only leads were left out."),
    ("Country Index tab", "Lists every country with supplier counts - click 'Go to' to jump straight to that country's first row."),
    ("Also operates in", "New column showing other countries a supplier covers (the Country column now holds one main country so the grouping works)."),
    ("Keeping your tracker notes", "If you already filled in the tracker in the previous file, copy the yellow columns across by matching the Company name - or send me the old file and I'll merge it."),
]:
    para(ws0, r, k, v, 32)
    r += 1
r += 1
ws0.cell(row=r, column=2, value="How to use this workbook").font = H2
r += 1
for k, v in [
    ("1. Suppliers", "The master list, grouped by Country A-Z, then Category A-Z, then Priority (5 = best fit for Amazon). Use the filter arrows to filter by Category, Country, Priority or Added."),
    ("1b. Country Index", "Jump to any country's block of suppliers with one click."),
    ("1d. Contact First", "Your shortlist: every priority 4-5 EU supplier with a direct phone/email, cheapest countries first. Start your outreach here."),
    ("1c. Best-Value Countries", "For each niche: the cheapest EU countries to buy from, why, and how many low-cost-country suppliers you already have. Plus anti-scam checks."),
    ("2. Yellow columns", "Your outreach tracker. Status, Method and Account Approved have drop-down lists. 'Suggested Follow-up' fills in automatically (5 working days after Date Contacted) and turns red when overdue."),
    ("3. LinkedIn Outreach", "One-click LinkedIn searches for each company page and its sales / account-manager staff, plus a tracker."),
    ("4. Niche Guide", "Read before contacting suppliers in a new niche - it lists the compliance documents to ask for."),
    ("5. Profit Calculator", "Check every product before ordering. Blue cells are inputs; black cells are formulas."),
    ("6. Templates", "Copy-paste first-contact email, follow-up, LinkedIn notes and invoice / ungating request."),
    ("7. Dashboard", "Live counts by niche, region and outreach status."),
    ("8. Find More Suppliers / Due Diligence", "Directories & trade shows to keep growing the list, and a checklist to vet suppliers before paying."),
]:
    para(ws0, r, k, v)
    r += 1
r += 1
ws0.cell(row=r, column=2, value="Priority score (1-5)").font = H2
r += 1
for k, v in [
    ("5", "Established, branded stock, sells to online / Amazon sellers or provides invoices suitable for ungating. Contact first."),
    ("4", "Established and branded, but may have higher MOQs, selective accounts or a narrower range."),
    ("3", "Credible, worth contacting - confirm terms, online-selling policy and invoice details."),
    ("2", "Lower fit (territory-limited, pro-only brands, limited info) or larger-scale target for later."),
    ("1", "Low confidence, known red flag, or not suitable for Amazon - kept so you know to avoid / verify."),
]:
    para(ws0, r, k, v)
    r += 1
r += 1
ws0.cell(row=r, column=2, value="Data confidence").font = H2
r += 1
for k, v in [
    ("Official / company website", "Details came from the supplier's own site or an official register (Companies House, KRS, MHRA, LEI)."),
    ("Directory / press / trade show", "From trade press, exhibitor lists or business directories - confirm on the company website before relying on them."),
    ("Marketplace / unverified", "Self-published profile only. Verify registration (Companies House / KvK / KRS / VIES VAT) before engaging."),
    ("Blank cells", "Not publicly available. MOQs are usually only shared once a trade account is approved - ask in your first email."),
]:
    para(ws0, r, k, v)
    r += 1
r += 1
ws0.cell(row=r, column=2, value="Key Amazon UK considerations").font = H2
r += 1
for k, v in [
    ("Brand / category gating", "Many brands in fragrance, beauty, toys, baby and health need approval. Amazon wants invoices from a real wholesaler/distributor (not a retailer) dated within 180 days, showing supplier name, address, phone, website, your business details and 10+ units."),
    ("EU suppliers after Brexit", "Buying from the EU means import VAT, possible duty and customs paperwork. Ask for DDP (delivered duty paid) quotes or use a freight forwarder, and get an EORI number. Use the Profit Calculator's freight & duty columns."),
    ("UK product compliance", "Cosmetics need a UK Responsible Person + SCPN notification; toys need UKCA/CE marking + EN71; electricals need UK plugs + UKCA/CE. EU-only labelled stock may not be compliant for the UK."),
    ("Online-selling policies", "Some suppliers forbid Amazon resale (see 'Sells to Online/Amazon Sellers?' column). Ask before applying."),
    ("Hazmat", "Perfume, aerosols, lithium batteries (power tools) and gas canisters are dangerous goods on Amazon - ask suppliers for Safety Data Sheets."),
]:
    para(ws0, r, k, v, 45)
    r += 1
r += 1
ws0.cell(row=r, column=2, value="About LinkedIn outreach").font = H2
r += 1
para(ws0, r, "", (
    "Messages must be sent from your own LinkedIn account. Automation tools break LinkedIn's terms and risk a ban, "
    "so this workbook gives you one-click searches + templates to make manual outreach fast. "
    "Tip: send ~15-25 connection requests per day, personalise the first line, and follow up after 4-5 working days."), 45)

# =========================================================================== Suppliers
ws = wb.create_sheet("Suppliers")
cols = [
    ("Country", 14), ("ID", 6), ("Priority (1-5)", 9), ("Category", 18), ("Company", 30), ("Website", 30),
    ("City / Region", 20), ("Also operates in", 16), ("Region", 10), ("Country Price Level", 12), ("Address", 34), ("Phone", 18), ("Email", 28), ("Supplier Type", 20),
    ("Key Brands / Products", 38), ("Segment", 20), ("MOQ / Min. Order", 22), ("Account Requirements", 28),
    ("Ships to UK?", 18), ("Sells to Online/Amazon Sellers?", 16), ("Dropship?", 11), ("Registry ID", 18),
    ("Legitimacy Evidence", 34), ("Amazon Fit Notes", 36), ("Notes / Red Flags", 36), ("Data Confidence", 22), ("Scam Check (Oct 2026)", 40),
    ("Source", 13), ("LinkedIn Company Search", 15), ("Added", 10),
    # tracker
    ("Status", 18), ("Date Contacted", 13), ("Method", 13), ("Contact Name", 18), ("Response / Notes", 30),
    ("Suggested Follow-up", 13), ("Account Approved?", 12), ("Next Step", 26),
]
C = {name: get_column_letter(i) for i, (name, _) in enumerate(cols, start=1)}
COLN = {name: i for i, (name, _) in enumerate(cols, start=1)}
TRACK_START = COLN["Status"]
header_row(ws, 1, [c[0] for c in cols], [c[1] for c in cols],
           {i: TRACK_HDR_FILL for i in range(TRACK_START, len(cols) + 1)})

for i, s in enumerate(rows, start=1):
    r = i + 1
    vals = {
        "ID": i, "Priority (1-5)": s["pri"], "Category": s["cat"], "Region": s["region"], "Country Price Level": s["cost"], "Company": s["name"],
        "Country": s["country"], "City / Region": s["city"], "Also operates in": s["also"], "Address": s["addr"], "Phone": s["phone"],
        "Email": s["email"], "Supplier Type": s["stype"], "Key Brands / Products": s["brands"],
        "Segment": s["segment"], "MOQ / Min. Order": s["moq"], "Account Requirements": s["req"],
        "Ships to UK?": s["uk"], "Sells to Online/Amazon Sellers?": s["amzsell"], "Dropship?": s["dropship"],
        "Registry ID": s["regid"], "Legitimacy Evidence": s["legit"], "Amazon Fit Notes": s["amazon"],
        "Notes / Red Flags": s["notes"], "Data Confidence": s["verified"], "Scam Check (Oct 2026)": s["scam"], "Added": s["round"],
        "Status": "Not contacted",
        "Suggested Follow-up": f'=IF({C["Date Contacted"]}{r}="","",WORKDAY({C["Date Contacted"]}{r},5))',
    }
    for name, col in COLN.items():
        c = ws.cell(row=r, column=col, value=vals.get(name))
        c.font = BODY
        c.alignment = WRAP
        c.border = BORDER
        if col >= TRACK_START:
            c.fill = TRACK_FILL
    if s["round"] == LATEST_ROUND:
        ws.cell(row=r, column=COLN["Company"]).fill = NEW_FILL
    band = BAND_FILLS[COUNTRIES.index(s["country"]) % 2]
    for nm in ("Country", "ID"):
        ws.cell(row=r, column=COLN[nm]).fill = band
    ws.cell(row=r, column=COLN["Country"]).font = BOLD
    if i == 1 or rows[i - 2]["country"] != s["country"]:  # thick line where a new country starts
        for col in range(1, len(cols) + 1):
            cell = ws.cell(row=r, column=col)
            cell.border = Border(left=THIN, right=THIN, bottom=THIN, top=Side(style="medium", color=NAVY))
    if s["web"]:
        set_link(ws.cell(row=r, column=COLN["Website"]), s["web"])
    else:
        set_link(ws.cell(row=r, column=COLN["Website"]),
                 "https://www.google.com/search?q=" + quote_plus(f'{s["name"]} {s["country"]} official website'),
                 "Not confirmed - click to search")
    set_link(ws.cell(row=r, column=COLN["Source"]), s["src"], "Source link")
    set_link(ws.cell(row=r, column=COLN["LinkedIn Company Search"]), linkedin_company(s["name"]), "Search LinkedIn")
    ws.cell(row=r, column=COLN["Priority (1-5)"]).alignment = Alignment(horizontal="center", vertical="top")
    ws.cell(row=r, column=COLN["Date Contacted"]).number_format = "dd/mm/yyyy"
    ws.cell(row=r, column=COLN["Suggested Follow-up"]).number_format = "dd/mm/yyyy"

ws.freeze_panes = "F2"
ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{LAST}"

for formula, col, kind in [
    ('"' + ",".join(STATUSES) + '"', "Status", "list"),
    ('"' + ",".join(METHODS) + '"', "Method", "list"),
    ('"Yes,No,Pending"', "Account Approved?", "list"),
]:
    dv = DataValidation(type=kind, formula1=formula, allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{C[col]}2:{C[col]}{LAST}")
dv_date = DataValidation(type="date", operator="greaterThan", formula1="DATE(2020,1,1)", allow_blank=True)
ws.add_data_validation(dv_date)
dv_date.add(f'{C["Date Contacted"]}2:{C["Date Contacted"]}{LAST}')

P = C["Priority (1-5)"]
for val, color in [("5", "63BE7B"), ("4", "B1D580"), ("1", "F8696B")]:
    ws.conditional_formatting.add(f"{P}2:{P}{LAST}", CellIsRule(operator="equal", formula=[val],
                                                                fill=PatternFill("solid", fgColor=color)))
FU, ST = C["Suggested Follow-up"], C["Status"]
ws.conditional_formatting.add(
    f"{FU}2:{FU}{LAST}",
    FormulaRule(formula=[f'AND({FU}2<>"",{FU}2<=TODAY(),OR({ST}2="Contacted",{ST}2="Follow-up sent"))'],
                fill=PatternFill("solid", fgColor="F8696B"), font=Font(name=FONT, bold=True, color="FFFFFF")))
SCK = C["Scam Check (Oct 2026)"]
for prefix, color in [("PASS", "C6EFCE"), ("CHECK", "FFEB9C"), ("CAUTION", "F8CBAD")]:
    ws.conditional_formatting.add(f"{SCK}2:{SCK}{LAST}", FormulaRule(
        formula=[f'LEFT({SCK}2,{len(prefix)})="{prefix}"'], fill=PatternFill("solid", fgColor=color)))
CL = C["Country Price Level"]
for val, color in [("Low-cost", "C6EFCE"), ("Mid", "FFEB9C")]:
    ws.conditional_formatting.add(f"{CL}2:{CL}{LAST}", CellIsRule(operator="equal", formula=[f'"{val}"'],
                                                                  fill=PatternFill("solid", fgColor=color)))
NT, AF, AS = C["Notes / Red Flags"], C["Amazon Fit Notes"], C["Sells to Online/Amazon Sellers?"]
ws.conditional_formatting.add(
    f"{NT}2:{NT}{LAST}",
    FormulaRule(formula=[f'OR(ISNUMBER(SEARCH("RED FLAG",{NT}2)),ISNUMBER(SEARCH("NOT SUITABLE",{AF}2)))'],
                fill=PatternFill("solid", fgColor="FCE4D6")))
ws.conditional_formatting.add(
    f"{AS}2:{AS}{LAST}",
    FormulaRule(formula=[f'ISNUMBER(SEARCH("Yes",{AS}2))'], fill=PatternFill("solid", fgColor="C6EFCE")))
ws.conditional_formatting.add(
    f"{AS}2:{AS}{LAST}",
    FormulaRule(formula=[f'ISNUMBER(SEARCH("estrict",{AS}2))'], fill=PatternFill("solid", fgColor="FFC7CE")))

# =========================================================================== LinkedIn Outreach
wl = wb.create_sheet("LinkedIn Outreach")
lcols = [("Country", 14), ("ID", 6), ("Company", 32), ("Category", 18), ("Company Page Search", 16),
         ("Find Sales / Account Managers", 20), ("Person Name", 20), ("Job Title", 20), ("Profile URL", 28),
         ("Connection Sent", 12), ("Accepted?", 10), ("Message Sent", 12), ("Reply?", 10), ("Notes", 34)]
header_row(wl, 1, [c[0] for c in lcols], [c[1] for c in lcols],
           {i: TRACK_HDR_FILL for i in range(7, len(lcols) + 1)})
for i, s in enumerate(rows, start=1):
    r = i + 1
    for col, src in enumerate(["Country", "ID", "Company", "Category"], start=1):
        c = wl.cell(row=r, column=col, value=f"=Suppliers!{C[src]}{r}")
        c.font = LINKED_FONT
        c.border = BORDER
        c.alignment = WRAP
    set_link(wl.cell(row=r, column=5), linkedin_company(s["name"]), "Company page")
    set_link(wl.cell(row=r, column=6), linkedin_people(s["name"]), "Find people")
    for col in (5, 6):
        wl.cell(row=r, column=col).border = BORDER
    for col in range(7, len(lcols) + 1):
        c = wl.cell(row=r, column=col)
        c.fill = TRACK_FILL
        c.border = BORDER
        c.font = BODY
        c.alignment = WRAP
    for col in (10, 12):
        wl.cell(row=r, column=col).number_format = "dd/mm/yyyy"
wl.freeze_panes = "C2"
wl.auto_filter.ref = f"A1:{get_column_letter(len(lcols))}{LAST}"
dv_yn = DataValidation(type="list", formula1='"Yes,No,Pending"', allow_blank=True)
wl.add_data_validation(dv_yn)
dv_yn.add(f"K2:K{LAST}")
dv_yn.add(f"M2:M{LAST}")

# =========================================================================== Niche Guide
# =========================================================================== Country Index
wc = wb.create_sheet("Country Index")
ccols = [("Country", 24), ("Suppliers", 11), ("Priority 4-5", 11), ("Niches covered", 70), ("Jump to list", 14),
         ("Price Level", 14)]
header_row(wc, 1, [c[0] for c in ccols], [c[1] for c in ccols])
crng = f'Suppliers!${C["Country"]}$2:${C["Country"]}${LAST}'
cpr = f'Suppliers!${C["Priority (1-5)"]}$2:${C["Priority (1-5)"]}${LAST}'
for k, country in enumerate(COUNTRIES):
    r = k + 2
    first_row = next(i for i, s_ in enumerate(rows, start=2) if s_["country"] == country)
    niches = sorted({s_["cat"] for s_ in rows if s_["country"] == country})
    vals = [country, f'=COUNTIF({crng},A{r})', f'=COUNTIFS({crng},A{r},{cpr},">=4")', ", ".join(niches)]
    for col, v in enumerate(vals, start=1):
        c = wc.cell(row=r, column=col, value=v)
        c.font = BOLD if col == 1 else BODY
        c.alignment = WRAP
        c.border = BORDER
        c.fill = BAND_FILLS[k % 2] if col == 1 else PatternFill()
    link = wc.cell(row=r, column=5, value="Go to >")
    link.hyperlink = f"#Suppliers!A{first_row}"
    link.font = LINK_FONT
    link.border = BORDER
    pl = wc.cell(row=r, column=6, value=COST_TIER.get(country, "Varies"))
    pl.font = BODY
    pl.border = BORDER
    if pl.value == "Low-cost":
        pl.fill = PatternFill("solid", fgColor="C6EFCE")
    elif pl.value == "Mid":
        pl.fill = PatternFill("solid", fgColor="FFEB9C")
tr = len(COUNTRIES) + 2
wc.cell(row=tr, column=1, value="Total").font = BOLD
wc.cell(row=tr, column=2, value=f"=SUM(B2:B{tr - 1})").font = BOLD
wc.cell(row=tr, column=3, value=f"=SUM(C2:C{tr - 1})").font = BOLD
wc.freeze_panes = "A2"

# =========================================================================== Best-Value Countries
wv = wb.create_sheet("Best-Value Countries")
wv.sheet_view.showGridLines = False
wv.cell(row=1, column=1, value="Where to buy each niche cheapest in the EU").font = TITLE
wv.cell(row=2, column=1, value=(
    "Guide only - always compare landed cost (unit price + freight + duty/VAT) in the Profit Calculator. "
    "Low-cost countries are cheapest for their OWN manufacturers' brands; big international brands are often "
    "cheapest from large German / Dutch distributors because of volume. 'On your list' counts are live formulas.")).font = BODY
wv.merge_cells("A2:F2")
wv.cell(row=2, column=1).alignment = WRAP
wv.row_dimensions[2].height = 42
vcols = [("Niche", 22), ("Cheapest EU countries (best first)", 30), ("Why it's cheaper there", 52),
         ("Good brands / makers to start with", 46), ("On your list: Low-cost countries", 16), ("On your list: total", 12)]
header_row(wv, 4, [c[0] for c in vcols], [c[1] for c in vcols])
BEST_VALUE = [
    ("Baby Products", "Poland, Spain, Lithuania",
     "Poland is a major nursery-goods producer with low labour costs (bottles, teethers, prams, car seats). Spain has big feeding/soother makers at mid prices.",
     "Canpol babies, BabyOno, Lionelo, Kinderkraft (PL); Suavinex, Jané (ES)"),
    ("Beauty", "Poland, Bulgaria, Czech Republic, Romania, Spain",
     "Poland has one of Europe's largest cosmetics industries with very low unit prices; Bulgaria is cheapest for rose-based products; Czech & Romanian brands are cheap with little UK competition.",
     "Ziaja, Eveline, Bielenda, Farmona, Delia (PL); Bulgarian Rose, Lema (BG); Dermacol, Manufaktura (CZ); Gerovital (RO)"),
    ("DIY & Tools", "Poland, Czech Republic, Spain",
     "Polish tool groups (TOYA/YATO, GTX/NEO, Dedra) import and assemble at scale and sell well below German brand prices.",
     "TOYA/YATO, GTX Poland, Dedra, Logo-Tools (PL); Bellota, EGA Master (ES)"),
    ("Fragrance", "Poland, Spain, Netherlands/Germany (distributors)",
     "Polish & Spanish fragrance houses make cheap 'inspired' and own-brand lines; genuine designer fragrance is usually cheapest from large NL/DE distributors - but check authenticity and invoices carefully.",
     "Parfum Company (PL); Instituto Español (ES); verified NL/DE distributors only"),
    ("General Wholesale / FMCG", "Poland, Netherlands, Germany",
     "Poland for cheap local FMCG; NL/DE for large multi-brand distributors and clearance stock.",
     "Check Due Diligence tab before any clearance / stock-lot deal"),
    ("Health & Personal Care", "Poland, Hungary, Czech Republic",
     "Poland & Hungary are big sports-nutrition producers (Olimp, Trec, BioTechUSA); Czech makers are cheap for oral care & brushes.",
     "Olimp, Trec (PL); BioTechUSA (HU); Nutrend, Spokar, Alpa (CZ)"),
    ("Home & Kitchen", "Poland, Czech Republic, Portugal",
     "Low manufacturing costs for cookware, cleaning tools, kitchen utensils and storage; Portugal is cheap for cookware, ceramics and textiles.",
     "Gerlach, Konex, Homla (PL); Tescoma, BLEX, Dřevotvar (CZ); Silampos (PT)"),
    ("Pet Supplies", "Poland, Czech Republic, Spain",
     "Poland is a major pet food & accessories producer (86-88% of its pet food is exported within the EU); Spanish & Italian accessory makers are mid-priced.",
     "Dingo, Vitapol, DermaPharm (PL); Funky Dog (CZ); Gaun (ES); Georplast (IT)"),
    ("Sports & Outdoors", "Poland, Czech Republic, Spain",
     "Polish fitness/sports accessory brands are cheap and well known in Central Europe; Spain for padel & fitness accessories.",
     "Spokey, Meteor, Bacha Sport (PL); Softee/Jim Sports (ES)"),
    ("Stationery & Office", "Poland, Czech Republic, Spain, Portugal",
     "Local paper & stationery industries with low costs; Spain's APLI & MILAN are cheap for labels and school supplies.",
     "Interdruk (PL); KOH-I-NOOR (CZ); APLI, MILAN (ES); Bi-silque (PT)"),
    ("Toys & Games", "Poland, Czech Republic, Spain",
     "Poland & Czechia make puzzles and board games cheaply in-house (Trefl, Dino); Spain's Ibi/Onil toy cluster for dolls, ride-ons and outdoor toys.",
     "Trefl, COBI, Wader, Granna (PL); Dino Toys, Albi (CZ); Miniland, Colorbaby, Famosa (ES)"),
    ("B2B Marketplace", "Varies",
     "Marketplaces aggregate many sellers - prices vary by seller. Verify each seller's company registration and VAT number.",
     "See Due Diligence tab"),
]
crng_v = f'Suppliers!${C["Category"]}$2:${C["Category"]}${LAST}'
cl_v = f'Suppliers!${C["Country Price Level"]}$2:${C["Country Price Level"]}${LAST}'
r = 5
for niche, ctys, why, brands in BEST_VALUE:
    if niche not in CATS:
        continue
    vals = [niche, ctys, why, brands, f'=COUNTIFS({crng_v},A{r},{cl_v},"Low-cost")', f'=COUNTIF({crng_v},A{r})']
    for col, v in enumerate(vals, start=1):
        c = wv.cell(row=r, column=col, value=v)
        c.font = BOLD if col == 1 else BODY
        c.alignment = WRAP
        c.border = BORDER
    wv.cell(row=r, column=2).fill = PatternFill("solid", fgColor="C6EFCE")
    wv.row_dimensions[r].height = 58
    r += 1
r += 1
wv.cell(row=r, column=1, value="Avoiding scammers when buying cheap").font = H2
r += 1
for tip in [
    "Prices far below every other quote are the #1 warning sign - genuine low-cost countries are cheaper, not 70% cheaper.",
    "Check the company on the official register: Poland KRS/CEIDG, Czech ARES/justice.cz, Bulgaria Commercial Register (EIK), Romania ONRC, Lithuania Registrų centras, Spain Registro Mercantil, Portugal NIF. Then check the VAT number on the EU VIES site.",
    "Prefer suppliers listed by a government export agency (CzechTrade, trade.gov.pl / PAIH, ICEX, AICEP) or exhibiting at major trade fairs - these are noted in the Legitimacy Evidence column.",
    "Bank details must be in the company's own name and country. Never pay a personal account, crypto, or a 'new' bank account sent by email - phone the supplier on a number from their website to confirm.",
    "Start with a small test order, ask for an invoice that meets Amazon's requirements, and use a card or escrow-style payment where possible for the first order.",
]:
    c = wv.cell(row=r, column=1, value="- " + tip)
    c.font = BODY
    c.alignment = WRAP
    wv.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    wv.row_dimensions[r].height = 30
    r += 1
wv.freeze_panes = "A5"

# =========================================================================== Contact First
# Shortlist: priority 4-5 EU suppliers with a direct phone/email, cheapest countries first.
TIER_ORDER = {"Low-cost": 0, "Mid": 1, "Higher": 2}
picks = [(i + 2, s_) for i, s_ in enumerate(rows)
         if s_["pri"] >= 4 and s_["cost"] in TIER_ORDER and s_["scam"].startswith("PASS") and ("@" in s_["email"] or any(ch.isdigit() for ch in s_["phone"]))]
picks.sort(key=lambda t: (TIER_ORDER[t[1]["cost"]], t[1]["country"], t[1]["cat"], -t[1]["pri"], t[1]["name"].lower()))
wk = wb.create_sheet("Contact First")
wk.cell(row=1, column=1, value="Contact First - best EU suppliers with a direct phone or email").font = TITLE
wk.cell(row=2, column=1, value=(
    f"{len(picks)} priority 4-5 EU suppliers that passed the scam check and list a phone number or email, ordered cheapest country first "
    "(Low-cost > Mid > Higher), then country and niche. Status updates live from the Suppliers tab - "
    "click 'Open row' to log your outreach there.")).font = BODY
wk.merge_cells("A2:J2")
wk.cell(row=2, column=1).alignment = WRAP
wk.row_dimensions[2].height = 30
kcols = [("Price Level", 12), ("Country", 14), ("Category", 20), ("Priority", 8), ("Company", 34), ("Phone", 22),
         ("Email", 32), ("Key Brands / Products", 44), ("Status (live)", 16), ("Go to", 10)]
header_row(wk, 4, [c[0] for c in kcols], [c[1] for c in kcols])
for k, (srow, s_) in enumerate(picks):
    r = k + 5
    vals = [s_["cost"], s_["country"], s_["cat"], s_["pri"], s_["name"], s_["phone"], s_["email"], s_["brands"],
            f'=Suppliers!{C["Status"]}{srow}']
    for col, v in enumerate(vals, start=1):
        c = wk.cell(row=r, column=col, value=v)
        c.font = LINKED_FONT if col == 9 else BODY
        c.alignment = WRAP
        c.border = BORDER
    wk.cell(row=r, column=1).fill = PatternFill("solid", fgColor={"Low-cost": "C6EFCE", "Mid": "FFEB9C"}.get(s_["cost"], "F2F2F2"))
    link = wk.cell(row=r, column=10, value="Open row >")
    link.hyperlink = f"#Suppliers!A{srow}"
    link.font = LINK_FONT
    link.border = BORDER
wk.freeze_panes = "F5"
wk.auto_filter.ref = f"A4:{get_column_letter(len(kcols))}{len(picks) + 4}"

wn = wb.create_sheet("Niche Guide")
ncols = [("Niche", 22), ("Suppliers in list", 11), ("Priority 4-5", 10), ("Amazon UK gating (check Seller Central)", 42),
         ("Compliance / documents to ask for", 46), ("What tends to sell", 40), ("Sourcing tips", 44)]
header_row(wn, 1, [c[0] for c in ncols], [c[1] for c in ncols])
NICHE = {
    "Fragrance": ("Many designer brands are brand-gated. Fragrance is also hazmat (flammable).",
                  "Safety Data Sheet (SDS) per product for hazmat review; sealed retail stock only (no testers); UK RP on pack.",
                  "Designer gift sets (Q4), Arabian brands (Lattafa, Armaf), mass fragrance & body sprays.",
                  "Arabian-brand distributors are often easier to get approved with; ask designer wholesalers for authorised-distributor invoices."),
    "Beauty": ("Many brands gated; prestige/luxury beauty is the hardest. Some topical products need approval.",
               "UK Responsible Person + SCPN notification; batch codes & expiry/PAO; INCI ingredients; CPNP for EU stock.",
               "K-beauty (COSRX, Beauty of Joseon, Anua), derma skincare (CeraVe), mass cosmetics, hair care.",
               "Counterfeits are common in CeraVe/The Ordinary - insist on authorised-distributor proof. Pro-salon brands usually ban Amazon."),
    "Health & Personal Care": ("Some brands gated; supplements, OTC medicines and topicals face extra scrutiny.",
                               "Supplements: label compliance & batch CoA; GSL medicines: MHRA rules; electrical grooming: UKCA/CE.",
                               "Oral care, shaving, deodorants, vitamins, sports nutrition, first aid.",
                               "Sports nutrition and first aid are strong for wholesale; check expiry dates for FBA (min. shelf life)."),
    "Baby Products": ("Category and many brands may need approval; formula, car seats & safety items are high scrutiny.",
                      "EN/BS safety standards (e.g. EN 14350 feeding, EN 1888 pushchairs), UKCA/CE, age warnings.",
                      "Feeding bottles, dummies, teethers, nappies, baby toiletries, monitors.",
                      "Avoid infant formula and car seats until established; feeding & soothers (MAM, Tommee Tippee) are steady sellers."),
    "Toys & Games": ("Brand-gated (LEGO, Disney, Hasbro, Mattel). Amazon has restricted new sellers in Q4 in past years.",
                     "UKCA/CE marking, EN71 test reports, age & small-parts warnings, UK importer address on pack.",
                     "Board games, LEGO-licensed goods, collectibles (Funko), pocket-money toys, licensed character toys.",
                     "Official UK distributors (A.B. Gee, Wind Designs) give the best invoices; board games via EPN are low-risk."),
    "Pet Supplies": ("Mostly open; some major brands restricted.",
                     "Pet food: labelling & expiry; accessories: general product safety.",
                     "Toys (KONG, Trixie), grooming, beds, treats, cat litter accessories.",
                     "Trixie sells direct to retailers with a UK warehouse - good first call. Heavy bulky food has high FBA fees."),
    "Home & Kitchen": ("Largely ungated; some premium brands restricted.",
                       "Electricals: UKCA/CE + UK plug + WEEE; food-contact materials compliance for kitchenware.",
                       "Small appliances (Tower, Swan, Kenwood), storage, kitchen gadgets, cookware.",
                       "Brand owners like RKW (Tower/Swan) supply directly; watch MAP pricing on premium cookware."),
    "DIY & Tools": ("Mostly ungated; big power-tool brands (DeWalt, Makita, Bosch) are often restricted.",
                    "Lithium batteries = hazmat (SDS / UN38.3); UKCA/CE for power tools; UK plugs.",
                    "Hand tools, accessories & consumables, garage/workshop, cordless tool kits.",
                    "Toolbank is trade-only for resellers; Draper has a stockist programme with brand-direct invoices."),
    "Sports & Outdoors": ("Mostly ungated; branded apparel/footwear (Nike, adidas) often restricted.",
                          "Gas canisters & some fuels are hazmat; bike parts safety; fitness equipment weight = high FBA fees.",
                          "Home fitness accessories, cycling accessories, camping gear, team sports.",
                          "Small/light items (bike accessories, resistance bands) work best for FBA fees."),
    "Stationery & Office": ("Largely ungated.",
                            "Ink/toner: counterfeit risk - originals only from authorised distributors; art materials: toy-safety if for children.",
                            "Branded pens (Pilot, BIC, Stabilo), notebooks, art supplies, school supplies, labels.",
                            "Low price points - bundle/multipacks to beat FBA fees."),
    "General Wholesale / FMCG": ("Grocery may need approval; FMCG brands vary.",
                                 "Expiry dates (FBA min. remaining shelf life), batch codes.",
                                 "Household cleaning, toiletries, confectionery, multipacks.",
                                 "Cash & carry promotions can work for arbitrage-style wholesale; margins are thin."),
    "B2B Marketplace": ("Depends on brand.", "Ask platform for commercial invoices + compliance docs per product.",
                        "Branded H&B (Qogita), FMCG (Parallel), general merchandise (BigBuy, zentrada).",
                        "Fastest way to test a niche with low MOQs; liquidation platforms are not suitable for 'New' Amazon listings."),
}
r = 2
for cat in CATS:
    g = NICHE.get(cat, ("", "", "", ""))
    vals = [cat, f'=COUNTIF(Suppliers!${C["Category"]}$2:${C["Category"]}${LAST},A{r})',
            f'=COUNTIFS(Suppliers!${C["Category"]}$2:${C["Category"]}${LAST},A{r},Suppliers!${P}$2:${P}${LAST},">=4")', *g]
    for col, v in enumerate(vals, start=1):
        c = wn.cell(row=r, column=col, value=v)
        c.font = BOLD if col == 1 else BODY
        c.alignment = WRAP
        c.border = BORDER
    wn.row_dimensions[r].height = 62
    r += 1
wn.freeze_panes = "B2"
wn.cell(row=r + 1, column=1, value=(
    "Gating rules change often - always confirm in Seller Central (Add a Product > search ASIN > 'Request approval').")).font = Font(name=FONT, size=9, italic=True)

# =========================================================================== Profit Calculator
wp = wb.create_sheet("Profit Calculator")
wp.sheet_view.showGridLines = False
wp.cell(row=1, column=1, value="Profit Calculator - Amazon UK (FBA)").font = TITLE
wp.cell(row=2, column=1, value="Blue = your inputs. Black = formulas. Assumes you are VAT-registered (input VAT reclaimed, fees shown ex VAT).").font = Font(name=FONT, size=9, italic=True)
settings = [
    ("EUR to GBP rate", 0.85, "0.0000", "Placeholder - update to today's rate (e.g. from xe.com) before using."),
    ("UK VAT rate", 0.20, "0%", "Standard UK VAT rate. Some baby/children's items are zero-rated - adjust per row."),
    ("Default referral fee", 0.15, "0%", "Typical Amazon UK referral fee; varies by category (check Amazon's fee schedule)."),
    ("Target ROI", 0.30, "0%", "Your minimum ROI to buy. Change to suit your strategy."),
]
for i, (label, val, fmt, note) in enumerate(settings):
    rr = 4 + i
    wp.cell(row=rr, column=1, value=label).font = BOLD
    c = wp.cell(row=rr, column=2, value=val)
    c.font = INPUT_FONT
    c.number_format = fmt
    c.fill = TRACK_FILL
    c.comment = Comment(note, "Crowsons")
    wp.cell(row=rr, column=3, value=note).font = Font(name=FONT, size=9, color="595959")
FX, VAT, REF, ROI = "$B$4", "$B$5", "$B$6", "$B$7"

pcols = [("Product", 26), ("Supplier", 20), ("ASIN", 13), ("Unit cost (supplier ccy, ex VAT)", 13), ("Currency", 9),
         ("FX to GBP", 9), ("Unit cost £", 10), ("Freight / unit £", 10), ("Import duty %", 9), ("Duty £", 9),
         ("Prep / other £", 9), ("Landed cost £", 11), ("Sell price inc VAT £", 11), ("VAT rate", 8),
         ("Sell price ex VAT £", 11), ("Referral %", 9), ("Referral fee £", 10), ("FBA fee £", 9),
         ("Storage / other fees £", 10), ("Net profit £", 11), ("ROI", 9), ("Margin", 9),
         ("Break-even price inc VAT £", 12), ("Verdict", 10)]
HR = 10
header_row(wp, HR, [c[0] for c in pcols], [c[1] for c in pcols])
wp.row_dimensions[HR].height = 45
INPUT_COLS = {"A", "B", "C", "D", "E", "H", "I", "K", "M", "N", "P", "R", "S"}
examples = [
    ["Example: Arabian EDP 100ml", "BJUTIP a.s.", "B0EXAMPLE1", 12.50, "EUR", None, None, 0.60, 0.0, None, 0.30,
     None, 32.99, None, None, None, None, 3.40, 0.15],
    ["Example: Pet toy (UK supplier)", "Pedigree Wholesale", "B0EXAMPLE2", 4.20, "GBP", None, None, 0.25, 0.0, None, 0.10,
     None, 12.99, None, None, None, None, 2.90, 0.05],
]
FIRST, LASTP = HR + 1, HR + 40
for r in range(FIRST, LASTP + 1):
    f = {
        "F": f'=IF(D{r}="","",IF(E{r}="EUR",{FX},1))',
        "G": f'=IF(D{r}="","",D{r}*F{r})',
        "J": f'=IF(D{r}="","",(G{r}+H{r})*I{r})',
        "L": f'=IF(D{r}="","",G{r}+H{r}+J{r}+K{r})',
        "N": f'=IF(M{r}="","",{VAT})',
        "O": f'=IF(M{r}="","",M{r}/(1+N{r}))',
        "P": f'=IF(M{r}="","",{REF})',
        "Q": f'=IF(M{r}="","",M{r}*P{r})',
        "T": f'=IF(OR(D{r}="",M{r}=""),"",O{r}-L{r}-Q{r}-R{r}-S{r})',
        "U": f'=IF(T{r}="","",IF(L{r}=0,"",T{r}/L{r}))',
        "V": f'=IF(T{r}="","",T{r}/O{r})',
        "W": f'=IF(OR(D{r}="",M{r}=""),"",IF((1/(1+N{r})-P{r})<=0,"",(L{r}+R{r}+S{r})/(1/(1+N{r})-P{r})))',
        "X": f'=IF(U{r}="","",IF(U{r}>={ROI},"BUY","SKIP"))',
    }
    ex = examples[r - FIRST] if r - FIRST < len(examples) else None
    for ci in range(1, len(pcols) + 1):
        L = get_column_letter(ci)
        c = wp.cell(row=r, column=ci)
        if L in f:
            c.value = f[L]
            c.font = BODY
        else:
            if ex is not None and ex[ci - 1] is not None:
                c.value = ex[ci - 1]
            c.font = INPUT_FONT
            c.fill = TRACK_FILL
        c.border = BORDER
        if L in {"D", "G", "H", "J", "K", "L", "M", "O", "Q", "R", "S", "T", "W"}:
            c.number_format = '£#,##0.00;[Red]-£#,##0.00;-' if L != "D" else '#,##0.00'
        if L in {"I", "N", "P", "U", "V"}:
            c.number_format = '0.0%;[Red]-0.0%;-'
        if L == "F":
            c.number_format = "0.0000"
# Rows that use default VAT/referral still let the user overwrite N/P with a value.
for r in range(FIRST, LASTP + 1):
    for L in ("N", "P"):
        wp[f"{L}{r}"].fill = TRACK_FILL
dv_ccy = DataValidation(type="list", formula1='"GBP,EUR"', allow_blank=True)
wp.add_data_validation(dv_ccy)
dv_ccy.add(f"E{FIRST}:E{LASTP}")
wp.conditional_formatting.add(f"X{FIRST}:X{LASTP}", CellIsRule(operator="equal", formula=['"BUY"'],
                              fill=PatternFill("solid", fgColor="C6EFCE"), font=Font(name=FONT, bold=True, color="006100")))
wp.conditional_formatting.add(f"X{FIRST}:X{LASTP}", CellIsRule(operator="equal", formula=['"SKIP"'],
                              fill=PatternFill("solid", fgColor="FFC7CE"), font=Font(name=FONT, bold=True, color="9C0006")))
wp.freeze_panes = f"B{FIRST}"
wp.cell(row=LASTP + 2, column=1, value=(
    "Notes: rows 11-12 are examples with made-up prices - overwrite them. FBA fee: use Amazon's Revenue Calculator for the ASIN. "
    "Import duty: look up the commodity code on the UK Trade Tariff (gov.uk/trade-tariff); EU-origin goods may qualify for 0% under the UK-EU TCA with proof of origin. "
    "VAT & Referral columns default from the settings above - type over them per product if different.")).font = Font(name=FONT, size=9, italic=True)
wp.merge_cells(start_row=LASTP + 2, start_column=1, end_row=LASTP + 2, end_column=14)
wp.cell(row=LASTP + 2, column=1).alignment = WRAP
wp.row_dimensions[LASTP + 2].height = 48

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
     "We sell branded [category] to UK customers through our online channels, including Amazon UK.\n\n"
     "We're looking for reliable, long-term suppliers and would like to open a trade account with [Company]. Could you please let me know:\n"
     "  1. Your trade account application process and requirements\n"
     "  2. Minimum order quantity / minimum order value\n"
     "  3. Current price list or stock list\n"
     "  4. Payment terms and delivery options to the UK\n"
     "  5. Whether you're happy to supply retailers who sell online / on marketplaces\n\n"
     "We place repeat orders on lines that sell well, and we're happy to start with a test order.\n\n"
     "Kind regards,\n[Your Name]\nCrowsons Distribution\n[Phone] | [Email] | [Website]"),
    ("Email 1b - EU supplier version", "Subject: Trade account enquiry - UK online retailer (delivery to UK)",
     "Hello [Name / Sales Team],\n\n"
     "I'm [Your Name] from Crowsons Distribution, a UK-registered online retailer (Company No. [xxxx], UK VAT No. [xxxx], EORI [GBxxxx]). "
     "We'd like to open a trade account with [Company] for [category].\n\n"
     "Could you please share:\n"
     "  1. Your account requirements and minimum order value\n"
     "  2. Your price list / stock list\n"
     "  3. Whether you deliver to the UK - ideally DDP (delivered duty paid) or with export paperwork (commercial invoice, statement of origin)\n"
     "  4. Whether products are labelled/compliant for the UK market (UK Responsible Person / UKCA where relevant)\n"
     "  5. Whether you supply retailers selling on online marketplaces\n\n"
     "Happy to start with a trial order. English is easiest for us, but we can work with a translated message if preferred.\n\n"
     "Best regards,\n[Your Name]\nCrowsons Distribution\n[Phone] | [Email] | [Website]"),
    ("Email 2 - Follow-up (5 working days)", "Subject: Re: Trade account enquiry - Crowsons Distribution",
     "Hi [Name],\n\nJust following up on my email from [day] about opening a trade account. "
     "We're keen to place an initial order in the next few weeks - is there a price list or application form you could share?\n\n"
     "If there's a better person to speak to, I'd be grateful if you could point me in the right direction.\n\n"
     "Thanks,\n[Your Name]"),
    ("LinkedIn connection note (max 300 chars)", "",
     "Hi [First name], I run Crowsons Distribution, a UK online retailer of branded [category]. "
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
     "If available, could you also send Safety Data Sheets (SDS) / compliance documents for the products?\n\n"
     "Many thanks,\n[Your Name]"),
]
r = 4
for title, subj, body in templates:
    wt.cell(row=r, column=2, value=title).font = H2
    if subj:
        wt.cell(row=r, column=3, value=subj).font = BOLD
        r += 1
    c = wt.cell(row=r, column=3, value=body)
    c.font = BODY
    c.alignment = WRAP
    c.fill = PatternFill("solid", fgColor="F2F2F2")
    wt.row_dimensions[r].height = max(45, 15 * (body.count("\n") + 2 + len(body) // 110))
    r += 2

# =========================================================================== Dashboard
wd = wb.create_sheet("Dashboard")
wd.sheet_view.showGridLines = False
wd.column_dimensions["A"].width = 3
wd.column_dimensions["B"].width = 28
for col in "CDEFGHI":
    wd.column_dimensions[col].width = 14
wd.cell(row=2, column=2, value="Outreach dashboard").font = TITLE
wd.cell(row=3, column=2, value="All figures are formulas linked to the Suppliers tab.").font = BODY

rng = f'Suppliers!${C["Category"]}$2:${C["Category"]}${LAST}'
reg = f'Suppliers!${C["Region"]}$2:${C["Region"]}${LAST}'
st = f'Suppliers!${C["Status"]}$2:${C["Status"]}${LAST}'
pr = f'Suppliers!${P}$2:${P}${LAST}'
ap = f'Suppliers!${C["Account Approved?"]}$2:${C["Account Approved?"]}${LAST}'
lc = f'Suppliers!${C["Country Price Level"]}$2:${C["Country Price Level"]}${LAST}'
hdr = ["Niche", "Suppliers", "UK", "EU / Europe", "Priority 4-5", "Contacted+", "Approved", "Low-cost country"]
for i, h in enumerate(hdr):
    c = wd.cell(row=5, column=2 + i, value=h)
    c.font = HDR_FONT
    c.fill = HDR_FILL
    c.border = BORDER
r = 6
for cat in CATS:
    wd.cell(row=r, column=2, value=cat)
    wd.cell(row=r, column=3, value=f'=COUNTIF({rng},B{r})')
    wd.cell(row=r, column=4, value=f'=COUNTIFS({rng},B{r},{reg},"UK")')
    wd.cell(row=r, column=5, value=f'=COUNTIFS({rng},B{r},{reg},"<>UK")')
    wd.cell(row=r, column=6, value=f'=COUNTIFS({rng},B{r},{pr},">=4")')
    wd.cell(row=r, column=7, value=f'=COUNTIFS({rng},B{r},{st},"<>Not contacted")')
    wd.cell(row=r, column=8, value=f'=COUNTIFS({rng},B{r},{ap},"Yes")')
    wd.cell(row=r, column=9, value=f'=COUNTIFS({rng},B{r},{lc},"Low-cost")')
    for col in range(2, 10):
        wd.cell(row=r, column=col).border = BORDER
        wd.cell(row=r, column=col).font = BODY
    r += 1
wd.cell(row=r, column=2, value="Total").font = BOLD
wd.cell(row=r, column=2).border = BORDER
for col in range(3, 10):
    L = get_column_letter(col)
    c = wd.cell(row=r, column=col, value=f"=SUM({L}6:{L}{r - 1})")
    c.font = BOLD
    c.border = BORDER

r += 3
for i, h in enumerate(["Outreach status", "Count", "% of list"]):
    c = wd.cell(row=r, column=2 + i, value=h)
    c.font = HDR_FONT
    c.fill = HDR_FILL
    c.border = BORDER
r += 1
for s_ in STATUSES:
    wd.cell(row=r, column=2, value=s_).font = BODY
    wd.cell(row=r, column=3, value=f'=COUNTIF({st},B{r})').font = BODY
    c = wd.cell(row=r, column=4, value=f'=IF(COUNTA({rng})=0,0,C{r}/COUNTA({rng}))')
    c.number_format = "0.0%"
    c.font = BODY
    for col in range(2, 5):
        wd.cell(row=r, column=col).border = BORDER
    r += 1
r += 1
fu = f'Suppliers!${FU}$2:${FU}${LAST}'
wd.cell(row=r, column=2, value="Follow-ups overdue").font = BOLD
wd.cell(row=r, column=3, value=(
    f'=SUMPRODUCT(({fu}<>"")*({fu}<=TODAY())*(({st}="Contacted")+({st}="Follow-up sent")))')).font = BOLD

# =========================================================================== Find More Suppliers
wf = wb.create_sheet("Find More Suppliers")
fcols = [("Resource", 34), ("Type", 18), ("Use it for", 62), ("Link", 45)]
header_row(wf, 1, [c[0] for c in fcols], [c[1] for c in fcols])
resources = [
    ("Companies House", "UK registry", "Verify any UK supplier: status, address, directors, SIC 46450 = perfume & cosmetics wholesale", "https://find-and-update.company-information.service.gov.uk/"),
    ("EU VIES VAT checker", "EU registry", "Confirm an EU supplier's VAT number is real and active", "https://ec.europa.eu/taxation_customs/vies/"),
    ("KvK (Netherlands)", "EU registry", "Verify Dutch companies (many EU wholesalers are Dutch)", "https://www.kvk.nl/en/"),
    ("KRS / rejestr.io (Poland)", "EU registry", "Verify Polish companies by KRS / NIP number", "https://rejestr.io/"),
    ("Handelsregister (Germany)", "EU registry", "Verify German companies (also check the website 'Impressum')", "https://www.handelsregister.de/"),
    ("GLEIF LEI search", "Global registry", "Check a company's Legal Entity Identifier", "https://search.gleif.org/"),
    ("MHRA licence register", "UK regulator", "Check a health/pharma wholesaler holds a wholesale dealer licence", "https://cms.mhra.gov.uk/mhra/wholesale-dealer-licences"),
    ("UK Trade Tariff", "UK gov tool", "Look up commodity codes & import duty for EU purchases", "https://www.gov.uk/trade-tariff"),
    ("Better Retailing Supplier Directory", "UK directory", "UK wholesalers incl. toys, health & beauty, grocery", "https://supplier-directory.betterretailing.com/"),
    ("Bira supplier directory", "UK directory", "Suppliers to independent retailers (housewares, DIY, toys, gifts)", "https://bira.co.uk/"),
    ("BHETA (housewares association)", "UK directory", "UK housewares & electrical suppliers", "https://www.bheta.co.uk/"),
    ("Pet Business World trade directory", "UK directory", "Pet wholesalers & distributors", "https://www.petbusinessworld.co.uk/trade-directory/"),
    ("great.gov.uk Find a Supplier", "UK gov directory", "UK companies listing their supply capability", "https://www.great.gov.uk/international/buy-from-the-uk/find-a-supplier/"),
    ("trade.gov.pl exporter catalogue", "PL gov directory", "Polish exporters & wholesalers by sector", "https://www.trade.gov.pl/en/"),
    ("CzechTrade exporters catalogue", "CZ gov directory", "Czech exporters (pet, toys, household)", "https://exporters.czechtrade.cz/en"),
    ("ARES (Czech business register)", "CZ registry", "Verify a Czech company by IČO", "https://ares.gov.cz/"),
    ("Bulgarian Commercial Register", "BG registry", "Verify a Bulgarian company by EIK", "https://portal.registryagency.bg/en/"),
    ("Romanian Trade Register (ONRC)", "RO registry", "Verify a Romanian company by CUI", "https://www.onrc.ro/index.php/en/"),
    ("Lithuanian Registry Centre", "LT registry", "Verify a Lithuanian company by code", "https://www.registrucentras.lt/en/"),
    ("Enterprise Lithuania exporters database", "LT gov directory", "Lithuanian manufacturers (profiles reviewed by the agency)", "https://www.enterpriselithuania.com/en/"),
    ("AICEP Portugal Global", "PT gov agency", "Portuguese exporters by sector (cookware, textiles, cork)", "https://www.portugalglobal.pt/en/"),
    ("ICEX Spain", "ES gov agency", "Spanish exporters & national pavilions at trade fairs", "https://www.icex.es/en/"),
    ("ASEPRI (Spanish children's products assoc.)", "ES trade assoc.", "Spanish baby & toy brands with export showrooms", "https://asepri.com/en/"),
    ("Heimtextil (Frankfurt, Jan)", "Trade show", "Towels & home textiles - Portuguese mills exhibit here", "https://heimtextil.messefrankfurt.com/"),
    ("Kids' Time (Kielce, Feb)", "Trade show", "Polish/CEE baby & toy makers", "https://www.targikielce.pl/en/kids-time"),
    ("Enterprise Europe Network partnering", "EU gov directory", "EU companies seeking distributors / buyers", "https://een.ec.europa.eu/partnering-opportunities"),
    ("Europages", "EU directory", "Search EU wholesalers by product & country", "https://www.europages.co.uk/"),
    ("wer liefert was (wlw)", "DE directory", "German B2B supplier search", "https://www.wlw.de/"),
    ("Kompass", "Global directory", "Company search by NACE code (e.g. 46.45 perfume & cosmetics wholesale)", "https://www.kompass.com/"),
    ("CosmeticIndex - EU distributors", "Beauty directory", "Cosmetic distributors & wholesalers across Europe", "https://www.cosmeticindex.com/~cosmetic-distributors-wholesalers_Europe"),
    ("Interzoo exhibitor list (Nuremberg)", "Trade show", "Every major EU pet brand & distributor - exhibitor pages list contacts", "https://www.interzoo.com/en/exhibitors"),
    ("Zoomark exhibitor catalogue (Bologna)", "Trade show", "Pet suppliers with full contact details", "https://www.zoomark.it/en/"),
    ("Ambiente (Frankfurt, Feb)", "Trade show", "Housewares, kitchen & home suppliers", "https://ambiente.messefrankfurt.com/"),
    ("IFA Berlin (Sept)", "Trade show", "Consumer electronics & small appliances wholesalers", "https://www.ifa-berlin.com/"),
    ("FIBO Cologne (April)", "Trade show", "Fitness & sports nutrition distributors", "https://www.fibo.com/"),
    ("Eurobike Frankfurt", "Trade show", "Cycling brands & distributors", "https://www.eurobike.com/"),
    ("Kind + Jugend Cologne", "Trade show", "Baby & nursery brands and distributors", "https://www.kindundjugend.com/"),
    ("Paperworld / Creativeworld (Frankfurt)", "Trade show", "Stationery, office & art/craft suppliers", "https://creativeworld.messefrankfurt.com/"),
    ("London Toy Fair (January)", "Trade show", "UK toy distributors - exhibitor list is a ready-made supplier list", "https://www.toyfair.co.uk/"),
    ("Spielwarenmesse Nuremberg (Jan/Feb)", "Trade show", "World's biggest toy fair - EU toy distributors", "https://www.spielwarenmesse.de/"),
    ("Cosmoprof Worldwide Bologna (March)", "Trade show", "Beauty & fragrance brands and distributors", "https://www.cosmoprof.com/"),
    ("Spring Fair Birmingham (Feb)", "Trade show", "UK gifts, toys, beauty & home wholesale", "https://www.springfair.com/"),
    ("Brand 'Where to buy' / 'Trade' pages", "Method", "Go to a brand's UK site and look for 'Stockists', 'Trade' or 'Distributors' to find authorised wholesalers", ""),
    ("LinkedIn search: 'distributor' + brand", "Method", "e.g. 'Trixie distributor UK' or 'Hasbro distributor' and filter by Companies / People", "https://www.linkedin.com/search/results/companies/?keywords=distributor"),
]
for i, (a, b, c_, d) in enumerate(resources, start=2):
    for col, v in enumerate([a, b, c_], start=1):
        cell = wf.cell(row=i, column=col, value=v)
        cell.font = BODY
        cell.alignment = WRAP
        cell.border = BORDER
    set_link(wf.cell(row=i, column=4), d)
    wf.cell(row=i, column=4).border = BORDER
wf.freeze_panes = "A2"

# =========================================================================== Due Diligence
wq = wb.create_sheet("Due Diligence")
qcols = [("Check", 44), ("Why it matters", 60), ("How", 54)]
header_row(wq, 1, [c[0] for c in qcols], [c[1] for c in qcols])
checks = [
    ("Company is registered & active", "Fake wholesalers often use made-up company names", "Companies House (UK), KvK (NL), KRS (PL), Handelsregister (DE), VIES VAT check (EU)"),
    ("Physical address matches registry", "A real warehouse/office is a good sign; residential or virtual offices are a warning", "Google Maps Street View + registry address"),
    ("Business email domain (not Gmail/Hotmail)", "Free email addresses are common with scam suppliers", "Ask for a contact on the company domain"),
    ("VAT number on invoices", "Needed for Amazon ungating and your VAT reclaim", "Check the VAT number on HMRC / VIES"),
    ("Brand authorisation (for gated brands)", "Authorised-distributor invoices are the most accepted for Amazon ungating", "Ask: 'Are you an authorised distributor for [brand]? Can you share a letter?'"),
    ("Prices are realistic", "Prices far below other wholesalers suggest counterfeit or grey stock", "Compare to 2-3 other suppliers and the Amazon Buy Box"),
    ("Reviews & reputation", "Past complaints reveal problems", "Trustpilot, Google reviews, UK Business Forums, Amazon seller forums, council / Trading Standards news"),
    ("Insolvency check", "Suppliers in administration may not deliver or honour returns", "Companies House filing history + The Gazette insolvency notices"),
    ("Safe payment for first order", "Bank transfer to a new supplier is hard to recover", "Start small; use credit card / trade credit where possible; never pay a personal account"),
    ("UK product compliance", "Non-compliant stock gets removed from Amazon", "Cosmetics: UK RP + SCPN. Toys: UKCA/CE + EN71. Electricals: UK plug + UKCA/CE. Fragrance/batteries: SDS"),
    ("EU import paperwork", "Missing paperwork = customs delays and surprise charges", "Get EORI; ask for commercial invoice + statement of origin; agree Incoterms (DDP easiest)"),
    ("Online / marketplace selling allowed", "Some suppliers cancel accounts that sell on Amazon", "Ask in your first email"),
    ("Sealed retail stock (no testers / returns)", "Testers, unboxed or returned goods cannot be sold as new on Amazon", "Confirm in writing before ordering"),
]
for i, row in enumerate(checks, start=2):
    for col, v in enumerate(row, start=1):
        c = wq.cell(row=i, column=col, value=v)
        c.font = BODY
        c.alignment = WRAP
        c.border = BORDER

# =========================================================================== Removed - Failed Check
wx = wb.create_sheet("Removed - Failed Check")
wx.cell(row=1, column=1, value="Suppliers removed after the anti-scam check (Oct 2026)").font = TITLE
wx.cell(row=2, column=1, value=(
    f"{len(REMOVED)} suppliers were taken off the Suppliers tab because they showed scam warning signs, insolvency, "
    "regulator fines, or no independent evidence that the business exists. Do NOT order from these.")).font = BODY
wx.merge_cells("A2:E2")
wx.cell(row=2, column=1).alignment = WRAP
wx.row_dimensions[2].height = 30
xcols = [("Company", 36), ("Country", 16), ("Category", 20), ("Why it failed", 80), ("Website (do not use)", 34)]
header_row(wx, 4, [c[0] for c in xcols], [c[1] for c in xcols])
for k, s_ in enumerate(sorted(REMOVED, key=lambda x: (x["country"], x["name"].lower())), start=5):
    for col, v in enumerate([s_["name"], s_["country"], s_["cat"], SC.FAIL[s_["name"]], s_["web"]], start=1):
        c = wx.cell(row=k, column=col, value=v)
        c.font = BODY
        c.alignment = WRAP
        c.border = BORDER
    wx.cell(row=k, column=4).fill = PatternFill("solid", fgColor="FCE4D6")
wx.freeze_panes = "A5"

wb.save(OUT)
print("saved", OUT, "suppliers:", N, "categories:", len(CATS))
