"""Small randomness experiment for CA2."""

import hashlib
import os
import time


def collect_timing(samples):
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
    system_random = os.urandom(64)
    noise = collect_timing(samples)
    seed = hashlib.sha3_512(system_random + noise).digest()
    return hashlib.shake_256(seed).digest(size)


if __name__ == "__main__":
    data = generate_bytes(4096)
    print("Preview (first 32 bytes):", data[:32].hex())
