# API 设计

## 上传与处理（简化为单表）
- POST `/api/bluewow/upload/activation`（支持 `.csv` / `.xlsx`）
- POST `/api/bluewow/process`

## 指标与数据
- GET `/api/bluewow/metrics/overview`（当仅有激活名单时，`total=activated`，`activation_rate=null`）
- GET `/api/bluewow/metrics/monthly`（返回每月激活人数，`activation_rate=null`）
- GET `/api/bluewow/metrics/by-subject?scope=monthly|overall`
- GET `/api/bluewow/unactivated`（无花名册时返回`available=false`）
- GET `/api/bluewow/unactivated/list?subject=...`（同上）
- GET `/api/bluewow/raw?ref=...`
- GET `/api/bluewow/download/{name}.csv`
  - `{name}` 支持：`monthly`、`subject_overall`、`activated`

## 调度与日志
- POST `/api/bluewow/update/run`
- GET `/api/bluewow/logs`

## 飞书集成
- GET `/api/bluewow/feishu/auth/login|callback`
- POST `/api/bluewow/feishu/event`
