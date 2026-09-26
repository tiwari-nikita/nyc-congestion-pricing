"""Step 0 - Pull the MTA data from New York State Open Data (Socrata API), aggregated to
daily totals so the raw pull stays small. Open NY data is published for public reuse.

Datasets:
  ebfx-2m7v  MTA Bridges and Tunnels Hourly Crossings: Beginning 2019
  sayj-mze2  MTA Daily Ridership and Traffic: Beginning 2020
  t6yz-b64h  MTA Congestion Relief Zone Vehicle Entries: Beginning 2025
The analysis window is pinned (crossings through 2026-09-08, zone entries through
2026-09-19), so re-running later reproduces the published figures exactly.
"""
import csv
import json
import pathlib
import time
import urllib.parse
import urllib.request

RAW = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"
BT_END, CRZ_END, RID_END = "2026-09-08", "2026-09-19", "2026-09-24"


def soql(ds, params, out, page=50000):
    dest = RAW / out
    if dest.exists():
        print("  exists   ", out)
        return
    rows, offset = [], 0
    while True:
        q = dict(params, **{"$limit": page, "$offset": offset})
        url = "https://data.ny.gov/resource/{}.json?{}".format(ds, urllib.parse.urlencode(q))
        with urllib.request.urlopen(url, timeout=300) as r:
            batch = json.load(r)
        rows += batch
        if len(batch) < page:
            break
        offset += page
        time.sleep(0.3)
    keys = sorted({k for r in rows for k in r})
    with open(dest, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print("  fetched  {:<45} {:>8,} rows".format(out, len(rows)))


RAW.mkdir(parents=True, exist_ok=True)
soql("ebfx-2m7v", {"$select": "date, facility, direction, sum(traffic_count) as crossings",
                    "$where": "date <= '{}T00:00:00'".format(BT_END),
                    "$group": "date, facility, direction", "$order": "date, facility, direction"},
     "bt_crossings_daily_by_facility.csv")
soql("sayj-mze2", {"$where": "date <= '{}T00:00:00'".format(RID_END), "$order": "date, mode"},
     "mta_daily_ridership_traffic.csv")
soql("t6yz-b64h", {"$select": "toll_date, detection_group, detection_region, vehicle_class, "
                               "sum(crz_entries) as crz_entries, sum(excluded_roadway_entries) as excluded_entries",
                    "$where": "toll_date <= '{}T00:00:00'".format(CRZ_END),
                    "$group": "toll_date, detection_group, detection_region, vehicle_class", "$order": "toll_date"},
     "crz_entries_daily_by_group_class.csv")
soql("t6yz-b64h", {"$select": "toll_date, time_period, vehicle_class, sum(crz_entries) as crz_entries",
                    "$where": "toll_date <= '{}T00:00:00'".format(CRZ_END),
                    "$group": "toll_date, time_period, vehicle_class", "$order": "toll_date"},
     "crz_entries_daily_by_period_class.csv")
