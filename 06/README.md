# Week 10: Nand2Tetris Hack Assembler (Project 6)

## 1. 專案架構與設計原理
本專案使用 Python 實作完整的 Two-Pass Hack 組譯器 (assembler.py)，將 .asm 組合語言轉換為 16-bit 二進位機器碼 .hack 檔案：
- First Pass (符號表建立)：掃描所有 (LABEL) 標籤並記錄對應的 ROM 指令位址，預載 R0-R15、SP、LCL、ARG、THIS、THAT、SCREEN、KBD 等內建符號。
- Second Pass (指令轉譯)：自動配置自訂變數自 RAM 位址 16 起算 (0vvvvvvvvvvvvvvv)，並查表轉換 C-Instruction 之 comp、dest 與 jump 欄位 (111accccccdddjjj)。

## 2. 執行方式
python assembler.py Add.asm Max.asm
