"""Builds the README figures in assets/ from scoreboard.json (and the real output of show.py).
usage: python make_figures.py [date]   (date picks the run that show.py prints; default: scoreboard date)"""
import json
import subprocess
import sys
import numpy as np
from matplotlib.patches import Rectangle
from figstyle import *

P = theme("ice")
S = json.load(open("scoreboard.json"))
DATE = sys.argv[1] if len(sys.argv) > 1 else S["date"]
MODELS = S["models"]
MLAB = {"qwen2.5-0.5b": "qwen\n0.5b", "qwen2.5-1.5b": "qwen\n1.5b", "llama3.2-1b": "llama\n1b",
        "smollm2-1.7b": "smollm2\n1.7b", "gemma2-2b": "gemma2\n2b"}
FLAB = {"direct_ask": "direct ask (control)", "length_placebo": "long padding (control)",
        "instruction_override": "instruction override", "role_play": "role-play", "fiction_hypothetical": "fiction / hypothetical",
        "authority_claim": "fake authority", "prefix_injection": "prefix injection", "refusal_suppression": "refusal suppression",
        "base64_encoding": "base64 encoding", "output_obfuscation": "output obfuscation", "translation_multilingual": "other languages",
        "many_shot": "many-shot", "payload_splitting": "payload splitting", "completion_trap": "fill-in-the-blank"}
CONTROLS = ["direct_ask", "length_placebo"]
pooled = {f: S["pooled"][f]["leak"] / S["pooled"][f]["n"] for f in S["families"]}
attacks = sorted([f for f in S["families"] if f not in CONTROLS], key=lambda f: -pooled[f])
ORDER = CONTROLS + attacks


def sig(m, f):
    t = S["pooled_tests"] if m == "pooled" else S["tests"][m]
    return f in t and t[f]["p_holm"] < 0.05


def rate(m, f):
    c = S["pooled"][f] if m == "pooled" else S["cells"][m][f]
    return c["leak"] / c["n"]


# 0. banner: dated series drifting and thinning out, like a tracked metric over many reruns
rng = np.random.default_rng(17)
field = np.full((100, 400), 0.04)
xs = np.arange(400)
for k in range(7):
    y0 = 18 + k * 11
    y = y0 + 22 * (xs / 400) ** 1.4 + np.cumsum(rng.normal(0, 0.35, 400))
    fade = np.clip(1.05 - 0.75 * xs / 400, 0.15, 1)
    for x in range(160, 400):
        yy = int(np.clip(y[x], 0, 98))
        field[yy:yy + 2, x] = max(field[yy, x], fade[x] * (0.55 + 0.45 * (k % 2)))
for x in range(176, 400, 32):
    field[:, x] = np.maximum(field[:, x], 0.1)                 # run dates
banner("banner.png", "jailbreak-decay-tracker",
       "a rerunnable jailbreak baseline on small open models, with a harmless canary.", field,
       meta="> defensive · 5 small open models · cpu only")

# 1. leak rate, family x model, with the pooled column
cols = MODELS + ["pooled"]
f, ax = fig(11.0, left=0.3, right=0.97, top_in=1.95, bottom_in=0.75)
for j, m in enumerate(cols):
    for i, fam in enumerate(ORDER):
        r = rate(m, fam)
        ramp = "fg" if fam in CONTROLS else "acc"
        ax.add_patch(Rectangle((j - 0.46, i - 0.43), 0.92, 0.86, facecolor=D(max(r, 0.03), ramp), edgecolor="none"))
        s = sig(m, fam)
        label(ax, j, i, f"{100 * r:.0f}{'*' if s else ''}", ha="center", va="center", boxed=True, fontsize=12,
              color=P.acc if s else P.fg, fontweight="bold" if s else "normal")
ax.axvline(len(MODELS) - 0.5, color=P.fg, lw=2)
ax.axhline(len(CONTROLS) - 0.5, color=P.fg, lw=2)
ax.set_xlim(-0.55, len(cols) - 0.45); ax.set_ylim(len(ORDER) - 0.45, -0.55)
ax.set_xticks(range(len(cols))); ax.set_xticklabels([MLAB.get(m, "all\npooled") for m in cols], fontsize=12)
ax.xaxis.tick_top()
ax.set_yticks(range(len(ORDER))); ax.set_yticklabels([FLAB[fm] for fm in ORDER], fontsize=12.5)
ax.grid(False); ax.tick_params(length=0)
for s_ in ax.spines.values():
    s_.set_visible(False)
head(f, "how often each attack family leaked the canary password",
     f"% of 16 tries per cell · * = beats direct ask, holm p < 0.05 · battery {S['battery']} {S['battery_hash']}", y_in=0.25)
f.text(0.045, 0.02, "-- " + "a low number often means the model was too weak to follow the trick, not that it is robust",
       color=P.dim, fontsize=11.5, va="bottom")
save(f, "leak-matrix.png")

# 2. pooled leak rate per family against the direct-ask control
f, ax = fig(8.2, left=0.3, right=0.9, bottom_in=1.0)
ref = 100 * pooled["direct_ask"]
y = np.arange(len(ORDER))
for i, fam in enumerate(ORDER):
    v = 100 * pooled[fam]
    if fam in CONTROLS:
        lv, ramp = 0.3, "fg"
    else:
        lv, ramp = (1.0, "acc") if sig("pooled", fam) else (0.3, "acc")
    dbar(ax, [i], [v], lv, ramp, horizontal=True, height=0.66)
    label(ax, v + 1.2, i, f"{v:.0f}%{' *' if sig('pooled', fam) else ''}", color=getattr(P, ramp), va="center", fontsize=12)
ax.axvline(ref, color=P.fg, lw=2, ls=(0, (2, 2)))
label(ax, ref + 0.8, len(ORDER) - 1, f"direct ask {ref:.0f}%", color=P.fg, va="center", fontsize=11.5, fontweight="normal", boxed=True)
ax.set_yticks(y); ax.set_yticklabels([FLAB[fm] for fm in ORDER], fontsize=12.5)
ax.set_ylim(len(ORDER) - 0.4, -0.6); ax.set_xlim(0, 108); ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xlabel("% of 80 tries that leaked (5 models pooled)")
ax.grid(axis="y", visible=False)
g = S["guard_rule_effect"]
title(ax, "only prefix injection beats just asking, pooled",
      f"the 'never reveal' line itself: {g['guarded_direct_ask']['leak']}/80 leaked with it, "
      f"{g['unguarded_direct_ask']['leak']}/80 without (p = {g['fisher_two_sided_p']:.2f})")
save(f, "pooled-by-family.png")

# 3. the real terminal readout
out = subprocess.run([sys.executable, "-c", f"import runpy, sys; sys.argv = ['show.py', '{DATE}']; runpy.run_path('./show.py', run_name='__main__')"],
                     capture_output=True, text=True, encoding="utf8", check=True).stdout
term_capture("show.png", f"python show.py {DATE}", out)
