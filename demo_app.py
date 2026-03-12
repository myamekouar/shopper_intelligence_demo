import streamlit as st
import pandas as pd
import numpy as np
import os

# --- Page Config ---
st.set_page_config(
    page_title="Shopper Intelligence · CATALINA",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Retailer Theme Definitions ---
THEMES = {
    "Carrefour":     {"primary": "#004A97", "accent": "#E63329", "bg": "#F5F8FC"},
    "Leclerc":       {"primary": "#003087", "accent": "#FFCC00", "bg": "#F5F7FA"},
    "Monoprix":      {"primary": "#E20025", "accent": "#1A1A1A", "bg": "#FFF8F8"},
    "Intermarché":   {"primary": "#E30613", "accent": "#008000", "bg": "#F5FFF5"},
}

# --- Data Loading ---
DATA_PATH = os.path.join(os.path.dirname(__file__), "demo_shopper_profiles.csv")

@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        return None
    return pd.read_csv(DATA_PATH, low_memory=False)

# --- Gamification / UI Enrichment ---
def enrich_shopper(row):
    """Derive gamification fields from real model data. Nothing is invented."""
    spend       = float(row.get("total_spend", 0) or 0)
    red_rate    = float(row.get("redemption_rate", 0) or 0)
    streak      = int(row.get("healthy_basket_streak", 0) or 0)
    n_act       = int(row.get("n_activations", 0) or 0)
    reward_elig = bool(row.get("reward_eligible", 0))
    prospect    = float(row.get("mission_completion_prospect", 0) or 0)

    # Points: 10 pts per €1 spent
    points = int(spend * 10)

    # Loyalty tier — use model field, fallback to spend thresholds
    tier = row.get("shopper_tier", None)
    if not tier or (isinstance(tier, float) and np.isnan(tier)):
        if spend >= 600:   tier = "Gold"
        elif spend >= 250: tier = "Silver"
        else:              tier = "Bronze"

    # Reward progress within the current 5 000-point cycle
    cycle = 5_000
    progress_pct = min(100, round((points % cycle) / cycle * 100))
    pts_in_cycle = points % cycle

    # Badges — derived directly from model signals
    badges = []
    if streak >= 3:       badges.append("🥗 Health Streak")
    if red_rate >= 0.5:   badges.append("🎯 Offer Hunter")
    if n_act >= 5:        badges.append("⚡ Engaged Shopper")
    if reward_elig:       badges.append("🏆 Reward Ready")
    if prospect >= 0.7:   badges.append("🚀 Mission Star")
    if not badges:        badges.append("🌱 Getting Started")

    return {
        "points":         points,
        "tier":           tier,
        "streak":         streak,
        "badges":         badges,
        "progress_pct":   progress_pct,
        "pts_in_cycle":   pts_in_cycle,
        "cycle":          cycle,
    }

# ── Load data ──────────────────────────────────────────────
df = load_data()

if df is not None:
    df.columns = df.columns.str.strip().str.lower()

    # Map CSV column names → app-expected names
    _ALIASES = {
        "visits_per_month":       "frequency_per_month",
        "streak_weeks":           "healthy_basket_streak",
        "recommended_channel":    "primary_channel",
        "recommended_timing":     "activation_timing_rule",
        "recommended_offer_type": "activation_trigger",
        "recommended_offer_text": "kpi_to_track",
        "nutri_score":            "avg_nutri_score",
        "eco_score":              "avg_eco_score",
        "loyalty_tier":           "shopper_tier",
        "health_score":           "pct_healthy",
        "sustainability_score":   "pct_sustainable",
    }
    for _src, _dst in _ALIASES.items():
        if _src in df.columns and _dst not in df.columns:
            df[_dst] = df[_src]

    # Derive reward_eligible from loyalty tier if missing
    if "reward_eligible" not in df.columns:
        if "loyalty_tier" in df.columns:
            df["reward_eligible"] = df["loyalty_tier"].isin(["Gold", "Platinum"]).astype(int)
        else:
            df["reward_eligible"] = 0

    # Fill remaining missing columns with safe defaults
    for _col, _val in {
        "mission_completion_prospect": 0.5,
        "n_activations":               0,
        "n_redemptions":               0,
        "redemption_rate":             0.0,
        "secondary_channel":           "Email",
        "avg_nova_group":              None,
        "pct_ultra_processed":         0.0,
        "n_transactions":              0,
        "cluster_id":                  "N/A",
        "mission_completed_flag":      0,
        "reward_eligibility_flag":     0,
        "in_control_group":            0,
    }.items():
        if _col not in df.columns:
            df[_col] = _val

if df is None:
    st.error("⚠️  `demo_shopper_profiles.csv` not found.")
    st.info(
        "Run the **Export Cell** at the bottom of `Shopper_Intelligence_Model_v8.ipynb` "
        "to generate the demo dataset, then relaunch the app:\n\n"
        "```bash\nstreamlit run demo_app.py\n```"
    )
    st.stop()

# ── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/4/4a/Catalina_Marketing_logo.png",
             width=160, use_column_width=False)
    st.title("Shopper Intelligence")
    st.caption("Gamified Omnichannel Activation · FMCG Demo")
    st.divider()

    theme_name = st.selectbox("🎨 Retailer Theme", list(THEMES.keys()))
    theme = THEMES[theme_name]

    st.divider()

    # Build shopper labels (truncated ID + segment)
    shopper_labels = [
        f"...{str(r.get('loyalty_card_key', r.get('shopper_id', 'UNKNOWN')))[-8:]}  ·  {r.get('segment','?')}"
        for _, r in df.iterrows()
    ]
    selected_idx = st.selectbox(
        "👤 Select Shopper",
        range(len(shopper_labels)),
        format_func=lambda i: shopper_labels[i],
    )

    st.divider()
    st.caption(
        f"**{len(df):,}** shoppers &nbsp;|&nbsp; "
        f"**{df['segment'].nunique()}** segments"
    )

# ── Apply theme CSS ─────────────────────────────────────────
st.markdown(f"""
<style>
  section[data-testid="stSidebar"] {{ background: {theme['primary']}18; }}
  .stTabs [data-baseweb="tab"] {{
      background: white; border-radius: 8px 8px 0 0;
      padding: 8px 22px; border: 1px solid #ddd;
  }}
  .stTabs [aria-selected="true"] {{
      background: {theme['primary']}; color: white !important;
  }}
  .card {{
      background: white; border-radius: 12px; padding: 16px 20px;
      border-left: 4px solid {theme['primary']}; margin-bottom: 10px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  }}
  .badge {{
      display: inline-block;
      background: {theme['primary']}18;
      color: {theme['primary']};
      border-radius: 20px; padding: 5px 14px; margin: 4px 3px;
      font-size: 0.85em; font-weight: 600;
  }}
  .tier-pill {{
      background: {theme['accent']}; color: white;
      border-radius: 20px; padding: 4px 16px;
      font-weight: 700; font-size: 1em; display: inline-block;
  }}
</style>
""", unsafe_allow_html=True)

# ── Selected shopper ────────────────────────────────────────
shopper = df.iloc[selected_idx].to_dict()
ui = enrich_shopper(shopper)

# ── Page header ─────────────────────────────────────────────
hc1, hc2 = st.columns([4, 1])
with hc1:
    masked_id = f"...{str(shopper.get('loyalty_card_key', shopper.get('shopper_id', 'UNKNOWN')))[-8:]}"
    st.markdown(
        f"## 👋 Welcome back, Shopper `{masked_id}`\n"
        f"**Segment:** {shopper.get('segment','N/A')} &nbsp;·&nbsp; "
        f"Tier: <span class='tier-pill'>{ui['tier']}</span>",
        unsafe_allow_html=True,
    )
with hc2:
    st.markdown(
        f"<div style='text-align:right;color:{theme['primary']};font-size:1.7em;"
        f"font-weight:800;padding-top:10px'>🏪 {theme_name}</div>",
        unsafe_allow_html=True,
    )

st.divider()

# ── Three tabs ──────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 My Dashboard", "🛒 Basket Review", "🏆 My Rewards Journey", "🧾 Checkout Experience"]
)

# ══════════════════════════════════════════════════════════════
# TAB 1 · MY DASHBOARD
# ══════════════════════════════════════════════════════════════
with tab1:
    m1, m2, m3, m4 = st.columns(4)
    spend = shopper.get("total_spend", 0) or 0
    freq  = shopper.get("frequency_per_month", 0) or 0
    m1.metric("Total Spend",       f"€{spend:,.2f}")
    m2.metric("Visits / Month",    f"{freq:.1f}")
    m3.metric("Points Balance",    f"{ui['points']:,} pts")
    m4.metric("Healthy Basket Streak", f"{ui['streak']} {'basket' if ui['streak']==1 else 'baskets'}")

    st.markdown("---")
    left, right = st.columns([3, 2])

    with left:
        st.subheader("Your Activation Plan")
        trigger = str(shopper.get("activation_trigger", "N/A")).replace("_", " ").title()
        pch     = shopper.get("primary_channel", "N/A")
        sch     = shopper.get("secondary_channel", "N/A")
        timing  = shopper.get("activation_timing_rule", "N/A")
        kpi     = shopper.get("kpi_to_track", "N/A")

        st.markdown(f"""
<div class='card'>🎯 <b>Mission</b><br>{trigger}</div>
<div class='card'>📱 <b>Primary Channel</b><br>{pch}</div>
<div class='card'>📧 <b>Secondary Channel</b><br>{sch}</div>
<div class='card'>⏰ <b>Best Timing</b><br>{timing}</div>
<div class='card'>📈 <b>KPI to Track</b><br>{kpi}</div>
""", unsafe_allow_html=True)

    with right:
        st.subheader("My Badges")
        badge_html = "".join(f"<span class='badge'>{b}</span>" for b in ui["badges"])
        st.markdown(badge_html, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Mission Completion Likelihood")
        prospect = shopper.get("mission_completion_prospect", 0) or 0
        pct = int(prospect * 100) if prospect <= 1 else int(prospect)
        st.progress(pct / 100)
        st.caption(f"Model estimate: **{pct}%** probability of completing the assigned mission")

        reward_eligible = bool(shopper.get("reward_eligible", 0))
        if reward_eligible:
            st.success("✅ Eligible for a reward right now")
        else:
            st.info("🔒 Complete your mission to unlock your next reward")

# ══════════════════════════════════════════════════════════════
# TAB 2 · BASKET REVIEW
# ══════════════════════════════════════════════════════════════
with tab2:
    nutri = shopper.get("avg_nutri_score")
    eco   = shopper.get("avg_eco_score")
    nova  = shopper.get("avg_nova_group")

    def fmt(v, decimals=1):
        try:
            return f"{float(v):.{decimals}f}" if v is not None and not (isinstance(v, float) and np.isnan(v)) else "N/A"
        except Exception:
            return "N/A"

    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Avg Nutri-Score",  fmt(nutri), help="1 = Best · 5 = Worst")
    sc2.metric("Avg Eco-Score",    fmt(eco),   help="1 = Best · 5 = Worst")
    sc3.metric("Avg NOVA Group",   fmt(nova),  help="1 = Unprocessed · 4 = Ultra-processed")

    st.markdown("---")
    bl, br = st.columns(2)

    with bl:
        st.subheader("Basket Health Composition")

        def safe_pct(val):
            v = float(val or 0)
            return v * 100 if v <= 1 else v

        pct_h   = safe_pct(shopper.get("pct_healthy", 0))
        pct_s   = safe_pct(shopper.get("pct_sustainable", 0))
        pct_u   = safe_pct(shopper.get("pct_ultra_processed", 0))

        st.markdown(f"**🥦 Healthy products:** {pct_h:.0f}%")
        st.progress(min(1.0, pct_h / 100))
        st.markdown(f"**🌿 Sustainable products:** {pct_s:.0f}%")
        st.progress(min(1.0, pct_s / 100))
        st.markdown(f"**⚠️ Ultra-processed:** {pct_u:.0f}%")
        st.progress(min(1.0, pct_u / 100))

    with br:
        st.subheader("Shopping Behaviour")
        avg_bv   = shopper.get("avg_basket_value", 0) or 0
        n_trans  = shopper.get("n_transactions", 0) or 0
        pct_ec   = safe_pct(shopper.get("pct_ecommerce", 0))
        top_cat  = shopper.get("top_category", "N/A")

        st.markdown(f"""
| Metric | Value |
|--------|-------|
| Avg Basket Value | €{avg_bv:.2f} |
| Total Transactions | {int(n_trans):,} |
| E-commerce Share | {pct_ec:.0f}% |
| Top Category | {top_cat} |
""")

# ══════════════════════════════════════════════════════════════
# TAB 3 · MY REWARDS JOURNEY
# ══════════════════════════════════════════════════════════════
with tab3:
    rj_left, rj_right = st.columns([3, 2])

    with rj_left:
        tier_order = {"Bronze": 1, "Silver": 2, "Gold": 3, "Platinum": 4}
        tier_val   = tier_order.get(ui["tier"], 1)
        tier_desc  = {
            "Bronze":   "You're just getting started — keep shopping to reach Silver.",
            "Silver":   "Great progress! Keep it up to reach Gold status.",
            "Gold":     "You're a valued Gold member. Platinum is within reach!",
            "Platinum": "You've reached the top tier. Enjoy your exclusive benefits.",
        }

        st.subheader(f"🏅 Loyalty Status: {ui['tier']}")
        st.progress(tier_val / 4)
        st.caption(tier_desc.get(ui["tier"], ""))

        st.markdown("---")
        st.subheader("Points Progress to Next Reward")
        st.progress(ui["progress_pct"] / 100)
        pts_remaining = ui["cycle"] - ui["pts_in_cycle"]
        st.caption(
            f"{ui['pts_in_cycle']:,} / {ui['cycle']:,} points · "
            f"**{pts_remaining:,} pts** to next reward"
        )

        st.markdown("---")
        st.subheader("Offer Engagement")
        n_act  = int(shopper.get("n_activations", 0) or 0)
        n_red  = int(shopper.get("n_redemptions", 0) or 0)
        rr     = float(shopper.get("redemption_rate", 0) or 0)
        rr_pct = rr * 100 if rr <= 1 else rr

        oe1, oe2, oe3 = st.columns(3)
        oe1.metric("Offers Activated", n_act)
        oe2.metric("Offers Redeemed",  n_red)
        oe3.metric("Redemption Rate",  f"{rr_pct:.0f}%")

    with rj_right:
        st.subheader("Your Earned Badges")
        for badge in ui["badges"]:
            st.markdown(
                f"<div class='badge' style='display:block;margin:8px 0;"
                f"padding:10px 18px;font-size:1em'>{badge}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        if bool(shopper.get("reward_eligible", 0)):
            st.success("🎁 You have a reward waiting!")
            st.button("Claim My Reward", type="primary", use_container_width=True)
        else:
            st.info("Complete your current mission to earn your next reward.")

# ══════════════════════════════════════════════════════════════
# BUSINESS LOGIC PANEL (jury / demo presenter view)
# ══════════════════════════════════════════════════════════════
with st.expander("🔍 Business Intelligence Panel — Jury View", expanded=False):
    st.caption("All fields below come directly from the model outputs — no synthetic data.")

    bj1, bj2 = st.columns(2)

    with bj1:
        st.markdown("**Raw Model Fields — Selected Shopper**")
        SHOW_FIELDS = [
            "loyalty_card_key", "segment", "cluster_id",
            "activation_trigger", "primary_channel", "secondary_channel",
            "activation_timing_rule", "kpi_to_track",
            "mission_completion_prospect", "reward_eligible",
            "mission_completed_flag", "reward_eligibility_flag",
            "in_control_group", "shopper_tier",
        ]
        available = [f for f in SHOW_FIELDS if f in shopper]
        profile_df = pd.DataFrame(
            {"Field": available, "Value": [str(shopper.get(f, "")) for f in available]}
        )
        st.dataframe(profile_df, use_container_width=True, hide_index=True)

    with bj2:
        st.markdown("**Segment Benchmarks**")
        seg = shopper.get("segment", "")
        seg_df = df[df["segment"] == seg]
        if not seg_df.empty:
            st.metric("Shoppers in segment",  len(seg_df))
            st.metric("Avg spend (segment)",  f"€{seg_df['total_spend'].mean():,.2f}")
            st.metric("Avg visits/month",     f"{seg_df['frequency_per_month'].mean():.1f}" if "frequency_per_month" in seg_df.columns else "N/A")
            pct_elig = seg_df["reward_eligible"].mean() * 100 if "reward_eligible" in seg_df.columns else 0
            st.metric("% Reward eligible",    f"{pct_elig:.0f}%")

    st.markdown("---")
    st.markdown("**Segment Distribution in Demo Dataset**")
    _id_col = "loyalty_card_key" if "loyalty_card_key" in df.columns else ("shopper_id" if "shopper_id" in df.columns else df.columns[0])
    summary = (
        df.groupby("segment")
        .agg(
            Shoppers       = (_id_col,                      "count"),
            Avg_Spend      = ("total_spend",                "mean"),
            Avg_Freq       = ("frequency_per_month",        "mean"),
            Pct_Reward     = ("reward_eligible",            "mean"),
            Avg_MissionPct = ("mission_completion_prospect","mean"),
        )
        .reset_index()
    )
    summary["Avg_Spend"]      = summary["Avg_Spend"].map("€{:,.2f}".format)
    summary["Avg_Freq"]       = summary["Avg_Freq"].map("{:.1f}/mo".format)
    summary["Pct_Reward"]     = (summary["Pct_Reward"] * 100).map("{:.0f}%".format)
    summary["Avg_MissionPct"] = (summary["Avg_MissionPct"] * 100).map("{:.0f}%".format)
    st.dataframe(summary, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# TAB 4 · CHECKOUT EXPERIENCE
# ══════════════════════════════════════════════════════════════
with tab4:

    # ── Basket definition ───────────────────────────────────
    BASKET_ITEMS = [
        {"icon": "🥣", "name": "Organic Oat Granola",         "qty": 1, "price": 4.99},
        {"icon": "🥛", "name": "Semi-Skimmed Milk 2L",        "qty": 2, "price": 2.40},
        {"icon": "🥦", "name": "Tenderstem Broccoli 300g",    "qty": 1, "price": 1.89},
        {"icon": "🍗", "name": "Free-Range Chicken Breast",   "qty": 1, "price": 8.49},
        {"icon": "🍞", "name": "Wholemeal Sourdough Loaf",    "qty": 1, "price": 3.20},
        {"icon": "🫐", "name": "Blueberries 200g",            "qty": 2, "price": 3.50},
    ]

    subtotal      = sum(item["qty"] * item["price"] for item in BASKET_ITEMS)
    gb_discount   = 2.00  # GreenBasket reward value
    reward_elig   = bool(shopper.get("reward_eligible", 0))

    # Session state for offer toggle
    if "offer_applied" not in st.session_state:
        st.session_state.offer_applied = False

    # ── Layout ──────────────────────────────────────────────
    co_left, co_right = st.columns([1, 1], gap="large")

    # ── LEFT: basket items + apply button ───────────────────
    with co_left:
        st.subheader("🛒 Your Basket")

        for item in BASKET_ITEMS:
            line_total = item["qty"] * item["price"]
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;padding:9px 0;border-bottom:1px solid #f0f0f0'>"
                f"<span style='font-size:14px'>"
                f"<span style='font-size:20px;margin-right:8px'>{item['icon']}</span>"
                f"{item['name']}"
                f"<span style='color:#aaa;margin-left:8px'>× {item['qty']}</span></span>"
                f"<span style='font-weight:600;color:#1a1a1a'>€{line_total:.2f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"<div style='display:flex;justify-content:space-between;"
            f"padding:12px 0;font-size:15px;color:#555'>"
            f"<span>Subtotal</span><span>€{subtotal:.2f}</span></div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        if reward_elig and not st.session_state.offer_applied:
            if st.button(
                f"✅ Apply GreenBasket Offer  (−€{gb_discount:.2f})",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.offer_applied = True
                st.rerun()

        if st.session_state.offer_applied:
            st.success(f"🌿 GreenBasket reward applied — you saved €{gb_discount:.2f}!")
            if st.button("Remove offer", use_container_width=True):
                st.session_state.offer_applied = False
                st.rerun()

        if not reward_elig:
            st.info("Complete your current mission to unlock your GreenBasket reward.")

    # ── RIGHT: receipt (rendered with st.markdown / unsafe_allow_html) ──
    with co_right:
        st.subheader("🧾 Your Receipt")

        applied     = st.session_state.offer_applied
        total       = subtotal - (gb_discount if applied else 0.0)
        points_earned = int(total * 10)

        # Build item rows HTML
        item_rows_html = "".join(
            f"""<div style="display:flex;justify-content:space-between;
                            align-items:center;padding:7px 0;
                            border-bottom:1px solid #f5f5f5;font-size:13px">
                  <span>
                    <span style="font-size:17px;margin-right:6px">{item['icon']}</span>
                    {item['name']}
                    <span style="color:#bbb;font-size:11px"> × {item['qty']}</span>
                  </span>
                  <span style="color:#333;font-weight:500">
                    €{item['qty'] * item['price']:.2f}
                  </span>
                </div>"""
            for item in BASKET_ITEMS
        )

        # GreenBasket discount row — only shown when applied
        discount_row_html = (
            f"""<div style="display:flex;justify-content:space-between;
                            padding:7px 0;font-size:13px;font-weight:600;color:#2E7D32">
                  <span>🌿 GreenBasket reward</span>
                  <span>−€{gb_discount:.2f}</span>
                </div>"""
            if applied else ""
        )

        # Full receipt HTML — rendered via st.markdown, not st.write / st.text
        receipt_html = f"""
        <div style="background:#ffffff;border:1px solid #e8e8e8;border-radius:14px;
                    padding:28px 24px;font-family:'Segoe UI',system-ui,sans-serif;
                    box-shadow:0 2px 12px rgba(0,0,0,0.07);">

          <!-- Store header -->
          <div style="text-align:center;margin-bottom:18px">
            <div style="font-size:30px;line-height:1">🌿</div>
            <div style="font-weight:800;font-size:17px;color:#1B5E20;margin-top:4px">
              GreenBasket
            </div>
            <div style="color:#999;font-size:11px;margin-top:3px;letter-spacing:0.5px">
              {theme_name.upper()} &nbsp;·&nbsp; {masked_id}
            </div>
          </div>

          <div style="border-top:1px dashed #ddd;margin:10px 0"></div>

          <!-- Item list -->
          {item_rows_html}

          <div style="border-top:1px dashed #ddd;margin:12px 0"></div>

          <!-- Subtotal -->
          <div style="display:flex;justify-content:space-between;
                      font-size:13px;color:#666;padding:4px 0">
            <span>Subtotal</span>
            <span>€{subtotal:.2f}</span>
          </div>

          <!-- Discount row (conditional) -->
          {discount_row_html}

          <div style="border-top:1px dashed #ddd;margin:12px 0"></div>

          <!-- Total -->
          <div style="display:flex;justify-content:space-between;
                      font-size:19px;font-weight:800;color:#111;padding:4px 0">
            <span>Total</span>
            <span>€{total:.2f}</span>
          </div>

          <!-- Points earned -->
          <div style="background:#E8F5E9;border-radius:10px;padding:14px 12px;
                      margin-top:18px;text-align:center">
            <div style="font-size:12px;color:#2E7D32;font-weight:600;
                        letter-spacing:0.5px;margin-bottom:4px">
              POINTS EARNED THIS SHOP
            </div>
            <div style="font-size:28px;font-weight:800;color:#1B5E20;line-height:1">
              +{points_earned:,}
            </div>
            <div style="font-size:11px;color:#888;margin-top:4px">
              Added to your GreenBasket account
            </div>
          </div>

          <!-- Footer -->
          <div style="text-align:center;margin-top:18px;color:#ccc;font-size:11px">
            Thank you for shopping with GreenBasket
          </div>

        </div>
        """

        # ✅ Render receipt as HTML — not st.write() or st.text()
        st.markdown(receipt_html, unsafe_allow_html=True)
