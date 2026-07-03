"""Dataset registry: every public source the pipeline pulls, with queries.

Verify field names against each dataset's API docs on first run
(https://dev.socrata.com/foundry/data.lacity.org/<id>) -- column names
occasionally change when the city republishes.
"""

from datetime import date, timedelta

TODAY = date.today()
LOOKBACK_PERMITS = (TODAY - timedelta(days=730)).isoformat()

SOCRATA_BASE = "https://data.lacity.org/resource"

DATASETS = {
    "ladbs_permits": {
        "url": f"{SOCRATA_BASE}/pi9x-tg5x.json",
        "params": {
            "$where": (
                f"issue_date > '{LOOKBACK_PERMITS}' "
                "AND valuation > 1000000 "
                "AND permit_type in ('Bldg-New','Bldg-Alter/Repair','Bldg-Addition')"
            ),
            "$order": "issue_date DESC",
            "$limit": 50000,
        },
    },
    "ladbs_inspections": {
        "url": f"{SOCRATA_BASE}/9w5z-rg2h.json",
        "params": {"$limit": 1000},
    },
    "ladbs_cofo": {
        "url": f"{SOCRATA_BASE}/3f9m-afei.json",
        "params": {
            "$where": f"cofo_issue_date > '{LOOKBACK_PERMITS}'",
            "$limit": 50000,
        },
    },
}

# LA City Planning entitlement cases live on GeoHub (ArcGIS REST).
# STATUS 2026-07-03: no public FeatureServer URL surfaced via search, and the
# dev sandbox's egress policy blocks geohub.lacity.org / arcgis.com, so this
# could not be pinned live. Run scripts/pin_check.py from an unrestricted
# machine -- it queries the ArcGIS Online sharing API for LAHub planning-case
# feature services and prints candidate URLs to paste here.
# Fallbacks if no bulk layer exists:
#   - DCP biweekly case filings API: planning.lacity.gov/dcpapi/general/biweeklycase/...
#   - data request to planning.metrics@lacity.gov (PCTS extract)
#   - LA County (unincorporated, secondary geo): "LA County Permitting
#     (EPIC-LA Case History)" geohub item b2a835d49c194029a525fb60cf24aa59_0
ARCGIS_PLANNING = {
    "url": "PIN_ME_ON_FIRST_RUN/FeatureServer/0/query",
    "params": {
        "where": (
            "CASE_ACTION = 'Approved' AND "
            "CASE_TYPE IN ('TOC','DB','ED1','VTT','ZC','CUP') AND "
            "COMPLETION_DATE >= DATE '2023-01-01'"
        ),
        "outFields": "*",
        "f": "json",
        "resultRecordCount": 2000,
    },
}

# Santa Monica migrated off Socrata -- data.smgov.net no longer resolves.
# Current portal is CKAN at data.santamonica.gov. Pinned 2026-07-03 to
# dataset "Active Building & Safety Permits":
#   https://data.santamonica.gov/dataset/active-building-and-safety-permits
# NOTE for the ingest adapter: CKAN is NOT SoQL. Response shape is
# {"result": {"records": [...]}} and filtering uses `q` / `filters` params.
SANTA_MONICA = {
    "url": "https://data.santamonica.gov/api/3/action/datastore_search",
    "params": {
        "resource_id": "d6867c7d-89bc-4975-be35-4d2673a4764b",
        "limit": 10000,
    },
}

# LADBS Palisades fire-rebuild / one-stop center feed.
# STATUS 2026-07-03: no machine-readable plan-check feed found yet. Known
# official trackers (dashboard scrape targets, verify via pin_check.py):
#   - LA County Recovers permitting dashboard (Palisades + Eaton):
#     https://recovery.lacounty.gov/rebuilding/permitting-progress-dashboard/
#   - City: https://recovery.lacity.gov (LA Strong: Return & Rebuild)
#   - Independent: Pali Builds (resident-run 90272 new-build permit tracker)
# Issued-permit rebuilds are already covered programmatically by pi9x-tg5x
# filtered to 90272 in segments.palisades_rebuilds(); this feed is only for
# catching owners earlier, at plan-check. PIN_ME.

ASSESSOR_NOTES = """
LA County Assessor bulk parcel roll: download quarterly, store as
data/raw/assessor_roll.parquet.
Join key: AIN = book(4) + page(3) + parcel(3) from LADBS records.
Fields needed: ain, owner_name, mailing_address, use_code, units,
lot_sqft, building_sqft, stories, year_built.
"""
