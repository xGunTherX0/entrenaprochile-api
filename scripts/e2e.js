// scripts/e2e.js
// Node script (requires Node 18+ for global fetch).
// Usage: node scripts/e2e.js
// Configure via env vars or edit the defaults below.

const API_URL = process.env.API_URL || 'https://entrenaprochile-api.onrender.com';
const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'admin@test.local';
const ADMIN_PASS = process.env.ADMIN_PASS || 'admin123';
const PROMOTE_SECRET = process.env.DEV_PROMOTE_SECRET || null; // optional

async function request(path, opts = {}) {
  const url = `${API_URL}${path}`;
  const res = await fetch(url, opts);
  const text = await res.text();
  let body = null;
  try { body = JSON.parse(text); } catch(e) { body = text; }
  return { status: res.status, body };
}

async function run() {
  const out = { steps: [] };
  // 1) login
  let r = await request('/api/usuarios/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: ADMIN_EMAIL, password: ADMIN_PASS })
  });
  out.steps.push({ step: 'login', status: r.status, body: r.body });
  if (r.status !== 200) {
    // try register admin as client
    const reg = await request('/api/usuarios/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: ADMIN_EMAIL, password: ADMIN_PASS, nombre: 'AutoAdmin' })
    });
    out.steps.push({ step: 'register_admin_attempt', status: reg.status, body: reg.body });
    if (reg.status >= 200 && reg.status < 300) {
      r = await request('/api/usuarios/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: ADMIN_EMAIL, password: ADMIN_PASS })
      });
      out.steps.push({ step: 'login-after-register', status: r.status, body: r.body });
    }
  }

  if (r.status !== 200) {
    console.error('Login failed, aborting.');
    console.log(JSON.stringify(out, null, 2));
    process.exit(2);
  }

  const token = r.body.token;
  const user_id = r.body.user_id;
  out.token = token ? ('[REDACTED length:'+token.length+']') : null;

  // optional: promote to entrenador if secret provided
  if (PROMOTE_SECRET) {
    const p = await request('/api/dev/promote_entrenador', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: ADMIN_EMAIL, secret: PROMOTE_SECRET })
    });
    out.steps.push({ step: 'promote', status: p.status, body: p.body });
  }

  const headers = { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token };

  // 2) Create measurement
  const meas = await request('/api/mediciones', {
    method: 'POST',
    headers,
    body: JSON.stringify({ peso: 70, fecha: new Date().toISOString().slice(0,10) })
  });
  out.steps.push({ step: 'create_medicion', status: meas.status, body: meas.body });

  // 3) Create rutina
  const rut = await request('/api/rutinas', {
    method: 'POST',
    headers,
    body: JSON.stringify({ nombre: 'E2E Rutina', ejercicios: ['A','B'] })
  });
  out.steps.push({ step: 'create_rutina', status: rut.status, body: rut.body });

  let rutina_id = null;
  if (rut.status >= 200 && rut.status < 300 && rut.body && rut.body.rutina && rut.body.rutina.id) rutina_id = rut.body.rutina.id;

  // 4) List rutinas for trainer (if user is entrenador)
  const list = await request(`/api/rutinas/${user_id}`, { method: 'GET', headers });
  out.steps.push({ step: 'list_rutinas', status: list.status, body: list.body });

  // 5) Delete created rutina if we have id
  if (rutina_id) {
    const del = await request(`/api/rutinas/${rutina_id}`, { method: 'DELETE', headers });
    out.steps.push({ step: 'delete_rutina', status: del.status, body: del.body });
  }

  console.log(JSON.stringify(out, null, 2));
}

run().catch(e => { console.error(e); process.exit(1); });
