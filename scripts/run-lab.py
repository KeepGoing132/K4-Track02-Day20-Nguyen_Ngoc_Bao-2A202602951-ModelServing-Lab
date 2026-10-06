#!/usr/bin/env python3
"""Run the base lab and retain unedited command output as evidence.

Usage: .venv\Scripts\python scripts/run-lab.py [--skip-measure]
Measurements use CPU, 14 threads, 4 slots and the shipped token budgets.
Screenshots and the student's interpretation remain separate submission steps.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
import labkit

EVIDENCE = ROOT / "benchmarks" / "evidence"


def launch(args: list[str], filename: str):
    path = EVIDENCE / filename
    log = path.open("w", encoding="utf-8")
    log.write(f"Started UTC: {datetime.now(timezone.utc).isoformat()}\n")
    log.write(f"Command: {subprocess.list2cmdline(args)}\n")
    knobs = ("LAB_N_GPU_LAYERS", "LAB_N_THREADS", "LAB_N_CTX", "LAB_PARALLEL",
             "LAB_REASONING", "LAB_MAX_TOKENS", "LAB_LOAD_SHORT_TOKENS",
             "LAB_LOAD_LONG_TOKENS", "LAB_TEMPERATURE", "LAB_SERVER_PORT")
    log.write("Environment: " + json.dumps({key: os.environ[key] for key in knobs
              if key in os.environ}, sort_keys=True) + "\n\n")
    log.flush()
    proc = subprocess.Popen(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    return proc, log


def finish(proc, log, filename):
    try:
        code = proc.wait()
        log.write(f"\nExit code: {code}\nFinished UTC: {datetime.now(timezone.utc).isoformat()}\n")
    finally:
        log.close()
    if code:
        raise RuntimeError(f"Exit {code}: see benchmarks/evidence/{filename}")
    print(f"OK: {filename}", flush=True)


def run(script: str, filename: str, *extra: str):
    print(f"Running {script} ...", flush=True)
    proc, log = launch([sys.executable, "-u", script, *extra], filename)
    finish(proc, log, filename)


def drain():
    import httpx
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        response = httpx.get(labkit.base_url() + "/metrics", timeout=10)
        response.raise_for_status()
        gauges = dict(line.split() for line in response.text.splitlines()
                      if not line.startswith("#") and len(line.split()) == 2)
        if all(float(gauges.get(key, 0)) == 0 for key in
               ("llamacpp:requests_processing", "llamacpp:requests_deferred")):
            return
        time.sleep(1)
    raise RuntimeError("Server did not drain; do not mix the next test with pending load")


def load(users: int, metrics: bool = False):
    filename = f"locust-{users}.txt"
    args = [sys.executable, "-u", "-m", "locust", "-f", "labs/02-serve/load-test.py",
            "--headless", "-u", str(users), "-r", "5" if users == 10 else "25",
            "-t", "1m", "--host", labkit.base_url(), "--csv",
            f"benchmarks/locust-{users}", "--csv-full-history"]
    request_log = EVIDENCE / f"requests-{users}.jsonl"
    request_log.write_text("", encoding="utf-8")
    os.environ["LAB_REQUEST_LOG"] = str(request_log)
    proc, log = launch(args, filename)
    metric_proc = metric_log = None
    try:
        if metrics:
            metric_proc, metric_log = launch(
                [sys.executable, "-u", "labs/02-serve/record-metrics.py",
                 "--duration", "60", "--label", "u50"], "metrics-u50.txt")
        finish(proc, log, filename)
        stats_path = ROOT / f"benchmarks/locust-{users}_stats.csv"
        # Locust on Windows may emit CRCRLF. Normalize line endings only;
        # preserve every generated number and CSV field.
        raw_stats = stats_path.read_bytes()
        stats_path.write_bytes(raw_stats.replace(b"\r\r\n", b"\n").replace(b"\r\n", b"\n"))
        if metric_proc:
            finish(metric_proc, metric_log, "metrics-u50.txt")
        drain()
    finally:
        for child, output in ((proc, log), (metric_proc, metric_log)):
            if child is not None and child.poll() is None:
                child.terminate()
                child.wait(timeout=15)
            if output and not output.closed:
                output.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-measure", action="store_true")
    args = parser.parse_args()
    os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                      LAB_N_GPU_LAYERS="0", LAB_N_THREADS="14", LAB_N_CTX="2048",
                      LAB_PARALLEL="4", LAB_REASONING="off", LAB_MAX_TOKENS="64",
                      LAB_LOAD_SHORT_TOKENS="48", LAB_LOAD_LONG_TOKENS="96",
                      LAB_TEMPERATURE="0.7")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    run("labs/00-setup/detect-hardware.py", "probe.txt")
    if not args.skip_measure:
        run("labs/01-measure/benchmark.py", "bench.txt")
        run("labs/01-measure/tune.py", "tune.txt")
    model = str(ROOT / labkit.primary_model())
    server, server_log = launch(labkit.server_cmd(model), "server.txt")
    try:
        if not labkit.wait_healthy(proc=server):
            raise RuntimeError("Server startup failed: see benchmarks/evidence/server.txt")
        run("labs/02-serve/smoke-test.py", "smoke.txt")
        load(10)
        load(50, metrics=True)
        run("labs/02-serve/load-report.py", "load-report.txt")
        run("labs/03-integrate/pipeline.py", "pipeline.txt")
    finally:
        server.terminate()
        try:
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
        server_log.close()
    print("Measurements complete. Read the reports, add real screenshots, then run verify.")


if __name__ == "__main__":
    main()
