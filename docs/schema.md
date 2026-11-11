# Lantern — 資料表設計（v1.1）

> 本文件依據已實作的 SQLAlchemy models 與第一份 Alembic migration 整理。程式碼才是最終依據；兩者不一致時，先更新程式碼，再回頭更新本文件。

## Enum（Postgres 型別）

| 型別名稱 | 值 | 對應 Python |
|---|---|---|
| `goal_status` | `active` / `completed` / `archived` | `GoalStatus` |
| `task_status` | `todo` / `doing` / `done` | `TaskStatus` |
| `llm_provider` | `gemini` / `claude` | `LLMProvider` |

Python 的 enum 成員名稱與值相同（皆小寫），因為 SQLAlchemy 預設把成員**名稱**存進資料庫。

## 共用欄位

所有表都有以下三個欄位：

| 欄位 | 型別 | 約束 | 預設值 |
|---|---|---|---|
| id | UUID | PK | Python 端：`uuid.uuid4()` |
| created_at | timestamptz | not null | 資料庫端：`now()` |
| updated_at | timestamptz | not null | 資料庫端：`now()`；更新時由 ORM（`onupdate`）寫入 |

## users

| 欄位 | 型別 | 約束 |
|---|---|---|
| id | UUID | PK |
| email | VARCHAR(255) | not null，unique |
| password_hash | VARCHAR | not null（無長度限制） |
| created_at | timestamptz | not null |
| updated_at | timestamptz | not null |

- email 小寫由應用層保證（註冊與登入時皆轉小寫），資料庫不強制

## user_llm_keys

| 欄位 | 型別 | 約束 |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | not null，FK → users.id，`ON DELETE CASCADE`，索引 |
| provider | `llm_provider` | not null |
| encrypted_key | TEXT | not null |
| last4 | VARCHAR(4) | not null |
| created_at | timestamptz | not null |
| updated_at | timestamptz | not null |

- `UNIQUE (user_id, provider)`，名稱 `uq_user_llm_keys_user_provider`
- `encrypted_key` 為 Fernet 輸出（base64 字串）；API 只回傳 `provider` 與 `last4`

## goals

| 欄位 | 型別 | 約束 |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | not null，FK → users.id，`ON DELETE CASCADE`，索引 |
| title | VARCHAR(200) | not null |
| background | TEXT | not null |
| status | `goal_status` | not null，Python 端預設 `active` |
| created_at | timestamptz | not null |
| updated_at | timestamptz | not null |

## milestones

| 欄位 | 型別 | 約束 |
|---|---|---|
| id | UUID | PK |
| goal_id | UUID | not null，FK → goals.id，`ON DELETE CASCADE`，索引 |
| week_index | INTEGER | not null |
| title | VARCHAR(200) | not null |
| description | TEXT | 可為空 |
| success_criteria | TEXT | 可為空（但 prompt 要求 LLM 一定產出） |
| created_at | timestamptz | not null |
| updated_at | timestamptz | not null |

- `CHECK (week_index >= 1)`，名稱 `ck_milestones_week_index_positive`
- 沒有 `status`：完成與否由底下 task 算出

## tasks

| 欄位 | 型別 | 約束 |
|---|---|---|
| id | UUID | PK |
| milestone_id | UUID | not null，FK → milestones.id，`ON DELETE CASCADE`，索引 |
| title | VARCHAR(200) | not null |
| description | TEXT | 可為空 |
| status | `task_status` | not null，Python 端預設 `todo` |
| estimate_hours | NUMERIC(4,1) | 可為空 |
| completed_at | timestamptz | 可為空 |
| created_at | timestamptz | not null |
| updated_at | timestamptz | not null |

- `CHECK (estimate_hours >= 0)`，名稱 `ck_tasks_estimate_hours_nonneg`（NULL 會通過，符合預期）
- `CHECK ((status = 'done') = (completed_at IS NOT NULL))`，名稱 `ck_tasks_done_iff_completed_at`

## 關係

```
users ─┬─< user_llm_keys
       └─< goals ─< milestones ─< tasks
```

全部 `ON DELETE CASCADE`：刪 user 會帶走其 key 與計畫；刪 goal 會帶走底下的 milestone 與 task。

milestones / tasks 不直接存 `user_id`，擁有者檢查沿著鏈往上 join 到 goals。

## 實作注意事項
1. **`completed_at`**：status 變成 `done` 時寫入當下時間，離開 `done` 時清為 null，統一在 service 層處理；資料庫的 CHECK 是最後防線
2. **時間**：一律存 UTC（timezone-aware），顯示時才轉時區
3. **預設值分兩層**：`id`、`status` 為 Python 端預設（`default=`），資料庫沒有預設值，直接寫 SQL 時必須明確給值；`created_at`、`updated_at` 為資料庫端預設（`server_default`）
4. **`updated_at` 的更新**由 ORM 的 `onupdate` 負責，不是資料庫 trigger；直接用 SQL 更新資料時不會自動變動
5. **`(goal_id, week_index)` 不設 unique**（允許同一週多個 milestone）
6. **命名慣例**：enum 型別 `goal_status` / `task_status` / `llm_provider`；CHECK 為 `ck_<table>_<說明>`；UNIQUE 為 `uq_<table>_<欄位>`；索引為 SQLAlchemy 預設的 `ix_<table>_<column>`
7. **Postgres enum 在 downgrade 時需手動 `DROP TYPE`**（autogenerate 不會處理），已寫入第一份 migration 的 `downgrade()`
8. **`user_llm_keys.user_id` 的獨立索引與 `UNIQUE (user_id, provider)` 的索引有重複**（後者已涵蓋以 `user_id` 開頭的查詢），目前刻意保留，見 `decisions.md` D-17

## 已決定與待決定
- 已決定：id 使用 UUID；v1 不做 dependency（之後放 Task 層）；Milestone 進度用算的；刪除採 cascade；`success_criteria` 為純文字；預設值放 Python 端
- 待決定：`(goal_id, week_index)` 是否設 unique