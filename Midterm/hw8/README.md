# Week 8: EDA 電子設計自動化軟體報告

## 1. 什麼是 EDA (Electronic Design Automation)？
電子設計自動化（EDA）是指用於設計、模擬、驗證與佈局積體電路（IC）及印刷電路板（PCB）的軟體工具鏈。隨著現代晶片電晶體數量突破數百億顆（如先進製程 SoC），工程師無法以人工方式繪製邏輯閘，必須依賴硬體描述語言（Verilog / SystemVerilog / VHDL）搭配 EDA 工具完成從 RTL 到 GDSII 光罩檔的完整流程。

## 2. 商業三大巨頭與開源 EDA 工具比較

| 類別 | 代表工具 / 廠商 | 核心功能與定位 | 優缺點分析 |
| :--- | :--- | :--- | :--- |
| **商業巨頭** | Synopsys, Cadence, Siemens EDA | 涵蓋邏輯合成 (Design Compiler)、佈局繞線 (Innovus)、靜態時序分析 (PrimeTime) | 支援台積電等先進製程 PDK、精準度極高；授權費用極昂貴 |
| **開源 RTL 模擬** | Verilator, Icarus Verilog + GTKWave | 高速 Verilog 編譯模擬與波形檢視 | 免費輕量、Verilator 轉譯 C++ 模擬極快；不支援實體繞線 |
| **視覺化數位邏輯** | Logisim-evolution, Digital | 互動式邏輯閘與 CPU 電路圖繪製模擬 | 即時觀察訊號高低電位，極適合計組教學；不適合大型百萬閘級設計 |
| **開源 ASIC 流程** | OpenROAD + Yosys + SkyWater PDK | RTL-to-GDSII 全自動開源晶片設計流程 | 真正實現免費下線 (Tape-out) 能力；生態系與先進製程支援仍在發展中 |

## 3. 與本課程 Nand2Tetris Hardware Simulator 之對照心得
在本課程 Project 1–5 中，我們使用 Nand2Tetris 的 HDL 建立從 `Nand` 閘、16-bit `ALU`、`RAM16K` 到完整 `HackCPU` 的架構：
1. **模組化階層設計 (Hierarchical Design)**：與業界 Verilog 開發完全一致，底層晶片驗證通過後即封裝為黑盒子（Black-box）供上層呼叫。
2. **時序與組合邏輯分離**：透過 `DFF` 隔離時脈狀態，避免組合邏輯迴圈（Combinational Loop），這也是商業 EDA 進行靜態時序分析（STA）的核心基礎。