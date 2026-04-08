from mesa.batchrunner import batch_run
from Model import RealEstateModel
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns # Pentru grafice comparative

# 1. Configurarea experimentului comparativ
params = {
    "width": 10,
    "height": 10,
    "num_buyers": 50,
    "num_sellers": 50,
    "dobanda_pornire": [0.02, 0.10] # Aici definim cele două scenarii
}

print("Se rulează experimentul comparativ (2 scenarii x 10 repetiții)network...")
results = batch_run(
RealEstateModel,
    parameters=params,
    rng=[None] * 10,  #Repetă de 10 ori
    max_steps=30,
    data_collection_period=1,
    display_progress=True
)

df_batch = pd.DataFrame(results)

# 2. Vizualizarea impactului asupra Prețului Mediu
plt.figure(figsize=(12, 6))
sns.lineplot(data=df_batch, x="Step", y="Pret_Mediu_Oferta", hue="dobanda_pornire", palette="viridis")
plt.title("Impactul Ratei Dobânzii asupra Evoluției Prețurilor Imobiliare")
plt.xlabel("Luni (Pas Simularea)")
plt.ylabel("Preț Mediu (Euro)")
plt.legend(title="Dobândă Inițială")
plt.grid(True, alpha=0.3)
plt.savefig("comparatie_scenarii_pret.png")
try:
    plt.show()
except Exception:
    print("Mediul nu are ecran (ex: Docker). Graficul a fost salvat direct pe disc.")

# 3. Vizualizarea impactului asupra Tranzacțiilor
plt.figure(figsize=(12, 6))
sns.boxplot(data=df_batch[df_batch["Step"] == 15], x="dobanda_pornire", y="Tranzactii_Totale")
plt.title("Total Tranzacții după 2 ani în funcție de Dobândă")
plt.xlabel("Scenariu Dobândă")
plt.ylabel("Număr Case Vândute")
plt.savefig("comparatie_tranzactii_box.png")
try:
    plt.show()
except Exception:
    print("Mediul nu are ecran (ex: Docker). Graficul a fost salvat direct pe disc.")