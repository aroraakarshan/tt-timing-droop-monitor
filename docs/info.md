## How it works

This project explores how controlled switching activity changes timing margin.
Four observable 16-bit LFSR banks create digital switching load. Simultaneous
mode updates every enabled bank once per four cycles; staggered mode distributes
the same updates across those four cycles. This holds average activity constant
while changing peak concurrent switching. A separate 16-bit source register
drives an explicit standard-cell inverter chain with selectable taps at 480,
600, 720, and 840 stages. The captured canary bit is accumulated into an 8-bit
signature during an exact 256-cycle measurement window.

The host pulses `start`, waits for the hardware `done` flag, and compares the
signature with the known-good RTL signature. It then increases the external
clock frequency until the signature becomes unreliable. Repeating the sweep
with different load masks estimates load-dependent timing degradation.

This is a timing experiment. It does not directly measure supply voltage,
current, resistance, current density, or electromigration.

## Controls

| Input | Function |
|---|---|
| `ui_in[3:0]` | Enable load banks 0 through 3 |
| `ui_in[4]` | Distribute bank updates across four cycles when high |
| `ui_in[6:5]` | Select the 480, 600, 720, or 840-stage canary tap |
| `ui_in[7]` | Start a new 256-cycle experiment on a rising edge |

`uo_out[7:0]` is the timing signature. The bidirectional pins are configured as
outputs: `uio_out[0]` is `done`, `uio_out[3:1]` exposes cycle-count bits, and
`uio_out[7:4]` exposes load-bank parity so the load logic remains observable.

## How to test

1. Select a canary depth and load configuration.
2. Assert reset for at least three clock cycles.
3. Release reset and pulse `start`.
4. Wait for `done`, then stop the clock and read the signature.
5. Repeat to establish that the signature is stable.
6. Sweep the external clock upward until signatures begin to mismatch.
7. Compare the maximum stable frequency with loads disabled, enabled
   simultaneously, and staggered.

The design is closed at a nominal 33.3 MHz. Characterization intentionally
sweeps above that value to locate each canary's failure boundary; operation
above the declared clock is experimental rather than guaranteed.

Report the result as timing degradation:

`100 * (baseline_fmax - loaded_fmax) / baseline_fmax`

A signature mismatch is consistent with a timing failure, but voltage,
temperature, process variation, clock quality, and test setup must be controlled
before attributing the change to switching-induced supply droop.

The repository includes `tools/characterize.py` for the Tiny Tapeout
MicroPython board and `tools/analyze_results.py` for reducing the captured CSV
to maximum all-pass frequency and degradation percentages.

## External hardware

Use the Tiny Tapeout demo board and a host script capable of setting the project
inputs, resetting the design, sweeping the clock, and reading the outputs.
