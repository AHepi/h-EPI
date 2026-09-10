"""Probe DeepSeek's own API with the arm-A brief that returned an empty reply through Ollama.

Same subject, same system prompt, same user brief, same per-call cap. The question is narrow:
does the model burn the whole allowance and return no content here too?
"""
import json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, "/home/user/h-EPI/src")
from pathlib import Path
from creib.forge.mini import usetest

KEY = Path(os.environ["DS_KEY_FILE"]).read_text().strip()
MODEL = sys.argv[1] if len(sys.argv) > 1 else "deepseek-flash"
MAX_TOKENS = int(sys.argv[2]) if len(sys.argv) > 2 else 32000
SUBJECT = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("/home/user/h-EPI/forge/mini/runs/usetest/v5-s2-2/subject.py")

system = usetest._ARM_A_SYSTEM
user = usetest._brief(SUBJECT, rules_only=False)
body = json.dumps({
    "model": MODEL,
    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    "temperature": 0,
    "max_tokens": MAX_TOKENS,
    "response_format": {"type": "json_object"},
    "stream": False,
}).encode("utf-8")

req = urllib.request.Request(
    "https://api.deepseek.com/chat/completions",
    data=body, method="POST",
    headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY},
)
started = time.monotonic()
try:
    with urllib.request.urlopen(req, timeout=900) as r:
        status, raw = r.status, r.read()
except urllib.error.HTTPError as e:
    raw = e.read()
    print("HTTP", e.code, raw.decode("utf-8", "replace").replace(KEY, "<redacted>")[:600])
    raise SystemExit(1)
elapsed = int(time.monotonic() - started)
parsed = json.loads(raw)
choice = (parsed.get("choices") or [{}])[0]
msg = choice.get("message") or {}
content = msg.get("content") or ""
reasoning = msg.get("reasoning_content") or ""
usage = parsed.get("usage") or {}
print(f"model={MODEL} status={status} elapsed={elapsed}s")
print(f"finish_reason={choice.get('finish_reason')!r}")
print(f"usage={json.dumps(usage)}")
print(f"content chars={len(content)}  reasoning chars={len(reasoning)}")
print("--- content ---")
print(content[:1200] if content else "(EMPTY — the same failure)")
out = Path(os.environ["OUT"])
out.write_text(json.dumps({"model": MODEL, "max_tokens": MAX_TOKENS, "subject": str(SUBJECT),
                           "finish_reason": choice.get("finish_reason"), "usage": usage,
                           "content": content, "reasoning_chars": len(reasoning),
                           "elapsed_s": elapsed}, indent=2), encoding="utf-8")
