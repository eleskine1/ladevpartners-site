"""Verify every pinned endpoint against the live portals and hunt the
remaining PIN_MEs. Run from a machine with open internet (the Claude Code
sandbox egress policy blocks these hosts):

    python scripts/pin_check.py

Checks, in order:
  1. The three LADBS Socrata datasets respond and their field names still
     match what src/ingest.py expects.
  2. Santa Monica CKAN datastore resource responds.
  3. ArcGIS Online sharing search for LAHub planning-case feature services
     -> prints candidate FeatureServer URLs to pin into ARCGIS_PLANNING.
"""

import sys

import requests

sys.path.insert(0, ".")
from src.datasets import DATASETS, SANTA_MONICA  # noqa: E402

EXPECTED_PERMIT_FIELDS = {
    "issue_date", "valuation", "permit_type", "permit_nbr",
    "address_start", "street_name", "zip_code",
    "assessor_book", "assessor_page", "assessor_parcel",
}


def check_socrata() -> None:
    for name, spec in DATASETS.items():
        try:
            r = requests.get(spec["url"], params={"$limit": 1}, timeout=30)
            r.raise_for_status()
            rows = r.json()
            fields = set(rows[0]) if rows else set()
            print(f"OK   {name}: {spec['url']}")
            if name == "ladbs_permits" and fields:
                missing = EXPECTED_PERMIT_FIELDS - fields
                if missing:
                    print(f"     !! fields missing vs ingest.py: {sorted(missing)}")
                    print(f"     actual fields: {sorted(fields)}")
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {name}: {e}")


def check_santa_monica() -> None:
    try:
        params = dict(SANTA_MONICA["params"], limit=1)
        r = requests.get(SANTA_MONICA["url"], params=params, timeout=30)
        r.raise_for_status()
        result = r.json()["result"]
        rec = result["records"][0] if result["records"] else {}
        print(f"OK   santa_monica CKAN: {result.get('total', '?')} total rows")
        print(f"     fields: {sorted(rec)}")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL santa_monica: {e}")


def find_planning_layer() -> None:
    """Search ArcGIS Online for the LA City planning-case layer to pin."""
    queries = [
        '"planning case" orgid:7nsPwEMP38bSkCjy type:"Feature Service"',
        '"entitlement" owner:LAHub type:"Feature Service"',
        'PCTS lacity type:"Feature Service"',
    ]
    for q in queries:
        try:
            r = requests.get(
                "https://www.arcgis.com/sharing/rest/search",
                params={"q": q, "f": "json", "num": 10},
                timeout=30,
            )
            r.raise_for_status()
            for item in r.json().get("results", []):
                print(f"CANDIDATE  {item.get('title')}\n           {item.get('url')}")
        except Exception as e:  # noqa: BLE001
            print(f"FAIL agol search '{q}': {e}")
    print(
        "\nPin the right candidate into ARCGIS_PLANNING in src/datasets.py\n"
        "(append /0/query) and confirm its field names match the `where`\n"
        "clause. If nothing fits, fall back to a PCTS extract request:\n"
        "planning.metrics@lacity.gov"
    )


if __name__ == "__main__":
    print("== Socrata (data.lacity.org) ==")
    check_socrata()
    print("\n== Santa Monica (data.santamonica.gov CKAN) ==")
    check_santa_monica()
    print("\n== ArcGIS planning-case layer discovery ==")
    find_planning_layer()
