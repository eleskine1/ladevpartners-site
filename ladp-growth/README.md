# ladp-growth

Lead generation pipeline for LA development partners. Sources high-intent
prospects from public permit and entitlement data, scores them against the
LADP ideal client profile (larger multifamily / investor-owned projects),
and feeds approved targets into direct mail (Lob) and email (Resend) outreach.

## Architecture

ingest (Socrata/ArcGIS pulls, daily)
  -> normalize (common schema: parcel, address, owner, signal, dates, valuation)
  -> enrich (assessor owner lookup, LLC/portfolio detection, dedupe)
  -> score (ICP fit x intent x timing -> 0-100)
  -> review queue (Eli approves batches)
  -> outreach (Lob letter / Resend sequence, logged)
  -> pipeline tracking (status per prospect)

## Data sources (v1)

- LADBS Building Permits Issued 2020-present (Socrata pi9x-tg5x)
- LA City Planning entitlement cases (GeoHub / PDIS): TOC, DB, ED1, VTT
- LADBS Certificates of Occupancy (Socrata 3f9m-afei)
- LADBS Inspections (Socrata 9w5z-rg2h) for stall detection
- Santa Monica open data (permits)
- LA County Assessor parcel roll: owner name + mailing address + portfolio
  detection + ADU capacity screening

## Target segments

1. Entitled-not-permitted: planning case approved > 6 months ago, >= 10
   units or >= $2M implied cost, no building permit issued since approval.
2. Permit issued, no progress: permit issued > 9 months ago, valuation
   >= $1M, no passing inspections.
3. Big new issuance: permit issued last 30 days, valuation >= $3M,
   investor-entity owner.
4. Portfolio owners: same mailing address on >= 3 parcels with activity.
   LWK-profile prospects -- pitch the platform, not the project.
5. Palisades fire rebuilds: 90272 rebuild permits >= $1.5M. Resource-first
   tone, attorney compliance check before any send.
6. SB 1211 ADU capacity: existing 8+ unit multifamily parcels with >= 5000sf
   buildable yard -> room for 8 detached ADUs. Proactive pitch; outreach
   asset is a per-parcel feasibility one-pager, not a letter.

## Runbook

pip install -r requirements.txt
python -m src.ingest
python -m src.enrich
python -m src.score

Scheduled via .github/workflows/daily.yml. Outreach modules only send
against data/approved/ -- nothing goes out without explicit approval.

## Guardrails

- Direct mail (Lob) is the default channel.
- Email only where an address is business-public. CAN-SPAM compliant:
  real postal address, working unsubscribe, honest subject lines.
  Suppression list checked before every send.
- No calls/texts from automation (TCPA). Phone outreach stays manual.
- One owner never receives more than 1 letter per 60 days across campaigns.
- Palisades segment: nothing sends until attorney confirms no
  disaster-solicitation restrictions apply to owner's-rep services.
