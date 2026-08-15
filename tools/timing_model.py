RUN_CYCLES = 256


def lfsr16_next(value):
    feedback = ((value >> 15) ^ (value >> 13) ^ (value >> 12) ^ (value >> 10)) & 1
    return ((value << 1) & 0xFFFF) | feedback


def selected_canary(value, depth_select):
    del depth_select
    return value & 1


def expected_signature(depth_select, cycles=RUN_CYCLES):
    source = 0x1ACE
    capture = 0
    signature = 0

    for _ in range(cycles):
        old_capture = capture
        capture = selected_canary(source, depth_select)
        source = lfsr16_next(source)
        feedback = (
            (signature >> 7) ^ (signature >> 5) ^ old_capture
        ) & 1
        signature = ((signature << 1) & 0xFF) | feedback

    return signature
