# Lantern — 資料表設計（v1）

> 本文件是設計意圖。實作後，SQLAlchemy models 與 Alembic migration 才是最終依據；兩者不一致時，先更新程式碼，再回頭更新本文件。

## Enum

| Enum | 值 |
|---|---|
| `GoalStatus` | `active` / `completed` / `archived` |
| `TaskStatus` | `todo` / `doing` / `done` |
| `LLMProvider` | `gemini` / `claude` |

## User

| 欄位 | 型別 | 約束 |
|---|---|---|
| id | UUID | PK |
| email | String(255) | unique、not null，存入前轉小寫 |
| password_hash | String | not null |
| created_at | timestamptz | not null，預設現在 |
| updated_at | timestamptz | not null |

## UserLLMKey

| 欄位 | 型別 | 約束 |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → User，`ON DELETE CASCADE`，索引 |
| provider | `LLMProvider` | not null |
| encrypted_key | Text | not null |
| last4 | String(4) | not null |
| created_at / updated_at | timestamptz | not null |

額外約束：`UNIQUE (user_id, provider)`

## Goal

| 欄位 | 型別 | 約束 |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → User，`ON DELETE CASCADE`，索引 |
| title | String(200) | not null |
| background | Text | not null |
| status | `GoalStatus` | not null，預設 `active` |
| created_at / updated_at | timestamptz | not null |

## Milestone

| 欄位 | 型別 | 約束 |
|---|---|---|
| id | UUID | PK |
| goal_id | UUID | FK → Goal，`ON DELETE CASCADE`，索引 |
| week_index | Integer | not null，`CHECK (week_index >= 1)` |
| title | String(200) | not null |
| description | Text | 可為空 |
| success_criteria | Text | 可為空（但 prompt 要求 LLM 一定產出） |
| created_at / updated_at | timestamptz | not null |

沒有 `status`：完成與否由底下 task 算出。

## Task

| 欄位 | 型別 | 約束 |
|---|---|---|
| id | UUID | PK |
| milestone_id | UUID | FK → Milestone，`ON DELETE CASCADE`，索引 |
| title | String(200) | not null |
| description | Text | 可為空 |
| status | `TaskStatus` | not null，預設 `todo` |
| estimate_hours | Numeric(4,1) | 可為空，`CHECK (estimate_hours >= 0)` |
| completed_at | timestamptz | 可為空 |
| created_at / updated_at | timestamptz | not null |

額外約束（建議）：`CHECK ((status = 'done') = (completed_at IS NOT NULL))`

## 關係

```
User ─┬─< UserLLMKey
      └─< Goal ─< Milestone ─< Task
```

全部 cascade：刪 User 會帶走其 key 與計畫；刪 Goal 會帶走底下的 Milestone 與 Task。

Milestone / Task 不直接存 `user_id`，擁有者檢查沿著鏈往上 join 到 Goal。

## 實作注意事項
1. `completed_at`：status 變成 `done` 時寫入當下時間，離開 `done` 時清為 null，統一在 service 層處理
2. 時間一律存 UTC（timezone-aware），顯示時才轉時區
3. `(goal_id, week_index)` 不設 unique（允許同一週多個 milestone）
4. `UserLLMKey.encrypted_key` 為 Fernet 輸出，主密鑰放環境變數；API 只回傳 `provider` 與 `last4`

## 已決定與待決定
- 已決定：v1 不做 dependency（之後放 Task 層）；Milestone 進度用算的；刪除採 cascade；`success_criteria` 為純文字
- 待決定：id 用 UUID 
