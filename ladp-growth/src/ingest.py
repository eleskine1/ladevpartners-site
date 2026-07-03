"""Pull all sources into data/raw/ and normalize to the common schema.

Common schema (data/normalized/prospects.parquet):
    parcel_ain, address, zip_code, signal, signal_date, valuation, units,
    permit_or_case, owner fields (post-enrichment), source
"""

import json
import pathlib
import time

import pandas as pd
import requests

from .datasets import DATASETS

RAW = pathlib.Path("data/raw")
NORM = pathlib.Path("data/normalized")
RAW.mkdir(parents=True, exist_ok=True)
NORM.mkdir(parents=True, exist_ok=True)

APP_TOKEN = None  # optional Socrata app token lifts rate limits -- free signup


def _get(url: str, params: dict) -> list[dict]:
    headers = {"X-App-Token": APP_TOKEN} if APP_TOKEN else {}
    r = requests.get(url, params=params, headers=headers, timeout=120)
    r.raise_for_status()
    return r.json()


def pull_socrata() -> None:
    for name, spec in DATASETS.items():
        if name == "ladbs_inspections":
            continue  # pulled per-permit in detect_stalled()
        rows = _get(spec["url"], spec["params"])
        (RAW / f"{name}.json").write_text(json.dumps(rows))
        print(f"{name}: {len(rows)} rows")
        time.sleep(2)


def detect_stalled(permits: pd.DataFrame) -> pd.DataFrame:
    """Issued >9mo ago, >=$1M, no passing inspections."""
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=270)
    candidates = permits[
        (pd.to_datetime(permits["issue_date"]) < cutoff)
        & (permits["valuation"].astype(float) >= 1_000_000)
    ]
    stalled = []
    insp_url = DATASETS["ladbs_inspections"]["url"]
    for _, p in candidates.iterrows():
        rows = _get(insp_url, {"$where": f"permit = '{p['permit_nbr']}'", "$limit": 50})
        passing = [r for r in rows if "approv" in str(r.get("inspection_result", "")).lower()]
        if len(passing) == 0:
            stalled.append(p["permit_nbr"])
        time.sleep(0.5)
    out = candidates[candidates["permit_nbr"].isin(stalled)].copy()
    out["signal"] = "permit_stalled_no_inspections"
    return out


def build_ain(row) -> str:
    return (
        str(row.get("assessor_book", "")).zfill(4)
        + str(row.get("assessor_page", "")).zfill(3)
        + str(row.get("assessor_parcel", "")).zfill(3)
    )


def normalize() -> None:
    from .segments import palisades_rebuilds, adu_capacity_plays

    permits = pd.DataFrame(json.loads((RAW / "ladbs_permits.json").read_text()))
    permits["parcel_ain"] = permits.apply(build_ain, axis=1)
    permits["address"] = (
        permits["address_start"].astype(str) + " " + permits["street_name"].astype(str)
    )

    recent_cut = pd.Timestamp.now() - pd.Timedelta(days=30)
    fresh = permits[pd.to_datetime(permits["issue_date"]) >= recent_cut].copy()
    fresh["signal"] = "large_permit_issued_30d"

    stalled = detect_stalled(permits)
    palisades = palisades_rebuilds()
    adu = adu_capacity_plays()

    frames = [f for f in (fresh, stalled, palisades, adu) if not f.empty]
    # TODO first session: planning entitlements -> entitled_not_permitted_6mo
    #   (join approved planning cases to permits on AIN; keep cases with no
    #    subsequent permit issuance)

    prospects = pd.concat(frames, ignore_index=True)
    prospects = prospects.rename(
        columns={"issue_date": "signal_date", "permit_nbr": "permit_or_case"}
    )
    keep = [
        "parcel_ain", "address", "zip_code", "signal", "signal_date",
        "valuation", "permit_or_case", "contractors_business_name",
        "applicant_first_name", "applicant_last_name", "use_desc",
        "adu_capacity_est", "buildable_yard", "units",
    ]
    prospects = prospects[[c for c in keep if c in prospects.columns]]
    prospects.to_parquet(NORM / "prospects.parquet")
    print(f"normalized: {len(prospects)} prospects")
    print(prospects["signal"].value_counts().to_string())


if __name__ == "__main__":
    pull_socrata()
    normalize()
