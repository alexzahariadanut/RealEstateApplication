import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
import numpy as np
from Model import RealEstateModel

# --- 1. CONFIGURARE PAGINĂ WEB ---
st.set_page_config(page_title="Simulare Imobiliară", layout="wide")
st.title("🏡 Dashboard Interactiv: Piața Imobiliară")

# --- 2. CONFIGURARE SLIDERE (BARA LATERALĂ) ---
st.sidebar.header("Parametri de Start (Necesită Reset)")
s_dim = st.sidebar.slider('Dimensiune Hartă', 10, 40, 20, 1)
s_buyers = st.sidebar.slider('Cumpărători', 5, 200, 50, 1)
s_sellers = st.sidebar.slider('Case', 5, 200, 50, 1)
s_budget = st.sidebar.slider('Buget Mediu (€)', 50000, 250000, 100000, 5000)

st.sidebar.header("Parametri Dinamici (Live)")
s_dobanda = st.sidebar.slider('Dobândă %', 1.0, 20.0, 5.0, 0.5)
s_optimism = st.sidebar.slider('Optimism %', -2.0, 2.0, 0.0, 0.1)

pasi_simulare = st.sidebar.slider("Câți pași (luni) simulăm?", 10, 200, 50, 10)
btn_start = st.sidebar.button("🚀 Rulează Animația")

# Un "container" gol pe pagina web în care desenăm cadrele animației
placeholder = st.empty()

# --- 3. LOGICA DE SIMULARE ȘI DESENARE ---
if btn_start:
    # Inițializăm modelul cu variabilele din slidere
    model = RealEstateModel(
        width=s_dim, height=s_dim,
        num_buyers=s_buyers, num_sellers=s_sellers,
        dobanda_pornire=s_dobanda / 100.0, budget=s_budget
    )

    istoric_pasi, istoric_oferta, istoric_tranzactii, istoric_dobanda = [], [], [], []
    BINS = np.linspace(30000, 250000, 30)

    # Structura vizuală o singură dată
    fig = plt.figure(figsize=(16, 9))
    gs = gridspec.GridSpec(2, 2, width_ratios=[1.2, 1], height_ratios=[1, 1])
    # Am redus marginea de jos (bottom) deoarece sliderele nu mai sunt pe imagine
    fig.subplots_adjust(bottom=0.1, hspace=0.35, wspace=0.2)

    ax_harta = fig.add_subplot(gs[:, 0])
    ax_grafic = fig.add_subplot(gs[0, 1])
    ax_hist = fig.add_subplot(gs[1, 1])
    ax_dobanda = ax_grafic.twinx()

    # Bucla de animație
    with st.spinner('Simularea rulează...'):
        for step in range(1, pasi_simulare + 1):

            # --- Actualizare parametri dinamici ---
            model.interest_rate = s_dobanda / 100.0

            # AICI E REPARAȚIA MESA 3.5.0: Folosim model.agents în loc de model.schedule.agents
            for a in model.agents:
                if type(a).__name__ == "Seller" and not getattr(a, 'is_sold', False):
                    a.price *= (1 + s_optimism / 100.0)

            # Rulăm motorul
            model.step()

            # --- Extragere date ---
            df = model.datacollector.get_model_vars_dataframe()
            if df.empty: continue

            p_oferta = df["Pret_Mediu_Oferta"].iloc[-1]
            if getattr(model, 'preturi_tranzactii_pas_curent', []):
                p_tranz = sum(model.preturi_tranzactii_pas_curent) / len(model.preturi_tranzactii_pas_curent)
            else:
                p_tranz = None

            istoric_pasi.append(model.steps)
            istoric_oferta.append(p_oferta if p_oferta > 0 else None)
            istoric_tranzactii.append(p_tranz)
            istoric_dobanda.append(model.interest_rate * 100)

            # --- Curățare ecrane ---
            ax_harta.clear()
            ax_grafic.clear()
            ax_dobanda.clear()
            ax_hist.clear()

            # --- 3.1. RANDARE HARTĂ ---
            ax_harta.set_xlim(-0.5, model.grid.width - 0.5)
            ax_harta.set_ylim(-0.5, model.grid.width - 0.5)

            # Filtrare agenți folosind direct model.agents (Reparație Mesa)
            b_pos = [a.pos for a in model.agents if
                     type(a).__name__ == "HomeBuyer" and not getattr(a, 'has_home', False) and a.pos]
            s_pos = [a.pos for a in model.agents if
                     type(a).__name__ == "Seller" and not getattr(a, 'is_sold', False) and a.pos]
            t_pos = [a.pos for a in model.agents if
                     type(a).__name__ == "HomeBuyer" and getattr(a, 'has_home', False) and a.pos]

            if b_pos: ax_harta.scatter(*zip(*b_pos), c='blue', marker='o', s=40, alpha=0.7)
            if s_pos: ax_harta.scatter(*zip(*s_pos), c='red', marker='s', s=40, alpha=0.7)
            if t_pos: ax_harta.scatter(*zip(*t_pos), c='green', marker='*', s=120)

            ax_harta.legend(handles=[
                Line2D([0], [0], marker='o', color='w', label='Cumpărător', markerfacecolor='blue', markersize=8),
                Line2D([0], [0], marker='s', color='w', label='Casă', markerfacecolor='red', markersize=8),
                Line2D([0], [0], marker='*', color='w', label='Vândut', markerfacecolor='green', markersize=12)
            ], loc='upper right', fontsize=8)

            sentiment = getattr(model, 'market_sentiment', 'N/A')
            ax_harta.set_title(
                f"Harta {model.grid.width}x{model.grid.width} | Pas {model.steps} | Sentiment: {sentiment}")

            # --- 3.2. RANDARE GRAFIC LINIAR ---
            l1, = ax_grafic.plot(istoric_pasi, istoric_oferta, color='purple', label="Preț Mediu Cerut", linewidth=2)
            scat = ax_grafic.scatter(istoric_pasi, istoric_tranzactii, color='green', s=25, label="Tranzacții Reale")
            l2, = ax_dobanda.plot(istoric_pasi, istoric_dobanda, color='orange', linestyle='--', label="Dobândă %")

            ax_grafic.set_ylim(40000, 250000)
            ax_dobanda.set_ylim(0, 22)
            ax_grafic.set_title("Evoluția Prețurilor vs Dobândă", fontsize=10)
            ax_grafic.legend(handles=[l1, scat, l2], loc='upper left', fontsize=7)

            # --- 3.3. RANDARE HISTOGRAMĂ ---
            bugete = [a.budget for a in model.agents if
                      type(a).__name__ == "HomeBuyer" and not getattr(a, 'has_home', False)]
            preturi = [a.price for a in model.agents if
                       type(a).__name__ == "Seller" and not getattr(a, 'is_sold', False)]

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

            # --- 4. AFIȘARE CADRU PE WEB ---
            # Suprascriem imaginea veche cu cea nouă, creând efectul de animație
            placeholder.pyplot(fig)

    st.success("Simulare finalizată cu succes!")

    # buton pentru descărcarea datelor generate
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descarcă Datele (CSV)",
        data=csv,
        file_name='date_disertatie.csv',
        mime='text/csv',
    )