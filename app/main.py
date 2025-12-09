from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from .database import Base, engine, SessionLocal
from .routers import users, calculations
from . import schemas, crud_users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI Calculator with Login + BREAD")

def seed_demo_user():
    db = SessionLocal()
    try:
        if not crud_users.get_user_by_username(db, "demo"):
            demo = schemas.UserCreate(username="demo", email="demo@example.com", password="Test123!")
            crud_users.create_user(db, demo)
    finally:
        db.close()

seed_demo_user()

app.include_router(users.router)
app.include_router(calculations.router)

CALC_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>FastAPI Calculator with Login & BREAD</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto;
           padding: 20px; border: 1px solid #ddd; border-radius: 8px; background:#fafafa; }
    h1 { margin-top: 0; }
    h2 { margin-top: 24px; }
    label { display:block; margin-top:10px; }
    input, select, button { padding:8px; margin-top:5px; width:100%; box-sizing:border-box; }
    button { margin-top:15px; cursor:pointer; }
    #result-box { margin-top:20px; padding:10px; border-radius:6px; background:#f4f4f4; }
    .error { color:#b00020; }
    .ok { color:#007700; }
    table { border-collapse: collapse; width:100%; margin-top:10px; }
    th, td { border:1px solid #ccc; padding:6px; text-align:left; font-size: 0.9rem; }
    th { background:#eee; }
    .section { padding:12px; margin-top:16px; border-radius:6px; background:#ffffff; border:1px solid #e0e0e0; }
  </style>
</head>
<body>
  <h1>FastAPI Calculator (with Login + BREAD)</h1>

  <div class="section">
    <h2>Login</h2>
    <p>Demo login: <code>demo</code> / <code>Test123!</code></p>
    <label for="username">Username:</label>
    <input id="username" type="text" value="demo" />
    <label for="password">Password:</label>
    <input id="password" type="password" value="Test123!" />
    <button id="login-btn">Login</button>
    <p id="login-status"></p>
  </div>

  <div class="section">
    <h2>Add / Update</h2>
    <label for="a">a:</label>
    <input type="number" id="a" step="any" />
    <label for="b">b:</label>
    <input type="number" id="b" step="any" />
    <label for="type">Operation:</label>
    <select id="type">
      <option value="add">Add</option>
      <option value="sub">Subtract</option>
      <option value="mul">Multiply</option>
      <option value="div">Divide</option>
    </select>

    <label for="calc-id-edit">Calculation ID (Read/Edit/Delete):</label>
    <input type="number" id="calc-id-edit" min="1" />

    <button id="calc-add-btn">Add (POST)</button>
    <button id="calc-update-btn">Update (PUT)</button>
    <button id="calc-read-btn">Read (GET)</button>
    <button id="calc-delete-btn">Delete (DELETE)</button>

    <div id="result-box">
      <strong>Last Result:</strong> <span id="result-value">N/A</span>
      <div id="calc-error" class="error"></div>
    </div>
  </div>

  <div class="section">
    <h2>Browse</h2>
    <button id="refresh-btn">Refresh List</button>
    <div id="browse-error" class="error"></div>
    <table>
      <thead>
        <tr><th>ID</th><th>a</th><th>b</th><th>Type</th><th>Result</th><th>Load</th></tr>
      </thead>
      <tbody id="calc-table-body"></tbody>
    </table>
  </div>

  <p>Docs: <a href="/docs" target="_blank">/docs</a></p>

<script>
let accessToken = null;
const loginStatus = document.getElementById('login-status');
const resultSpan = document.getElementById('result-value');
const calcError = document.getElementById('calc-error');
const browseError = document.getElementById('browse-error');
const tableBody = document.getElementById('calc-table-body');

function requireAuth() {
  if (!accessToken) {
    calcError.textContent = 'Please login first.';
    return false;
  }
  return true;
}

function validateInputs() {
  calcError.textContent = '';
  const aV = document.getElementById('a').value;
  const bV = document.getElementById('b').value;
  const t = document.getElementById('type').value;
  if (aV === '' || bV === '') { calcError.textContent = 'Enter both numbers.'; return null; }
  const a = parseFloat(aV); const b = parseFloat(bV);
  if (!Number.isFinite(a) || !Number.isFinite(b)) { calcError.textContent = 'Invalid numbers.'; return null; }
  if (t === 'div' && b === 0) { calcError.textContent = 'Division by zero not allowed.'; return null; }
  return { type: t, a, b };
}

function authHeadersJson() {
  return { 'Authorization': 'Bearer ' + accessToken, 'Content-Type': 'application/json' };
}

async function login() {
  loginStatus.textContent = '';
  const u = document.getElementById('username').value.trim();
  const p = document.getElementById('password').value.trim();
  const form = new URLSearchParams(); form.append('username', u); form.append('password', p);

  const resp = await fetch('/users/login', { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: form.toString() });
  if (!resp.ok) {
    const err = await resp.json().catch(()=> ({}));
    loginStatus.textContent = err.detail || 'Login failed';
    loginStatus.className = 'error';
    accessToken = null;
    return;
  }
  const data = await resp.json();
  accessToken = data.access_token;
  loginStatus.textContent = 'Login successful.';
  loginStatus.className = 'ok';
  await refresh();
}

function render(list) {
  tableBody.innerHTML = '';
  list.forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${item.id}</td><td>${item.a}</td><td>${item.b}</td><td>${item.type}</td><td>${item.result}</td>
      <td><button data-id="${item.id}" class="load">Load</button></td>`;
    tableBody.appendChild(tr);
  });
  document.querySelectorAll('button.load').forEach(btn => {
    btn.addEventListener('click', async () => {
      document.getElementById('calc-id-edit').value = btn.getAttribute('data-id');
      await readById();
    });
  });
}

async function refresh() {
  browseError.textContent = '';
  if (!requireAuth()) return;
  const resp = await fetch('/calculations/', { headers:{'Authorization':'Bearer ' + accessToken} });
  if (!resp.ok) { browseError.textContent = 'Failed to load'; render([]); return; }
  render(await resp.json());
}

async function addCalc() {
  if (!requireAuth()) return;
  const payload = validateInputs(); if (!payload) return;
  const resp = await fetch('/calculations/', { method:'POST', headers: authHeadersJson(), body: JSON.stringify(payload) });
  if (!resp.ok) { calcError.textContent = 'Error adding'; return; }
  const data = await resp.json(); resultSpan.textContent = data.result;
  await refresh();
}

async function readById() {
  if (!requireAuth()) return;
  const id = document.getElementById('calc-id-edit').value;
  if (!id) { calcError.textContent = 'Enter ID'; return; }
  const resp = await fetch(`/calculations/${id}`, { headers:{'Authorization':'Bearer ' + accessToken} });
  if (!resp.ok) { calcError.textContent = 'Not found'; return; }
  const data = await resp.json();
  document.getElementById('a').value = data.a;
  document.getElementById('b').value = data.b;
  document.getElementById('type').value = data.type;
  resultSpan.textContent = data.result;
}

async function updateById() {
  if (!requireAuth()) return;
  const id = document.getElementById('calc-id-edit').value;
  if (!id) { calcError.textContent = 'Enter ID'; return; }
  const payload = validateInputs(); if (!payload) return;
  const resp = await fetch(`/calculations/${id}`, { method:'PUT', headers: authHeadersJson(), body: JSON.stringify(payload) });
  if (!resp.ok) { calcError.textContent = 'Error updating'; return; }
  const data = await resp.json(); resultSpan.textContent = data.result;
  await refresh();
}

async function deleteById() {
  if (!requireAuth()) return;
  const id = document.getElementById('calc-id-edit').value;
  if (!id) { calcError.textContent = 'Enter ID'; return; }
  const resp = await fetch(`/calculations/${id}`, { method:'DELETE', headers:{'Authorization':'Bearer ' + accessToken} });
  if (!(resp.status === 204 || resp.ok)) { calcError.textContent = 'Error deleting'; return; }
  resultSpan.textContent = 'Deleted ' + id;
  await refresh();
}

document.getElementById('login-btn').addEventListener('click', login);
document.getElementById('refresh-btn').addEventListener('click', refresh);
document.getElementById('calc-add-btn').addEventListener('click', addCalc);
document.getElementById('calc-read-btn').addEventListener('click', readById);
document.getElementById('calc-update-btn').addEventListener('click', updateById);
document.getElementById('calc-delete-btn').addEventListener('click', deleteById);
</script>
</body></html>"""

@app.get("/", response_class=HTMLResponse)
def root():
    return HTMLResponse(CALC_HTML)
