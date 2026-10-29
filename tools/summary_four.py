"""汇总四域全域结果，给出按对合计与等权合计。"""

from pathlib import Path

ROWS = [
    # 域, 我们对数, 我们 ASR, 我们 UA, 报告对数, 报告 ASR, 报告 UA
    ("banking",   144, 0.0000, 0.6528, 144, 0.0000, 0.7153),
    ("workspace", 235, 0.0085, 0.5234, 240, 0.0000, 0.7708),
    ("slack",     105, 0.0952, 0.4000, 105, 0.0190, 0.6667),
    ("travel",    140, 0.0429, 0.2929, 140, 0.0143, 0.6429),
]

header = "{:10s} {:>5s} {:>9s} {:>8s} {:>9s} {:>8s} {:>7s}".format(
    "域", "对数", "我们ASR", "我们UA", "报告ASR", "报告UA", "UA差")
print(header)
print("-" * len(header))
n_sum = asr_sum = ua_sum = 0.0
rn_sum = rasr_sum = rua_sum = 0.0
for name, n, asr, ua, rn, rasr, rua in ROWS:
    print("{:10s} {:5d} {:8.2f}% {:8.3f} {:8.2f}% {:8.3f} {:+7.3f}".format(
        name, n, asr * 100, ua, rasr * 100, rua, ua - rua))
    n_sum += n
    asr_sum += asr * n
    ua_sum += ua * n
    rn_sum += rn
    rasr_sum += rasr * rn
    rua_sum += rua * rn

print()
print(f"按对合计  我们 {n_sum:.0f} 对：ASR {asr_sum / n_sum * 100:.2f}%  UA {ua_sum / n_sum:.4f}")
print(f"按对合计  报告 {rn_sum:.0f} 对：ASR {rasr_sum / rn_sum * 100:.2f}%  UA {rua_sum / rn_sum:.4f}")

w_asr = sum(r[2] for r in ROWS) / 4
w_ua = sum(r[3] for r in ROWS) / 4
r_asr = sum(r[5] for r in ROWS) / 4
r_ua = sum(r[6] for r in ROWS) / 4
print(f"等权      我们：ASR {w_asr * 100:.2f}%  UA {w_ua:.4f}")
print(f"等权      报告：ASR {r_asr * 100:.2f}%  UA {r_ua:.4f}")
