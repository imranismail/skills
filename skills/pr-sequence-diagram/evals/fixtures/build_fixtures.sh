#!/usr/bin/env bash
# Builds 3 synthetic PR fixtures. Each fixture is a git repo with a main
# branch and a feature branch. Run fresh each time — wipes existing dirs.
set -euo pipefail

FIXTURES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$FIXTURES_DIR"

export GIT_CONFIG_GLOBAL=/dev/null
gitq() { git -c user.email=bot@example.com -c user.name=Bot "$@" >/dev/null; }

rm -rf node-api-stripe-cancel python-queue-welcome-emails react-onboarding-flag

############################################
# Fixture 1: node-api-stripe-cancel
############################################
mkdir -p node-api-stripe-cancel/src
cd node-api-stripe-cancel
gitq init -b main

cat > package.json <<'EOF'
{
  "name": "billing-api",
  "version": "0.1.0",
  "dependencies": {
    "express": "^4.18.0",
    "pg": "^8.11.0"
  }
}
EOF

cat > src/server.js <<'EOF'
const express = require('express');
const { pool } = require('./db');
const { requireAuth } = require('./auth');

const app = express();
app.use(express.json());

app.get('/api/health', (req, res) => res.json({ ok: true }));

app.get('/api/users/:id', requireAuth, async (req, res) => {
  const { rows } = await pool.query(
    'SELECT id, email FROM users WHERE id = $1',
    [req.params.id]
  );
  if (!rows[0]) return res.status(404).end();
  res.json(rows[0]);
});

app.get('/api/subscriptions/:id', requireAuth, async (req, res) => {
  const { rows } = await pool.query(
    'SELECT * FROM subscriptions WHERE id = $1 AND user_id = $2',
    [req.params.id, req.user.id]
  );
  if (!rows[0]) return res.status(404).end();
  res.json(rows[0]);
});

app.listen(3000);
EOF

cat > src/db.js <<'EOF'
const { Pool } = require('pg');
exports.pool = new Pool({ connectionString: process.env.DATABASE_URL });
EOF

cat > src/auth.js <<'EOF'
const { pool } = require('./db');

exports.requireAuth = async (req, res, next) => {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) return res.status(401).end();
  const { rows } = await pool.query(
    'SELECT id, email FROM users WHERE session_token = $1',
    [token]
  );
  if (!rows[0]) return res.status(401).end();
  req.user = rows[0];
  next();
};
EOF

cat > README.md <<'EOF'
# billing-api

Simple billing API.
EOF

gitq add .
gitq commit -m "initial billing api"

gitq checkout -b add-subscription-cancel

cat > src/stripe.js <<'EOF'
const Stripe = require('stripe');
const client = new Stripe(process.env.STRIPE_KEY);

exports.cancelSubscription = async (stripeSubscriptionId) => {
  return client.subscriptions.cancel(stripeSubscriptionId);
};
EOF

cat > src/emails.js <<'EOF'
exports.sendEmail = async (to, subject, body) => {
  const res = await fetch('https://api.sendgrid.com/v3/mail/send', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.SENDGRID_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      personalizations: [{ to: [{ email: to }] }],
      from: { email: 'noreply@billing.example.com' },
      subject,
      content: [{ type: 'text/plain', value: body }],
    }),
  });
  if (!res.ok) throw new Error(`sendgrid ${res.status}`);
};
EOF

cat > src/server.js <<'EOF'
const express = require('express');
const { pool } = require('./db');
const { requireAuth } = require('./auth');
const { cancelSubscription } = require('./stripe');
const { sendEmail } = require('./emails');

const app = express();
app.use(express.json());

app.get('/api/health', (req, res) => res.json({ ok: true }));

app.get('/api/users/:id', requireAuth, async (req, res) => {
  const { rows } = await pool.query(
    'SELECT id, email FROM users WHERE id = $1',
    [req.params.id]
  );
  if (!rows[0]) return res.status(404).end();
  res.json(rows[0]);
});

app.get('/api/subscriptions/:id', requireAuth, async (req, res) => {
  const { rows } = await pool.query(
    'SELECT * FROM subscriptions WHERE id = $1 AND user_id = $2',
    [req.params.id, req.user.id]
  );
  if (!rows[0]) return res.status(404).end();
  res.json(rows[0]);
});

app.post('/api/subscriptions/:id/cancel', requireAuth, async (req, res) => {
  const { rows } = await pool.query(
    'SELECT * FROM subscriptions WHERE id = $1 AND user_id = $2',
    [req.params.id, req.user.id]
  );
  const sub = rows[0];
  if (!sub) return res.status(404).end();
  if (sub.status === 'canceled') return res.status(409).json({ error: 'already canceled' });

  await cancelSubscription(sub.stripe_subscription_id);
  await pool.query(
    'UPDATE subscriptions SET status = $1, canceled_at = NOW() WHERE id = $2',
    ['canceled', sub.id]
  );
  await sendEmail(
    req.user.email,
    'Your subscription has been canceled',
    'We have canceled your subscription. You will retain access until the end of the billing period.'
  );

  res.json({ ok: true });
});

app.listen(3000);
EOF

gitq add .
gitq commit -m "add subscription cancel endpoint

POST /api/subscriptions/:id/cancel cancels the subscription in Stripe,
marks it canceled in our DB, and sends a confirmation email via SendGrid."

cd "$FIXTURES_DIR"

############################################
# Fixture 2: python-queue-welcome-emails
############################################
mkdir -p python-queue-welcome-emails
cd python-queue-welcome-emails
gitq init -b main

cat > requirements.txt <<'EOF'
flask==3.0.0
psycopg[binary]==3.1.18
EOF

cat > db.py <<'EOF'
import os
import psycopg

def _conn():
    return psycopg.connect(os.environ["DATABASE_URL"])

def create_user(email: str, password_hash: str):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                (email, password_hash),
            )
            (user_id,) = cur.fetchone()
            return {"id": user_id, "email": email}
EOF

cat > emails.py <<'EOF'
import os
import smtplib
from email.message import EmailMessage

def send_welcome_email(to_address: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = "Welcome!"
    msg["From"] = "hello@example.com"
    msg["To"] = to_address
    msg.set_content("Thanks for signing up.")

    with smtplib.SMTP(os.environ["SMTP_HOST"], 587) as s:
        s.starttls()
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)
EOF

cat > app.py <<'EOF'
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash

from db import create_user
from emails import send_welcome_email

app = Flask(__name__)

@app.post("/signup")
def signup():
    data = request.get_json()
    user = create_user(data["email"], generate_password_hash(data["password"]))
    send_welcome_email(user["email"])
    return jsonify({"id": user["id"]}), 201
EOF

gitq add .
gitq commit -m "initial signup app"

gitq checkout -b queue-welcome-emails

cat > requirements.txt <<'EOF'
flask==3.0.0
psycopg[binary]==3.1.18
redis==5.0.1
rq==1.16.0
EOF

cat > queue_client.py <<'EOF'
import os
from redis import Redis
from rq import Queue

_redis = Redis.from_url(os.environ["REDIS_URL"])
_queue = Queue("emails", connection=_redis)

def enqueue_welcome_email(email: str) -> None:
    _queue.enqueue("worker.send_welcome_email_job", email)
EOF

cat > worker.py <<'EOF'
import os
import sys
from redis import Redis
from rq import Worker, Queue

from emails import send_welcome_email

def send_welcome_email_job(email: str) -> None:
    send_welcome_email(email)

if __name__ == "__main__":
    redis = Redis.from_url(os.environ["REDIS_URL"])
    queue = Queue("emails", connection=redis)
    Worker([queue], connection=redis).work()
EOF

cat > app.py <<'EOF'
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash

from db import create_user
from queue_client import enqueue_welcome_email

app = Flask(__name__)

@app.post("/signup")
def signup():
    data = request.get_json()
    user = create_user(data["email"], generate_password_hash(data["password"]))
    enqueue_welcome_email(user["email"])
    return jsonify({"id": user["id"]}), 201
EOF

gitq add .
gitq commit -m "move welcome email off request path

The signup endpoint was blocking on SMTP, which made P95 signup latency
spike whenever the email provider slowed down. Now signup enqueues a job
to Redis (via RQ) and a worker process actually sends the email."

cd "$FIXTURES_DIR"

############################################
# Fixture 3: react-onboarding-flag
############################################
mkdir -p react-onboarding-flag/src/pages react-onboarding-flag/src/hooks
cd react-onboarding-flag
gitq init -b main

cat > package.json <<'EOF'
{
  "name": "webapp",
  "version": "0.1.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0"
  }
}
EOF

cat > src/api.js <<'EOF'
export async function apiPost(path, body) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}

export async function apiGet(path) {
  const res = await fetch(path, { credentials: 'include' });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}
EOF

cat > src/App.jsx <<'EOF'
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
EOF

cat > src/pages/Login.jsx <<'EOF'
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiPost } from '../api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    await apiPost('/api/login', { email, password });
    navigate('/dashboard');
  }

  return (
    <form onSubmit={onSubmit}>
      <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
      <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="password" />
      <button type="submit">Log in</button>
    </form>
  );
}
EOF

cat > src/pages/Dashboard.jsx <<'EOF'
export default function Dashboard() {
  return <h1>Welcome back</h1>;
}
EOF

gitq add .
gitq commit -m "initial webapp with login + dashboard"

gitq checkout -b add-onboarding-flag

cat > src/hooks/useFeatureFlag.js <<'EOF'
import { useEffect, useState } from 'react';
import { apiGet } from '../api';

export function useFeatureFlag(name) {
  const [enabled, setEnabled] = useState(null);
  useEffect(() => {
    let cancelled = false;
    apiGet(`/api/flags/${name}`)
      .then((res) => { if (!cancelled) setEnabled(Boolean(res.enabled)); })
      .catch(() => { if (!cancelled) setEnabled(false); });
    return () => { cancelled = true; };
  }, [name]);
  return enabled;
}
EOF

cat > src/pages/Onboarding.jsx <<'EOF'
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiPost } from '../api';

const STEPS = ['profile', 'preferences', 'invite-team'];

export default function Onboarding() {
  const [step, setStep] = useState(0);
  const navigate = useNavigate();

  async function next(data) {
    await apiPost('/api/onboarding/step', { step: STEPS[step], data });
    if (step + 1 >= STEPS.length) {
      await apiPost('/api/onboarding/complete', {});
      navigate('/dashboard');
    } else {
      setStep(step + 1);
    }
  }

  return (
    <div>
      <h1>Welcome — let's get set up</h1>
      <p>Step {step + 1} of {STEPS.length}: {STEPS[step]}</p>
      <button onClick={() => next({})}>Next</button>
    </div>
  );
}
EOF

cat > src/pages/Login.jsx <<'EOF'
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiPost, apiGet } from '../api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    await apiPost('/api/login', { email, password });
    const flag = await apiGet('/api/flags/new-onboarding');
    if (flag.enabled) {
      navigate('/onboarding');
    } else {
      navigate('/dashboard');
    }
  }

  return (
    <form onSubmit={onSubmit}>
      <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
      <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="password" />
      <button type="submit">Log in</button>
    </form>
  );
}
EOF

cat > src/App.jsx <<'EOF'
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Onboarding from './pages/Onboarding';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/onboarding" element={<Onboarding />} />
      </Routes>
    </BrowserRouter>
  );
}
EOF

gitq add .
gitq commit -m "dark-launch new onboarding flow behind feature flag

After successful login, the app now checks the 'new-onboarding' flag
and routes first-run users through a 3-step onboarding flow when the
flag is enabled. Falls back to the existing dashboard route otherwise
so we can safely dark-launch to a cohort."

cd "$FIXTURES_DIR"

echo "Done. Created:"
ls -d */ | sed 's/^/  /'
