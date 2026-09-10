"""The cheapest alternative to mini: one call, rules and source, asked for a divergence.

Not part of BUILD-TEST-1. A baseline, run outside the block, to answer whether the thing the
reconstruction arm found was reachable without any loop at all.
"""
import json, os, sys, urllib.request, urllib.error, time
sys.path.insert(0, "/home/user/h-EPI/src")
from pathlib import Path
from creib.forge.mini.usetest import rules_text, subject_source

SYSTEM = (
    "You are auditing one module. You are given its documented rules and its complete source. "
    "Find the strongest single place where the CODE does something the DOCSTRING as written does "
    "not license — a divergence between what a function's description says and what it does. "
    "Return JSON only: {\"function\": \"...\", \"docstring_words\": \"the exact words you read it from\", "
    "\"code_does\": \"...\", \"example_input\": \"one exact input showing the difference\"}. "
    "Write nothing outside the JSON object."
)
src = subject_source()
USER = "## The documented rules\n\n" + rules_text(src) + "\n\n## The source\n\n" + src

key = Path(os.environ["DEEPSEEK_KEY_FILE"]).read_text().strip()
model = sys.argv[1]; n = int(sys.argv[2])
out = []
for i in range(n):
    body = json.dumps({"model": model,
                       "messages": [{"role": "system", "content": SYSTEM},
                                    {"role": "user", "content": USER + (f"\n\n(attempt {i+1}; give a different answer from any obvious one)" if i else "")}],
                       "temperature": 0, "max_tokens": 32000,
                       "response_format": {"type": "json_object"}, "stream": False}).encode()
    req = urllib.request.Request("https://api.deepseek.com/chat/completions", data=body, method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    t = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=900) as r: raw = r.read()
    except urllib.error.HTTPError as e:
        out.append({"attempt": i, "error": f"HTTP {e.code}"}); continue
    p = json.loads(raw.decode().replace(key, "<redacted>"))
    c = (p.get("choices") or [{}])[0]
    txt = ((c.get("message") or {}).get("content")) or ""
    try: parsed = json.loads(txt)
    except ValueError: parsed = {"unparsed": txt[:500]}
    out.append({"attempt": i, "elapsed_s": int(time.monotonic()-t), **parsed})
    print(f"[{i}] {parsed.get('function','?')}: {str(parsed.get('code_does',''))[:110]}", flush=True)
Path(os.environ["OUT"]).write_text(json.dumps({"model": model, "attempts": out}, indent=2) + "\n")
