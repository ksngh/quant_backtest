# Frontend Status

## Current Purpose
Frontend dashboard integration with read-only backtest API verified in Task 078.

## Active Task
No active frontend task. Task 146 display semantics update completed in the Tasks 140-148 window.

## Stack Decision Boundary
- Selected stack: Next.js App Router + React + TypeScript.
- Do not combine Next.js and Vite in the same app.
- Frontend uses backend API only via `NEXT_PUBLIC_BACKTEST_API_BASE_URL`.
- Backtest cash display distinguishes cash balance from free cash when account-state metadata is available.
