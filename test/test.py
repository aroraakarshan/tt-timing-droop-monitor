# SPDX-FileCopyrightText: 2026 Akarshan Arora
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, ReadOnly, RisingEdge, Timer


def lfsr16_next(value: int) -> int:
    feedback = ((value >> 15) ^ (value >> 13) ^ (value >> 12) ^ (value >> 10)) & 1
    return ((value << 1) & 0xFFFF) | feedback


def canary_round(value: int) -> int:
    value = (value + 0x6D2B) & 0xFFFF
    rotate_5 = ((value << 5) | (value >> 11)) & 0xFFFF
    rotate_13 = ((value << 13) | (value >> 3)) & 0xFFFF
    return rotate_5 ^ rotate_13 ^ 0xA7C5


def selected_canary(value: int, depth: int) -> int:
    for _ in range(depth + 1):
        value = canary_round(value)
    return value


async def reset(dut, controls: int = 0) -> None:
    dut.ena.value = 1
    dut.ui_in.value = controls
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 3)
    await Timer(1, unit="ns")
    dut.rst_n.value = 1


def expected_signature(cycles: int, depth: int) -> int:
    source = 0x1ACE
    capture = 0
    signature = 0

    for _ in range(cycles):
        old_capture = capture
        capture = selected_canary(source, depth)
        source = lfsr16_next(source)
        signature = (
            ((signature << 1) & 0xFF)
            | ((signature >> 7) & 1)
        ) ^ (old_capture & 0xFF) ^ (old_capture >> 8)

    return signature


@cocotb.test()
async def test_canary_depths_and_signature(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="us").start())

    for depth in range(4):
        controls = depth << 5
        await reset(dut, controls)
        await ClockCycles(dut.clk, 24)
        await Timer(1, unit="ns")
        assert dut.uo_out.value.to_unsigned() == expected_signature(24, depth)
        assert (dut.uio_out.value.to_unsigned() & 0x0F) == 8


@cocotb.test()
async def test_freeze_holds_experiment_state(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="us").start())

    await reset(dut, controls=0x0F)
    await ClockCycles(dut.clk, 12)
    await Timer(1, unit="ns")
    dut.ui_in.value = 0x8F
    await ClockCycles(dut.clk, 2)
    await Timer(1, unit="ns")

    frozen_signature = dut.uo_out.value.to_unsigned()
    frozen_status = dut.uio_out.value.to_unsigned()
    await ClockCycles(dut.clk, 10)
    await Timer(1, unit="ns")

    assert dut.uo_out.value.to_unsigned() == frozen_signature
    assert dut.uio_out.value.to_unsigned() == frozen_status


@cocotb.test()
async def test_staggered_load_updates_one_selected_bank_per_cycle(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="us").start())

    await reset(dut, controls=0x1F)
    previous_parity = (dut.uio_out.value.to_unsigned() >> 4) & 0x0F

    for cycle in range(8):
        await RisingEdge(dut.clk)
        await ReadOnly()
        parity = (dut.uio_out.value.to_unsigned() >> 4) & 0x0F
        changed = parity ^ previous_parity
        assert changed & ~(1 << (cycle % 4)) == 0
        previous_parity = parity
