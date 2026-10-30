#!/usr/bin/env python3
"""Build bonus.html (read-only player view of the Bonus Marks board) from exported DB docs.
Usage: build_bonus.py <dir with players/ marks/ queue/ settings/ JSON docs> <output.html>
Writes the output only; prints CHANGED or UNCHANGED (data compared without the timestamp)."""
import json, glob, os, sys, re
from datetime import datetime
from zoneinfo import ZoneInfo
src, out = sys.argv[1], sys.argv[2]
PARIS = ZoneInfo("Europe/Paris")
def load(c):
    d = {}
    for f in glob.glob(os.path.join(src, c, "*.json")):
        j = json.load(open(f, encoding="utf8")); d[os.path.basename(f)[:-5]] = j.get("data", j) if isinstance(j.get("data"), dict) else j
    return d
players, marks, queue, settings = load("players"), load("marks"), load("queue"), load("settings")
sl = (settings.get("main") or {}).get("slots") or {}
slots = {t: max(1, min(10, int(sl.get(t) or 2))) for t in ("research", "construction")}
def ts(date, time):
    y, m, d = map(int, date.split("-")); hh, mm = map(int, (time or "00:00").split(":"))
    return int(datetime(y, m, d, hh, mm, tzinfo=PARIS).timestamp() * 1000)
def pname(pid, fb):
    return (players.get(pid) or {}).get("name") or fb or "?"
def prank(pid):
    return (players.get(pid) or {}).get("rank")
M = []
for k, m in marks.items():
    if not m.get("start"): continue
    M.append(dict(t=m["type"], n=pname(m.get("pid"), m.get("name")), r=prank(m.get("pid")), d=m["days"], s=ts(m["start"], m.get("time")),
                  e=(ts(m["end"], "00:00") if m.get("end") else None), c=m.get("created") or 0))
M.sort(key=lambda x: (x["s"], x["c"]))
for x in M: x.pop("c")
Q = sorted(({"t": q["type"], "n": pname(q.get("pid"), q.get("name")), "r": prank(q.get("pid")), "d": q["days"], "o": q.get("order") or 0} for q in queue.values()), key=lambda x: x["o"])
for x in Q: x.pop("o")
data = {"slots": slots, "marks": M, "queue": Q}
blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
old = ""
if os.path.exists(out):
    m = re.search(r"const DATA=(.*?);\n", open(out, encoding="utf8").read())
    old = m.group(1) if m else ""
stamp = datetime.now(PARIS).strftime("%d %b %Y, %H:%M")
html = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bonus_template.html"), encoding="utf8").read()
html = html.replace("__DATA__", blob).replace("__STAMP__", stamp)
if old == blob:
    print("UNCHANGED"); sys.exit(0)
open(out, "w", encoding="utf8").write(html); print("CHANGED")
