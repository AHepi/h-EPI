"""The same arm-A call through ollama.com, with and without num_predict.

H4 leaves two mechanisms open. If removing the cap makes the same call terminate, the cap is
counting reasoning against the same budget as content and truncating the generation before any
content is emitted. If it still does not terminate, the cap is innocent and the path's serving
configuration is the difference.
"""
import json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, "/home/user/h-EPI/src")
from pathlib import Path
from creib.forge.mini import usetest

KEY = os.environ["OLLAMA_API_KEY"]
SUBJECT = Path("/home/user/h-EPI/forge/mini/runs/usetest/v5-s2-2/subject.py")
cap = None if sys.argv[1] == "none" else int(sys.argv[1])

options = {"temperature": 0, "seed": 7}
if cap is not None:
    options["num_predict"] = cap
payload = {
    "model": "deepseek-v4-pro:0813",
    "messages": [
        {"role": "system", "content": usetest._ARM_A_SYSTEM},
        {"role": "user", "content": usetest._brief(SUBJECT, rules_only=False)},
    ],
    "stream": False,
    "options": options,
    "format": usetest.PACKET_SCHEMA,
    "think": True,
}
req = urllib.request.Request(
    "https://ollama.com/api/chat", data=json.dumps(payload).encode("utf-8"), method="POST",
    headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY},
)
started = time.monotonic()
try:
    with urllib.request.urlopen(req, timeout=1800) as r:
        raw = r.read()
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode("utf-8", "replace").replace(KEY, "<redacted>")[:400]); raise SystemExit(1)
elapsed = int(time.monotonic() - started)
d = json.loads(raw)
msg = d.get("message") or {}
content = msg.get("content") or ""
thinking = msg.get("thinking") or ""
print(f"num_predict={cap} elapsed={elapsed}s done={d.get('done')} done_reason={d.get('done_reason')!r}")
print(f"eval_count={d.get('eval_count')} prompt_eval_count={d.get('prompt_eval_count')}")
print(f"content chars={len(content)}  thinking chars={len(thinking)}")
print("--- content ---")
print(content[:900] if content else "(EMPTY)")
Path(os.environ["OUT"]).write_text(json.dumps({
    "path": "https://ollama.com", "model": "deepseek-v4-pro:0813", "num_predict": cap,
    "done": d.get("done"), "done_reason": d.get("done_reason"),
    "eval_count": d.get("eval_count"), "prompt_eval_count": d.get("prompt_eval_count"),
    "content": content, "thinking_chars": len(thinking), "elapsed_s": elapsed,
}, indent=2) + "\n", encoding="utf-8")
