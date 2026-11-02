#!/usr/bin/env python3
"""Build the site data from e-GP contracts: one small JSON file per district.

    python3 build.py egp-data/2568/*.csv   # files from `egp download 2568` (about 5 GB)
    python3 build.py 2568                  # or stream the year from data.go.th without keeping files
"""
import csv
import http.client
import json
import os
import re
import shutil
import sys
from collections import defaultdict

import thai_egp  # pip install git+https://github.com/nuttakulsv/thai-egp

MIN_BAHT = 100_000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
COLS = ["id", "name", "unit", "kind", "baht", "ref", "winner", "date", "lat", "lon"]
METHOD_TAIL = re.compile(r"\s*(โดย|ด้วย)\s*วิธี\S*(\s*\(e-bidding\))?\s*$")


ORG_WORDS = re.compile(r"กรม|กอง|สำนัก|โรงพยาบาล|วิทยาลัย|โรงเรียน|เทศบาล|มูลนิธิ|สมาคม|วิสาหกิจ|การไฟฟ้า|การประปา"
                       r"|ธนาคาร|สถาบัน|ศูนย์|\bllc\b|\bl\.p\.|universit|hospital|hotel|school", re.I)


def shown_name(r):
    """The winner's name, or "" when it might be a person. Only people are hidden, but when unsure, hide."""
    name, p = r["winner_name"], r["winner_prefix"] or ""
    if not r["winner_juristic"]:
        return ""
    registered = len(p) == 6 and p[1:3] != "99" and p[3] in thai_egp.ENTITY  # a company number from DBD
    return name if registered or thai_egp.COMPANY_WORDS.search(name) or ORG_WORDS.search(name) else ""


def short_name(s):
    return METHOD_TAIL.sub("", s)[:200]


def slug(s):
    """File name for a district: keep Thai letters, drop anything that could leave the folder."""
    return re.sub(r"[^\w\u0E00-\u0E7F-]", "_", s).strip("._") or "_"


def rows(args, tries=3):
    """Rows of every file. A file that breaks halfway is read again from the start; main() drops the repeats."""
    for a in args:
        srcs = [url for _, url, _ in thai_egp.parts(int(a))] if re.fullmatch(r"25\d\d", a) else [a]
        for src in srcs:
            for i in range(tries):
                try:
                    yield from thai_egp.read(src)
                    break
                except (OSError, http.client.HTTPException, csv.Error) as e:
                    if i == tries - 1:
                        raise
                    print(f"{src}: {e}, reading it again", file=sys.stderr)


def main(args):
    by_area = defaultdict(list)
    seen = set()
    years = set()
    for r in rows(args):
        amt = r["amount"] or 0
        if amt < MIN_BAHT or not r["province"]:
            continue
        key = (r["project_id"], r["winner_name"], r["contract_no"], amt)
        if key in seen:
            continue
        seen.add(key)
        years.add(r["fiscal_year"])
        by_area[(r["province"], r["district"] or "ไม่ระบุอำเภอ")].append([
            r["project_id"], short_name(r["project_name"]), r["subdept"] or r["dept"], r["method_kind"] or "",
            round(amt), round(r["reference_price"] or 0), shown_name(r),
            r["contract_date"] or r["transaction_date"] or "",
            round(r["lat"], 4) if r["lat"] else None, round(r["lon"], 4) if r["lon"] else None,
        ])
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    index = {}
    for (prov, dist), items in by_area.items():
        items.sort(key=lambda x: -x[4])
        units, winners = {}, {"": 0}  # names repeat on every row; store each once per file
        for x in items:
            x[2] = units.setdefault(x[2], len(units))
            x[6] = winners.setdefault(x[6], len(winners))
        folder = os.path.join(OUT, slug(prov))
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, slug(dist) + ".json"), "w", encoding="utf-8") as f:
            json.dump({"cols": COLS, "units": list(units), "winners": list(winners), "rows": items}, f,
                      ensure_ascii=False, separators=(",", ":"))
        index.setdefault(prov, {})[dist] = [len(items), sum(x[4] for x in items), slug(prov) + "/" + slug(dist)]
    with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"years": sorted(years), "min_baht": MIN_BAHT, "provinces": index}, f,
                  ensure_ascii=False, separators=(",", ":"))
    n = sum(len(v) for v in by_area.values())
    print(f"{n:,} contracts in {len(by_area):,} districts of {len(index)} provinces -> {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:] or ["2568"])
