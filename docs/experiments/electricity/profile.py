"""Offline inspection only: profile downloaded snapshots without loading a domain.

Run from the checkout root: .venv/bin/python docs/experiments/electricity/profile.py
Downloads stay in ignored data/raw/electricity-inspection/. No network or DB writes.
"""

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile


RAW = Path("data/raw/electricity-inspection")
OUT = Path("docs/experiments/electricity/source-profile.json")
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def csv_rows(name):
    with (RAW / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def workbook_rows():
    with zipfile.ZipFile(RAW / "annual-2025.download") as archive:
        workbook = zipfile.ZipFile(io.BytesIO(archive.read(archive.namelist()[0])))
    strings = ["".join(node.itertext()) for node in ET.fromstring(
        workbook.read("xl/sharedStrings.xml")).findall("m:si", NS)]
    relations = {node.attrib["Id"]: node.attrib["Target"] for node in ET.fromstring(
        workbook.read("xl/_rels/workbook.xml.rels"))}
    sheets = ET.fromstring(workbook.read("xl/workbook.xml")).findall("m:sheets/m:sheet", NS)
    generation = next(sheet for sheet in sheets if sheet.attrib["name"] == "GENERACIÓN")
    target = relations[generation.attrib[
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]]
    path = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
    rows = []
    for node in ET.fromstring(workbook.read(path)).findall("m:sheetData/m:row", NS):
        cells = {}
        for cell in node:
            value = cell.find("m:v", NS)
            if value is not None:
                cells["".join(c for c in cell.attrib["r"] if c.isalpha())] = (
                    strings[int(value.text)] if cell.attrib.get("t") == "s" else value.text)
        rows.append((int(node.attrib["r"]), cells))
    header = next(cells for row, cells in rows if row == 33)
    data = [(row, cells) for row, cells in rows if row > 33 and cells.get("A") in {"2024", "2025"}]
    unit = next(cells["A"] for row, cells in rows if row == 31)
    return [sheet.attrib["name"] for sheet in sheets], header, data, unit


plants = csv_rows("plants.csv")
generation = csv_rows("generation.csv")
agents = csv_rows("agents.csv")
plant_codes = {row["central"] for row in plants if row["central"]}
old_codes = {row["central"] for row in generation}
sheets, header, monthly, detail_unit = workbook_rows()
keys = Counter((cells["A"], cells["B"], cells["C"]) for _, cells in monthly)
market_keys = Counter((cells["A"], cells["B"], cells["C"], cells["O"]) for _, cells in monthly)
source_urls = {
    "plant-metadata.json": "https://datos.energia.gob.ar/api/3/action/package_show?id=generacion-electrica-centrales-de-generacion-",
    "cammesa-metadata.json": "https://datos.energia.gob.ar/api/3/action/package_show?id=publicaciones-cammesa",
    "cammesa-annual.html": "https://cammesaweb.cammesa.com/informe-anual/",
    "annual-2025.download": "https://cammesaweb.cammesa.com/?wpdmdl=52496",
    "cammesa-access-policy.html": "https://cammesaweb.cammesa.com/politicas-de-acceso/",
    "pampa-report-2019.pdf": "https://pampa.com/wp-content/uploads/2024/01/PAM_Reporte2019_ESP.pdf",
    "pampa-annual-2024.pdf": "https://cdn-sites-assets.mziq.com/wp-content/uploads/sites/1438/2025/04/PESA-Memoria-Anual-2024-EXE-Edicion-Especial.pdf",
    "pampa-investor-kit.html": "https://ri.pampa.com/en/financial-information/investor-kit/",
    "authorization-2019.html": "https://www.boletinoficial.gob.ar/detalleAviso/primera/206470/20190429",
}
metadata = {}
for name in ["plant", "cammesa"]:
    item = json.loads((RAW / f"{name}-metadata.json").read_text())["result"]
    metadata[name] = {key: item.get(key) for key in ["id", "license_id", "metadata_modified", "extras"]}
    for resource in item["resources"]:
        for file, resource_id in [
            ("plants.csv", "230fdf38-8f12-4017-a1e8-d7a1bc4a1c1c"),
            ("generation.csv", "7da95282-a903-47f0-b4bc-cd1387a62dd3"),
            ("agents.csv", "ac27b401-3800-4a98-9535-3fc715228d84"),
        ]:
            if resource["id"] == resource_id:
                source_urls[file] = resource["url"]

profile = {
    "status": "inspection_only_not_business_approved",
    "snapshot_date": "2026-10-22",
    "artifacts": [{"path": str(RAW / file), "url": url,
                   "sha256": hashlib.sha256((RAW / file).read_bytes()).hexdigest(),
                   "bytes": (RAW / file).stat().st_size} for file, url in source_urls.items()],
    "metadata": metadata,
    "plants": {"rows": len(plants), "columns": list(plants[0]),
               "systems": dict(Counter(row["sistema"] for row in plants)),
               "origins": dict(Counter(row["fuente"] for row in plants)),
               "mem_origins": dict(Counter(row["fuente"] for row in plants
                                           if row["sistema"] == "Interconectado MEM")),
               "empty_codes": sum(not row["central"] for row in plants),
               "nonempty_distinct_codes": len(plant_codes)},
    "old_generation": {"rows": len(generation), "columns": list(generation[0]),
                       "periods": sorted({row["indice_tiempo"] for row in generation}),
                       "process_dates": sorted({row["fecha_proceso"] for row in generation}),
                       "plant_codes": len(old_codes),
                       "exact_registry_code_overlap": len(old_codes & plant_codes),
                       "unmatched_code_sample": sorted(old_codes - plant_codes)[:20]},
    "agents": {"rows": len(agents), "columns": list(agents[0]),
               "process_dates": sorted({row["fecha_proceso"] for row in agents})},
    "annual_workbook": {"sheets": sheets, "generation_header_row": 33, "generation_columns": header,
                        "generation_detail_unit_cell": "A31", "generation_detail_unit": detail_unit,
                        "rows": len(monthly), "year_counts": dict(Counter(c["A"] for _, c in monthly)),
                        "market_counts": dict(Counter(c["O"] for _, c in monthly)),
                        "duplicate_year_month_machine_extra_rows": sum(n - 1 for n in keys.values()),
                        "duplicate_year_month_machine_market_extra_rows": sum(n - 1 for n in market_keys.values()),
                        "years": {}},
    "candidate_identity_examples": [
        {key: row[key] for key in ["nombre", "central", "nombre_agente", "provincia", "fuente"]}
        for row in plants if row["central"] in {"GUEM", "GEBA", "PILB", "PAMEEO", "BAHIEO", "CAPE", "ACAJ"}],
}
for year in ["2024", "2025"]:
    subset = [c for _, c in monthly if c["A"] == year]
    codes = {c["D"] for c in subset}
    profile["annual_workbook"]["years"][year] = {
        "excel_month_serials": sorted({c["B"] for c in subset}, key=float),
        "plant_codes": len(codes), "exact_registry_code_overlap": len(codes & plant_codes),
        "unmatched_code_sample": sorted(codes - plant_codes)[:20],
    }
OUT.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n")
print(f"Wrote {OUT}; inspection only, no answers scored or links approved.")
