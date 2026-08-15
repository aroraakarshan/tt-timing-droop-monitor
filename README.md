# Tiny Tapeout Timing Droop Monitor

A digital silicon experiment for observing how programmable switching activity
changes the maximum reliable operating frequency of a timing-canary datapath.

The design combines:

- four independently enabled 32-bit switching-load banks;
- simultaneous and staggered activity modes;
- four selectable combinational canary depths;
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
