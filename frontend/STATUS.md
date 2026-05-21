# Frontend Status

## Current Purpose
Frontend dashboard integration with read-only backtest API verified in Task 078.

## Active Task
Task 078 completed.

## Stack Decision Boundary
- Selected stack: Next.js App Router + React + TypeScript.
- Do not combine Next.js and Vite in the same app.
- Frontend uses backend API only via `NEXT_PUBLIC_BACKTEST_API_BASE_URL`.
