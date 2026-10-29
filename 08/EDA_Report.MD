# 第八週作業：IC 設計的 EDA 是什麼？暨 `veryl2chip` 實作報告

## 一、IC 設計的 EDA 是什麼？

**EDA（Electronic Design Automation，電子設計自動化）** 是指利用電腦輔助軟體工具，自動化完成積體電路（IC，Integrated Circuit）從高階邏輯設計、功能驗證、邏輯合成、實體佈局繞線，一直到最終製造檔案產出的整套軟硬體開發流程。

在早期的簡單電路中，工程師還能以人工方式繪製邏輯閘與電晶體佈局；但現代晶片（如 CPU、GPU、SoC）動輒包含數十億至上千億顆電晶體，若沒有 EDA 工具進行自動化最佳化與物理規則檢查，根本無法設計與製造。因此，EDA 常被稱為**「晶片之母」**，在半導體產業鏈中扮演連接「IC 設計」與「晶圓代工製造（Foundry）」的關鍵橋樑（業界三大主流商業軟體巨頭為 Synopsys、Cadence 與 Siemens EDA）。

### 標準數位 IC 設計與 EDA 流程
數位 IC 設計的 EDA 流程通常分為**前端（Front-End，邏輯與功能面）**與**後端（Back-End，實體與物理面）**：

1. **硬體描述語言設計（HDL / RTL Design）**：使用 Verilog、SystemVerilog、VHDL 或現代化的 **Veryl** 撰寫暫存器傳輸級（RTL）程式碼，定義資料路徑與控制邏輯。
2. **功能模擬與驗證（Simulation & Verification）**：透過 Testbench 輸入測試向量，檢查波形（Waveform）與斷言（Assertion），確保電路邏輯在合成前完全正確。
3. **邏輯合成（Logic Synthesis）**：將抽象的 RTL 程式碼轉換為由邏輯閘組成的網表（Gate-level Netlist），並進行布林代數化簡與面積／速度最佳化。
4. **技術映射（Technology Mapping）**：
   * **FPGA 流程**：映射至查找表（LUT，如 LUT4）與配置記憶體區塊（BRAM）。
   * **ASIC 流程**：映射至特定製程廠（PDK，如 SkyWater SKY130）的標準元件庫（Standard Cells，如 NAND、NOR、DFF）。
5. **佈局與繞線（Placement & Routing, P&R）**：決定每個邏輯元件在晶片畫布上的實體座標（Placement），建立時脈樹合成（CTS, Clock Tree Synthesis）確保時脈同步，並完成金屬層走線連接（Global & Detail Routing）。
6. **靜態時序分析與簽核驗證（STA, Power & DRC Sign-off）**：
   * **STA（Static Timing Analysis）**：計算關鍵路徑延遲（Critical Path Delay），確認電路最高運作頻率（$F_{\max}$）並檢查是否有 Setup/Hold Time 違規。
   * **功耗與壓降分析（Power & IR Drop）**：評估動態與靜態功耗及供電網路穩定度。
   * **DRC / LVS（設計規則檢查）**：確保幾何佈局符合晶圓廠的物理製程限制。
7. **產出製造／燒錄檔（Tape-out / Bitstream）**：ASIC 產出最終交付晶圓廠光罩製造的 **GDSII** 檔案；FPGA 則產出可燒錄至開發板的 **Bitstream（`.bin` / `.bit`）**。

---

## 二、EDA 軟體實作體驗：`veryl2chip`

本次作業實際操作課堂提供的開源線上 EDA 環境 **[veryl2chip Web IDE](https://ccc-eda.github.io/veryl2chip/web/dist/index.html)**（原始碼見 **[veryl2chip 專案庫](https://github.com/ccc-eda/veryl2chip/)**）。這是一套以 Rust 開發並編譯為 WebAssembly 的全流程教學型與實戰型 EDA 工具，免安裝即可在瀏覽器中走完從 **Veryl HDL** 到 **FPGA Bitstream** 與 **ASIC SKY130 GDSII** 的完整流程。

### 1. RTL 撰寫與波形模擬（Simulation）
在 IDE 中載入範例專案（如閃爍燈控制 `blinky`、佇列緩衝 `fifo` 與 `rv32i` 處理器模組）後：
* 編輯器提供即時語法檢查，能快速觀察模組的輸出入埠（Ports）、時脈（`clk`）、重置訊號（`rst`）與狀態機邏輯。
* 點擊 **模擬（`▶`）** 執行內建的 `#[test]` 測試平台（Testbench），下方波形檢視器（Waveform Viewer）會即時繪出每個時脈週期（Clock Cycle）各訊號線的高低電位變化。更特別的是，工具支援**合成後閘級模擬（Gate-level Simulation）**，能用同一套 Testbench 驗證合成後的 Netlist 是否與原始 RTL 行為一致。

### 2. 邏輯合成與實體設計階段觀察（Synthesis & P&R）
切換至合成檢視後，可以逐步點選各個階段，直觀看到程式碼如何一步步變成實體硬體：
* **階段 ①～③（前端共用流程）**：可以看到 `RTL → Logic` 將 `always_ff` / `always_comb` 轉化為多工器（MUX）、加法器與正反器（Flip-Flop），接著在 **Tech-indep Syn** 階段消去冗餘邏輯閘，精簡整體元件數。
* **FPGA 後端流程（iCE40UP5K）**：
  * 在 **LUT4 Techmap** 階段，組合邏輯被打包進 4 輸入查找表（LUT4）。
  * 在 **Placement** 階段，開啟模擬退火（Simulated Annealing）動畫，能親眼看到演算法不斷交換元件位置以最小化總繞線長度（Wirelength）。
  * 完成繞線與 STA 時序分析後，可直接點擊 **`⚡`（Virtual iCEBreaker）**，將產出的 `.bin` Bitstream 燒錄到網頁上的虛擬開發板，直接按壓開關觀察 LED 亮滅與週邊互動。
* **ASIC 後端流程（SKY130 PDK）**：
  * 切換至 **ASIC · SKY130** 後，電路改為映射至真實的 130nm 開源製程標準元件庫（`sky130_fd_sc_hd`）。
  * 經過 **Row Placement（列式擺放）**、**CTS（時脈樹合成）** 與 **Detail Routing（細部繞線）** 後，工具會計算關鍵路徑時序（STA）與 IR Drop 壓降分佈，最終通過 DRC 規則檢查並可匯出真實的 `.gds` 版圖檔。

---

## 三、FPGA 與 ASIC 流程實測比較

透過 `veryl2chip` 內建的 **`⇄ FPGA vs ASIC`** 對照視圖，可以清楚比較同一份 Veryl 硬體描述語言在兩種不同目標架構下的物理特性差異：

| 比較項目 | FPGA 流程（如 Lattice iCE40UP5K） | ASIC 流程（如 SkyWater SKY130） |
| :--- | :--- | :--- |
| **基本組成單元** | 查找表（LUT4）、可程式邏輯區塊、BRAM | 標準邏輯閘元件（Standard Cells：NAND、DFF 等） |
| **面積與繞線效率** | 面積較大，需透過可程式開關矩陣繞線 | 元件緊密排列於標準列（Rows），面積小、走線短 |
| **最高運作頻率（$F_{\max}$）** | 較低（受限於可程式路由延遲） | 較高（專用金屬層直接連線，關鍵路徑延遲小） |
| **功耗表現（Power）** | 靜態與動態功耗相對較高 | 功耗更低，適合大規模量產與低功耗應用 |
| **開發彈性與成本** | 可重複燒錄修改（產生 `.bin`），NRE 成本極低，適合原型驗證與小量應用 | 開光罩（產生 `.gds` Tape-out）成本高、不可修改邏輯，但量產單價極低 |

---

## 四、實作心得與總結

過去在計算機結構課程中學習布林代數、組合邏輯、ALU 與 RISC-V 處理器時，多半停留在抽象的方塊圖或高階模擬層次。這次實際操作 `veryl2chip` 走完一遍 IC EDA 流程後，最大的收穫是**把「寫程式（HDL）」與「物理晶片限制」真正連結起來**：

1. **硬體描述不是一般軟體程式**：在 C 或 Python 裡寫迴圈與條件判斷是交給 CPU 循序執行；但在 Veryl 等 HDL 中，每一行邏輯都會在合成階段實例化為真實佔用面積的邏輯閘與走線，且必須嚴格滿足時脈邊緣（Setup / Hold Time）的物理延遲限制，否則 $F_{\max}$ 就會大幅下降甚至產生時序違規。
2. **視覺化大幅降低 EDA 學習門檻**：傳統商業級 EDA 工具環境龐大、指令複雜且授權昂貴，初學者很難一窺全貌。`veryl2chip` 利用 Rust 與 WebAssembly 將模擬、合成、模擬退火擺放、繞線、STA 到 GDSII 輸出濃縮在一個瀏覽器分頁中，讓我們能清楚看見每一個階段的資料轉換與最佳化目標。
3. **AI 與開源生態對晶片設計的改變**：從這個專案也能看到，結合開源製程套件（如 SKY130）、現代化語言（Rust / Veryl）與 AI 輔助開發，過往高度封閉的晶片設計自動化工具正在變得更加透明且易於學習，對於理解底層計算機硬體實作有極大的幫助。

---

## 五、參考資源
* [veryl2chip GitHub 專案庫](https://github.com/ccc-eda/veryl2chip/)
* [veryl2chip 線上 IDE](https://ccc-eda.github.io/veryl2chip/web/dist/index.html)
* [EDA 電子書教材](https://github.com/ccc-eda/eda-books/tree/main/book)
* [康乃爾大學 ECE 5745 數位 IC 設計講義](https://www.csl.cornell.edu/courses/ece5745/handouts.html)