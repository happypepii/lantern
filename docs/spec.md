# Lantern — 專案 Spec（v0.4）

> 取名由來：提燈不替你走路，只照亮腳下這一步。路還是你自己走。

## 一句話定位
幫人把「我想成為某種人」變成一條具體、可追蹤、會隨進度調整的路。

## 第一個場景
拿到 junior dev 工作。作者本人是第一個使用者。

## 第一版使用流程
註冊 / 登入 → 在設定頁填入自己的 LLM API key → 輸入目標與背景 → AI 產出 milestone 與 task → 存進資料庫 → 看板顯示 → 勾選完成、看進度

## 核心設計決定
- **登入制**：使用者帳號（email + 密碼），JWT 認證，所有資源綁定 `user_id`
- **使用者自帶 API key（BYOK）**：AI 呼叫成本與額度由使用者自己承擔，平台不替任何人付費
- **加密存放在後端（方案 A）**：之後 MCP 整合與背景重新規劃都需要後端能自行呼叫 LLM

## 技術選型

| 層 | 選擇 | 理由 |
|---|---|---|
| 後端 | Python + FastAPI | 型別驗證、自動 API 文件、AI 生態完整 |
| 資料庫 | PostgreSQL + SQLAlchemy + Alembic | 關聯資料多，migration 有紀錄 |
| 認證 | JWT access token + argon2 / bcrypt 密碼雜湊 | 常見做法 |
| 密鑰保管 | Fernet（或 AES-GCM）加密，主密鑰放環境變數 | 使用者的 API key 不明文存放 |
| AI | `LLMClient` 介面，每次依使用者的 key 建立；先實作 Gemini，之後可加 Claude | 抽象層讓供應商可替換 |
| 結構化輸出 | JSON schema + 驗證 + 重試 | 計畫要能被程式解析 |
| 前端 | Vue 3 + Vite | 作者較熟，開發快 |
| 部署 | Docker + Render 或 Fly.io | 要有可點開的連結 |
| 測試 | pytest（LLM 一律 mock） | 履歷可寫測試覆蓋 |

## 資料模型草圖
- `User`：id, email, password_hash, created_at
- `UserLLMKey`：id, user_id, provider（gemini / claude…）, encrypted_key, last4, created_at
- `Goal`：id, user_id, title, background, status, created_at
- `Milestone`：id, goal_id, week_index, title, success_criteria（怎樣算完成）
- `Task`：id, milestone_id, title, description, status（todo / doing / done）, estimate_hours, completed_at
- `TaskDependency`：task_id, depends_on_id（之後再做）

## API key 安全規則
1. 加密後才寫入資料庫，主密鑰只放環境變數，不進 repo
2. API 永遠不回傳完整 key，只回傳 `last4`
3. key 不得出現在 log、錯誤訊息、任何 response 中（需有測試驗證）
4. 使用者可自行更新與刪除 key
5. 介面上提醒：使用者的目標與背景會送到其選擇的供應商

## 授權規則
- 每個 endpoint 都要檢查資源是否屬於當前使用者（A 不能讀寫 B 的 Goal / Milestone / Task）
- 授權檢查必須有對應測試

## LLM 呼叫的錯誤處理
需區分並向使用者清楚說明：key 無效、額度用完、被限流、供應商逾時、輸出格式錯誤（schema 驗證失敗後重試）。

## 功能清單

### 必做（v1）
- 註冊、登入、JWT 認證
- 使用者 LLM key 的加密儲存、更新、刪除
- Goal / Milestone / Task 的 CRUD API，含擁有者檢查
- 呼叫 LLM 產生計畫，驗證 JSON 格式，失敗時重試
- Vue 看板、登入頁、設定頁、整體進度百分比
- 部署上線、README、基本測試

### 之後再做
- MCP server 整合（在對話裡直接存計畫、更新進度）
- 重新規劃（落後時根據剩餘任務重排）
- Roadmap 圖（時間軸或依賴圖）
- 多供應商選擇（Claude 等）
- Email 驗證、忘記密碼、OAuth、refresh token
- 呼叫次數的限流（防止誤用）

## 「好計畫」的標準（之後作為評估方式）
1. 每週任務總時數不超過使用者可用時間
2. 每個 milestone 都有可驗證的成果（例如「部署上線一個專案」，而非「學習後端」）
3. 依賴順序正確
4. 格式一定可被解析（schema 驗證，統計失敗率）
5. 記錄每次呼叫的成本與延遲

## 里程碑
- **第 1 週**：專案骨架、資料庫 schema（含 User）、註冊 / 登入 / JWT、Goal / Milestone / Task CRUD、擁有者檢查與授權測試、Docker 本機可跑
- **第 2 週**：API key 加密儲存、`LLMClient` 抽象層（先做 Gemini）、規劃層（prompt、結構化輸出、驗證、重試、錯誤分類），測試以 mock 為主，並用作者自己的 key 實際跑 10 次，看品質與失敗率
- **第 3 週**：Vue 看板、登入頁、設定頁（管理 key）、進度計算
- **第 4 週**：部署上線、README（架構圖、設計取捨、安全設計）、`docs/decisions.md`
- **第 5 週之後**：MCP 整合 → 重新規劃 → roadmap 圖 → 限流

## 開發原則
- 每個 commit 都要能解釋「做了什麼、為什麼這樣寫」
- 一次做一個功能：先請 AI 提 plan → 自己決定 → 實作 → review → 測試 → commit
- 核心模組（資料模型、認證、規劃邏輯）自己主導設計
- 開發時用自己的 key 放在環境變數，測試不真的呼叫 API
- 重要決策記錄在 `docs/decisions.md`
