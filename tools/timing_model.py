RUN_CYCLES = 256


def lfsr16_next(value):
    feedback = ((value >> 15) ^ (value >> 13) ^ (value >> 12) ^ (value >> 10)) & 1
    return ((value << 1) & 0xFFFF) | feedback


def canary_round(value):
    value = (value + 0x6D2B) & 0xFFFF
    rotate_5 = ((value << 5) | (value >> 11)) & 0xFFFF
    rotate_13 = ((value << 13) | (value >> 3)) & 0xFFFF
    return rotate_5 ^ rotate_13 ^ 0xA7C5


def selected_canary(value, depth_select):
    for _ in range(depth_select + 3):
        value = canary_round(value)
    return value


def expected_signature(depth_select, cycles=RUN_CYCLES):
    source = 0x1ACE
    capture = 0
    signature = 0

    for _ in range(cycles):
        old_capture = capture
        capture = selected_canary(source, depth_select)
        source = lfsr16_next(source)
        feedback = ((signature >> 7) ^ (signature >> 5)) & 1
        rotated = ((signature << 1) & 0xFF) | feedback
        high_byte = old_capture >> 8
        swapped_high = ((high_byte & 0x0F) << 4) | (high_byte >> 4)
        signature = rotated ^ (old_capture & 0xFF) ^ swapped_high

    return signature
