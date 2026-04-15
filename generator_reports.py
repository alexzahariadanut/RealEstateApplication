import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from mesa.batchrunner import batch_run
from model import RealEstateModel

def salvare_grafic_sigur(nume_fisier):
    """Funcție ajutătoare pentru a salva și afișa graficele în siguranță pe medii Docker."""
    plt.savefig(nume_fisier, bbox_inches='tight')
    try:
        plt.show()
    except Exception:
        print(f"Mediul nu are ecran. Graficul '{nume_fisier}' a fost salvat direct pe disc.")
    plt.close() # Eliberăm memoria

# ==========================================
# PARTEA A: ANALIZĂ MACROECONOMICĂ SINGULARĂ
# ==========================================
print("--- START PARTEA A: Rularea simulării macroeconomice (60 luni) ---")

model_macro = RealEstateModel(width=20, height=20, num_buyers=50, num_sellers=50, dobanda_pornire=0.05, budget=100000)

for _ in range(60):
    model_macro.step()

df_macro = model_macro.datacollector.get_model_vars_dataframe()

# 1. Grafic Corelație Bursă vs. Dobândă
fig, ax1 = plt.subplots(figsize=(12, 6))
color_sp = 'tab:blue'
ax1.set_xlabel('Luni (Pași)')
ax1.set_ylabel('Indice Bursier', color=color_sp)

if 'SP500' in df_macro.columns:
    ax1.plot(df_macro.index, df_macro['SP500'], color=color_sp, label='S&P 500 (Global)', linewidth=2)
if 'Bursa_Locala' in df_macro.columns:
    ax1.plot(df_macro.index, df_macro['Bursa_Locala'], color='tab:cyan', label='Bursa Locală (BET)', linestyle='--')

ax1.tick_params(axis='y', labelcolor=color_sp)
ax1.legend(loc='upper left')

ax2 = ax1.twinx()
color_int = 'tab:red'
ax2.set_ylabel('Rata Dobânzii (%)', color=color_int)
if 'Dobanda' in df_macro.columns:
    ax2.plot(df_macro.index, df_macro['Dobanda'], color=color_int, label='Dobândă BNR', linewidth=2)
ax2.tick_params(axis='y', labelcolor=color_int)

plt.title('Corelația între Piața de Capital și Politica Monetară')
plt.grid(True, alpha=0.3)
salvare_grafic_sigur("grafic_1_corelatie_economica.png")

# 2. Evoluția Prețurilor
plt.figure(figsize=(10, 5))
if 'Pret_Mediu_Oferta' in df_macro.columns:
    plt.plot(df_macro.index, df_macro['Pret_Mediu_Oferta'], color='green', label='Preț Mediu Oferte')
plt.xlabel('Luni')
plt.ylabel('Preț (Euro)')
plt.title('Evoluția Prețurilor Imobiliare pe parcursul a 5 ani')
plt.legend()
plt.grid(True, alpha=0.3)
salvare_grafic_sigur("grafic_2_evolutie_preturi.png")


# ==========================================
# PARTEA B: ANALIZĂ COMPARATIVĂ (BATCH RUN)
# ==========================================
print("\n--- START PARTEA B: Rularea experimentului comparativ (Batch Run) ---")

params_batch = {
    "width": 10,
    "height": 10,
    "num_buyers": 50,
    "num_sellers": 50,
    "budget": 100000,
    "dobanda_pornire": [0.02, 0.10] # Testăm piața la 2% vs 10% dobândă
}

results = batch_run(
    RealEstateModel,
    parameters=params_batch,
    rng=[None] * 10,  # 10 repetiții
    max_steps=30,     # 30 de luni
    data_collection_period=1,
    display_progress=True
)

df_batch = pd.DataFrame(results)

# 3. Impactul Dobânzii asupra Prețului Mediu
plt.figure(figsize=(12, 6))
sns.lineplot(data=df_batch, x="Step", y="Pret_Mediu_Oferta", hue="dobanda_pornire", palette="viridis")
plt.title("Impactul Ratei Dobânzii asupra Evoluției Prețurilor Imobiliare")
plt.xlabel("Luni (Pas Simulare)")
plt.ylabel("Preț Mediu (Euro)")
plt.legend(title="Dobândă Inițială")
plt.grid(True, alpha=0.3)
salvare_grafic_sigur("grafic_3_comparatie_scenarii_pret.png")

# 4. Impactul asupra Tranzacțiilor
plt.figure(figsize=(12, 6))
# "Tranzactii_Totale" există în model.py -> DataCollector
if "Tranzactii_Totale" in df_batch.columns:
    sns.boxplot(data=df_batch[df_batch["Step"] == 15], x="dobanda_pornire", y="Tranzactii_Totale")
    plt.title("Total Tranzacții după 15 luni în funcție de Dobândă")
    plt.xlabel("Scenariu Dobândă (%)")
    plt.ylabel("Număr Case Vândute")
    salvare_grafic_sigur("grafic_4_comparatie_tranzactii_box.png")
else:
    print("Avertisment: Coloana 'Tranzactii_Totale' nu există în DataCollector, graficul boxplot a fost omis.")

print("\nToate rapoartele au fost generate cu succes!")