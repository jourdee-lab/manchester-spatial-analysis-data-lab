#!/usr/bin/env python3
"""
Dissertation Analysis: Spatial Analysis of Chinese Immigrant Integration
in Manchester (1981–2001)

Produces structured findings for all five research questions.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

CSV_PATH = "data/processed/indicators/temporal/manchester_harmonised_indicators_1981_1991_2001.csv"

df = pd.read_csv(CSV_PATH)
print(f"Loaded {len(df)} wards × {len(df.columns)} columns\n")

# ────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ────────────────────────────────────────────────────────────────────────────

def dissimilarity_index(chinese_col, total_col, data):
    """D = 0.5 * Σ |c_i/C - nc_i/NC|"""
    c = data[chinese_col].astype(float)
    t = data[total_col].astype(float)
    nc = t - c
    C = c.sum()
    NC = nc.sum()
    if C == 0 or NC == 0:
        return np.nan
    return 0.5 * np.abs(c / C - nc / NC).sum()

def top_n(data, col, n=5, name_col="ward_name_2001"):
    """Return top-n rows by col."""
    return data.nlargest(n, col)[[name_col, col]]

def weighted_mean(vals, weights):
    """Weighted mean ignoring NaN."""
    mask = vals.notna() & weights.notna()
    return (vals[mask] * weights[mask]).sum() / weights[mask].sum()

sep = "\n" + "=" * 80 + "\n"

# ────────────────────────────────────────────────────────────────────────────
# RQ1 — SPATIAL DISTRIBUTION & CONCENTRATION
# ────────────────────────────────────────────────────────────────────────────
print(sep)
print("RQ1 — SPATIAL DISTRIBUTION & CONCENTRATION (1981–2001)")
print(sep)

# Q1.1 — Top-5 wards each year
print("── Q1.1: Top-5 wards by Chinese concentration ──\n")

print("1981 (PCT_CHINESE_BORN_1981, birthplace proxy):")
t1981 = top_n(df, "PCT_CHINESE_BORN_1981")
for _, r in t1981.iterrows():
    print(f"  {r['ward_name_2001']:25s}  {r['PCT_CHINESE_BORN_1981']:.2f}%")

print("\n1991 (PCT_CHINESE_ETHNIC_1991, self-identified):")
t1991 = top_n(df, "PCT_CHINESE_ETHNIC_1991")
for _, r in t1991.iterrows():
    print(f"  {r['ward_name_2001']:25s}  {r['PCT_CHINESE_ETHNIC_1991']:.2f}%")

print("\n2001 (chinese_ethnic_pct, self-identified):")
t2001 = top_n(df, "chinese_ethnic_pct")
for _, r in t2001.iterrows():
    print(f"  {r['ward_name_2001']:25s}  {r['chinese_ethnic_pct']:.2f}%")

# Q1.2 — Index of Dissimilarity
print("\n── Q1.2: Index of Dissimilarity (D) ──\n")
D_1981 = dissimilarity_index("CHINESE_BORN_1981", "TOTAL_RES_1981", df)
D_1991 = dissimilarity_index("CHINESE_ETHNIC_1991", "TOTAL_RES_1991", df)
D_2001 = dissimilarity_index("chinese_ethnic_count", "total_pop", df)

print(f"  1981: D = {D_1981:.4f}")
print(f"  1991: D = {D_1991:.4f}")
print(f"  2001: D = {D_2001:.4f}")
trend = "dispersing" if D_2001 < D_1981 else "concentrating"
print(f"  Trend: Chinese community is {trend} over time.")

# Q1.3 — Sustained high-concentration wards
print("\n── Q1.3: Sustained high-concentration wards ──\n")
# Define "high" as top-10 (roughly top quartile of 33)
top10_81 = set(df.nlargest(10, "PCT_CHINESE_BORN_1981")["ward_name_2001"])
top10_91 = set(df.nlargest(10, "PCT_CHINESE_ETHNIC_1991")["ward_name_2001"])
top10_01 = set(df.nlargest(10, "chinese_ethnic_pct")["ward_name_2001"])

sustained = top10_81 & top10_91 & top10_01
ascending = (top10_01 - top10_81)
declining = (top10_81 - top10_01)

print("Sustained high concentration (top-10 in ALL three years):")
for w in sorted(sustained):
    vals = df[df["ward_name_2001"] == w][["PCT_CHINESE_BORN_1981", "PCT_CHINESE_ETHNIC_1991", "chinese_ethnic_pct"]].values[0]
    print(f"  {w:25s}  1981={vals[0]:.2f}%  1991={vals[1]:.2f}%  2001={vals[2]:.2f}%")

print("\nAscending (top-10 in 2001 but NOT in 1981):")
for w in sorted(ascending):
    vals = df[df["ward_name_2001"] == w][["PCT_CHINESE_BORN_1981", "PCT_CHINESE_ETHNIC_1991", "chinese_ethnic_pct"]].values[0]
    print(f"  {w:25s}  1981={vals[0]:.2f}%  1991={vals[1]:.2f}%  2001={vals[2]:.2f}%")

print("\nDeclining (top-10 in 1981 but NOT in 2001):")
for w in sorted(declining):
    vals = df[df["ward_name_2001"] == w][["PCT_CHINESE_BORN_1981", "PCT_CHINESE_ETHNIC_1991", "chinese_ethnic_pct"]].values[0]
    print(f"  {w:25s}  1981={vals[0]:.2f}%  1991={vals[1]:.2f}%  2001={vals[2]:.2f}%")

# ────────────────────────────────────────────────────────────────────────────
# RQ2 — HOUSING INTEGRATION
# ────────────────────────────────────────────────────────────────────────────
print(sep)
print("RQ2 — SOCIOECONOMIC INTEGRATION: HOUSING")
print(sep)

# Q2.4 — Owner-occupation comparison
print("── Q2.4: Owner-occupation rates ──\n")

# Manchester ward-level means (population-weighted)
manc_oo_1981 = weighted_mean(df["PCT_OWNER_OCC_1981"], df["TOTAL_HH_1981"])
print(f"  1981 Manchester mean owner-occ rate: {manc_oo_1981:.1f}%")

# 1991 Chinese owner-occ: only available for wards with Chinese HHs
chinese_hh_91 = df[df["CHINESE_HOUSEHOLDS_1991"] > 0].copy()
if len(chinese_hh_91) > 0:
    chinese_oo_91 = chinese_hh_91["CHINESE_OWNER_OCC_1991"].sum() / chinese_hh_91["CHINESE_HOUSEHOLDS_1991"].sum() * 100
    print(f"  1991 Chinese owner-occ rate (aggregated): {chinese_oo_91:.1f}%")

# General 1991 ward owner-occ not directly available — note this
# Use 2001 for comparison
manc_oo_2001 = weighted_mean(df["owner_occ_rate"], df["total_pop"])
print(f"  2001 Manchester mean owner-occ rate: {manc_oo_2001:.1f}%")

# Owner-occ in high-Chinese vs low-Chinese wards in 2001
median_ch_2001 = df["chinese_ethnic_pct"].median()
hi_ch_2001 = df[df["chinese_ethnic_pct"] >= median_ch_2001]
lo_ch_2001 = df[df["chinese_ethnic_pct"] < median_ch_2001]
oo_hi = weighted_mean(hi_ch_2001["owner_occ_rate"], hi_ch_2001["total_pop"])
oo_lo = weighted_mean(lo_ch_2001["owner_occ_rate"], lo_ch_2001["total_pop"])
print(f"  2001 Owner-occ — high-Chinese wards: {oo_hi:.1f}%, low-Chinese: {oo_lo:.1f}%")

# Top-5 Chinese wards owner-occ trajectory
print("\n  Owner-occ in top-5 Chinese wards (2001 ranking):")
top5_2001 = df.nlargest(5, "chinese_ethnic_pct")
for _, r in top5_2001.iterrows():
    print(f"    {r['ward_name_2001']:25s}  1981={r['PCT_OWNER_OCC_1981']:.1f}%  2001={r['owner_occ_rate']:.1f}%")

# Q2.5 — Housing quality: overcrowding
print("\n── Q2.5: Overcrowding comparison ──\n")

# 1981: Compare overcrowding in high-Chinese vs low-Chinese wards
median_ch_81 = df["PCT_CHINESE_BORN_1981"].median()
hi_81 = df[df["PCT_CHINESE_BORN_1981"] >= median_ch_81]
lo_81 = df[df["PCT_CHINESE_BORN_1981"] < median_ch_81]
oc_hi_81 = weighted_mean(hi_81["PCT_OVERCROWD_GT1P5_1981"], hi_81["TOTAL_HH_1981"])
oc_lo_81 = weighted_mean(lo_81["PCT_OVERCROWD_GT1P5_1981"], lo_81["TOTAL_HH_1981"])
print(f"  1981 severe overcrowding (>1.5 ppm):")
print(f"    High-Chinese wards: {oc_hi_81:.2f}%   Low-Chinese wards: {oc_lo_81:.2f}%")

# 1991: Chinese-specific overcrowding vs ward average
# Ward-level general overcrowding is not directly in 1991 data, but Chinese-specific is
chinese_hh_oc_91 = df[df["CHINESE_HOUSEHOLDS_1991"] > 5].copy()  # filter small n
if len(chinese_hh_oc_91) > 0:
    ch_oc_91_agg = chinese_hh_oc_91["CHINESE_OVERCROWD_GT1P5_1991"].sum() / chinese_hh_oc_91["CHINESE_HOUSEHOLDS_1991"].sum() * 100
    print(f"\n  1991 Chinese-headed HH severe overcrowding (aggregated): {ch_oc_91_agg:.2f}%")
    print(f"  1991 Top wards by PCT_CHINESE_OVERCROWD_1991 (where Chinese HH > 5):")
    for _, r in chinese_hh_oc_91.nlargest(5, "PCT_CHINESE_OVERCROWD_1991").iterrows():
        print(f"    {r['ward_name_2001']:25s}  {r['PCT_CHINESE_OVERCROWD_1991']:.1f}% (n={int(r['CHINESE_HOUSEHOLDS_1991'])} HH)")

# 2001: overcrowding in wards with above-median Chinese pct
hi_ch_oc_2001 = weighted_mean(hi_ch_2001["overcrowd_severe_rate"], hi_ch_2001["total_pop"])
lo_ch_oc_2001 = weighted_mean(lo_ch_2001["overcrowd_severe_rate"], lo_ch_2001["total_pop"])
manc_oc_2001 = weighted_mean(df["overcrowd_severe_rate"], df["total_pop"])
print(f"\n  2001 severe overcrowding:")
print(f"    High-Chinese wards: {hi_ch_oc_2001:.2f}%   Low-Chinese: {lo_ch_oc_2001:.2f}%   Manchester: {manc_oc_2001:.2f}%")

# Q2.6 — Basic amenities
print("\n── Q2.6: Housing quality — basic amenities ──\n")

# 1981 — top Chinese wards
print("  1981 PCT_NO_BATH_OR_WC in top-5 Chinese wards:")
for _, r in df.nlargest(5, "PCT_CHINESE_BORN_1981").iterrows():
    print(f"    {r['ward_name_2001']:25s}  {r['PCT_NO_BATH_OR_WC_1981']:.2f}%  (Chinese: {r['PCT_CHINESE_BORN_1981']:.2f}%)")
manc_no_bath_81 = weighted_mean(df["PCT_NO_BATH_OR_WC_1981"], df["TOTAL_HH_1981"])
print(f"  Manchester mean: {manc_no_bath_81:.2f}%")

# 2001
print("\n  2001 no_bath_wc_rate in top-5 Chinese wards:")
for _, r in df.nlargest(5, "chinese_ethnic_pct").iterrows():
    print(f"    {r['ward_name_2001']:25s}  {r['no_bath_wc_rate']:.2f}%  (Chinese: {r['chinese_ethnic_pct']:.2f}%)")
manc_no_bath_2001 = weighted_mean(df["no_bath_wc_rate"], df["total_pop"])
print(f"  Manchester mean: {manc_no_bath_2001:.2f}%")


# ────────────────────────────────────────────────────────────────────────────
# RQ3 — EMPLOYMENT & ECONOMIC POSITION
# ────────────────────────────────────────────────────────────────────────────
print(sep)
print("RQ3 — SOCIOECONOMIC INTEGRATION: EMPLOYMENT & ECONOMIC POSITION")
print(sep)

# Q3.7 — 1991 Chinese employment vs general
print("── Q3.7: 1991 Chinese vs general employment ──\n")
# Aggregate Chinese employment across all wards
ch_emp_91 = df["CHINESE_ECON_ACTIVE_1991"].sum() - df["CHINESE_UNEMPLOYED_1991"].sum()
ch_ea_91 = df["CHINESE_ECON_ACTIVE_1991"].sum()
ch_16plus_91 = df["CHINESE_16PLUS_1991"].sum()
ch_total_91 = df["CHINESE_ETHNIC_1991"].sum()

ch_emp_rate_91_agg = ch_emp_91 / ch_16plus_91 * 100 if ch_16plus_91 > 0 else np.nan
ch_unemp_rate_91_agg = df["CHINESE_UNEMPLOYED_1991"].sum() / ch_ea_91 * 100 if ch_ea_91 > 0 else np.nan
ch_ea_rate_91_agg = ch_ea_91 / ch_16plus_91 * 100 if ch_16plus_91 > 0 else np.nan

print(f"  Chinese (Manchester-wide, 1991):")
print(f"    Total Chinese: {int(ch_total_91)}")
print(f"    Chinese 16+: {int(ch_16plus_91)}")
print(f"    Economic activity rate: {ch_ea_rate_91_agg:.1f}%")
print(f"    Employment rate (employed/16+): {ch_emp_rate_91_agg:.1f}%")
print(f"    Unemployment rate (ILO): {ch_unemp_rate_91_agg:.1f}%")

# Ward-level comparison where Chinese n > 20
sig_wards = df[df["CHINESE_ETHNIC_1991"] >= 20].copy()
print(f"\n  Wards with Chinese n ≥ 20 ({len(sig_wards)} wards):")
print(f"  {'Ward':<25s} {'Ch.EmpRate':>10s} {'Ch.UnempRate':>12s} {'Ch.16+':>8s}")
for _, r in sig_wards.sort_values("PCT_CHINESE_ETHNIC_1991", ascending=False).iterrows():
    print(f"  {r['ward_name_2001']:<25s} {r['CHINESE_EMP_RATE_1991']:>9.1f}% {r['CHINESE_UNEMP_RATE_1991']:>11.1f}% {int(r['CHINESE_16PLUS_1991']):>8d}")

# Q3.8 — 2001 self-employment in high-Chinese wards
print("\n── Q3.8: 2001 Self-employment in high-Chinese wards ──\n")
manc_se_2001 = weighted_mean(df["self_employment_rate"], df["pop_16_74"])
print(f"  Manchester mean self-employment rate: {manc_se_2001:.1f}%")
print(f"\n  Top-10 wards by chinese_ethnic_pct (2001):")
for _, r in df.nlargest(10, "chinese_ethnic_pct").iterrows():
    flag = " ▲" if r["self_employment_rate"] > manc_se_2001 else ""
    print(f"    {r['ward_name_2001']:25s}  Chinese={r['chinese_ethnic_pct']:.2f}%  SelfEmp={r['self_employment_rate']:.1f}%{flag}")

# Correlation
corr_se_ch = df[["chinese_ethnic_pct", "self_employment_rate"]].corr().iloc[0, 1]
print(f"\n  Pearson r(chinese_ethnic_pct, self_employment_rate) = {corr_se_ch:.3f}")

# Q3.9 — 1981 employment by Chinese quintile
print("\n── Q3.9: 1981 Employment rate by Chinese-born quintile ──\n")
df["ch_quintile_81"] = pd.qcut(df["PCT_CHINESE_BORN_1981"], 5, labels=["Q1 (lowest)", "Q2", "Q3", "Q4", "Q5 (highest)"])
q_summary = df.groupby("ch_quintile_81", observed=False).apply(
    lambda g: pd.Series({
        "n_wards": len(g),
        "mean_emp_rate": weighted_mean(g["EMP_RATE_1981"], g["TOTAL_RES_1981"]),
        "mean_pct_chinese": g["PCT_CHINESE_BORN_1981"].mean()
    })
).reset_index()
for _, r in q_summary.iterrows():
    print(f"  {r['ch_quintile_81']:15s}  n={int(r['n_wards'])}  Mean Chinese={r['mean_pct_chinese']:.2f}%  Emp rate={r['mean_emp_rate']:.1f}%")

corr_emp_ch_81 = df[["PCT_CHINESE_BORN_1981", "EMP_RATE_1981"]].corr().iloc[0, 1]
print(f"\n  Pearson r(PCT_CHINESE_BORN_1981, EMP_RATE_1981) = {corr_emp_ch_81:.3f}")


# ────────────────────────────────────────────────────────────────────────────
# RQ4 — AGE STRUCTURE & LONG-TERM SETTLEMENT (1991)
# ────────────────────────────────────────────────────────────────────────────
print(sep)
print("RQ4 — AGE STRUCTURE AND LONG-TERM SETTLEMENT (1991)")
print(sep)

# Q4.10 — Young Chinese residents
print("── Q4.10: Wards with high proportions of young Chinese residents ──\n")

sig_91 = df[df["CHINESE_ETHNIC_1991"] >= 20].copy()
sig_91["pct_0_4"] = sig_91["CHINESE_AGE_0_4_1991"] / sig_91["CHINESE_ETHNIC_1991"] * 100
sig_91["pct_5_15"] = sig_91["CHINESE_AGE_5_15_1991"] / sig_91["CHINESE_ETHNIC_1991"] * 100
sig_91["pct_16_29"] = sig_91["CHINESE_AGE_16_29_1991"] / sig_91["CHINESE_ETHNIC_1991"] * 100
sig_91["pct_under_16"] = sig_91["pct_0_4"] + sig_91["pct_5_15"]
sig_91["pct_30_pension"] = sig_91["CHINESE_AGE_30_PENSION_1991"] / sig_91["CHINESE_ETHNIC_1991"] * 100
sig_91["pct_pensionable"] = sig_91["CHINESE_PENSIONABLE_1991"] / sig_91["CHINESE_ETHNIC_1991"] * 100

print(f"  {'Ward':<25s} {'Total':>6s} {'<16':>6s} {'16-29':>6s} {'30-Pen':>7s} {'Pen+':>6s}")
for _, r in sig_91.sort_values("CHINESE_ETHNIC_1991", ascending=False).iterrows():
    print(f"  {r['ward_name_2001']:<25s} {int(r['CHINESE_ETHNIC_1991']):>6d} "
          f"{r['pct_under_16']:>5.1f}% {r['pct_16_29']:>5.1f}% "
          f"{r['pct_30_pension']:>6.1f}% {r['pct_pensionable']:>5.1f}%")

# Aggregate age structure
total_ch_91 = df["CHINESE_ETHNIC_1991"].sum()
print(f"\n  Manchester-wide Chinese age structure (n={int(total_ch_91)}):")
age_cols = ["CHINESE_AGE_0_4_1991", "CHINESE_AGE_5_15_1991", "CHINESE_AGE_16_29_1991",
            "CHINESE_AGE_30_PENSION_1991", "CHINESE_PENSIONABLE_1991"]
age_labels = ["0–4", "5–15", "16–29", "30–pension", "Pensionable+"]
for c, l in zip(age_cols, age_labels):
    n = df[c].sum()
    print(f"    {l:15s}  {int(n):>5d}  ({n/total_ch_91*100:.1f}%)")

# Q4.11 — Pensionable-age Chinese
print("\n── Q4.11: Wards with pensionable-age Chinese residents ──\n")
pen_wards = df[df["CHINESE_PENSIONABLE_1991"] > 0].copy()
pen_wards = pen_wards.sort_values("CHINESE_PENSIONABLE_1991", ascending=False)
print(f"  {len(pen_wards)} wards have at least one pensionable-age Chinese resident.")
for _, r in pen_wards.head(10).iterrows():
    print(f"    {r['ward_name_2001']:25s}  Pensionable={int(r['CHINESE_PENSIONABLE_1991'])}  "
          f"Total Chinese={int(r['CHINESE_ETHNIC_1991'])}  "
          f"({r['CHINESE_PENSIONABLE_1991']/max(r['CHINESE_ETHNIC_1991'],1)*100:.1f}%)")


# ────────────────────────────────────────────────────────────────────────────
# RQ5 — TEMPORAL CHANGE SUMMARY
# ────────────────────────────────────────────────────────────────────────────
print(sep)
print("RQ5 — TEMPORAL CHANGE SUMMARY")
print(sep)

# Q5.12 — Change table
print("── Q5.12: Ward-level change table ──\n")

ct = df[["ward_name_2001"]].copy()
ct["ch_1981"] = df["PCT_CHINESE_BORN_1981"]
ct["ch_1991"] = df["PCT_CHINESE_ETHNIC_1991"]
ct["ch_2001"] = df["chinese_ethnic_pct"]
ct["delta_ch_81_01"] = ct["ch_2001"] - ct["ch_1981"]

ct["oo_1981"] = df["PCT_OWNER_OCC_1981"]
ct["oo_2001"] = df["owner_occ_rate"]
ct["delta_oo_81_01"] = ct["oo_2001"] - ct["oo_1981"]

ct["oc_1981"] = df["PCT_OVERCROWD_GT1P5_1981"]
ct["oc_2001"] = df["overcrowd_severe_rate"]
ct["delta_oc_81_01"] = ct["oc_2001"] - ct["oc_1981"]

print(f"  {'Ward':<25s} {'Δ Chinese%':>10s} {'Δ OwnerOcc%':>12s} {'Δ Overcrowd%':>13s}")
for _, r in ct.sort_values("delta_ch_81_01", ascending=False).iterrows():
    print(f"  {r['ward_name_2001']:<25s} {r['delta_ch_81_01']:>+9.2f}pp {r['delta_oo_81_01']:>+11.1f}pp {r['delta_oc_81_01']:>+12.2f}pp")

# Summary statistics
print("\n  Summary:")
print(f"    Mean Δ Chinese concentration: {ct['delta_ch_81_01'].mean():+.2f}pp")
print(f"    Mean Δ Owner-occupation: {ct['delta_oo_81_01'].mean():+.1f}pp")
print(f"    Mean Δ Overcrowding (severe): {ct['delta_oc_81_01'].mean():+.2f}pp")

# Manchester-wide aggregates
ch_total_81 = df["CHINESE_BORN_1981"].sum()
pop_81 = df["TOTAL_RES_1981"].sum()
ch_total_01 = df["chinese_ethnic_count"].sum()
pop_01 = df["total_pop"].sum()
print(f"\n  Manchester-wide Chinese population:")
print(f"    1981: {ch_total_81:.0f} Far East-born / {pop_81:.0f} total ({ch_total_81/pop_81*100:.2f}%)")
print(f"    1991: {ch_total_91:.0f} Chinese ethnic / {df['TOTAL_RES_1991'].sum():.0f} total ({ch_total_91/df['TOTAL_RES_1991'].sum()*100:.2f}%)")
print(f"    2001: {ch_total_01:.0f} Chinese ethnic / {pop_01:.0f} total ({ch_total_01/pop_01*100:.2f}%)")

# Convergence analysis
# Compare top-5 Chinese wards to Manchester mean on key indicators over time
print("\n  Convergence/Divergence Analysis (top-5 Chinese wards vs Manchester mean):")
top5 = df.nlargest(5, "chinese_ethnic_pct")["ward_name_2001"].values
top5_mask = df["ward_name_2001"].isin(top5)

indicators = [
    ("Owner-occ", "PCT_OWNER_OCC_1981", "owner_occ_rate", "TOTAL_HH_1981", "total_pop"),
    ("No-car", "PCT_NO_CAR_1981", "no_car_rate", "TOTAL_HH_1981", "total_pop"),
]
for label, col81, col01, w81, w01 in indicators:
    manc_81 = weighted_mean(df[col81], df[w81])
    manc_01 = weighted_mean(df[col01], df[w01])
    top_81 = weighted_mean(df.loc[top5_mask, col81], df.loc[top5_mask, w81])
    top_01 = weighted_mean(df.loc[top5_mask, col01], df.loc[top5_mask, w01])
    gap_81 = top_81 - manc_81
    gap_01 = top_01 - manc_01
    direction = "CONVERGING" if abs(gap_01) < abs(gap_81) else "DIVERGING"
    print(f"    {label}: Top5 gap 1981={gap_81:+.1f}pp → 2001={gap_01:+.1f}pp  [{direction}]")

# ────────────────────────────────────────────────────────────────────────────
# INTERPOLATION QUALITY CHECK
# ────────────────────────────────────────────────────────────────────────────
print(sep)
print("METHODOLOGICAL NOTE: Interpolation Quality")
print(sep)

flagged = df[df["interp_uncertainty_flag"] == "low"]  # might be string
if len(flagged) == 0:
    flagged = df[df["interp_uncertainty_flag"] == 1]
if len(flagged) == 0:
    flagged = df[df["interp_uncertainty_flag"] == "1"]

low_cov = df[df["interp_coverage"].astype(float) < 0.95]
print(f"  Wards with interp_coverage < 0.95: {len(low_cov)}")
for _, r in low_cov.iterrows():
    print(f"    {r['ward_name_2001']:25s}  coverage={r['interp_coverage']:.3f}  n_eds={r['n_source_eds']}")

print(f"\n  Wards with uncertainty flag:")
flag_vals = df["interp_uncertainty_flag"].unique()
print(f"    Unique flag values: {flag_vals}")
for fv in flag_vals:
    n = len(df[df["interp_uncertainty_flag"] == fv])
    print(f"    '{fv}': {n} wards")

# Small-n flag for 1991 Chinese rates
small_n_91 = df[df["CHINESE_ETHNIC_1991"] < 20]
print(f"\n  Wards with Chinese n < 20 in 1991 (unstable rates): {len(small_n_91)}")
for _, r in small_n_91.iterrows():
    print(f"    {r['ward_name_2001']:25s}  n={int(r['CHINESE_ETHNIC_1991'])}")

print("\n\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
