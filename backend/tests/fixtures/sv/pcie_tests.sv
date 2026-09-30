// Small SystemVerilog fixture for the catalog scanner.
class pcie_base_test extends uvm_test;
  `uvm_component_utils(pcie_base_test)
endclass

class pcie_gen4_linkup_test extends pcie_base_test;
  // ...
endclass

/* block comment mentioning class fake_should_not_match extends uvm_test */
class pcie_mps_512_test extends uvm_test;
endclass

covergroup cg_ltssm;
  cp_rate: coverpoint ltssm_rate;
  cp_width: coverpoint ltssm_width;
  cx_rate_x_width: cross cp_rate, cp_width;
endgroup

module pcie_sva;
  a_ltssm_legal_trans: assert property (@(posedge clk) legal_transition);
  a_ecrc_irq_latency: assert property (@(posedge clk) ecrc_irq |-> ##[1:16] irq);
endmodule
