#!/usr/bin/env python3

import argparse
import csv
from collections import defaultdict


def load_results(path):
    grouped = defaultdict(lambda: defaultdict(list))
    with open(path, newline="", encoding="utf-8") as results_file:
        for row in csv.DictReader(results_file):
            key = (row["scenario"], int(row["canary_stages"]))
            grouped[key][int(row["frequency_hz"])].append(int(row["passed"]))
    return grouped


def maximum_all_pass_frequency(frequencies):
    passing = [
        frequency
        for frequency, results in frequencies.items()
        if results and all(results)
    ]
    return max(passing, default=None)


def main():
    parser = argparse.ArgumentParser(
        description="Summarize Tiny Tapeout timing-droop characterization CSV."
    )
    parser.add_argument("results_csv")
    args = parser.parse_args()

    grouped = load_results(args.results_csv)
    print("scenario,canary_stages,max_all_pass_hz,degradation_percent")

    for depth in (480, 600, 720, 840):
        baseline = maximum_all_pass_frequency(
            grouped.get(("baseline", depth), {})
        )
        for scenario in (
            "baseline",
            "one_bank",
            "all_simultaneous",
            "all_staggered",
        ):
            maximum = maximum_all_pass_frequency(
                grouped.get((scenario, depth), {})
            )
            degradation = ""
            if baseline and maximum is not None:
                degradation = "{:.2f}".format(
                    100.0 * (baseline - maximum) / baseline
                )
            print(
                "{},{},{},{}".format(
                    scenario,
                    depth,
                    "" if maximum is None else maximum,
                    degradation,
                )
            )


if __name__ == "__main__":
    main()
