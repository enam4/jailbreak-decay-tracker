import json, sys, os, datetime
here = os.path.dirname(os.path.abspath(__file__))
date = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
S = json.load(open(f"{here}/results/{date}-summary.json"))
B, R0, G, Rd, Y, Cy, Dm = "\x1b[1m", "\x1b[0m", "\x1b[32m", "\x1b[31m", "\x1b[33m", "\x1b[36m", "\x1b[90m"
short = {"qwen2.5-0.5b": "qwen.5b", "qwen2.5-1.5b": "qwen1.5b", "llama3.2-1b": "llama1b", "smollm2-1.7b": "smol1.7b", "gemma2-2b": "gemma2b"}
fams = S["families"]
print(f"{B}jailbreak decay tracker {S['battery']}{R0} \u00b7 run {date} \u00b7 battery {S['battery_hash']} \u00b7 canary: planted password")
print(f"{Dm}leak rate per model x family, n={S['cells'][S['models'][0]]['direct_ask']['n']} each \u00b7 * = beats direct ask (holm p<0.05){R0}")
print()
print(f"{B}{'family':<26}" + "".join(f"{short[m]:>10}" for m in S["models"]) + f"{'all':>10}{R0}")
for f in fams:
    row = f"{f:<26}"
    for m in S["models"] + ["pooled"]:
        c = S["pooled"][f] if m == "pooled" else S["cells"][m][f]
        r = c["leak"] / max(1, c["n"])
        p = 1 if f == "direct_ask" else (S["pooled_tests"][f]["p_holm"] if m == "pooled" else S["tests"][m][f]["p_holm"])
        col = Rd if r >= 0.5 else (Y if r >= 0.2 else G)
        cell = f"{round(100 * r)}%" + ("*" if p < 0.05 else " ")
        row += f"{col}{cell:>10}{R0}"
    print(row if f != "direct_ask" else f"{Cy}{row}{R0}")
print()
print(f"{Dm}ceiling (no 'never reveal' rule): " + "  ".join(f"{short[m]} {S['ceiling'][m]['leak']}/{S['ceiling'][m]['n']}" for m in S["models"]) + R0)
