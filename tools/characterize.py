"""Run on the Tiny Tapeout MicroPython demo board and capture stdout as CSV."""

import time

from timing_model import expected_signature


PROJECT_NAME = "tt_um_aroraakarshan_timing_droop_monitor"
FREQUENCIES_HZ = (
    10_000_000,
    20_000_000,
    30_000_000,
    40_000_000,
    50_000_000,
    55_000_000,
    60_000_000,
    65_000_000,
)
REPEATS = 5
TIMEOUT_MS = 100
SCENARIOS = (
    ("baseline", 0x0, 0),
    ("one_bank", 0x1, 0),
    ("all_simultaneous", 0xF, 0),
    ("all_staggered", 0xF, 1),
)


def read_port(port):
    return int(port.value) if hasattr(port, "value") else int(port)


def write_inputs(tt, value):
    if hasattr(tt.ui_in, "value"):
        tt.ui_in.value = value
    else:
        tt.ui_in = value


def wait_done(tt):
    start_ms = time.ticks_ms()
    while not (read_port(tt.uio_out) & 0x01):
        if time.ticks_diff(time.ticks_ms(), start_ms) > TIMEOUT_MS:
            raise RuntimeError("measurement timed out before done")


def measure(tt, controls, frequency_hz):
    tt.clock_project_PWM(frequency_hz)
    write_inputs(tt, controls)
    time.sleep_ms(1)
    write_inputs(tt, controls | 0x80)
    time.sleep_ms(1)
    write_inputs(tt, controls)
    wait_done(tt)
    tt.clock_project_stop()
    return read_port(tt.uo_out)


def main():
    from ttboard.demoboard import DemoBoard

    tt = DemoBoard.get()
    getattr(tt.shuttle, PROJECT_NAME).enable()
    tt.clock_project_stop()
    tt.reset_project(True)
    time.sleep_ms(1)
    tt.reset_project(False)

    print(
        "scenario,canary_stages,load_mask,staggered,"
        "frequency_hz,repeat,signature,expected,passed"
    )

    for scenario, load_mask, staggered in SCENARIOS:
        for depth_select in range(4):
            controls = load_mask | (staggered << 4) | (depth_select << 5)
            expected = expected_signature(depth_select)
            for repeat in range(REPEATS):
                signature = measure(tt, controls, FREQUENCIES_HZ[0])
                for frequency_hz in FREQUENCIES_HZ:
                    if frequency_hz != FREQUENCIES_HZ[0]:
                        signature = measure(tt, controls, frequency_hz)
                    passed = int(signature == expected)
                    print(
                        "{},{},{},{},{},{},{},{},{}".format(
                            scenario,
                            (480, 600, 720, 840)[depth_select],
                            load_mask,
                            staggered,
                            frequency_hz,
                            repeat,
                            signature,
                            expected,
                            passed,
                        )
                    )

    tt.clock_project_stop()


if __name__ == "__main__":
    main()
