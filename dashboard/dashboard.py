from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

st.set_page_config(page_title="E-Commerce Dashboard", page_icon="🛒", layout="wide")
sns.set_theme(style="whitegrid")

BASE = Path(__file__).parent
BLUE, LIGHT, RED = "#1f4e79", "#9dbbd6", "#c0392b"


@st.cache_data
def load_data():
    df = pd.read_csv(BASE / "main_data.csv", parse_dates=["order_purchase_timestamp"])
    geo = pd.read_csv(BASE / "state_geo.csv")
    return df, geo


df, state_geo = load_data()

# ---------------------------------------------------------------- Sidebar
st.sidebar.title("🛒 Filter")
min_d, max_d = df["order_purchase_timestamp"].min().date(), df["order_purchase_timestamp"].max().date()
date_range = st.sidebar.date_input("Rentang tanggal pembelian", (min_d, max_d), min_value=min_d, max_value=max_d)
if len(date_range) != 2:
    st.info("Pilih tanggal awal dan akhir pada sidebar.")
    st.stop()

states = sorted(df["customer_state"].unique())
sel_states = st.sidebar.multiselect("State pelanggan", states, default=states)

mask = (
    (df["order_purchase_timestamp"].dt.date >= date_range[0])
    & (df["order_purchase_timestamp"].dt.date <= date_range[1])
    & (df["customer_state"].isin(sel_states))
)
data = df[mask]
if data.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()
orders = data.drop_duplicates("order_id")  # 1 baris = 1 pesanan

# ---------------------------------------------------------------- Header & KPI
st.title("Dashboard Analisis E-Commerce (Olist, Brasil)")
st.caption("Pesanan berstatus delivered, Januari 2017 - Agustus 2018. Revenue = total harga produk (tanpa ongkir), dalam R$.")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total revenue", f"R$ {data['price'].sum()/1e6:,.2f} jt")
c2.metric("Jumlah pesanan", f"{orders['order_id'].nunique():,}")
c3.metric("Rata-rata lama kirim", f"{orders['delivery_days'].mean():.1f} hari")
c4.metric("Pesanan terlambat", f"{orders['is_late'].mean()*100:.1f}%")
c5.metric("Rata-rata review", f"{orders['review_score'].mean():.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Tren & Kategori (P1)", "🚚 Pengiriman & Review (P2)", "🗺️ Geospasial", "👥 RFM"])

# ---------------------------------------------------------------- Tab 1
with tab1:
    st.subheader("Tren revenue bulanan")
    monthly = data.groupby(data["order_purchase_timestamp"].dt.to_period("M").astype(str))["price"].sum().reset_index()
    fig, ax = plt.subplots(figsize=(11, 3.5))
    ax.plot(monthly["order_purchase_timestamp"], monthly["price"] / 1e3, marker="o", color=BLUE)
    ax.set_ylabel("Revenue (ribu R$)"); ax.set_xlabel("")
    ax.set_ylim(bottom=0)
    plt.xticks(rotation=45, ha="right"); sns.despine(); plt.tight_layout()
    st.pyplot(fig)

    st.subheader("Kategori produk teratas")
    n_top = st.slider("Jumlah kategori ditampilkan", 5, 20, 10)
    cat = (data.groupby("category")
           .agg(revenue=("price", "sum"), items=("order_item_id", "size"), avg_review=("review_score", "mean"))
           .sort_values("revenue", ascending=False))
    cat["share"] = cat["revenue"] / cat["revenue"].sum() * 100
    top = cat.head(n_top).reset_index()
    top["label"] = top["category"].str.replace("_", " ")
    avg_all = data["review_score"].mean()

    col_a, col_b = st.columns([1.4, 1])
    with col_a:
        fig, ax = plt.subplots(figsize=(8, 0.45 * n_top + 1.5))
        sns.barplot(data=top, y="label", x="revenue", palette=[BLUE] + [LIGHT] * (n_top - 1), ax=ax)
        for i, (r, s) in enumerate(zip(top["revenue"], top["share"])):
            ax.text(r, i, f"  {r/1e6:.2f} jt ({s:.1f}%)", va="center", fontsize=8)
        ax.set_xlim(0, top["revenue"].max() * 1.3); ax.set_xlabel("Total revenue (R$)"); ax.set_ylabel("")
        ax.set_title("Revenue per kategori", loc="left", fontweight="bold")
        sns.despine(); plt.tight_layout(); st.pyplot(fig)
    with col_b:
        fig, ax = plt.subplots(figsize=(5.5, 0.45 * n_top + 1.5))
        y = np.arange(n_top)
        colors = [RED if s < avg_all else BLUE for s in top["avg_review"]]
        ax.hlines(y, avg_all, top["avg_review"], color=colors, lw=2)
        ax.scatter(top["avg_review"], y, c=colors, s=70, zorder=3)
        ax.axvline(avg_all, color="gray", ls="--", lw=1)
        ax.set_yticks(y); ax.set_yticklabels([]); ax.set_ylim(n_top - 0.5, -0.5)
        lo = min(top["avg_review"].min(), avg_all) - 0.15
        hi = max(top["avg_review"].max(), avg_all) + 0.15
        ax.set_xlim(lo, hi)
        for i, s in enumerate(top["avg_review"]):
            ax.text(s + (0.01 if s >= avg_all else -0.01), i, f"{s:.2f}", va="center",
                    ha="left" if s >= avg_all else "right", fontsize=8)
        ax.set_xlabel(f"Review score (rata-rata semua: {avg_all:.2f}; merah = di bawahnya)", fontsize=8)
        ax.set_title("Rata-rata review", loc="left", fontweight="bold")
        sns.despine(); plt.tight_layout(); st.pyplot(fig)
    st.caption(f"{n_top} kategori teratas menyumbang {top['share'].sum():.1f}% revenue pada filter ini.")

# ---------------------------------------------------------------- Tab 2
with tab2:
    st.subheader("Keterlambatan pengiriman per state")
    min_orders = st.slider("Minimal jumlah pesanan per state", 50, 1000, 300, step=50)
    st_sum = (orders.groupby("customer_state")
              .agg(orders=("order_id", "size"), days=("delivery_days", "mean"), late=("is_late", "mean"), review=("review_score", "mean")))
    st_sum["late"] *= 100
    st_sum = st_sum[st_sum["orders"] >= min_orders].sort_values("late", ascending=False).reset_index()
    nat = orders["is_late"].mean() * 100

    col_a, col_b = st.columns([1.3, 1])
    with col_a:
        if st_sum.empty:
            st.info("Tidak ada state yang memenuhi batas minimal pesanan.")
        else:
            fig, ax = plt.subplots(figsize=(8, 0.33 * len(st_sum) + 1.5))
            sns.barplot(data=st_sum, y="customer_state", x="late",
                        palette=[RED if v > nat * 1.5 else LIGHT for v in st_sum["late"]], ax=ax)
            ax.axvline(nat, color="gray", ls="--", lw=1)
            ax.text(nat + 0.2, -0.75, f"rata-rata {nat:.1f}%", color="gray", fontsize=8)
            for i, (l, d) in enumerate(zip(st_sum["late"], st_sum["days"])):
                ax.text(l, i, f"  {l:.1f}% ({d:.0f} hari)", va="center", fontsize=8)
            ax.set_xlim(0, st_sum["late"].max() * 1.3); ax.set_xlabel("% pesanan tiba setelah estimasi"); ax.set_ylabel("")
            ax.set_title("Merah: >1,5x rata-rata", loc="left", fontweight="bold", fontsize=11)
            sns.despine(); plt.tight_layout(); st.pyplot(fig)
    with col_b:
        o = orders.dropna(subset=["review_score"]).copy()
        o["bin"] = pd.cut(o["delivery_days"], [0, 7, 14, 21, 30, np.inf], labels=["≤7 hari", "8-14", "15-21", "22-30", ">30 hari"])
        b = o.groupby("bin", observed=True).agg(n=("order_id", "size"), score=("review_score", "mean")).reset_index()
        fig, ax = plt.subplots(figsize=(6, 4.5))
        sns.barplot(data=b, x="bin", y="score", palette=[LIGHT, LIGHT, LIGHT, "#e08e7f", RED], ax=ax)
        ax.set_ylim(0, 5); ax.set_xlabel("Lama pengiriman"); ax.set_ylabel("Rata-rata review score")
        for i, (s, n) in enumerate(zip(b["score"], b["n"])):
            ax.text(i, s + 0.08, f"{s:.2f}\n(n={n:,})", ha="center", fontsize=8)
        ax.set_title("Review vs lama pengiriman", loc="left", fontweight="bold", fontsize=11)
        sns.despine(); plt.tight_layout(); st.pyplot(fig)

    on_time = orders.loc[~orders["is_late"], "review_score"].mean()
    late = orders.loc[orders["is_late"], "review_score"].mean()
    st.info(f"Review rata-rata pesanan **tepat waktu: {on_time:.2f}** vs **terlambat: {late:.2f}**.")

# ---------------------------------------------------------------- Tab 3
with tab3:
    st.subheader("Peta bubble per state")
    st.caption("Ukuran bubble = jumlah pesanan, warna = rata-rata lama pengiriman (hari). Posisi = rata-rata koordinat kode pos pelanggan di state tersebut.")
    g = (orders.groupby("customer_state").agg(orders=("order_id", "size"), days=("delivery_days", "mean")).reset_index()
         .merge(state_geo, on="customer_state"))
    fig, ax = plt.subplots(figsize=(8, 7))
    sc = ax.scatter(g["lng"], g["lat"], s=g["orders"] / g["orders"].max() * 1800 + 40, c=g["days"],
                    cmap="YlOrRd", alpha=0.75, edgecolor="gray")
    for _, r in g.iterrows():
        ax.annotate(r["customer_state"], (r["lng"], r["lat"]), ha="center", va="center", fontsize=8, fontweight="bold")
    plt.colorbar(sc, ax=ax, shrink=0.7, label="Rata-rata lama kirim (hari)")
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude"); ax.set_aspect("equal"); sns.despine()
    st.pyplot(fig)

# ---------------------------------------------------------------- Tab 4
with tab4:
    st.subheader("Segmentasi pelanggan (RFM)")
    st.caption("Recency dihitung dari 1 hari setelah pembelian terakhir pada data terfilter. Skor R & M berdasarkan kuartil, F: 1, 2, ≥3 pesanan.")
    snap = data["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    rfm = data.groupby("customer_unique_id").agg(last=("order_purchase_timestamp", "max"), frequency=("order_id", "nunique"),
                                                 price=("price", "sum"), freight=("freight_value", "sum"))
    rfm["monetary"] = rfm["price"] + rfm["freight"]
    rfm["recency"] = (snap - rfm["last"]).dt.days
    if len(rfm) >= 8:
        rfm["R"] = pd.qcut(rfm["recency"].rank(method="first"), 4, labels=[4, 3, 2, 1]).astype(int)
        rfm["M"] = pd.qcut(rfm["monetary"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
        rfm["F"] = rfm["frequency"].clip(upper=3)

        def segment(r):
            if r["F"] >= 2: return "Repeat Buyer"
            if r["R"] >= 3 and r["M"] >= 3: return "Recent Big Spender"
            if r["R"] >= 3: return "Recent One-time"
            if r["M"] >= 3: return "Lapsed Big Spender"
            return "Lapsed Low Value"

        rfm["segment"] = rfm.apply(segment, axis=1)
        order_seg = ["Repeat Buyer", "Recent Big Spender", "Recent One-time", "Lapsed Big Spender", "Lapsed Low Value"]
        seg = (rfm.groupby("segment").agg(customers=("recency", "size"), avg_recency=("recency", "mean"),
                                          avg_monetary=("monetary", "mean"), total=("monetary", "sum"))
               .reindex(order_seg).dropna().reset_index())
        seg["revenue_pct"] = seg["total"] / seg["total"].sum() * 100
        pal = ["#1f4e79", "#2e86c1", LIGHT, "#e08e7f", RED][: len(seg)]
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        sns.barplot(data=seg, x="customers", y="segment", palette=pal, ax=axes[0])
        axes[0].set_title("Jumlah pelanggan", loc="left", fontweight="bold"); axes[0].set_ylabel(""); axes[0].set_xlabel("")
        for i, n in enumerate(seg["customers"]): axes[0].text(n, i, f"  {n:,}", va="center", fontsize=9)
        axes[0].set_xlim(0, seg["customers"].max() * 1.2)
        sns.barplot(data=seg, x="revenue_pct", y="segment", palette=pal, ax=axes[1])
        axes[1].set_title("% revenue", loc="left", fontweight="bold"); axes[1].set_ylabel(""); axes[1].set_xlabel(""); axes[1].set_yticklabels([])
        for i, p in enumerate(seg["revenue_pct"]): axes[1].text(p, i, f"  {p:.1f}%", va="center", fontsize=9)
        axes[1].set_xlim(0, seg["revenue_pct"].max() * 1.2)
        sns.despine(); plt.tight_layout(); st.pyplot(fig)
        st.dataframe(seg.rename(columns={"avg_recency": "rata2 recency (hari)", "avg_monetary": "rata2 monetary (R$)",
                                         "total": "total monetary (R$)", "revenue_pct": "% revenue"}).round(1),
                     hide_index=True)
    else:
        st.info("Data terlalu sedikit untuk segmentasi RFM pada filter ini.")
