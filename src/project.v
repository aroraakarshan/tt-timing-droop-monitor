/*
 * Copyright (c) 2026 Akarshan Arora
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_aroraakarshan_timing_droop_monitor (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

  reg [15:0] source_state;
  reg canary_capture;
  reg [7:0] signature;
  reg [7:0] cycle_count;
  reg running;
  reg done;
  reg start_delayed;

  reg [15:0] load_bank_0;
  reg [15:0] load_bank_1;
  reg [15:0] load_bank_2;
  reg [15:0] load_bank_3;

  wire [3:0] load_mask = ui_in[3:0];
  wire staggered = ui_in[4];
  wire [1:0] canary_depth = ui_in[6:5];
  wire start = ui_in[7];

  function [15:0] lfsr16_next;
    input [15:0] value;
    begin
      lfsr16_next = {value[14:0], value[15] ^ value[13] ^ value[12] ^ value[10]};
    end
  endfunction

`ifdef RTL_SIM
  wire selected_canary = source_state[0];
`else
  (* keep *) wire [840:0] canary_chain;
  assign canary_chain[0] = source_state[0];

  genvar canary_stage;
  generate
    for (canary_stage = 0; canary_stage < 840; canary_stage = canary_stage + 1) begin : generate_canary
      (* keep *) sky130_fd_sc_hd__inv_1 canary_inverter (
        .A(canary_chain[canary_stage]),
        .Y(canary_chain[canary_stage + 1])
      );
    end
  endgenerate

  reg selected_canary;
  always @(*) begin
    case (canary_depth)
      2'd0: selected_canary = canary_chain[480];
      2'd1: selected_canary = canary_chain[600];
      2'd2: selected_canary = canary_chain[720];
      default: selected_canary = canary_chain[840];
    endcase
  end
`endif

  wire [3:0] stagger_select = 4'b0001 << cycle_count[1:0];
  wire burst_cycle = cycle_count[1:0] == 2'b00;
  wire [3:0] active_loads = staggered
    ? (load_mask & stagger_select)
    : (burst_cycle ? load_mask : 4'b0000);
  wire [3:0] load_parity = {
    ^load_bank_3,
    ^load_bank_2,
    ^load_bank_1,
    ^load_bank_0
  };

  always @(posedge clk) begin
    if (!rst_n) begin
      source_state  <= 16'h1ACE;
      canary_capture <= 1'b0;
      signature     <= 8'h00;
      cycle_count   <= 8'h00;
      running       <= 1'b0;
      done          <= 1'b0;
      start_delayed <= 1'b0;
      load_bank_0   <= 16'h1357;
      load_bank_1   <= 16'h2468;
      load_bank_2   <= 16'h0F0F;
      load_bank_3   <= 16'h55AA;
    end else if (ena) begin
      start_delayed <= start;

      if (start && !start_delayed && !running) begin
        source_state   <= 16'h1ACE;
        canary_capture <= 1'b0;
        signature      <= 8'h00;
        cycle_count    <= 8'h00;
        running        <= 1'b1;
        done           <= 1'b0;
        load_bank_0    <= 16'h1357;
        load_bank_1    <= 16'h2468;
        load_bank_2    <= 16'h0F0F;
        load_bank_3    <= 16'h55AA;
      end else if (running) begin
      source_state   <= lfsr16_next(source_state);
      canary_capture <= selected_canary;
      signature      <= {
        signature[6:0],
        signature[7] ^ signature[5] ^ canary_capture
      };
      cycle_count    <= cycle_count + 1'b1;

      if (active_loads[0])
          load_bank_0 <= lfsr16_next(load_bank_0);
      if (active_loads[1])
          load_bank_1 <= lfsr16_next(load_bank_1);
      if (active_loads[2])
          load_bank_2 <= lfsr16_next(load_bank_2);
      if (active_loads[3])
          load_bank_3 <= lfsr16_next(load_bank_3);

        if (cycle_count == 8'hFF) begin
          running <= 1'b0;
          done    <= 1'b1;
        end
      end
    end
  end

  assign uo_out = signature;
  assign uio_out = {load_parity, cycle_count[2:0], done};
  assign uio_oe = 8'hFF;

  wire _unused = &{uio_in, 1'b0};

endmodule

`default_nettype wire
