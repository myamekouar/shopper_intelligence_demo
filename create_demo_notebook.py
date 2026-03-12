#!/usr/bin/env python3
"""
Run once to generate GreenBasket_Demo.ipynb

    python create_demo_notebook.py

Then open GreenBasket_Demo.ipynb in Jupyter and run all cells.
"""
import json

OUT = "GreenBasket_Demo.ipynb"


def md_cell(src):
    return {"cell_type": "markdown",
            "id": str(abs(hash(src[:40])) % 999999),
            "metadata": {}, "source": src}


def code_cell(src):
    return {"cell_type": "code", "execution_count": None,
            "id": str(abs(hash(src[:40])) % 999999),
            "metadata": {}, "outputs": [], "source": src}


# ---------------------------------------------------------------------------
# INTRO (markdown)
# ---------------------------------------------------------------------------
INTRO = (
    "# 🛒 GreenBasket · Shopper Intelligence Demo\n"
    "## Omnichannel Activation & Gamification Platform\n"
    "### Powered by Catalina Shopper Analytics\n\n"
    "---\n\n"
    "This interactive demo shows how **transactional purchase data**, "
    "**product enrichment data** (Nutri-Score, Eco-Score), "
    "and **omnichannel activation logic** can be combined to:\n\n"
    "- 🔍 **Identify** individual shopper profiles and behavioural segments\n"
    "- 🌿 **Score** shoppers on health and sustainability dimensions\n"
    "- 📣 **Recommend** personalised, channel-optimised activation campaigns\n"
    "- 🎮 **Gamify** the journey toward healthier grocery choices\n\n"
    "---\n\n"
    "### ▶ How to use\n"
    "1. **Run all cells** — `Cell → Run All`\n"
    "2. Use the **dropdown** to select any of the 15 shopper profiles\n"
    "3. Explore their personalised dashboard, activation plan, and rewards journey\n\n"
    "---\n"
    "*All shopper data is synthetic and produced for demonstration purposes only.*"
)

# ---------------------------------------------------------------------------
# SETUP cell
# Note: triple-single-quoted outer string so the inner f-triple-double-quote
# strings in render() do not collide with the outer delimiter.
# ---------------------------------------------------------------------------
SETUP = '''import os, base64, warnings
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
from IPython.display import display, HTML, clear_output
import ipywidgets as widgets

warnings.filterwarnings("ignore")
matplotlib.rcParams["figure.dpi"] = 110

# ── Load data ────────────────────────────────────────────────────────────────
df = pd.read_csv("demo_shopper_profiles.csv")

# ── Palette (Carrefour-inspired) ─────────────────────────────────────────────
C_BLUE  = "#004A97"
C_RED   = "#CC0000"
C_GREEN = "#2E7D32"
C_AMBER = "#F57F17"

PERSONA_BG = {
    "Health Pioneer":   ("#E8F5E9", "#2E7D32"),
    "Eco Explorer":     ("#E0F2F1", "#00695C"),
    "Family Organiser": ("#E3F2FD", "#1565C0"),
    "Smart Saver":      ("#FFF8E1", "#E65100"),
    "Routine Loyalist": ("#F3E5F5", "#6A1B9A"),
    "Weekend Foodie":   ("#FFF3E0", "#BF360C"),
    "Budget-Conscious": ("#FFF8E1", "#BF360C"),
    "Eco-Progressive":  ("#E8F5E9", "#2E7D32"),
}
SEG_ICON = {"Premium Loyal": "💎", "Regular Engaged": "⭐", "Occasional": "🌱"}


def _b64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return b64


def radar(row):
    cats = ["Health", "Sustain-\\nability", "Frequency",
            "Engage-\\nment", "E-com", "Loyalty"]
    tmap = {"Bronze": .25, "Silver": .5, "Gold": .75, "Platinum": 1.}
    vals = [row["health_score"] / 100,
            row["sustainability_score"] / 100,
            min(row["visits_per_month"] / 12, 1.),
            min(row["streak_weeks"] / 8, 1.),
            min(row["pct_ecommerce"] / 50, 1.),
            tmap.get(row["loyalty_tier"], .5)]
    N   = len(cats)
    ang = [n / N * 2 * np.pi for n in range(N)] + [0]
    vp  = vals + vals[:1]
    fig, ax = plt.subplots(figsize=(3.4, 3.4), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#F6F9FF")
    ax.plot(ang, vp, "o-", lw=2.5, color=C_BLUE)
    ax.fill(ang, vp, alpha=.20, color=C_BLUE)
    ax.set_xticks(ang[:-1])
    ax.set_xticklabels(cats, fontsize=8, color="#444", fontweight="600")
    ax.set_ylim(0, 1)
    ax.set_yticks([.25, .5, .75, 1.])
    ax.set_yticklabels(["", "", "", ""])
    ax.grid(color="#C8D8F0", linestyle="--", lw=.8, alpha=.7)
    ax.spines["polar"].set_color("#DDDDDD")
    plt.tight_layout()
    return _b64(fig)


def scol(v):
    return C_GREEN if v >= 70 else (C_AMBER if v >= 50 else C_RED)


def bcol(s):
    return {"A": "#038141", "B": "#85BB2F", "C": "#FFCC00",
            "D": "#EE8100", "E": "#E63312"}.get(str(s), "#AAAAAA")


def tcol(t):
    return {"Bronze": "#B87333", "Silver": "#757575",
            "Gold": "#F9A825", "Platinum": "#455A64"}.get(t, "#757575")


def cicon(ch):
    return {
        "App Push Notification": "📱", "Email Campaign": "📧",
        "In-Store Coupon": "🏪",       "E-commerce Banner": "🛒",
        "Weekend Email": "📧",          "In-Store Flyer": "📄",
        "Email + App Push": "📱📧",     "App Challenge": "🏆",
    }.get(ch, "📣")


def sbar(label, val, col):
    return (
        f\'<div style="margin:8px 0">\'
        f\'<div style="display:flex;justify-content:space-between;margin-bottom:3px">\'
        f\'<span style="font-size:13px;color:#555;font-weight:500">{label}</span>\'
        f\'<span style="font-size:13px;font-weight:700;color:{col}">{val}/100</span>\'
        f\'</div><div style="background:#E8EAED;border-radius:6px;height:10px">\'
        f\'<div style="width:{val}%;background:{col};border-radius:6px;height:10px">\'
        f\'</div></div></div>\'
    )


def render(sid):
    r   = df[df["shopper_id"] == sid].iloc[0]
    rd  = radar(r)
    pbg, pcol = PERSONA_BG.get(r["persona"], ("#E8F1FB", C_BLUE))
    tc  = tcol(r["loyalty_tier"])
    hc  = scol(r["health_score"])
    sc  = scol(r["sustainability_score"])
    nc  = bcol(r["nutri_score"])
    ec  = bcol(r["eco_score"])
    chi = cicon(r["recommended_channel"])
    si  = SEG_ICON.get(r["segment"], "📊")
    prog = int(r["points_balance"] / (r["points_balance"] + r["points_to_next_reward"]) * 100)
    blist = [str(r.get(b, "")) for b in ["badge_health", "badge_eco", "badge_loyalty"]]
    pills = "".join(
        f\'<span style="background:#E8F1FB;color:#004A97;padding:4px 11px;\'
        f\'border-radius:20px;font-size:12px;font-weight:600;margin:2px 3px;\'
        f\'display:inline-block;border:1px solid #B3D1F0">\'
        f\'&#127893; {b}</span>\'
        for b in blist if b not in ("", "nan")
    ) or \'<span style="color:#aaa;font-size:12px">No badges yet — start your journey!</span>\'
    sb_h = sbar("Health Score",        r["health_score"],        hc)
    sb_s = sbar("Sustainability Score", r["sustainability_score"], sc)

    return f"""
<style>
.gb{{font-family:"Segoe UI",Arial,sans-serif;max-width:960px;margin:0 auto;
     background:#EEF2F7;padding:18px;border-radius:16px}}
.gb-card{{background:#fff;border-radius:10px;padding:18px 20px;
          box-shadow:0 2px 8px rgba(0,0,0,.07)}}
.gb-kpi{{text-align:center;border-radius:10px;padding:14px;background:#fff;
         box-shadow:0 2px 8px rgba(0,0,0,.07)}}
.gb-lbl{{font-size:10px;color:#999;text-transform:uppercase;
         letter-spacing:1px;margin-bottom:6px}}
.gb-val{{font-size:22px;font-weight:900}}
.gb-sec{{font-size:12px;font-weight:700;text-transform:uppercase;
         letter-spacing:1.2px;margin-bottom:14px}}
.gb-imp{{text-align:center;background:#F1F8F2;border-radius:10px;
         padding:14px;border-bottom:3px solid}}
</style>
<div class="gb">

<!-- HEADER -->
<div style="background:linear-gradient(135deg,#004A97 0%,#0066CC 100%);
            border-radius:12px;padding:22px 26px;margin-bottom:14px;
            display:flex;align-items:center;justify-content:space-between">
  <div>
    <div style="font-size:10px;color:#A8C8F0;text-transform:uppercase;
                letter-spacing:2px;margin-bottom:5px">
      Catalina · GreenBasket Intelligence Demo
    </div>
    <div style="font-size:26px;font-weight:800;color:#fff;margin-bottom:8px">
      {r["name"]}
    </div>
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <span style="background:{pbg};color:{pcol};padding:5px 14px;
                   border-radius:20px;font-size:13px;font-weight:700">
        ✦ {r["persona"]}
      </span>
      <span style="background:rgba(255,255,255,.15);color:#fff;
                   padding:5px 14px;border-radius:20px;font-size:12px">
        {si} {r["segment"]}
      </span>
      <span style="background:{tc};color:#fff;padding:5px 14px;
                   border-radius:20px;font-size:12px;font-weight:700">
        ⭐ {r["loyalty_tier"]}
      </span>
    </div>
  </div>
  <div style="text-align:right;color:#fff">
    <div style="font-size:11px;color:#A8C8F0">Age Group</div>
    <div style="font-size:20px;font-weight:700">{r["age_group"]}</div>
  </div>
</div>

<!-- KPI ROW -->
<div style="display:grid;grid-template-columns:repeat(4,1fr);
            gap:10px;margin-bottom:14px">
  <div class="gb-kpi" style="border-top:4px solid #004A97">
    <div class="gb-lbl">Annual Spend</div>
    <div class="gb-val" style="color:#004A97">€{r["total_spend"]:,.0f}</div>
  </div>
  <div class="gb-kpi" style="border-top:4px solid #CC0000">
    <div class="gb-lbl">Avg Basket</div>
    <div class="gb-val" style="color:#CC0000">€{r["avg_basket_value"]:,.1f}</div>
  </div>
  <div class="gb-kpi" style="border-top:4px solid #2E7D32">
    <div class="gb-lbl">Visits / Month</div>
    <div class="gb-val" style="color:#2E7D32">{r["visits_per_month"]}</div>
  </div>
  <div class="gb-kpi" style="border-top:4px solid #F57F17">
    <div class="gb-lbl">Points Balance</div>
    <div class="gb-val" style="color:#F57F17">{r["points_balance"]:,} pts</div>
  </div>
</div>

<!-- PROFILE + HEALTH -->
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px">

  <div class="gb-card">
    <div class="gb-sec" style="color:#004A97">📈 Behavioural Profile</div>
    <div style="text-align:center">
      <img src="data:image/png;base64,{rd}" style="width:224px;height:224px"/>
    </div>
    <div style="font-size:11px;color:#aaa;text-align:center;margin-top:4px">
      Multi-dimensional shopper behaviour analysis
    </div>
  </div>

  <div class="gb-card">
    <div class="gb-sec" style="color:#2E7D32">🌿 Health &amp; Sustainability</div>
    <div style="display:flex;gap:10px;align-items:flex-start;margin-bottom:14px">
      <div style="background:{nc};color:#fff;width:52px;height:52px;
                  border-radius:10px;display:flex;flex-direction:column;
                  align-items:center;justify-content:center;
                  font-size:22px;font-weight:900;flex-shrink:0">
        {r["nutri_score"]}<span style="font-size:8px;font-weight:400">NUTRI</span>
      </div>
      <div style="background:{ec};color:#fff;width:52px;height:52px;
                  border-radius:10px;display:flex;flex-direction:column;
                  align-items:center;justify-content:center;
                  font-size:22px;font-weight:900;flex-shrink:0">
        {r["eco_score"]}<span style="font-size:8px;font-weight:400">ECO</span>
      </div>
      <div>
        <div style="font-size:12px;color:#666">Avg basket quality scores</div>
        <div style="font-size:12px;color:#666">Top category:
          <strong style="color:#333">{r["top_category"]}</strong></div>
        <div style="font-size:12px;color:#666">E-commerce share:
          <strong style="color:#333">{r["pct_ecommerce"]}%</strong></div>
      </div>
    </div>
    {sb_h}
    {sb_s}
    <div style="margin-top:12px;background:#F8F9FA;border-radius:8px;
                padding:10px;font-size:12px;color:#555">
      🔥 <strong>{r["streak_weeks"]}-week</strong> healthy basket streak
    </div>
  </div>

</div>

<!-- REWARDS + ACTIVATION -->
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px">

  <div class="gb-card">
    <div class="gb-sec" style="color:#004A97">🎮 Rewards Journey</div>
    <div style="display:flex;justify-content:space-between;margin-bottom:6px">
      <span style="font-size:13px;color:#555;font-weight:500">
        Progress to next reward
      </span>
      <span style="font-size:14px;font-weight:800;color:#004A97">{prog}%</span>
    </div>
    <div style="background:#E8EAED;border-radius:8px;height:13px;
                overflow:hidden;margin-bottom:4px">
      <div style="width:{prog}%;height:13px;border-radius:8px;
                  background:linear-gradient(90deg,#004A97,#0066CC)"></div>
    </div>
    <div style="display:flex;justify-content:space-between;
                font-size:11px;color:#999;margin-bottom:14px">
      <span>{r["points_balance"]:,} pts accumulated</span>
      <span>{r["points_to_next_reward"]:,} pts to next reward</span>
    </div>
    <div style="font-size:12px;color:#555;font-weight:600;margin-bottom:6px">
      Earned Badges:
    </div>
    <div style="margin-bottom:12px">{pills}</div>
    <div style="background:linear-gradient(135deg,#E8F1FB,#F0F7FF);
                border:1px solid #B3D1F0;border-radius:8px;padding:12px">
      <div style="font-size:12px;color:#004A97;font-weight:700;margin-bottom:4px">
        🎯 Active Mission
      </div>
      <div style="font-size:13px;color:#333">{r["recommended_offer_text"]}</div>
    </div>
  </div>

  <div class="gb-card">
    <div class="gb-sec" style="color:#CC0000">📣 Omnichannel Activation</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">
      <div style="background:#FFF5F5;border-radius:8px;padding:10px;
                  border-left:3px solid #CC0000">
        <div style="font-size:10px;color:#999;text-transform:uppercase;
                    letter-spacing:1px">Channel</div>
        <div style="font-size:14px;font-weight:700;color:#CC0000;margin-top:3px">
          {chi} {r["recommended_channel"]}
        </div>
      </div>
      <div style="background:#FFF5F5;border-radius:8px;padding:10px;
                  border-left:3px solid #CC0000">
        <div style="font-size:10px;color:#999;text-transform:uppercase;
                    letter-spacing:1px">Best Timing</div>
        <div style="font-size:14px;font-weight:700;color:#CC0000;margin-top:3px">
          ⏰ {r["recommended_timing"]}
        </div>
      </div>
    </div>
    <div style="background:#FFF5F5;border-radius:8px;padding:10px;
                border-left:3px solid #CC0000;margin-bottom:10px">
      <div style="font-size:10px;color:#999;text-transform:uppercase;
                  letter-spacing:1px;margin-bottom:3px">Offer Type</div>
      <div style="font-size:14px;font-weight:700">
        🎁 {r["recommended_offer_type"]}
      </div>
    </div>
    <div style="background:#F8F9FA;border-radius:8px;padding:12px;
                font-size:12px;color:#555;line-height:1.6">
      <strong style="color:#333">Why this activation?</strong><br/>
      {r["activation_reason"]}
    </div>
  </div>

</div>

<!-- IMPACT -->
<div class="gb-card" style="margin-bottom:12px">
  <div class="gb-sec" style="color:#2E7D32">
    📊 Expected Campaign Impact &nbsp;
    <span style="font-size:10px;font-weight:400;color:#aaa;
                 text-transform:none;letter-spacing:0">
      — simulated model output
    </span>
  </div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px">
    <div class="gb-imp" style="border-color:#2E7D32">
      <div style="font-size:26px;font-weight:900;color:#2E7D32">
        {r["engagement_uplift_pct"]}
      </div>
      <div style="font-size:11px;color:#555;margin-top:4px">Engagement Uplift</div>
    </div>
    <div class="gb-imp" style="border-color:#43A047">
      <div style="font-size:26px;font-weight:900;color:#43A047">
        {r["health_shift_pct"]}
      </div>
      <div style="font-size:11px;color:#555;margin-top:4px">Healthier Basket Shift</div>
    </div>
    <div class="gb-imp" style="border-color:#66BB6A">
      <div style="font-size:26px;font-weight:900;color:#66BB6A">
        {r["sustainability_improvement_pct"]}
      </div>
      <div style="font-size:11px;color:#555;margin-top:4px">Sustainability Gain</div>
    </div>
    <div class="gb-imp" style="border-color:#004A97">
      <div style="font-size:26px;font-weight:900;color:#004A97">
        {r["retention_pct"]}
      </div>
      <div style="font-size:11px;color:#555;margin-top:4px">Retention Likelihood</div>
    </div>
  </div>
</div>

<div style="text-align:center;font-size:11px;color:#bbb;padding:6px 0">
  Catalina Shopper Intelligence · GreenBasket Demo ·
  Synthetic data for presentation purposes only
</div>
</div>"""


print("✅  GreenBasket demo loaded — use the dropdown below.")
'''

# ---------------------------------------------------------------------------
# SELECTOR markdown
# ---------------------------------------------------------------------------
SELECTOR = (
    "## 🎯 Interactive Shopper Explorer\n\n"
    "Select any of the 15 shopper profiles from the dropdown.\n"
    "The full intelligence dashboard updates instantly.\n\n"
    "---"
)

# ---------------------------------------------------------------------------
# WIDGET cell  (triple-double-quoted — no ''' inside)
# ---------------------------------------------------------------------------
WIDGET = """opts = [
    (f"{r['name']}  ·  {r['persona']}  ({r['segment']})", r["shopper_id"])
    for _, r in df.sort_values(["segment", "persona"]).iterrows()
]

dd  = widgets.Dropdown(options=opts, value=opts[0][1],
                        layout=widgets.Layout(width="540px"))
out = widgets.Output()


def _upd(change):
    if change["name"] == "value":
        with out:
            clear_output(wait=True)
            display(HTML(render(change["new"])))


dd.observe(_upd)

display(HTML(
    "<div style=\\"font-family:'Segoe UI',Arial,sans-serif;"
    "background:#004A97;color:#fff;padding:13px 20px;"
    "border-radius:10px 10px 0 0;font-size:14px;font-weight:700;"
    "letter-spacing:.4px\\">👤&nbsp; Select Shopper Profile</div>"
))
display(dd)

with out:
    display(HTML(render(opts[0][1])))
display(out)
"""

# ---------------------------------------------------------------------------
# Build and write notebook
# ---------------------------------------------------------------------------
nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.9.0"},
    },
    "cells": [
        md_cell(INTRO),
        code_cell(SETUP),
        md_cell(SELECTOR),
        code_cell(WIDGET),
    ],
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"✅  Created: {OUT}")
print("   Open it in Jupyter → Cell → Run All")
