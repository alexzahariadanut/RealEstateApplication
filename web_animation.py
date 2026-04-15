import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
import numpy as np
import time
from model import RealEstateModel

# --- 1. CONFIGURARE PAGINĂ WEB ---
st.set_page_config(page_title="Simulare Imobiliară", layout="wide")
st.title("🏡 Dashboard Interactiv: Piața Imobiliară")

# --- 2. MEMORIA APLICAȚIEI (SESSION STATE) ---
if "model" not in st.session_state:
    st.session_state.model = None
    st.session_state.istoric_pasi = []
    st.session_state.istoric_oferta = []
    st.session_state.istoric_tranzactii = []
    st.session_state.istoric_dobanda = []
    st.session_state.istoric_sp500 = []
    st.session_state.istoric_bursa_locala = []

# --- 3. BARĂ LATERALĂ ---
st.sidebar.header("1. Parametri de Start")
s_dim = st.sidebar.slider('Dimensiune Hartă', 10, 40, 20, 1)
s_buyers = st.sidebar.slider('Cumpărători', 5, 200, 50, 1)
s_sellers = st.sidebar.slider('Case', 5, 200, 50, 1)
s_budget = st.sidebar.slider('Buget Mediu (€)', 50000, 250000, 100000, 5000)

btn_reset = st.sidebar.button("🔄 Generează Piață Nouă")
st.sidebar.divider()

st.sidebar.header("2. Interacțiune Live")
s_dobanda = st.sidebar.slider('Dobândă %', 1.0, 20.0, 5.0, 0.5)
s_optimism = st.sidebar.slider('Optimism %', -2.0, 2.0, 0.0, 0.1)

ruleaza_live = st.sidebar.checkbox("▶️ Rulează Animația")
viteza_animatie = st.sidebar.slider("Pauză între cadre (sec)", 0.0, 1.0, 0.1, 0.1)

# --- 4. LOGICA DE REINIȚIALIZARE ---
if btn_reset or st.session_state.model is None:
    st.session_state.model = RealEstateModel(
        width=s_dim, height=s_dim,
        num_buyers=s_buyers, num_sellers=s_sellers,
        dobanda_pornire=s_dobanda / 100.0, budget=s_budget
    )
    st.session_state.istoric_pasi = []
    st.session_state.istoric_oferta = []
    st.session_state.istoric_tranzactii = []
    st.session_state.istoric_dobanda = []
    st.session_state.istoric_sp500 = []
    st.session_state.istoric_bursa_locala = []

model = st.session_state.model
BINS = np.linspace(30000, 250000, 30)

# --- 5. LOGICA DE SIMULARE (DOAR DACĂ E PE PLAY) ---
if ruleaza_live:
    model.interest_rate = s_dobanda / 100.0
    for a in model.agents:
        if type(a).__name__ == "Seller" and not getattr(a, 'is_sold', False):
            a.price *= (1 + s_optimism / 100.0)

    model.step()

    df = model.datacollector.get_model_vars_dataframe()
    if not df.empty:
        p_oferta = df["Pret_Mediu_Oferta"].iloc[-1]
        if getattr(model, 'preturi_tranzactii_pas_curent', []):
            p_tranz = sum(model.preturi_tranzactii_pas_curent) / len(model.preturi_tranzactii_pas_curent)
        else:
            p_tranz = None

        valoare_sp500 = df["SP500"].iloc[-1] if "SP500" in df.columns else 0
        valoare_bursa_locala = df["Bursa_Locala"].iloc[-1] if "Bursa_Locala" in df.columns else 0

        st.session_state.istoric_pasi.append(model.steps)
        st.session_state.istoric_oferta.append(p_oferta if p_oferta > 0 else None)
        st.session_state.istoric_tranzactii.append(p_tranz)
        st.session_state.istoric_dobanda.append(model.interest_rate * 100)

        # Corectare: Adăugăm datele bursiere în istoric
        st.session_state.istoric_sp500.append(valoare_sp500)
        st.session_state.istoric_bursa_locala.append(valoare_bursa_locala)

# --- 6. AFIȘARE INDICATORI FINANCIARI LIVE (KPIs) ---
st.markdown("### Indicatori Macroeconomici")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Pas Simulare (Luni)", value=model.steps)
with col2:
    st.metric(label="Rata Dobânzii Curentă", value=f"{model.interest_rate * 100:.2f}%")
with col3:
    if st.session_state.istoric_sp500:
        val_curenta_sp = st.session_state.istoric_sp500[-1]
        val_trecuta_sp = st.session_state.istoric_sp500[-2] if len(
            st.session_state.istoric_sp500) > 1 else val_curenta_sp
        st.metric(label="S&P 500 (Global)", value=f"{val_curenta_sp:.0f} pct",
                  delta=f"{val_curenta_sp - val_trecuta_sp:.0f} pct")
    else:
        st.metric(label="S&P 500 (Global)", value="Așteptare...")
with col4:
    if st.session_state.istoric_bursa_locala:
        val_curenta_bet = st.session_state.istoric_bursa_locala[-1]
        val_trecuta_bet = st.session_state.istoric_bursa_locala[-2] if len(
            st.session_state.istoric_bursa_locala) > 1 else val_curenta_bet
        st.metric(label="Bursa Locală (BET)", value=f"{val_curenta_bet:.0f} pct",
                  delta=f"{val_curenta_bet - val_trecuta_bet:.0f} pct")
    else:
        st.metric(label="Bursa Locală (BET)", value="Așteptare...")

st.divider()

# --- 7. RANDAREA VIZUALĂ A GRAFICELOR ---
fig = plt.figure(figsize=(16, 9))
gs = gridspec.GridSpec(2, 2, width_ratios=[1.2, 1], height_ratios=[1, 1])
fig.subplots_adjust(bottom=0.1, hspace=0.35, wspace=0.2)

ax_harta = fig.add_subplot(gs[:, 0])
ax_grafic = fig.add_subplot(gs[0, 1])
ax_hist = fig.add_subplot(gs[1, 1])
ax_dobanda = ax_grafic.twinx()

# Harta
ax_harta.set_xlim(-0.5, model.grid.width - 0.5)
ax_harta.set_ylim(-0.5, model.grid.width - 0.5)

b_pos = [a.pos for a in model.agents if type(a).__name__ == "HomeBuyer" and not getattr(a, 'has_home', False) and a.pos]
s_pos = [a.pos for a in model.agents if type(a).__name__ == "Seller" and not getattr(a, 'is_sold', False) and a.pos]
t_pos = [a.pos for a in model.agents if type(a).__name__ == "HomeBuyer" and getattr(a, 'has_home', False) and a.pos]

if b_pos: ax_harta.scatter(*zip(*b_pos), c='blue', marker='o', s=40, alpha=0.7)
if s_pos: ax_harta.scatter(*zip(*s_pos), c='red', marker='s', s=40, alpha=0.7)
if t_pos: ax_harta.scatter(*zip(*t_pos), c='green', marker='*', s=120)

ax_harta.legend(handles=[
    Line2D([0], [0], marker='o', color='w', label='Cumpărător', markerfacecolor='blue', markersize=8),
    Line2D([0], [0], marker='s', color='w', label='Casă', markerfacecolor='red', markersize=8),
    Line2D([0], [0], marker='*', color='w', label='Vândut', markerfacecolor='green', markersize=12)
], loc='upper right', fontsize=8)

sentiment = getattr(model, 'market_sentiment', 'N/A')
ax_harta.set_title(f"Harta {model.grid.width}x{model.grid.width} | Pas {model.steps} | Sentiment: {sentiment}")

# Grafic Liniar
if st.session_state.istoric_pasi:
    l1, = ax_grafic.plot(st.session_state.istoric_pasi, st.session_state.istoric_oferta, color='purple',
                         label="Preț Mediu Cerut", linewidth=2)
    scat = ax_grafic.scatter(st.session_state.istoric_pasi, st.session_state.istoric_tranzactii, color='green', s=25,
                             label="Tranzacții Reale")
    l2, = ax_dobanda.plot(st.session_state.istoric_pasi, st.session_state.istoric_dobanda, color='orange',
                          linestyle='--', label="Dobândă %")
    ax_grafic.legend(handles=[l1, scat, l2], loc='upper left', fontsize=7)

ax_grafic.set_ylim(40000, 250000)
ax_dobanda.set_ylim(0, 22)
ax_grafic.set_title("Evoluția Prețurilor vs Dobândă", fontsize=10)

# Histograma
bugete = [a.budget for a in model.agents if type(a).__name__ == "HomeBuyer" and not getattr(a, 'has_home', False)]
preturi = [a.price for a in model.agents if type(a).__name__ == "Seller" and not getattr(a, 'is_sold', False)]

if bugete: ax_hist.hist(bugete, bins=BINS, color='blue', alpha=0.5, label='Bugete (Cerere)')
if preturi: ax_hist.hist(preturi, bins=BINS, color='red', alpha=0.5, label='Prețuri (Ofertă)')

ax_hist.set_title("Distribuția Banii vs. Prețurile Cerute", fontsize=10)
ax_hist.set_xlabel("Suma (€)")
ax_hist.set_ylabel("Număr de Agenți")
ax_hist.legend(loc='upper right', fontsize=7)

if bugete and preturi:
    zona_max = max(bugete)
    zona_min = min(preturi)
    if zona_max >= zona_min:
        ax_hist.axvspan(zona_min, zona_max, color='green', alpha=0.1, label="Zonă Tranzacționabilă")

st.pyplot(fig)

# --- 8. BUCLA DE ANIMAȚIE ---
if ruleaza_live:
    time.sleep(viteza_animatie)
    st.rerun()