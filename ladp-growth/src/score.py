"""Score enriched prospects against config.yaml -> data/scored/targets.csv.

Score = intent (max one primary signal) + fit (additive) - staleness decay.
Tier A >=75 -> personal letter + Eli call
Tier B >=55 -> Lob letter + email sequence
Tier C >=40 -> nurture
"""

import pathlib

import pandas as pd
import yaml

CFG = yaml.safe_load(open("config.yaml"))
NORM = pathlib.Path("data/normalized")
ENR = pathlib.Path("data/enriched")
OUT = pathlib.Path("data/scored")
OUT.mkdir(parents=True, exist_ok=True)

INVESTOR_TOKENS = (" LLC", " L.L.C", " LP", " L.P", " LTD", " TRUST",
                   " PARTNERS", " CAPITAL", " HOLDINGS", " INVESTMENTS", " PROPERTIES")


def is_investor_entity(owner: str) -> bool:
    o = f" {str(owner).upper()}"
    return any(tok in o for tok in INVESTOR_TOKENS)


def score_row(r: pd.Series) -> tuple[int, list[str]]:
    pts, why = 0, []
    sig = CFG["intent_signals"].get(r.get("signal"), 0)
    pts += sig
    why.append(f"signal:{r.get('signal')}(+{sig})")

    val = float(r.get("valuation") or 0)
    if val >= CFG["project_floor"]["sweet_spot_valuation_usd"]:
        pts += CFG["fit_signals"]["valuation_over_sweet_spot"]
        why.append("valuation>=sweet_spot(+20)")

    units = int(float(r.get("units") or 0))
    if units >= 10:
        pts += CFG["fit_signals"]["units_10_plus"]; why.append("units10+(+10)")
    if units >= 25:
        pts += CFG["fit_signals"]["units_25_plus"]; why.append("units25+(+10)")

    if is_investor_entity(r.get("owner_name", "")):
        pts += CFG["fit_signals"]["investor_entity_owner"]
        why.append("investor_entity(+15)")

    if int(r.get("owner_parcel_count") or 0) >= CFG["owner_profile"]["portfolio_bonus_threshold"]:
        pts += CFG["fit_signals"]["portfolio_owner_3plus"]
        why.append("portfolio3+(+15)")

    if r.get("signal") == "palisades_fire_rebuild" and val >= 2_000_000:
        pts += CFG["fit_signals"]["rebuild_valuation_2m_plus"]
        why.append("rebuild$2M+(+15)")

    if int(float(r.get("adu_capacity_est") or 0)) >= 12:
        pts += CFG["fit_signals"]["adu_capacity_12_plus"]
        why.append("aducap12+(+10)")

    age_days = (pd.Timestamp.now() - pd.to_datetime(r.get("signal_date"))).days
    decay = (age_days // 90) * CFG["decay"]["points_per_90d"]
    pts -= decay
    if decay:
        why.append(f"decay(-{decay})")
    return pts, why


def tier(score: int) -> str:
    t = CFG["tiers"]
    if score >= t["A"]:
        return "A"
    if score >= t["B"]:
        return "B"
    if score >= t["C"]:
        return "C"
    return "ignore"


def main() -> None:
    src = ENR / "prospects_enriched.parquet"
    if not src.exists():
        src = NORM / "prospects.parquet"  # degrade gracefully pre-enrichment
    df = pd.read_parquet(src)

    scored = df.apply(score_row, axis=1, result_type="expand")
    df["score"], df["score_reasons"] = scored[0], scored[1].str.join("; ")
    df["tier"] = df["score"].apply(tier)
    df = df[df["tier"] != "ignore"].sort_values("score", ascending=False)

    df.to_csv(OUT / "targets.csv", index=False)
    print(df["tier"].value_counts().to_string())
    print(f"\nTop 10:\n{df[['address','signal','score','tier']].head(10).to_string()}")


if __name__ == "__main__":
    main()
