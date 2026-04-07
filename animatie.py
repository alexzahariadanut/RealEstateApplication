import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button
from matplotlib.lines import Line2D
import numpy as np
from Model import RealEstateModel
from Agents import HomeBuyer, Seller

# --- CONFIGURARE INIȚIALĂ ---
GRID_SIZE = 20
params = {"width": GRID_SIZE, "height": GRID_SIZE, "num_buyers": 50, "num_sellers": 50, "budget": 100000}
model = RealEstateModel(**params)

# --- CONFIGURARE LAYOUT (GridSpec) ---
fig = plt.figure(figsize=(16, 9))
# Împărțim fereastra: harta ia toată stânga, dreapta e împărțită sus-jos
gs = gridspec.GridSpec(2, 2, width_ratios=[1.2, 1], height_ratios=[1, 1])
fig.subplots_adjust(bottom=0.25, hspace=0.35, wspace=0.2)

ax_harta = fig.add_subplot(gs[:, 0])  # Toată coloana stângă
ax_grafic = fig.add_subplot(gs[0, 1])  # Dreapta Sus
ax_hist = fig.add_subplot(gs[1, 1])  # Dreapta Jos (NOU)
ax_dobanda = ax_grafic.twinx()

# --- SLIDERE (Compactate jos) ---
ax_sd = plt.axes([0.10, 0.15, 0.25, 0.02]);
s_dobanda = Slider(ax_sd, 'Dobândă %', 1.0, 20.0, valinit=5.0, color="orange")
ax_so = plt.axes([0.10, 0.10, 0.25, 0.02]);
s_optimism = Slider(ax_so, 'Optimism %', -2.0, 2.0, valinit=0.0, color="purple")
ax_bg = plt.axes([0.10, 0.05, 0.25, 0.02]);
s_budget = Slider(ax_bg, 'Buget (€)', 50000, 250000, valinit=100000, valfmt='%0.0f', color="green")

ax_nb = plt.axes([0.45, 0.15, 0.25, 0.02]);
s_buyers = Slider(ax_nb, 'Cumpărători', 5, 200, valinit=50, valfmt='%0.0f', color="blue")
ax_ns = plt.axes([0.45, 0.10, 0.25, 0.02]);
s_sellers = Slider(ax_ns, 'Case', 5, 200, valinit=50, valfmt='%0.0f', color="red")
ax_dim = plt.axes([0.45, 0.05, 0.25, 0.02]);
s_dim = Slider(ax_dim, 'Dim. Hartă', 10, 40, valinit=20, valfmt='%0.0f', color="gray")

ax_res = plt.axes([0.80, 0.08, 0.1, 0.06]);
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
    istoric_pasi.clear();
    istoric_oferta.clear();
    istoric_tranzactii.clear();
    istoric_dobanda.clear()


btn_reset.on_clicked(reset_model)

# Setăm limite fixe pentru histogramă ca să nu "sară" vizual
BINS = np.linspace(30000, 250000, 30)


def update(frame):
    global model

    # Update live parametri
    model.interest_rate = s_dobanda.val / 100
    for a in model.agents:
        if isinstance(a, Seller) and not a.is_sold:
            a.price *= (1 + s_optimism.val / 100)

    model.step()

    df = model.datacollector.get_model_vars_dataframe()
    if df.empty: return

    p_oferta = df["Pret_Mediu_Oferta"].iloc[-1]
    p_tranz = sum(model.preturi_tranzactii_pas_curent) / len(
        model.preturi_tranzactii_pas_curent) if model.preturi_tranzactii_pas_curent else None

    istoric_pasi.append(model.steps)
    istoric_oferta.append(p_oferta if p_oferta > 0 else None)
    istoric_tranzactii.append(p_tranz)
    istoric_dobanda.append(model.interest_rate * 100)

    # --- 1. RANDAȚI HARTA ---
    ax_harta.clear()
    current_grid_size = model.grid.width
    ax_harta.set_xlim(-0.5, current_grid_size - 0.5)
    ax_harta.set_ylim(-0.5, current_grid_size - 0.5)

    b_pos = [a.pos for a in model.agents if isinstance(a, HomeBuyer) and not a.has_home and a.pos]
    s_pos = [a.pos for a in model.agents if isinstance(a, Seller) and not a.is_sold and a.pos]
    t_pos = [a.pos for a in model.agents if isinstance(a, HomeBuyer) and a.has_home and a.pos]

    if b_pos: ax_harta.scatter(*zip(*b_pos), c='blue', marker='o', s=40, alpha=0.7)
    if s_pos: ax_harta.scatter(*zip(*s_pos), c='red', marker='s', s=40, alpha=0.7)
    if t_pos: ax_harta.scatter(*zip(*t_pos), c='green', marker='*', s=120)

    ax_harta.legend(handles=[
        Line2D([0], [0], marker='o', color='w', label='Cumpărător', markerfacecolor='blue', markersize=8),
        Line2D([0], [0], marker='s', color='w', label='Casă', markerfacecolor='red', markersize=8),
        Line2D([0], [0], marker='*', color='w', label='Vândut', markerfacecolor='green', markersize=12)
    ], loc='upper right', fontsize=8)
    ax_harta.set_title(
        f"Harta {current_grid_size}x{current_grid_size} | Pas {model.steps} | Sentiment: {model.market_sentiment}")

    # --- 2. RANDAȚI GRAFICUL LINIAR ---
    ax_grafic.clear();
    ax_dobanda.clear()
    l1, = ax_grafic.plot(istoric_pasi, istoric_oferta, color='purple', label="Preț Mediu Cerut", linewidth=2)
    scat = ax_grafic.scatter(istoric_pasi, istoric_tranzactii, color='green', s=25, label="Tranzacții Reale")
    l2, = ax_dobanda.plot(istoric_pasi, istoric_dobanda, color='orange', linestyle='--', label="Dobândă %")
    ax_grafic.set_ylim(40000, 250000);
    ax_dobanda.set_ylim(0, 22)
    ax_grafic.set_title("Evoluția Prețurilor vs Dobândă", fontsize=10)
    ax_grafic.legend(handles=[l1, scat, l2], loc='upper left', fontsize=7)

    # --- 3. RANDAȚI HISTOGRAMA (CERERE VS OFERTĂ) ---
    ax_hist.clear()

    # Colectăm bugetele și prețurile actuale din piață
    bugete = [a.budget for a in model.agents if isinstance(a, HomeBuyer) and not a.has_home]
    preturi = [a.price for a in model.agents if isinstance(a, Seller) and not a.is_sold]

    # Desenăm cele două distribuții
    if bugete: ax_hist.hist(bugete, bins=BINS, color='blue', alpha=0.5, label='Bugete (Cerere)')
    if preturi: ax_hist.hist(preturi, bins=BINS, color='red', alpha=0.5, label='Prețuri (Ofertă)')

    ax_hist.set_title("Distribuția Banii vs. Prețurile Cerute (Order Book)", fontsize=10)
    ax_hist.set_xlabel("Suma (€)")
    ax_hist.set_ylabel("Număr de Agenți")
    ax_hist.legend(loc='upper right', fontsize=7)

    # Evidențiem zona de intersecție (unde se pot face tranzacții)
    if bugete and preturi:
        zona_max = max(bugete)
        zona_min = min(preturi)
        if zona_max >= zona_min:
            ax_hist.axvspan(zona_min, zona_max, color='green', alpha=0.1, label="Zonă Tranzacționabilă")


ani = FuncAnimation(fig, update, frames=1000, interval=200, repeat=False)
plt.show()

model.datacollector.get_model_vars_dataframe().to_csv("date_disertatie.csv")