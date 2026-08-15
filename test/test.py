# SPDX-FileCopyrightText: 2026 Akarshan Arora
# SPDX-License-Identifier: Apache-2.0

import cocotb
import sys
from pathlib import Path

from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge, Timer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from timing_model import expected_signature

SETTLE_NS = 100


async def reset(dut, controls: int = 0) -> None:
    dut.ena.value = 1
    dut.ui_in.value = controls
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 3)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1


async def start_run(dut, controls: int) -> None:
    dut.ui_in.value = controls & 0x7F
    await FallingEdge(dut.clk)
    dut.ui_in.value = controls | 0x80
    await RisingEdge(dut.clk)
    await Timer(SETTLE_NS, unit="ns")
    dut.ui_in.value = controls & 0x7F


@cocotb.test()
async def test_canary_depths_and_signature(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="us").start())

    for depth in range(4):
        controls = depth << 5
        await reset(dut, controls)
        await start_run(dut, controls)
        await ClockCycles(dut.clk, 256)
        await Timer(SETTLE_NS, unit="ns")
        assert dut.uo_out.value.to_unsigned() == expected_signature(depth)
        assert dut.uio_out.value.to_unsigned() & 1 == 1


@cocotb.test()
async def test_completed_run_holds_experiment_state(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="us").start())

    await reset(dut, controls=0x0F)
    await start_run(dut, controls=0x0F)
    await ClockCycles(dut.clk, 256)
    await Timer(SETTLE_NS, unit="ns")

    frozen_signature = dut.uo_out.value.to_unsigned()
    frozen_status = dut.uio_out.value.to_unsigned()
    await ClockCycles(dut.clk, 10)
    await Timer(SETTLE_NS, unit="ns")

    assert dut.uo_out.value.to_unsigned() == frozen_signature
    assert dut.uio_out.value.to_unsigned() == frozen_status


@cocotb.test()
async def test_staggered_load_updates_one_selected_bank_per_cycle(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="us").start())

    await reset(dut, controls=0x1F)
    await start_run(dut, controls=0x1F)
    previous_parity = (dut.uio_out.value.to_unsigned() >> 4) & 0x0F

    for cycle in range(8):
        await RisingEdge(dut.clk)
        await Timer(SETTLE_NS, unit="ns")
        parity = (dut.uio_out.value.to_unsigned() >> 4) & 0x0F
        changed = parity ^ previous_parity
        assert changed & ~(1 << (cycle % 4)) == 0
        previous_parity = parity


@cocotb.test()
async def test_simultaneous_loads_only_update_on_burst_cycle(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="us").start())

    await reset(dut, controls=0x0F)
    await start_run(dut, controls=0x0F)
    previous_parity = (dut.uio_out.value.to_unsigned() >> 4) & 0x0F

    for cycle in range(8):
        await RisingEdge(dut.clk)
        await Timer(SETTLE_NS, unit="ns")
        parity = (dut.uio_out.value.to_unsigned() >> 4) & 0x0F
        if cycle % 4:
            assert parity == previous_parity
        previous_parity = parity
