#!/usr/bin/env python3
"""Check raw benchmark/load evidence against generated summaries (no dependencies)."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmarks"


def percentile(values, q):
    return sorted(values)[max(0, math.ceil(len(values) * q / 100) - 1)]


def main():
    baseline = json.loads((BENCH / "01-quickstart-results.json").read_text(encoding="utf-8"))
    for label, summary in baseline.items():
        rows = summary["requests"]
        assert len(rows) == summary["n_requests"] == 10, label
        assert all(row["token_count_source"] == "timings" for row in rows), label
        for prefix, key, digits in (("ttft", "ttft_ms", 1), ("tpot", "tpot_ms", 2),
                                     ("e2e", "e2e_ms", 1)):
            for q in (50, 95, 99) if prefix == "e2e" else (50, 95):
                assert summary[f"{prefix}_p{q}"] == round(
                    percentile([row[key] for row in rows], q), digits), (label, prefix, q)
        assert summary["decode_tok_s"] == round(
            1000 / percentile([row["tpot_ms"] for row in rows], 50), 1)

    serving = json.loads((BENCH / "02-server-results.json").read_text(encoding="utf-8"))
    for run in serving["runs"]:
        users = run["users"]
        rows = [json.loads(line) for line in
                (BENCH / "evidence" / f"requests-{users}.jsonl").read_text(encoding="utf-8").splitlines()]
        assert len(rows) == run["requests"], users
        assert sum(not row["success"] for row in rows) == run["failures"], users
        assert math.isclose(sum(row["elapsed_ms"] for row in rows) / len(rows),
                            run["avg_ms"], abs_tol=0.001), users
        assert math.isclose(max(row["elapsed_ms"] for row in rows), run["max_ms"], abs_tol=0.001)
        with (BENCH / f"locust-{users}_stats.csv").open(newline="", encoding="utf-8") as file:
            aggregate = next(row for row in csv.DictReader(file) if row["Name"] == "Aggregated")
        assert int(aggregate["Request Count"]) == len(rows), users

    tune = json.loads((BENCH / "01-tuning-tg128.json").read_text(encoding="utf-8"))
    assert tune["best"]["tok_s"] == max(row["tok_s"] for row in tune["rows"])
    assert all(row["tok_s"] > 0 and "±" in row["raw_output"] for row in tune["rows"])
    rag = json.loads((BENCH / "03-integration-results.json").read_text(encoding="utf-8"))
    assert len(rag["results"]) == 3
    assert all(row["answer"] and row["contexts"] for row in rag["results"])
    for key, expected in rag["mean_ms"].items():
        assert round(sum(row["timings_ms"][key] for row in rag["results"]) / 3, 1) == expected
    print("PASS: raw timings, token counts, Locust CSVs, tuning and 3 RAG queries agree.")


if __name__ == "__main__":
    main()
