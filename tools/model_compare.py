"""两模型 × 两臂的四域切片对照（同批对）。"""

# (域, 对数, qwen-plus 无防御 ASR/UA, qwen-plus 守卫 ASR/UA,
#            qwen3.5-27b 无防御 ASR/UA, qwen3.5-27b 守卫 ASR/UA)
ROWS = [
    ("banking", 30, (0.5333, 0.2667), (0.0000, 0.5333), (0.5000, 0.8000), (0.0000, 0.6667)),
    ("workspace", 30, (0.0000, 0.6667), (0.0333, 0.7000), (0.3000, 0.4667), (0.0667, 0.8333)),
    ("travel", 30, (0.5333, 0.3667), (0.0667, 0.7333), (0.4000, 0.6000), (0.0000, 1.0000)),
    ("slack", 25, (0.9600, 0.9200), (0.0400, 0.7600), (0.8800, 0.9600), (0.0400, 0.7600)),
]

print(f"{'域':10s} {'plus无防':>12s} {'plus守卫':>12s} {'效应':>7s} "
      f"{'3.5-27b无防':>13s} {'3.5-27b守卫':>13s} {'效应':>7s}")
for name, n, pu, pg, nu, ng in ROWS:
    eff_p = pg[1] - pu[1]
    eff_n = ng[1] - nu[1]
    print(f"{name:10s} {pu[0]*100:5.1f}/{pu[1]:5.3f} {pg[0]*100:5.1f}/{pg[1]:5.3f} "
          f"{eff_p:+7.3f} {nu[0]*100:6.1f}/{nu[1]:5.3f} {ng[0]*100:6.1f}/{ng[1]:5.3f} {eff_n:+7.3f}")

avg_p = sum(r[2][1] for r in ROWS) / 4
avg_pg = sum(r[3][1] for r in ROWS) / 4
avg_n = sum(r[4][1] for r in ROWS) / 4
avg_ng = sum(r[5][1] for r in ROWS) / 4
print()
print(f"等权平均  qwen-plus  无防御 {avg_p:.3f} → 守卫 {avg_pg:.3f}（{avg_pg-avg_p:+.3f}）")
print(f"等权平均  qwen3.5-27b 无防御 {avg_n:.3f} → 守卫 {avg_ng:.3f}（{avg_ng-avg_n:+.3f}）")
