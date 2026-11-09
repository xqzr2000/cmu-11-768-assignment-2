"""Regenerate the synthetic CSV inputs for the Part 3 tasks (seeded, deterministic).

    uv run python scripts/make_part3_inputs.py

Writes tasks/<task_id>/inputs/*.csv. The files are large on purpose: the
validator clips each input file at 20k characters, so the judge cannot read
every row and has to trust or recompute aggregates.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / "tasks"
REGIONS = ["North", "South", "East", "West"]
PRODUCTS = ["Atlas", "Beacon", "Cobalt", "Delta", "Ember", "Falcon", "Granite",
            "Harbor", "Iris", "Juniper", "Krypton", "Lumen"]


def transactions() -> pd.DataFrame:
    rng = np.random.default_rng(768)
    n = 3000
    days = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, n), unit="D")
    region = rng.choice(REGIONS, n, p=[0.31, 0.22, 0.27, 0.20])
    weights = np.linspace(2.0, 0.4, len(PRODUCTS))
    product = rng.choice(PRODUCTS, n, p=weights / weights.sum())
    base_price = dict(zip(PRODUCTS, np.round(rng.uniform(8, 60, len(PRODUCTS)), 2)))
    units = rng.integers(1, 25, n)
    price = np.array([base_price[p] for p in product]) * rng.uniform(0.9, 1.1, n)
    frame = pd.DataFrame({
        "order_id": [f"A{100000 + i}" for i in range(n)],
        "date": days.strftime("%Y-%m-%d"),
        "region": region,
        "product": product,
        "units": units,
        "unit_price": np.round(price, 2),
    }).sort_values(["date", "order_id"]).reset_index(drop=True)
    return frame


def sensors() -> pd.DataFrame:
    rng = np.random.default_rng(11768)
    stamps = pd.date_range("2025-06-01", periods=14 * 24 * 12, freq="5min")
    rows = []
    for sensor, offset, noise in (("S1", 21.0, 0.8), ("S2", 24.5, 1.4), ("S3", 19.0, 0.6)):
        hours = stamps.hour + stamps.minute / 60
        temp = offset + 3.5 * np.sin((hours - 9) / 24 * 2 * np.pi) + rng.normal(0, noise, len(stamps))
        temp += np.linspace(0, 2.0 if sensor == "S2" else 0.5, len(stamps))
        temp = np.round(np.asarray(temp, dtype=float), 2).astype(object)
        temp[rng.random(len(stamps)) < 0.04] = ""  # dropouts
        rows.append(pd.DataFrame({"timestamp": stamps.strftime("%Y-%m-%d %H:%M"),
                                  "sensor": sensor, "temp_c": temp}))
    return pd.concat(rows).sort_values(["timestamp", "sensor"]).reset_index(drop=True)


def main() -> None:
    sales = transactions()
    for task in ("quarterly-revenue-by-region", "top-products-unit-share"):
        out = ROOT / task / "inputs"
        out.mkdir(parents=True, exist_ok=True)
        sales.to_csv(out / "transactions.csv", index=False)
    out = ROOT / "sensor-daily-median" / "inputs"
    out.mkdir(parents=True, exist_ok=True)
    sensors().to_csv(out / "sensors.csv", index=False)
    for path in sorted(ROOT.glob("*/inputs/*.csv")):
        print(f"{path.relative_to(ROOT.parent)}: {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
