"""Run the small experiment used in the report. Keep every result."""

import csv
import hashlib
import os
import platform
import time
from pathlib import Path

from randomness import check_randomness, generate_bytes

TRIALS = 30


def main():
    folder = Path("results")
    folder.mkdir(exist_ok=True)
    rows = []
    for size in (1024, 4096, 16384):
        for trial in range(1, TRIALS + 1):
            for source, generate in (("generator", generate_bytes), ("OS baseline", os.urandom)):
                start = time.perf_counter()
                data = generate(size)
                result = check_randomness(data)
                result["seconds"] = time.perf_counter() - start
                result["source"] = source
                result["trial"] = trial
                rows.append(result)

    for name, data in (
        ("all zeros", bytes(4096)),
        ("all ones", b"\xff" * 4096),
        ("alternating bits", b"\xaa" * 4096),
        ("repeated 0011", b"\x33" * 4096),
        ("cycling byte values", bytes(range(256)) * 16),
        ("biased halves", bytes(2048) + b"\xff" * 2048),
        ("repeated 64-byte block", hashlib.shake_256(b"block").digest(64) * 64),
        ("known seed SHAKE", hashlib.shake_256(b"known seed").digest(4096)),
    ):
        result = check_randomness(data)
        result.update(seconds=0, source=name, trial=1)
        rows.append(result)

    with (folder / "evaluation.csv").open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    environment = f"Python {platform.python_version()}\n{platform.platform()}\n"
    (folder / "environment.txt").write_text(environment, encoding="utf-8")
    print(environment, end="")
    for source in ("generator", "OS baseline"):
        for size in (1024, 4096, 16384):
            group = [r for r in rows if r["source"] == source and r["bytes"] == size]
            passed = sum(r["passed"] for r in group)
            mean_time = sum(r["seconds"] for r in group) / len(group)
            print(f"{source}, {size} bytes: {passed}/{TRIALS} passed; mean {mean_time:.6f} s")
    for row in rows[-8:]:
        print(row["source"] + ":", "PASS" if row["passed"] else "FAIL", row["failed_checks"])
    print(f"Saved all {len(rows)} rows to results/evaluation.csv")


if __name__ == "__main__":
    main()
