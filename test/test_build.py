"""Run: PYTHONPATH=path/to/thai-egp python3 test/test_build.py"""
import csv
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import build
import thai_egp

CAT = "วิธีการจัดหา ประกาศเชิญชวนทั่วไป คัดเลือก เฉพาะเจาะจง"


def row(**v):
    r = [""] * 28
    base = dict(project_id="68019000001", project_name="จ้างก่อสร้างถนน หมู่ 3 โดยวิธีเฉพาะเจาะจง", project_type="จ้างก่อสร้าง",
                dept="เทศบาลตำบลทดสอบ", subdept="เทศบาลตำบลทดสอบ", m1=CAT, m2="เฉพาะเจาะจง", announce_date="-",
                budget="450000", reference_price="450000", agreed_price="449000", fiscal_year="2568",
                transaction_date="1 ธ.ค. 67", province="เชียงใหม่", district="แม่ริม", subdistrict="ริมใต้",
                project_status="สิ้นสุดสัญญา", winner_id="0505560001234", winner_name="ห้างหุ้นส่วนจำกัด ทดสอบการโยธา",
                contract_no="1/2568", contract_date="2 ธ.ค. 67", contract_end="30 ธ.ค. 67", contract_amount="449000",
                contract_status="สิ้นสุดสัญญา", lat="18.9", lon="98.9")
    base.update(v)
    for k, val in base.items():
        r[thai_egp.NARROW[k]] = val
    return r


def test_build():
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "x.csv")
        with open(src, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["header"])
            w.writerow(row())
            w.writerow(row())  # exact duplicate row, counted once
            w.writerow(row(project_id="2", contract_amount="5000", agreed_price="5000"))  # under 100,000 baht
            w.writerow(row(project_id="3", winner_id="352050022xxxx", winner_name="นายทดสอบ ระบบ", contract_amount="200000"))
            w.writerow(row(project_id="4", district="../../etc", contract_amount="300000"))
            w.writerow(row(project_id="5", winner_id="0994000123456", winner_name="JOHN TEST PERSON", contract_amount="150000"))
            w.writerow(row(project_id="6", winner_id="0994000654321", winner_name="โรงพยาบาลทดสอบ", contract_amount="150000"))
        build.OUT = os.path.join(d, "data")
        build.main([src])
        idx = json.load(open(os.path.join(build.OUT, "index.json"), encoding="utf-8"))
        assert idx["years"] == [2568]
        mr = idx["provinces"]["เชียงใหม่"]["แม่ริม"]
        assert mr[0] == 4 and mr[1] == 449000 + 200000 + 300000, mr
        data = json.load(open(os.path.join(build.OUT, mr[2] + ".json"), encoding="utf-8"))
        names = [data["winners"][r[6]] for r in data["rows"]]
        dump = json.dumps(data, ensure_ascii=False)
        assert "นายทดสอบ ระบบ" not in dump and "JOHN TEST PERSON" not in dump  # people are never written out
        assert "โรงพยาบาลทดสอบ" in dump  # a public body with a Revenue Department number is
        assert "" in names and "ห้างหุ้นส่วนจำกัด ทดสอบการโยธา" in names
        assert data["rows"][0][1] == "จ้างก่อสร้างถนน หมู่ 3"  # method suffix trimmed
        for root, _, files in os.walk(build.OUT):  # odd district names stay inside data/
            assert os.path.realpath(root).startswith(os.path.realpath(build.OUT))


def test_retry():
    calls = []

    def flaky(src):
        calls.append(src)
        yield {"n": 1}
        if len(calls) == 1:
            raise TimeoutError("The read operation timed out")
        yield {"n": 2}

    real, thai_egp.read = thai_egp.read, flaky
    try:
        got = list(build.rows(["x.csv"]))
    finally:
        thai_egp.read = real
    assert calls == ["x.csv", "x.csv"] and got == [{"n": 1}, {"n": 1}, {"n": 2}], got  # main() drops the repeat


if __name__ == "__main__":
    test_build()
    test_retry()
    print("ok test_build test_retry")
