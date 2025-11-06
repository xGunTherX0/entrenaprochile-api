Delivery: Admin endpoints, Admin UI, tests and how to verify

This file documents the recent additions (Nov 2025): admin endpoints on the backend, an Admin Dashboard in the frontend, unit tests and how to verify locally and in production.

What's included

- Backend (backend/app.py):
  - GET /api/admin/usuarios — list users with role detection
  - POST /api/admin/usuarios/<id>/promote — promote a user to Entrenador
  - DELETE /api/admin/usuarios/<id> — delete a user and related Cliente/Entrenador rows
  - GET /api/admin/metrics — aggregate counts: users, clientes, entrenadores, mediciones, rutinas

- Frontend (frontend/src/views/Admin.vue): Admin Dashboard UI that shows metrics, lists users and allows Promote/Delete actions. Uses token from localStorage (auth.js).

- Tests: tests/test_admin.py — pytest flow covering admin login, list, promote, metrics and delete.

Environment variables

- Backend (Render / local):
  - DATABASE_URL
  - JWT_SECRET
  - ADMIN_EMAIL, ADMIN_PASSWORD (defaults: admin@test.local / admin123)
  - CORS_ORIGINS (include Netlify domain)

- Frontend (Netlify):
  - VITE_API_BASE (e.g. https://entrenaprochile-api.onrender.com)

How to run tests locally (PowerShell)

1. Activate virtualenv: & .\venv\Scripts\Activate.ps1
2. Install deps: .\venv\Scripts\python.exe -m pip install -r requirements.txt
3. Run tests: .\venv\Scripts\python.exe -m pytest -q

E2E script (quick check)

Script: scripts/e2e.js (Node 18+). Env vars used: API_URL, ADMIN_EMAIL, ADMIN_PASS, DEV_PROMOTE_SECRET.
Run example (PowerShell):
$env:API_URL = 'https://entrenaprochile-api.onrender.com'
$env:ADMIN_EMAIL = 'admin@test.local'
$env:ADMIN_PASS = 'admin123'
node .\scripts\e2e.js

How to trigger redeploy (manual)

- Netlify: push to repository branch or use Netlify dashboard -> Trigger deploy.
- Render: if connected to GitHub, push will trigger; otherwise use Render dashboard to redeploy.

Notes

- I pushed the admin endpoints and Admin UI to master already. If you want I can run the E2E script now against production and report results. To trigger deploys programmatically we would need API tokens for Render/Netlify.
