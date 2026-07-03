"""Enrich normalized prospects with assessor ownership + portfolio signals.

Requires data/raw/assessor_roll.parquet (quarterly download).
Adds: owner_name, mailing_address, units, owner_parcel_count.
"""

import pathlib

import pandas as pd

NORM = pathlib.Path("data/normalized")
RAW = pathlib.Path("data/raw")
ENR = pathlib.Path("data/enriched")
ENR.mkdir(parents=True, exist_ok=True)


def load_suppression() -> set[str]:
    p = pathlib.Path("data/suppression.csv")
    if not p.exists():
        return set()
    return set(pd.read_csv(p)["owner_name"].str.upper())


def main() -> None:
    prospects = pd.read_parquet(NORM / "prospects.parquet")
    roll_path = RAW / "assessor_roll.parquet"
    if not roll_path.exists():
        print("WARNING: assessor roll missing -- writing through un-enriched")
        prospects.to_parquet(ENR / "prospects_enriched.parquet")
        return

    roll = pd.read_parquet(roll_path)[
        ["ain", "owner_name", "mailing_address", "units"]
    ]
    df = prospects.merge(
        roll, left_on="parcel_ain", right_on="ain", how="left",
        suffixes=("", "_roll"),
    )
    if "units" not in prospects.columns:
        df["units"] = df.get("units_roll")

    addr_counts = roll.groupby("mailing_address")["ain"].count().rename("owner_parcel_count")
    df = df.merge(addr_counts, on="mailing_address", how="left")
    df["owner_parcel_count"] = df["owner_parcel_count"].fillna(1).astype(int)

    df = df.sort_values("valuation", ascending=False).drop_duplicates("parcel_ain")

    supp = load_suppression()
    df = df[~df["owner_name"].fillna("").str.upper().isin(supp)]

    df.to_parquet(ENR / "prospects_enriched.parquet")
    print(f"enriched: {len(df)} prospects")


if __name__ == "__main__":
    main()
