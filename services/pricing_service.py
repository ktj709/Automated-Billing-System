from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd


MASTER_EXCEL_PATH = Path("data/Blessings_City_Master_Data.xlsx")


class PricingService:
    """Lookup helper for per-flat pricing.

    This service reads the Blessings City master Excel file to obtain
    the per-unit rate and fixed charge for each flat (by flat code,
    e.g. "B17-FF").

    It is intentionally read-only and does not modify any database
    data, including the November bills.

    The effective 9₹/no-fixed-charge units observed in the live
    Supabase bills (e.g. C14-SF, D3-SF, D4-SF) are enforced here as a
    small in-code override so that the workflow and estimates stay
    aligned with production pricing even if the master Excel does not
    yet mark them as 9₹.

    In addition, fixed charges can depend on the BHK count when that
    information is encoded in the identifier (e.g. "5BHK-B17-FF").
    Where a recognised BHK prefix is present, we apply the following
    per-type fixed charges unless the flat is a special 9₹/no-fixed
    unit:

      - 5 BHK: 2311
      - 4 BHK: 1890
      - 2 BHK: 1474

    These values are applied consistently across the workflow so that
    all 5/4/2 BHK units share the same maintenance component.
    """

    @staticmethod
    def normalize_flat_code(identifier: str | None) -> str | None:
        """Normalise a unit/flat identifier into a canonical code.

        The UI often uses values like "5BHK-B17-FF" where the first
        segment encodes the unit type. The master pricing sheet and
        Supabase `flats.code` store just "B17-FF". This helper strips
        any leading type prefix and returns the last two segments so
        that lookups remain consistent.
        """
        if not identifier:
            return None

        raw = str(identifier).strip().upper()
        if not raw:
            return None

        parts = [p for p in raw.split("-") if p]
        if len(parts) >= 2:
            return "-".join(parts[-2:])
        return raw

    @staticmethod
    def extract_bhk_from_identifier(identifier: str | None) -> int | None:
        """Extract the BHK count from a unit identifier, if present.

        Examples::

            "5BHK-B17-FF" -> 5
            "2BHK-A01-GF" -> 2

        If no BHK pattern is found, returns None so that callers can
        fall back to per-flat or default pricing.
        """
        if not identifier:
            return None

        raw = str(identifier).strip().upper()
        if not raw:
            return None

        if "BHK" not in raw:
            return None

        prefix = raw.split("BHK", 1)[0]
        digits = "".join(ch for ch in prefix if ch.isdigit())
        if not digits:
            return None

        try:
            return int(digits)
        except Exception:
            return None

    @classmethod
    @lru_cache(maxsize=1)
    def _load_master(cls) -> Dict[str, Dict[str, float]]:
        """Load master Excel and build a flat_code -> pricing map.

        Expected columns (case-insensitive match):
          - "Flat no"      : flat identifier (e.g. "B17")
          - "Floor"        : floor code ("GF"/"FF"/"SF")
          - "Fixed Charge" : fixed maintenance charge (₹)
          - "Rate Per Unit": energy rate (₹/kWh), e.g. 12 or 9
        """
        path = MASTER_EXCEL_PATH
        if not path.exists():
            return {}

        # Try legacy header row index first (row 3), then fall back to
        # the first row if required columns are not found.
        df = pd.read_excel(path, header=2)

        # Normalise column names for robust lookup
        cols = {str(c).strip().lower(): c for c in df.columns}

        def find_col(name_sub: str) -> str | None:
            for key, col in cols.items():
                if name_sub in key:
                    return col
            return None

        col_flat = find_col("flat no") or find_col("flat_no") or find_col("flat")
        col_floor = find_col("floor")
        col_fixed = find_col("fixed charge") or find_col("fixed_charges")
        col_rate = find_col("rate per unit") or find_col("rate_per_unit")

        # If we didn't find the required columns, try again using the
        # first row as the header (header=0). This matches the current
        # Blessings master file layout.
        if not (col_flat and col_floor and col_fixed and col_rate):
            df = pd.read_excel(path, header=0)
            cols = {str(c).strip().lower(): c for c in df.columns}

            col_flat = find_col("flat no") or find_col("flat_no") or find_col("flat")
            col_floor = find_col("floor")
            col_fixed = find_col("fixed charge") or find_col("fixed_charges")
            col_rate = find_col("rate per unit") or find_col("rate_per_unit")

            if not (col_flat and col_floor and col_fixed and col_rate):
                # Missing required cols – return empty map so callers fall back
                return {}

        pricing: Dict[str, Dict[str, float]] = {}

        for _, row in df.iterrows():
            flat_no = str(row.get(col_flat, "")).strip()
            floor = str(row.get(col_floor, "")).strip()
            if not flat_no or not floor or flat_no.lower() == "nan":
                continue

            flat_code = f"{flat_no}-{floor}".upper()

            try:
                fixed_val = float(str(row.get(col_fixed, 0)).replace(",", "").strip() or 0)
            except Exception:
                fixed_val = 0.0

            try:
                rate_val = float(str(row.get(col_rate, 0)).replace(",", "").strip() or 0)
            except Exception:
                rate_val = 0.0

            pricing[flat_code] = {
                "rate_per_unit": rate_val,
                "fixed_charge": fixed_val,
            }

        return pricing

    @classmethod
    def get_pricing_for_flat(cls, flat_code: str) -> Tuple[float, float]:
        """Return (rate_per_unit, fixed_charge) for a flat/unit.

        ``flat_code`` may be either a plain flat code ("B17-FF") or a
        richer identifier such as "5BHK-B17-FF". We first extract any
        BHK prefix for use in BHK-based fixed-charge rules, then
        normalise to a canonical flat code ("B17-FF") for the
        Excel-based lookup.

        If the flat is not found or the master file is missing, this
        falls back to a default of (12.0, 0.0) before any BHK or
        9₹-unit overrides are applied.
        """
        bhk_count = cls.extract_bhk_from_identifier(flat_code)
        norm_code = cls.normalize_flat_code(flat_code)
        if not norm_code:
            return 12.0, 0.0

        mapping = cls._load_master()
        info = mapping.get(norm_code)
        if not info:
            return 12.0, 0.0

        rate = float(info.get("rate_per_unit", 12.0))
        fixed = float(info.get("fixed_charge", 0.0))

        # Apply BHK-based fixed charges when we have a recognised BHK
        # prefix. This ensures all 5/4/2 BHK units share the same
        # maintenance component regardless of per-flat values in the
        # master sheet.
        bhk_fixed_overrides = {
            5: 2311.0,
            4: 1890.0,
            2: 1474.0,
        }
        if bhk_count in bhk_fixed_overrides:
            fixed = bhk_fixed_overrides[bhk_count]

        # Supabase-based override: these flats are billed at 9₹ with no
        # fixed charge in production. Enforce that explicitly so the
        # workflow matches existing bills even if the master sheet is
        # not yet updated.
        nine_rupee_flats = {"C14-SF", "D3-SF", "D4-SF"}
        if norm_code in nine_rupee_flats:
            rate = 9.0
            fixed = 0.0

        # Business rule: units billed at ₹9/kWh should not have any
        # fixed/maintenance charges applied, even if the master sheet
        # or BHK rules contain a non-zero value. Enforce that
        # explicitly here so all downstream calculations stay
        # consistent.
        if abs(rate - 9.0) < 1e-6:
            fixed = 0.0

        return rate, fixed
