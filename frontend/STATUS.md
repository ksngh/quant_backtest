# Frontend Status

## Current Purpose
Frontend dashboard integration with read-only backtest API verified in Task 078.

## Active Task
No active frontend task. Task 150 `BACKTEST_DASHBOARD_VISUAL_ANALYTICS_UPGRADE` completed.

## Stack Decision Boundary
- Selected stack: Next.js App Router + React + TypeScript.
- Do not combine Next.js and Vite in the same app.
- Frontend uses backend API only via `NEXT_PUBLIC_BACKTEST_API_BASE_URL`.
- Backtest cash display distinguishes cash balance from free cash when account-state metadata is available.
- Dashboard implementation should show semantic position signals first, keep raw execution side as audit context, and render parameters/metadata as curated UI rather than raw JSON by default.
- The dashboard now includes range-inspectable charts, compact paged trade review, curated parameter/runtime panels, and strategy indicator/economic explanation sections.
