"""Small randomness experiment for CA2."""

import argparse
import hashlib
import math
import os
import time


# Share a 1% significance budget between four statistical checks.
THRESHOLD = 0.01 / 4
LAGS = (1, 2, 3, 4, 8, 16, 32, 64)


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


def block_balance(bits):
    """Check balance in 16 sections, including every bit."""
    statistic = 0.0
    for index in range(16):
        block = bits[index * len(bits) // 16:(index + 1) * len(bits) // 16]
        difference = block.count("1") - len(block) / 2
        statistic += 4 * difference ** 2 / len(block)

    # Chi-square survival probability for 16 degrees of freedom.
    # This finite sum avoids needing scipy for this fixed block count.
    x = statistic / 2
    term = total = 1.0
    for k in range(1, 8):
        term *= x / k
        total += term
    return math.exp(-x) * total


def lag_balance(bits):
    """Look for matching or opposite bits at several distances."""
    smallest_p = 1.0
    worst_lag = LAGS[0]
    for lag in LAGS:
        pairs = len(bits) - lag
        different = sum(a != b for a, b in zip(bits, bits[lag:]))
        p_value = math.erfc(abs(2 * different - pairs) / math.sqrt(2 * pairs))
        if p_value < smallest_p:
            smallest_p = p_value
            worst_lag = lag
    # Bonferroni adjustment for inspecting eight distances.
    return min(1.0, smallest_p * len(LAGS)), worst_lag


def repeated_period(data):
    """Find an exact byte period up to 256 bytes, with at least four cycles."""
    for period in range(1, min(256, len(data) // 4) + 1):
        if data[period:] == data[:-period]:
            return period
    return 0


def check_randomness(data):
    """Check balance, runs, local bias, correlations and exact repetition."""
    if len(data) < 128:
        raise ValueError("Use at least 128 bytes for the checks.")

    bits = "".join(f"{byte:08b}" for byte in data)
    n = len(bits)
    ones = bits.count("1")
    proportion = ones / n

    # Frequency and runs formulas: NIST SP 800-22, sections 2.1 and 2.3.
    frequency_p = math.erfc(abs(2 * ones - n) / math.sqrt(2 * n))
    runs = 1
    longest = 0
    current = 0
    for index, bit in enumerate(bits):
        if index > 0 and bit != bits[index - 1]:
            runs += 1
        if bit == "1":
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    runs_p = 0.0
    runs_applicable = abs(proportion - 0.5) < 2 / math.sqrt(n)
    if runs_applicable:
        expected = 2 * n * proportion * (1 - proportion)
        denominator = 2 * math.sqrt(2 * n) * proportion * (1 - proportion)
        runs_p = math.erfc(abs(runs - expected) / denominator)

    entropy = 0.0
    for probability in (proportion, 1 - proportion):
        if probability > 0:
            entropy -= probability * math.log2(probability)

    block_p = block_balance(bits)
    lag_p, worst_lag = lag_balance(bits)
    period = repeated_period(data)
    checks = {
        "frequency": frequency_p >= THRESHOLD,
        "runs": runs_applicable and runs_p >= THRESHOLD,
        "block balance": block_p >= THRESHOLD,
        "lag balance": lag_p >= THRESHOLD,
        "repetition": period == 0,
    }
    failed_checks = ", ".join(name for name, passed in checks.items() if not passed)

    return {
        "bytes": len(data),
        "ones_percent": proportion * 100,
        "frequency_p": frequency_p,
        "runs": runs,
        "runs_p": runs_p,
        "runs_applicable": runs_applicable,
        "bit_entropy": entropy,
        "longest_ones": longest,
        "block_p": block_p,
        "lag_p": lag_p,
        "worst_lag": worst_lag,
        "repeat_period_bytes": period,
        "failed_checks": failed_checks,
        "passed": all(checks.values()),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Simple randomness experiment")
    parser.add_argument("--bytes", type=int, default=4096, help="128 to 1048576")
    parser.add_argument("--samples", type=int, default=256, help="32 to 4096")
    args = parser.parse_args(argv)

    data = generate_bytes(args.bytes, args.samples)
    result = check_randomness(data)

    print(f"Bytes: {result['bytes']}")
    print(f"Ones: {result['ones_percent']:.3f}%")
    print(f"Frequency p-value: {result['frequency_p']:.6f}")
    print(f"Runs: {result['runs']}")
    print(f"Runs p-value: {result['runs_p']:.6f}")
    if not result["runs_applicable"]:
        print("Runs prerequisite failed: bit balance is too uneven.")
    print(f"Block balance p-value: {result['block_p']:.6f}")
    print(f"Lag balance p-value (adjusted): {result['lag_p']:.6f}")
    print(f"Strongest lag: {result['worst_lag']} bits")
    print(f"Exact repeat period: {result['repeat_period_bytes']} bytes (0 = none)")
    print(f"Statistical threshold: {THRESHOLD}")
    print(f"Bit-frequency entropy: {result['bit_entropy']:.6f} bits/bit")
    print(f"Longest run of ones: {result['longest_ones']}")
    print("Checks:", "PASS" if result["passed"] else "FAIL")
    if not result["passed"]:
        print("Failed checks:", result["failed_checks"])
    print("Preview (first 32 bytes):", data[:32].hex())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
