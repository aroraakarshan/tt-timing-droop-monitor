# Tiny Tapeout Timing Droop Monitor

A digital silicon experiment for observing how programmable switching activity
changes the maximum reliable operating frequency of a timing-canary datapath.

The design combines:

- four independently enabled 16-bit switching-load banks;
- equal-average-activity simultaneous-burst and staggered modes;
- an explicit 840-stage standard-cell canary with four selectable taps;
- an exact hardware-controlled 256-cycle measurement window;
- a deterministic signature for host-side pass/fail comparison; and
- observable load parity and cycle-count status.

The intended measurement is the change in maximum passing clock frequency
between an unloaded baseline and loaded experiments. It is not a direct
millivolt IR-drop or electromigration measurement.

See [the project datasheet](docs/info.md) for controls and characterization
steps.

## Simulation

```sh
cd test
python3 -m pip install -r requirements.txt
make
```

## Tiny Tapeout flow

This project uses the official
[Tiny Tapeout Verilog template](https://github.com/TinyTapeout/ttsky-verilog-template).
GitHub Actions run RTL tests and the LibreLane ASIC flow after the repository is
published.

Before submission, inspect post-layout timing and confirm that the load banks
and selectable canary paths remain present in the synthesized netlist.

## Silicon characterization

Copy `tools/characterize.py` and `tools/timing_model.py` to the Tiny Tapeout
demo board, then capture the script's stdout:

```python
import characterize
characterize.main()
```

The script runs five measurements at each frequency for the baseline, one-bank,
all-bank simultaneous, and all-bank staggered configurations. Save its CSV
output as `results.csv`, then summarize maximum all-pass frequency and relative
timing degradation:

```sh
python3 tools/analyze_results.py results.csv
```
