# ภาษีบ้านฉันไปไหน ("where did my local tax go")

[ภาษาไทย](README.md) · **[Open the site](https://nuttakulsv.github.io/thai-local-spend/)** · Built with [thai-egp](https://github.com/nuttakulsv/thai-egp)

Pick a province and a district and see what the public bodies there bought, from whom, and for how much: sub-district councils, municipalities, schools, district hospitals. The data is Thailand's public procurement system (e-GP), run by the Comptroller General's Department.

For each district you get:

- total baht, number of contracts, and the share of each procurement method (e-bidding, direct procurement, ...)
- the units that spent the most and the contractors that received the most; click a name to filter by it
- every contract, searchable by project, unit, contractor or project number
- a map of the projects whose location the unit recorded

Every view has a shareable link, e.g. `#เชียงใหม่/แม่ริม`.

## Reading the numbers

- **Grouped by where the buying unit is, not where the project is.** Local councils sit in their own area, but a road contracted by the Department of Highways shows up where the highway district office is, and ministries show up in Bangkok, which is why Bangkok's totals are so large.
- **Contracts with no district are under "ไม่ระบุอำเภอ" (district not given) in each province.** The 2568 data fills blanks with the pair อ.ตรอน / ต.เพ, which doesn't exist; those rows are moved there.
- **Contracts of 100,000 baht and more only.** There are millions of small purchases; including them would make the site too slow to use.
- **Contractors who are individuals are not named.** Their contracts still count in the totals, and the page says how many there are. When it isn't clear whether a contractor is a company or a person (say, a name with no company word and a Revenue Department number), the name is hidden too.
- **The numbers are what agencies typed in.** The 11-digit project number can be looked up in e-GP or on the government's [ภาษีไปไหน](https://govspending.data.go.th) site.

## Build it yourself

Python 3.9+ and [thai-egp](https://github.com/nuttakulsv/thai-egp).

```
pip install git+https://github.com/nuttakulsv/thai-egp
egp download 2568                        # the raw year, about 5 GB; resumes if the server stalls
python3 build.py egp-data/2568/*.csv     # writes data/ in a few minutes
python3 -m http.server                   # http://localhost:8000
```

`python3 build.py 2568` reads straight from data.go.th without keeping raw files, but a stall halfway through a file means reading that file again from the start. Either way you get one JSON file per district under `data/`. The site is a single HTML file with no front-end build step, so GitHub Pages serves it as is.

data.go.th rarely answers machines outside Thailand, so there's no GitHub Actions refresh yet; run the build from a machine in Thailand.

Tests: `PYTHONPATH=../thai-egp python3 test/test_build.py`, and with jsdom installed, `node test/page.test.js .`

## Data source

Procurement data from the Comptroller General's Department e-GP system, published by the Digital Government Development Agency on [data.go.th](https://data.go.th) under Creative Commons Attribution. Map tiles © OpenStreetMap contributors.

Code: MIT.
