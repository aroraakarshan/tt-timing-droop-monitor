## How it works

This project explores how controlled switching activity changes timing margin.
Four observable 32-bit LFSR banks create digital switching load. A separate
16-bit source register drives a selectable one-to-four-round combinational
timing canary. The captured canary values are accumulated into an 8-bit
signature.

The host resets the design, runs a fixed number of cycles, freezes it, and
compares the signature with the known-good RTL signature. It then increases the
external clock frequency until the signature becomes unreliable. Repeating the
sweep with different load masks estimates load-dependent timing degradation.

This is a timing experiment. It does not directly measure supply voltage,
current, resistance, current density, or electromigration.

## Controls

| Input | Function |
|---|---|
| `ui_in[3:0]` | Enable load banks 0 through 3 |
| `ui_in[4]` | Update enabled banks one at a time when high |
| `ui_in[6:5]` | Select canary depth from one through four rounds |
| `ui_in[7]` | Freeze all experiment state |

`uo_out[7:0]` is the timing signature. The bidirectional pins are configured as
outputs: `uio_out[3:0]` exposes the low cycle-count bits and
`uio_out[7:4]` exposes load-bank parity so the load logic remains observable.

## How to test

1. Select a canary depth and load configuration.
2. Assert reset for at least three clock cycles.
3. Release reset and run a fixed cycle count.
4. Set `freeze` and read the signature.
5. Repeat to establish that the signature is stable.
6. Sweep the external clock upward until signatures begin to mismatch.
7. Compare the maximum stable frequency with loads disabled, enabled
   simultaneously, and staggered.

Report the result as timing degradation:

`100 * (baseline_fmax - loaded_fmax) / baseline_fmax`

A signature mismatch is consistent with a timing failure, but voltage,
temperature, process variation, clock quality, and test setup must be controlled
before attributing the change to switching-induced supply droop.

## External hardware

Use the Tiny Tapeout demo board and a host script capable of setting the project
inputs, resetting the design, sweeping the clock, and reading the outputs.
