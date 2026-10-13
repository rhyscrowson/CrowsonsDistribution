# Contact-detail and status corrections found during the quality audit (Oct 2026).
# Applied by build_workbook.py on top of the round data files, keyed by exact supplier name.
UPDATES = {
    "SPOKAR a.s.": dict(web="http://www.spokar.com"),
    "ALPA, a.s.": dict(phone="+420 566 521 401 (switchboard)", addr="Hornoměstská 378/74, 594 01 Velké Meziříčí",
                       regid="IČO 27666468 / DIČ CZ27666468"),
    "Remoska s.r.o.": dict(city="Kopřivnice (Vlčovice)", addr="Průmyslový park 303, Vlčovice, 742 21 Kopřivnice"),
    "Delia Cosmetics Sp. z o.o.": dict(web="https://www.delia.pl", phone="+48 42 225 44 84 (verify)"),
    "Bulgarian Rose AD (Bulgarska Roza Karlovo)": dict(email="Via official distributor Cosmetics Bulgaria (cosmeticsbulgaria.com)"),
    "Laboratorium Kosmetyczne Joanna sp.j.": dict(email="joanna@joanna.pl", regid="NIP 1180024208"),
    "Amiplay Sp. z o.o. (Comfy)": dict(web="https://www.amiplay.eu", phone="+48 696 607 221 (export director: +48 888 787 666)",
                                      addr="ul. Meliorantów 67AB, 42-209 Częstochowa (Comfy brand office: ul. Krasnowolska 50, Warsaw)",
                                      city="Częstochowa / Warsaw"),
    "PILANA Metal spol. s r.o.": dict(web="http://www.pilanametal.cz"),
    "MPPK Group Sp. z o.o.": dict(notes="Acquired by private-equity fund Avallon MBO (2023) - stable owner; contact via trade.gov.pl profile"),
    "GOSBI PET FOOD S.A.": dict(web="https://www.gosbi.com", phone="+34 972 527 102 (export manager: Egle Irtmonaite)",
                               city="Santa Llogaia d'Àlguema (Girona)", addr="Crta. N-IIa km 1.5, 17771 Santa Llogaia d'Àlguema, Girona"),
    "SFD S.A. (Allnutrition)": dict(web="https://sfdsa.pl", phone="+48 77 549 25 00", email="sekretariat@sfd.pl (ask for export / wholesale)"),
    "Plastkon product s.r.o. (Gizmo Riders)": dict(web="http://www.plastkon.cz"),
}
# Suppliers dropped after the audit because no verifiable contact route or registry ID could be found.
REMOVE = {
    "JUKO petfood s.r.o.",
}
