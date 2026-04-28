import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button
from matplotlib.lines import Line2D
import numpy as np
from model import RealEstateModel
from agents import HomeBuyer, Seller

# --- 1. CONFIGURARE INIȚIALĂ ---
GRID_SIZE = 20
# Am adăugat "dobanda_pornire" pentru a corespunde cu noul agent refactorizat model.py
params = {
    "width": GRID_SIZE,
    "height": GRID_SIZE,
    "num_buyers": 50,
    "num_sellers": 50,
    "dobanda_pornire": 0.05,
    "budget": 100000
}
model = RealEstateModel(**params)

# --- 2. CONFIGURARE LAYOUT (GridSpec) ---
fig = plt.figure(figsize=(16, 9))
# Am lăsat mai mult spațiu în partea de sus (top=0.88) pentru panoul bursier
fig.subplots_adjust(top=0.88, bottom=0.25, hspace=0.35, wspace=0.2)

gs = gridspec.GridSpec(2, 2, width_ratios=[1.2, 1], height_ratios=[1, 1])

ax_harta = fig.add_subplot(gs[:, 0])  # Toată coloana stângă
ax_grafic = fig.add_subplot(gs[0, 1])  # Dreapta Sus
ax_hist = fig.add_subplot(gs[1, 1])  # Dreapta Jos
ax_dobanda = ax_grafic.twinx()

# --- NOU: PANOU INFORMATIV (KPIs BURSĂ) ---
# Un text dinamic plasat în partea superioară a ferestrei
kpi_text = fig.text(0.5, 0.95, 'Se inițializează piața...', fontsize=12, ha='center', va='center',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='#2C3E50', edgecolor='none', alpha=0.9),
                    color='white', weight='bold')

# --- 3. SLIDERE (Compactate jos) ---
ax_sd = plt.axes([0.10, 0.15, 0.25, 0.02])
s_dobanda = Slider(ax_sd, 'Dobândă %', 1.0, 20.0, valinit=5.0, color="orange")
ax_so = plt.axes([0.10, 0.10, 0.25, 0.02])
s_optimism = Slider(ax_so, 'Optimism %', -2.0, 2.0, valinit=0.0, color="purple")
ax_bg = plt.axes([0.10, 0.05, 0.25, 0.02])
s_budget = Slider(ax_bg, 'Buget (€)', 50000, 250000, valinit=100000, valfmt='%0.0f', color="green")

ax_nb = plt.axes([0.45, 0.15, 0.25, 0.02])
s_buyers = Slider(ax_nb, 'Cumpărători', 5, 200, valinit=50, valfmt='%0.0f', color="blue")
ax_ns = plt.axes([0.45, 0.10, 0.25, 0.02])
s_sellers = Slider(ax_ns, 'Case', 5, 200, valinit=50, valfmt='%0.0f', color="red")
ax_dim = plt.axes([0.45, 0.05, 0.25, 0.02])
s_dim = Slider(ax_dim, 'Dim. Hartă', 10, 40, valinit=20, valfmt='%0.0f', color="gray")

ax_res = plt.axes([0.80, 0.08, 0.1, 0.06])
btn_reset = Button(ax_res, 'RESTART', color='lightgray', hovercolor='lime')

istoric_pasi, istoric_oferta, istoric_tranzactii, istoric_dobanda = [], [], [], []


def reset_model(event):
    global model, istoric_pasi, istoric_oferta, istoric_tranzactii, istoric_dobanda
    grid_size = int(s_dim.val)
    model = RealEstateModel(
        width=grid_size, height=grid_size,
        num_buyers=int(s_buyers.val), num_sellers=int(s_sellers.val),
        dobanda_pornire=s_dobanda.val / 100, budget=s_budget.val
    )
    istoric_pasi.clear()
    istoric_oferta.clear()
    istoric_tranzactii.clear()
    istoric_dobanda.clear()


btn_reset.on_clicked(reset_model)

BINS = np.linspace(30000, 250000, 30)


# --- 4. BUCLA DE ANIMAȚIE LVE ---
def update(frame):
    global model

    # Update live parametri în model
    model.interest_rate = s_dobanda.val / 100
    for a in model.agents:
        if isinstance(a, Seller) and not getattr(a, 'is_sold', False):
            a.price *= (1 + s_optimism.val / 100)

    model.step()

    df = model.datacollector.get_model_vars_dataframe()
    if df.empty: return

    # Extragere date standard
    p_oferta = df["Pret_Mediu_Oferta"].iloc[-1]
    p_tranz = sum(model.preturi_tranzactii_pas_curent) / len(model.preturi_tranzactii_pas_curent) if getattr(model,
                                                                                                             'preturi_tranzactii_pas_curent',
                                                                                                             []) else None

    # Extragere date bursiere
    val_sp500 = df["SP500"].iloc[-1] if "SP500" in df.columns else 0
    val_bursa = df["Bursa_Locala"].iloc[-1] if "Bursa_Locala" in df.columns else 0

    istoric_pasi.append(model.steps)
    istoric_oferta.append(p_oferta if p_oferta > 0 else None)
    istoric_tranzactii.append(p_tranz)
    istoric_dobanda.append(model.interest_rate * 100)

    # Actualizare Panou KPI (Titlul dinamic)
    kpi_text.set_text(
        f" S&P 500: {val_sp500:.0f} pct  |  Bursa Locală (BET): {val_bursa:.0f} pct  |  Dobândă: {model.interest_rate * 100:.2f}% ")

    # RANDARE HARTĂ
    ax_harta.clear()
    current_grid_size = model.grid.width
    ax_harta.set_xlim(-0.5, current_grid_size - 0.5)
    ax_harta.set_ylim(-0.5, current_grid_size - 0.5)

    b_pos = [a.pos for a in model.agents if isinstance(a, HomeBuyer) and not getattr(a, 'has_home', False) and a.pos]
    s_pos = [a.pos for a in model.agents if isinstance(a, Seller) and not getattr(a, 'is_sold', False) and a.pos]
    t_pos = [a.pos for a in model.agents if isinstance(a, HomeBuyer) and getattr(a, 'has_home', False) and a.pos]

    if b_pos: ax_harta.scatter(*zip(*b_pos), c='blue', marker='o', s=40, alpha=0.7)
    if s_pos: ax_harta.scatter(*zip(*s_pos), c='red', marker='s', s=40, alpha=0.7)
    if t_pos: ax_harta.scatter(*zip(*t_pos), c='green', marker='*', s=120)

    ax_harta.legend(handles=[
        Line2D([0], [0], marker='o', color='w', label='Cumpărător', markerfacecolor='blue', markersize=8),
        Line2D([0], [0], marker='s', color='w', label='Casă', markerfacecolor='red', markersize=8),
        Line2D([0], [0], marker='*', color='w', label='Vândut', markerfacecolor='green', markersize=12)
    ], loc='upper right', fontsize=8)

    # Formatare nouă pentru sentimentul continuu
    sentiment_val = getattr(model, 'market_sentiment', 0.5)
    if isinstance(sentiment_val, float):
        stare = "Optimist" if sentiment_val > 0.6 else ("Anxios" if sentiment_val < 0.4 else "Neutru")
        sentiment_text = f"{sentiment_val:.2f} ({stare})"
    else:
        sentiment_text = str(sentiment_val)

    ax_harta.set_title(f"Harta {current_grid_size}x{current_grid_size} | Pas {model.steps} | Sentiment: {sentiment_text}")

    # RANDARE GRAFIC LINIAR
    ax_grafic.clear()
    ax_dobanda.clear()
    l1, = ax_grafic.plot(istoric_pasi, istoric_oferta, color='purple', label="Preț Mediu Cerut", linewidth=2)
    scat = ax_grafic.scatter(istoric_pasi, istoric_tranzactii, color='green', s=25, label="Tranzacții Reale")
    l2, = ax_dobanda.plot(istoric_pasi, istoric_dobanda, color='orange', linestyle='--', label="Dobândă %")
    ax_grafic.set_ylim(40000, 250000)
    ax_dobanda.set_ylim(0, 22)
    ax_grafic.set_title("Evoluția Prețurilor vs Dobândă", fontsize=10)
    ax_grafic.legend(handles=[l1, scat, l2], loc='upper left', fontsize=7)

    # RANDARE HISTOGRAMA (CERERE VS OFERTĂ)
    ax_hist.clear()
    bugete = [a.budget for a in model.agents if isinstance(a, HomeBuyer) and not getattr(a, 'has_home', False)]
    preturi = [a.price for a in model.agents if isinstance(a, Seller) and not getattr(a, 'is_sold', False)]

    if bugete: ax_hist.hist(bugete, bins=BINS, color='blue', alpha=0.5, label='Bugete (Cerere)')
    if preturi: ax_hist.hist(preturi, bins=BINS, color='red', alpha=0.5, label='Prețuri (Ofertă)')

    ax_hist.set_title("Distribuția Banii vs. Prețurile Cerute (Order Book)", fontsize=10)
    ax_hist.set_xlabel("Suma (€)")
    ax_hist.set_ylabel("Număr de Agenți")
    ax_hist.legend(loc='upper right', fontsize=7)

    if bugete and preturi:
        zona_max = max(bugete)
        zona_min = min(preturi)
        if zona_max >= zona_min:
            ax_hist.axvspan(zona_min, zona_max, color='green', alpha=0.1, label="Zonă Tranzacționabilă")


ani = FuncAnimation(fig, update, frames=1000, interval=200, repeat=False)
plt.show()

# La final, datele se salvează local pentru acces ușor
model.datacollector.get_model_vars_dataframe().to_csv("date_disertatie_local.csv")