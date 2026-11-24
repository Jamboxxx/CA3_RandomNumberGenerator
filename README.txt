Randomness generator

Run these commands from the project folder with Python 3.8 or newer.
Both scripts use the standard library.

    python3 randomness.py

Generates 4,096 bytes using operating-system randomness and timing samples.
It checks the bytes for patterns and shows a short preview if they pass.

    python3 evaluate.py

Compares the generator with direct operating-system randomness and eight
fixed examples. See results/evaluation.csv for the outcome of each check.
Running the evaluation again replaces that CSV with fresh results.

These checks can flag patterns. Passing them does not prove the bytes
are unpredictable.
