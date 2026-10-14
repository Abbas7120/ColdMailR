const express = require('express');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

function getPython() {
  const venvPy = process.platform === 'win32'
    ? path.join(__dirname, '.venv', 'Scripts', 'python.exe')
    : path.join(__dirname, '.venv', 'bin', 'python');
  if (fs.existsSync(venvPy)) return venvPy;
  if (process.env.PYTHON_PATH) return process.env.PYTHON_PATH;
  return process.platform === 'win32' ? 'python' : 'python3';
}

function runPython(payload) {
  return new Promise((resolve, reject) => {
    const py = spawn(getPython(), [path.join(__dirname, 'tinker_generator.py')], {
      cwd: __dirname,
      env: { ...process.env, PYTHONUTF8: '1', PYTHONIOENCODING: 'utf-8' },
    });
    let out = '', err = '';
    py.stdout.on('data', d => (out += d));
    py.stderr.on('data', d => (err += d));
    py.on('error', e => reject(new Error('Could not start Python: ' + e.message)));
    py.on('close', code => {
      if (err.trim()) console.log('[python]', err.trim());
      const last = out.trim().split('\n').pop();
      let parsed = null;
      try { parsed = JSON.parse(last); } catch (e) {}
      if (parsed && parsed.email) return resolve(parsed.email);
      const msg = (parsed && parsed.error) || err.trim().split('\n').pop() || ('Python exited with code ' + code);
      reject(new Error(msg));
    });
    py.stdin.write(JSON.stringify(payload));
    py.stdin.end();
  });
}

app.get('/', (req, res) => {
  res.send(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ColdMailr AI - Zero-Prompt Cold Emails</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f8fafc; margin: 0; padding: 40px 20px; color: #1e293b; }
    .container { max-width: 600px; margin: 0 auto; background: #fff; padding: 35px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
    h1 { color: #0f172a; margin-top: 0; text-align: center; font-size: 26px; }
    p.subtitle { text-align: center; color: #64748b; margin-bottom: 30px; font-size: 14px; }
    label { display: block; font-weight: 600; margin-bottom: 6px; margin-top: 18px; font-size: 14px; }
    input, textarea { width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 14px; font-family: inherit; }
    input:focus, textarea:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
    button.generate-btn { background: #2563eb; color: #fff; border: none; padding: 14px 20px; font-size: 16px; font-weight: 600; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 25px; transition: background 0.2s; }
    button.generate-btn:hover { background: #1d4ed8; }
    .result-box { margin-top: 25px; background: #f1f5f9; border: 1px solid #cbd5e1; padding: 20px; border-radius: 8px; white-space: pre-wrap; font-size: 14px; display: none; position: relative; }
    .copy-btn { position: absolute; top: 12px; right: 12px; background: #2563eb; color: #fff; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; }
    .progress-wrap { display: none; margin-top: 22px; }
    .progress-track { height: 8px; background: #e2e8f0; border-radius: 99px; overflow: hidden; }
    .progress-fill { height: 100%; width: 0%; background: linear-gradient(90deg,#2563eb,#60a5fa); border-radius: 99px; transition: width 0.4s ease; }
    .progress-text { margin-top: 10px; font-size: 13px; color: #475569; text-align: center; font-weight: 600; }
    .error-box { display: none; margin-top: 20px; background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: 14px; border-radius: 8px; font-size: 14px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>ColdMailr AI</h1>
    <p class="subtitle">Skip tedious prompt engineering. Generate tailored cold emails in 1 click.</p>

    <label>1. Target Company Name</label>
    <input type="text" id="company" placeholder="e.g. Vercel, Stripe, Acme Corp" />

    <label>2. Role / Goal</label>
    <input type="text" id="role" placeholder="e.g. Full-Stack Developer, Growth Intern" />

    <label>3. Your Core Highlight / Achievement</label>
    <textarea id="highlight" rows="3" placeholder="e.g. Built a React/Express app with 500 active users and cut query time by 40%"></textarea>

    <button id="genBtn" class="generate-btn" onclick="generateEmail()">Generate Cold Email</button>

    <div id="progressWrap" class="progress-wrap">
      <div class="progress-track"><div id="progressFill" class="progress-fill"></div></div>
      <div id="progressText" class="progress-text">Starting...</div>
    </div>

    <div id="errorBox" class="error-box"></div>

    <div id="resultBox" class="result-box">
      <button class="copy-btn" onclick="copyEmail()">Copy Email</button>
      <div id="emailOutput"></div>
    </div>
  </div>

  <script>
    var progressTimer = null;
    var STAGES = [
      [0,  'Reading your details...'],
      [20, 'Matching tone to the role...'],
      [45, 'Writing your email...'],
      [70, 'Checking quality and facts...'],
      [88, 'Final polish...']
    ];

    function startProgress() {
      var fill = document.getElementById('progressFill');
      var text = document.getElementById('progressText');
      document.getElementById('progressWrap').style.display = 'block';
      var pct = 0;
      fill.style.width = '0%';
      clearInterval(progressTimer);
      progressTimer = setInterval(function () {
        pct += (92 - pct) * 0.04;
        fill.style.width = pct.toFixed(1) + '%';
        for (var i = STAGES.length - 1; i >= 0; i--) {
          if (pct >= STAGES[i][0]) { text.innerText = STAGES[i][1] + ' ' + Math.round(pct) + '%'; break; }
        }
      }, 200);
    }

    function stopProgress() {
      clearInterval(progressTimer);
      document.getElementById('progressWrap').style.display = 'none';
    }

    function finishProgress(done) {
      clearInterval(progressTimer);
      document.getElementById('progressFill').style.width = '100%';
      document.getElementById('progressText').innerText = 'Done! 100%';
      setTimeout(function () { stopProgress(); done(); }, 450);
    }

    async function generateEmail() {
      var company = document.getElementById('company').value.trim();
      var role = document.getElementById('role').value.trim();
      var highlight = document.getElementById('highlight').value.trim();
      var resultBox = document.getElementById('resultBox');
      var errorBox = document.getElementById('errorBox');
      var btn = document.getElementById('genBtn');

      if (!company || !role || !highlight) { alert('Please fill out all 3 fields!'); return; }

      btn.disabled = true; btn.style.opacity = '0.6';
      resultBox.style.display = 'none';
      errorBox.style.display = 'none';
      startProgress();

      try {
        var response = await fetch('/api/generate-cold-email', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ company: company, role: role, highlight: highlight })
        });
        var data = await response.json();
        if (!response.ok || !data.email) { throw new Error(data.error || 'Unknown error'); }
        finishProgress(function () {
          document.getElementById('emailOutput').innerText = data.email;
          resultBox.style.display = 'block';
          btn.disabled = false; btn.style.opacity = '1';
        });
      } catch (err) {
        stopProgress();
        errorBox.innerText = 'Could not generate the email: ' + err.message + ' (nothing was faked, please try again)';
        errorBox.style.display = 'block';
        btn.disabled = false; btn.style.opacity = '1';
      }
    }

    function copyEmail() {
      navigator.clipboard.writeText(document.getElementById('emailOutput').innerText);
      alert('Cold email copied to clipboard!');
    }
  </script>
</body>
</html>`);
});

app.post('/api/generate-cold-email', async (req, res) => {
  const { company, role, highlight } = req.body || {};
  if (!company || !role || !highlight) {
    return res.status(400).json({ error: 'company, role and highlight are required' });
  }
  try {
    const email = await runPython({ company, role, highlight });
    console.log('OK: generated by Tinker for', company);
    res.json({ success: true, email });
  } catch (e) {
    console.error('FAILED:', e.message);
    res.status(500).json({ error: e.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log('ColdMailr AI running on http://localhost:' + PORT));