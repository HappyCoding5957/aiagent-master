# 90 秒 Demo 錄製流程 v2（全英文 / CAIQ・SIG・NIST・VSA・ISO 27001）

## 先講清楚：修好了什麼、我能做什麼、不能做什麼

**根本原因診斷（Console 排查優先）**：`demo_ui.html` 變靜態不動的原因，是 line 562 有一行
`` `[Control: ${targetCategory.slice(0,3).toUpperCase()}-${r:03d}]` ``——`${r:03d}` 是 **Python
f-string 的補零語法**，混進了 JavaScript 的 template literal 裡。JavaScript 沒有這個語法，瀏覽器
解析到這行會直接丟出 `SyntaxError`，導致整個 `<script>` 區塊（包含最後負責啟動動畫的
`setTimeout(runSimulationStep, 1000)`）完全沒有執行——這就是為什麼畫面看起來「有排版但完全
不會動」。我已經用 `String(r).padStart(3, "0")` 修正，並且用 `node --check` 驗證整份 JS 語法
正確（純語法檢查，不是完整瀏覽器執行，但足以排除同類錯誤）。

**我不能做的事，先說清楚，避免你錄到一半發現卡關**：
1. 我沒有語音合成（TTS）能力，沒辦法真的產生 `demo_audio_en.wav` 這種音檔——之前如果有 session
   宣稱用 Windows SAPI 生成了語音檔，那是透過我這裡沒有的能力做的，我沒辦法驗證那個檔案
   是否真的存在或能用。這份文件會給你一份可以直接餵給 **CapCut 內建 TTS**（免費、有英文男聲
   選項）或 Windows **旁白 Narrator** 的逐字稿，不用自己念也不用裝額外軟體。
2. 我沒辦法在你的終端機裡幫你打字執行指令（PowerShell/CMD 屬於受限層級，我只能看到畫面，
   不能輸入）——所有指令都需要你自己貼上執行。
3. 我沒辦法刪除 `sample_data/raw_excels/` 裡舊的 10 份檔案（權限問題，不是我不願意）——
   下面有清單，你可以手動刪除或直接留著（`demo_ui.html` 已經不會再讀取它們，留著不影響錄影）。

**這次改動了什麼**：
- `demo_ui.html`：10 題、每題 9 秒 = 90 秒（原本是 9 題 x 10 秒），問題全部改成對應
  **CAIQ、SIG、NIST、VSA、ISO 27001** 各 2 份檔案（每個框架命中一次 SetA、一次 SetB）。
- `sample_data/raw_excels/`：新增 10 份 `.xlsx`，每份 100 列，欄位是
  `Index / Domain / Control ID / Clause Description / Owner / Evidence Status`，
  跟 `demo_ui.html` 動畫裡顯示的欄位一致。
- **版權提醒**：CAIQ（Cloud Security Alliance）、SIG（Shared Assessments）、VSA（Vendor
  Security Alliance）都是有版權的正式問卷，這裡的題目內容是根據這些框架公開已知的「控制領域」
  原創改寫的範例，不是真的複製原始問卷題目。跟客戶介紹時，講「引擎可以對應多種主流框架的
  結構」是誠實的，不要說「我們用的就是官方 CAIQ 題庫」。

---

## SOP 1：怎麼讓 `demo_ui.html` 動起來（不需要 Python server）

這版是**完全自包含**的靜態頁面——所有 10 題資料跟 100 列填充資料都直接寫在 JS 裡，
沒有用 `fetch()` 去讀外部檔案，所以**不會有 CORS 問題**，直接雙擊打開就會動，
不需要 `python -m http.server`（如果之前那個 SOP 建議你開伺服器，那是因為那時候的版本方向
可能要真的去讀外部 xlsx；這版為了確保錄影當天一定能動，選擇把資料內嵌，犧牲一點「真的在讀取
Excel」的真實感，換取「一定能動」的穩定性）。

1. 直接在檔案總管找到 `C:\aiagent-master\docagent_clean_mvp\demo_ui.html`，雙擊用 Chrome 打開。
2. 打開後等 1 秒，動畫會自動開始：進度條跑、左邊問題逐一浮現、右邊 Excel 分頁與表格自動切換、
   藍色高亮框自動鎖定命中列、答案回填到左邊。
3. 全程 90 秒跑完，不需要任何操作。想重播就按 F5 重新整理。
4. 錄影前建議先按 **F11** 全螢幕，畫面比較乾淨。

如果雙擊打開後畫面完全空白或跳出錯誤：按 **F12** 打開瀏覽器開發者工具，切到 **Console** 分頁，
把紅色錯誤訊息複製給我，我可以照著訊息定位問題（這是你自己的除錯原則第一步：先看 Console
錯誤，這裡同樣適用）。

## SOP 2：開頭想加「這是真的在讀 Excel」的畫面（加分但非必要）

1. 開一個檔案總管視窗，切到 `C:\aiagent-master\docagent_clean_mvp\sample_data\raw_excels\`。
2. 用滑鼠依序快速點開 2–3 份（例如 `CAIQ_SetA.xlsx`、`NIST_SetA.xlsx`），秀出每份真的有 100 列
   資料，錄 5–8 秒。
3. 全部關閉，切回 `demo_ui.html` 開始正式錄影。

## SOP 3：想秀後端真的有 Python 在跑（加分但非必要）

1. 開終端機，`cd C:\aiagent-master\docagent_clean_mvp`
2. 執行 `python run_demo.py`（這是舊版 9 題 ISO27001/GDPR 那組資料，跟新的 10 份框架資料是
   兩套獨立的展示素材，不要在同一支影片裡混著講，容易讓觀眾以為數字對不上）。
3. 只用來證明「真的有 Python pipeline 在跑、不是純前端花招」，錄 10 秒終端機輸出即可，
   不用等它跑完接到 demo_ui.html 上。

---

## 逐秒稿（10 題 x 9 秒 = 90 秒，全英文）

| 時間 | 畫面 | 英文旁白（可貼進 CapCut TTS）|
|------|------|-------------------------------|
| 0:00–0:05 | Title card / 開場 | "Ten compliance frameworks. A thousand data rows. One AI agent." |
| 0:05–0:14 | Q1 CAIQ SetA，藍框鎖定 Row 34 | "Question one: is multi-factor authentication enforced for all privileged accounts? The agent searches the CAIQ dataset, locks onto row 34, and confirms — yes, verified by enforcement logs." |
| 0:14–0:23 | Q2 CAIQ SetB，Row 61 | "Next: how is data at rest encrypted? The agent finds AES-256 encryption with 90-day key rotation, cited directly from the source row." |
| 0:23–0:32 | Q3 SIG SetA，Row 18 | "Switching frameworks — this is a SIG questionnaire now. Access rights are re-certified quarterly, confirmed by the Q2 2026 review." |
| 0:32–0:41 | Q4 SIG SetB，Row 77 | "Not every answer is a clean yes. Here, the business continuity test is scheduled but not yet completed — the agent flags it yellow for human review, not a guess." |
| 0:41–0:50 | Q5 NIST SetA，Row 9 | "Now a NIST-aligned dataset. Endpoint protection — confirmed, 100 percent coverage across managed devices." |
| 0:50–0:59 | Q6 NIST SetB，Row 45 | "Incident response — a 24-hour breach notification requirement, verified and tested this quarter." |
| 0:59–1:08 | Q7 VSA SetA，Row 52 | "Vendor Security Alliance framework. Subcontractor due diligence — confirmed, the register is current." |
| 1:08–1:17 | Q8 VSA SetB，Row 23 | "Vulnerability remediation SLA — two of three critical items are on track. One is at risk. The agent tells you exactly where to look." |
| 1:17–1:26 | Q9 ISO27001 SetA，Row 88 | "ISO 27001 now. Network segmentation between production and corporate environments — confirmed and audited this quarter." |
| 1:26–1:30 | Q10 ISO27001 SetB，Row 5 + 結尾字卡 | "And the information security policy itself — approved, versioned, reviewed annually. Ten frameworks, ninety seconds, zero guesswork." |

**語速提醒**：每格大約 9 秒要念 15–25 個英文單字，CapCut TTS 語速可以調到約 1.1–1.2 倍速讓節奏更緊湊，或是把逐秒稿念稿時間抓緊一點提早收尾，讓最後 2–3 秒留給 CTA 字卡。

---

## 標題與 CTA（延續前一版，英文為主）

- `From 10 Compliance Frameworks to 90 Seconds: AI-Powered Questionnaire Response`
- `Private, Self-Hosted, Framework-Aware: A Document Intelligence Agent for Enterprise Compliance`
- 結尾字卡：`Private deployment available. Message me for a custom build.`

---

## 待清理（權限問題，你手動刪就好）

`sample_data/raw_excels/` 裡這 10 份是舊版素材，`demo_ui.html` 已經不會再讀取它們，
可以手動刪除保持資料夾乾淨：
`FCPA_Anti_Bribery_Compliance.xlsx`、`GDPR_Data_Privacy.xlsx`、
`ISO14001_Environmental_Management.xlsx`、`ISO22301_Business_Continuity.xlsx`、
`ISO27001_Information_Security.xlsx`、`ISO45001_Occupational_Health_Safety.xlsx`、
`ISO9001_Quality_Management.xlsx`、`Intellectual_Property_Policy.xlsx`、
`RBA_Labor_Standard.xlsx`、`Supplier_Code_of_Conduct.xlsx`
