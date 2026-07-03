"""Proactive target segments beyond the core stall queries.

1. Palisades fire rebuilds -- SFR owners in 90272 pulling rebuild permits.
   High valuation, zero construction experience, navigating insurance +
   LADBS one-stop rebuild center simultaneously. Resource-first tone;
   attorney compliance check required before any send.

2. SB 1211 ADU capacity plays -- existing 8+ unit multifamily parcels with
   enough unbuilt lot area to site 8+ detached ADUs. The 1810 12th St
   playbook applied as prospecting: we approach the owner WITH the analysis.
   No intent signal exists yet; the pitch creates it.
"""

import json
import pathlib

import pandas as pd
import yaml

from .datasets import DATASETS

CFG = yaml.safe_load(open("config.yaml"))
RAW = pathlib.Path("data/raw")


def palisades_rebuilds() -> pd.DataFrame:
    from .ingest import _get, build_ain

    p = CFG["segment_params"]["palisades"]
    zips = "','".join(p["zips"])
    kw = " OR ".join(f"upper(work_desc) like '%{k}%'" for k in p["keywords"])
    params = {
        "$where": (
            f"zip_code in ('{zips}') "
            f"AND valuation > {p['min_valuation_usd']} "
            f"AND permit_type in ('Bldg-New','Bldg-Alter/Repair') "
            f"AND ({kw})"
        ),
        "$order": "issue_date DESC",
        "$limit": 5000,
    }
    rows = _get(DATASETS["ladbs_permits"]["url"], params)
    (RAW / "palisades_rebuilds.json").write_text(json.dumps(rows))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["parcel_ain"] = df.apply(build_ain, axis=1)
    df["address"] = df["address_start"].astype(str) + " " + df["street_name"].astype(str)
    df["signal"] = "palisades_fire_rebuild"
    return df


def adu_capacity_plays() -> pd.DataFrame:
    """Screen the assessor roll for SB 1211 capacity: 8+ existing units AND
    room for 8+ detached ADUs. Pure parcel geometry + ownership screening.

    Heuristic is deliberately crude (ignores setbacks/parking/slope) --
    over-inclusion is correct for a first screen; expect ~10:1 raw-to-real.
    """
    p = CFG["segment_params"]["adu_capacity"]
    roll_path = RAW / "assessor_roll.parquet"
    if not roll_path.exists():
        print("adu_capacity: assessor roll missing, skipping segment")
        return pd.DataFrame()

    roll = pd.read_parquet(roll_path)
    # Verify field names on first run against actual roll schema:
    #   units, lot_sqft, building_sqft, stories, use_code
    mf = roll[
        (roll["units"].fillna(0).astype(int) >= p["min_existing_units"])
        & (roll["use_code"].astype(str).str.startswith(tuple(
            str(c) for c in p["multifamily_use_codes"])))
    ].copy()

    est_stories = mf.get("stories", pd.Series(2, index=mf.index)).fillna(2).clip(lower=1)
    mf["est_footprint"] = mf["building_sqft"].astype(float) / est_stories
    mf["buildable_yard"] = mf["lot_sqft"].astype(float) - mf["est_footprint"]
    mf = mf[mf["buildable_yard"] >= p["min_buildable_yard_sqft"]]

    mf["adu_capacity_est"] = (
        mf["buildable_yard"] / (p["adu_footprint_sqft"] * 1.4)  # 40% circulation
    ).astype(int).clip(upper=8)  # SB 1211 detached cap
    mf = mf[mf["adu_capacity_est"] >= 8]

    mf["signal"] = "sb1211_adu_capacity"
    mf["signal_date"] = pd.Timestamp.now().date().isoformat()  # no decay
    mf["parcel_ain"] = mf["ain"]
    mf["valuation"] = mf["adu_capacity_est"] * 250_000  # rough project value proxy
    mf["permit_or_case"] = "prospect"
    return mf
