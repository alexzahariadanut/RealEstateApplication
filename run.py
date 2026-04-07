import matplotlib.pyplot as plt
import pandas as pd
from Model import RealEstateModel

# 1. Configurarea și rularea modelului
LATIME, INALTIME = 10, 10
CUMPARATORI, VANZATORI = 50, 50
PASI_SIMULARE = 60 # 5 ani de zile (60 luni)

model = RealEstateModel(LATIME, INALTIME, CUMPARATORI, VANZATORI)

print("Simularea rulează...")
for i in range(PASI_SIMULARE):
    model.step()

# 2. Extragerea datelor
df = model.datacollector.get_model_vars_dataframe()

# 3. Crearea Graficelor
fig, ax1 = plt.subplots(figsize=(12, 6))

# Axa 1: Bursa (S&P 500 și Locală)
color_sp = 'tab:blue'
color_local = 'tab:cyan'
ax1.set_xlabel('Luni (Pasi)')
ax1.set_ylabel('Indice Bursier', color=color_sp)
ax1.plot(df.index, df['SP500'], color=color_sp, label='S&P 500 (Global)', linewidth=2)
ax1.plot(df.index, df['Bursa_Locala'], color=color_local, label='Bursa Locală (BET)', linestyle='--')
ax1.tick_params(axis='y', labelcolor=color_sp)
ax1.legend(loc='upper left')

# Axa 2: Dobânda (pe aceeași figură, dar scară diferită)
ax2 = ax1.twinx()
color_int = 'tab:red'
ax2.set_ylabel('Rata Dobânzii (%)', color=color_int)
ax2.plot(df.index, df['Dobanda'], color=color_int, label='Dobândă BNR', linewidth=2)
ax2.tick_params(axis='y', labelcolor=color_int)

plt.title('Corelația între Piața de Capital și Politica Monetară')
plt.grid(True, alpha=0.3)
plt.savefig("grafic_corelatie_economica.png") # Salvează imaginea pentru disertație
plt.show()

# 4. Grafic pentru Prețul Mediu al Caselor
plt.figure(figsize=(10, 5))
plt.plot(df.index, df['Pret_Mediu'], color='green', label='Preț Mediu Imobile')
plt.xlabel('Luni')
plt.ylabel('Preț (Euro)')
plt.title('Evoluția Prețurilor Imobiliare în funcție de Ciclul Economic')
plt.legend()
plt.savefig("evolutie_preturi_case.png")
plt.show()