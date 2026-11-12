"""Small randomness experiment for CA2."""

import argparse
import hashlib
import os
import time


def collect_timing(samples):
    """Measure how long a short calculation takes each time."""
    timings = []
    for _ in range(samples):
        start = time.perf_counter_ns()
        sum(i * i for i in range(100))
        timings.append(time.perf_counter_ns() - start)

    noise = bytearray()
    for value in timings:
        noise.extend(value.to_bytes(8, "big"))
    return bytes(noise)


def generate_bytes(size, samples=256):
    """Mix fresh OS randomness and timing data, then expand the seed."""
    if not 128 <= size <= 1_048_576:
        raise ValueError("Byte count must be between 128 and 1048576.")
    if not 32 <= samples <= 4096:
        raise ValueError("Sample count must be between 32 and 4096.")

    system_random = os.urandom(64)
    noise = collect_timing(samples)
    seed = hashlib.sha3_512(system_random + noise).digest()
    return hashlib.shake_256(seed).digest(size)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Simple randomness experiment")
    parser.add_argument("--bytes", type=int, default=4096, help="128 to 1048576")
    parser.add_argument("--samples", type=int, default=256, help="32 to 4096")
    args = parser.parse_args(argv)

    data = generate_bytes(args.bytes, args.samples)
    print(f"Bytes: {len(data)}")
    print("Preview (first 32 bytes):", data[:32].hex())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
