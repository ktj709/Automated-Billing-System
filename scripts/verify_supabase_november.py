import os
from datetime import datetime

import pandas as pd

from services.database_service import DatabaseService


EXCEL_PATH = r"d:\\Machine Learning Projects\\Billing\\data\\Bills_Summary_November2025.xlsx"


def load_excel_map() -> dict:
    """Load flat -> total_amount mapping from the November 2025 Excel file.

    This mirrors the logic in verify_data.py so we use the same header
    detection and column selection heuristics.
    """
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"Excel file not found at {EXCEL_PATH}")

    temp_df = pd.read_excel(EXCEL_PATH, header=None)
    header_idx = -1
    for i, row in temp_df.iterrows():
        row_str = " ".join([str(x) for x in row if pd.notna(x)])
        if "Flat" in row_str and ("Amount" in row_str or "Units" in row_str):
            header_idx = i
            break

    if header_idx == -1:
        raise RuntimeError("Could not locate header row in November Excel sheet")

    df = pd.read_excel(EXCEL_PATH, header=header_idx)

    flat_col = None
    amount_col = None

    for c in df.columns:
        c_str = str(c)
        if "Flat" in c_str and ("No" in c_str or "Code" in c_str):
            flat_col = c
        if "Amount" in c_str and "Total" in c_str:
            amount_col = c
        if "Bill" in c_str and "Amount" in c_str and not amount_col:
            amount_col = c

    if not flat_col or not amount_col:
        # Fallback heuristics, identical to verify_data.py
        if not flat_col:
            flat_col = df.columns[0]
        if not amount_col:
            candidates = [c for c in df.columns if "Amount" in str(c)]
            if candidates:
                amount_col = candidates[0]

    excel_map: dict[str, float] = {}
    for _, row in df.iterrows():
        flat = str(row[flat_col]).strip()
        if not flat:
            continue
        try:
            amount = float(row[amount_col])
        except Exception:
            amount = 0.0
        excel_map[flat] = amount

    return excel_map


def load_snapshot_map() -> dict:
    """Load flat -> total_amount mapping from the original JSON snapshots.

    These batch JSON files (batch1.json, batch2.json, batch3.json) were
    exported from Supabase at the time of the original November 2025
    verification and serve as our "baseline" view of that data.
    """
    snapshot_files = ["batch1.json", "batch2.json", "batch3.json"]
    combined: list[dict] = []
    for name in snapshot_files:
        if os.path.exists(name):
            df_path = os.path.abspath(name)
            with open(df_path, "r", encoding="utf-8") as f:
                try:
                    combined.extend(pd.read_json(f).to_dict(orient="records"))
                except ValueError:
                    # Fallback: standard json.load in case file isn't strict JSON-Lines
                    import json

                    f.seek(0)
                    combined.extend(json.load(f))

    snapshot_map: dict[str, float] = {}
    for item in combined:
        code = str(item.get("code", "")).strip()
        if not code:
            continue
        try:
            amount = float(item.get("total_amount", 0) or 0)
        except Exception:
            amount = 0.0
        snapshot_map[code] = amount

    return snapshot_map


def load_supabase_map() -> dict:
    """Load flat -> total_amount mapping for November 2025 from live Supabase.

    Uses the normalized `bills` + `flats` tables and aggregates
    `total_amount` by flat code.
    """
    db = DatabaseService()
    if not getattr(db, "use_supabase", False):
        raise RuntimeError("DatabaseService is not in Supabase mode; cannot verify Supabase data.")

    sb = db.supabase

    # Map flat_id -> flat code
    flats_resp = sb.table("flats").select("id, code").execute()
    flats = flats_resp.data or []
    id_to_code: dict[int, str] = {}
    for f in flats:
        flat_id = f.get("id")
        code = f.get("code")
        if flat_id is not None and code:
            id_to_code[int(flat_id)] = str(code).strip()

    # Fetch all bills whose billing_period_start falls in November 2025
    start = "2025-11-01"
    next_month = "2025-12-01"

    bills_resp = (
        sb.table("bills")
        .select("flat_id, total_amount, billing_period_start")
        .gte("billing_period_start", start)
        .lt("billing_period_start", next_month)
        .execute()
    )

    bills = bills_resp.data or []

    supabase_map: dict[str, float] = {}
    for b in bills:
        flat_id = b.get("flat_id")
        if flat_id is None:
            continue
        code = id_to_code.get(int(flat_id))
        if not code:
            continue
        try:
            amt_raw = b.get("total_amount", 0) or 0
            amount = float(amt_raw)
        except Exception:
            amount = 0.0

        supabase_map[code] = supabase_map.get(code, 0.0) + amount

    return supabase_map


def main() -> None:
    excel_map = load_excel_map()
    supabase_map = load_supabase_map()
    snapshot_map = load_snapshot_map()

    # 1) Live Supabase vs Excel
    mismatches: list[tuple[str, float, float]] = []
    missing_in_supabase: list[str] = []
    missing_in_excel: list[str] = []

    all_flats_excel = set(excel_map.keys()) | set(supabase_map.keys())

    for flat in sorted(all_flats_excel):
        if flat not in excel_map:
            missing_in_excel.append(flat)
            continue
        if flat not in supabase_map:
            missing_in_supabase.append(flat)
            continue

        val_excel = excel_map[flat]
        val_supabase = supabase_map[flat]

        if abs(val_excel - val_supabase) > 1.0:  # allow tiny rounding difference
            mismatches.append((flat, val_excel, val_supabase))

    lines: list[str] = []
    lines.append("# Live Supabase vs Excel Verification: November 2025")
    lines.append(f"**Run at:** {datetime.now().isoformat()}")
    lines.append(f"**Excel Source:** `{EXCEL_PATH}`")
    lines.append("\n## Summary (Live Supabase vs Excel)")

    if not mismatches and not missing_in_supabase and not missing_in_excel:
        summary = "✅ SUCCESS: Live Supabase November 2025 data matches the Excel baseline."
        lines.append(summary)
        print(summary)
    else:
        lines.append("❌ DISCREPANCIES FOUND between live Supabase and Excel.")
        lines.append(f"- Mismatches: {len(mismatches)}")
        lines.append(f"- Missing in Supabase: {len(missing_in_supabase)}")
        lines.append(f"- Missing in Excel: {len(missing_in_excel)}")

        if mismatches:
            lines.append("\n### Mismatches (|diff| > 1.0)")
            lines.append("| Flat Code | Excel Amount | Supabase Amount | Difference |")
            lines.append("|---|---|---|---|")
            for flat, v_excel, v_supa in mismatches:
                diff = v_excel - v_supa
                lines.append(f"| {flat} | {v_excel} | {v_supa} | {diff:.2f} |")

        if missing_in_supabase:
            lines.append("\n### Missing in Supabase")
            lines.append(", ".join(sorted(missing_in_supabase)))

        if missing_in_excel:
            lines.append("\n### Missing in Excel")
            lines.append(", ".join(sorted(missing_in_excel)))

    # 2) Live Supabase vs original JSON snapshot ("beginning" state)
    snapshot_mismatches: list[tuple[str, float, float]] = []
    snapshot_missing_live: list[str] = []
    snapshot_missing_baseline: list[str] = []

    all_flats_snapshot = set(snapshot_map.keys()) | set(supabase_map.keys())

    for flat in sorted(all_flats_snapshot):
        if flat not in snapshot_map:
            snapshot_missing_baseline.append(flat)
            continue
        if flat not in supabase_map:
            snapshot_missing_live.append(flat)
            continue

        v_baseline = snapshot_map[flat]
        v_live = supabase_map[flat]

        if abs(v_baseline - v_live) > 1.0:
            snapshot_mismatches.append((flat, v_baseline, v_live))

    lines.append("\n## Live Supabase vs Original JSON Snapshot")

    if not snapshot_mismatches and not snapshot_missing_live and not snapshot_missing_baseline:
        summary2 = "✅ Live Supabase November 2025 totals match the original batch JSON snapshot (no changes since baseline)."
        lines.append(summary2)
        print(summary2)
    else:
        lines.append("❌ Differences detected between live Supabase and the original JSON snapshot.")
        lines.append(f"- Mismatches: {len(snapshot_mismatches)}")
        lines.append(f"- Missing in Live Supabase: {len(snapshot_missing_live)}")
        lines.append(f"- Missing in Baseline Snapshot: {len(snapshot_missing_baseline)}")

        if snapshot_mismatches:
            lines.append("\n### Snapshot Mismatches (|diff| > 1.0)")
            lines.append("| Flat Code | Baseline Amount | Live Supabase Amount | Difference |")
            lines.append("|---|---|---|---|")
            for flat, v_base, v_live in snapshot_mismatches:
                diff = v_base - v_live
                lines.append(f"| {flat} | {v_base} | {v_live} | {diff:.2f} |")

        if snapshot_missing_live:
            lines.append("\n### Missing in Live Supabase")
            lines.append(", ".join(sorted(snapshot_missing_live)))

        if snapshot_missing_baseline:
            lines.append("\n### Missing in Baseline Snapshot")
            lines.append(", ".join(sorted(snapshot_missing_baseline)))

    report_path = "verification_report_supabase_nov2025.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
