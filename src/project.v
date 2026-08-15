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
  reg [15:0] canary_capture;
  reg [7:0] signature;
  reg [7:0] cycle_count;

  reg [31:0] load_bank_0;
  reg [31:0] load_bank_1;
  reg [31:0] load_bank_2;
  reg [31:0] load_bank_3;

  wire [3:0] load_mask = ui_in[3:0];
  wire staggered = ui_in[4];
  wire [1:0] canary_depth = ui_in[6:5];
  wire freeze = ui_in[7];

  function [15:0] lfsr16_next;
    input [15:0] value;
    begin
      lfsr16_next = {value[14:0], value[15] ^ value[13] ^ value[12] ^ value[10]};
    end
  endfunction

  function [31:0] lfsr32_next;
    input [31:0] value;
    begin
      lfsr32_next = {value[30:0], value[31] ^ value[21] ^ value[1] ^ value[0]};
    end
  endfunction

  function [15:0] canary_round;
    input [15:0] value;
    reg [15:0] sum;
    begin
      sum = value + 16'h6D2B;
      canary_round = {sum[10:0], sum[15:11]} ^ {sum[2:0], sum[15:3]} ^ 16'hA7C5;
    end
  endfunction

  wire [15:0] canary_1 = canary_round(source_state);
  wire [15:0] canary_2 = canary_round(canary_1);
  wire [15:0] canary_3 = canary_round(canary_2);
  wire [15:0] canary_4 = canary_round(canary_3);

  reg [15:0] selected_canary;
  always @(*) begin
    case (canary_depth)
      2'd0: selected_canary = canary_1;
      2'd1: selected_canary = canary_2;
      2'd2: selected_canary = canary_3;
      default: selected_canary = canary_4;
    endcase
  end

  wire [3:0] stagger_select = 4'b0001 << cycle_count[1:0];
  wire [3:0] active_loads = staggered ? (load_mask & stagger_select) : load_mask;
  wire [3:0] load_parity = {
    ^load_bank_3,
    ^load_bank_2,
    ^load_bank_1,
    ^load_bank_0
  };

  always @(posedge clk) begin
    if (!rst_n) begin
      source_state  <= 16'h1ACE;
      canary_capture <= 16'h0000;
      signature     <= 8'h00;
      cycle_count   <= 8'h00;
      load_bank_0   <= 32'h1357_9BDF;
      load_bank_1   <= 32'h2468_ACE1;
      load_bank_2   <= 32'h0F0F_C3C3;
      load_bank_3   <= 32'h55AA_A55A;
    end else if (ena && !freeze) begin
      source_state   <= lfsr16_next(source_state);
      canary_capture <= selected_canary;
      signature      <= {signature[6:0], signature[7]} ^
                        canary_capture[7:0] ^
                        canary_capture[15:8];
      cycle_count    <= cycle_count + 1'b1;

      if (active_loads[0])
        load_bank_0 <= lfsr32_next(load_bank_0);
      if (active_loads[1])
        load_bank_1 <= lfsr32_next(load_bank_1);
      if (active_loads[2])
        load_bank_2 <= lfsr32_next(load_bank_2);
      if (active_loads[3])
        load_bank_3 <= lfsr32_next(load_bank_3);
    end
  end

  assign uo_out = signature;
  assign uio_out = {load_parity, cycle_count[3:0]};
  assign uio_oe = 8'hFF;

  wire _unused = &{uio_in, 1'b0};

endmodule

`default_nettype wire
