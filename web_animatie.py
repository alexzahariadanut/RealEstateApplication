import streamlit as st
import matplotlib.pyplot as plt
from Model import RealEstateModel

# Configurăm pagina web
st.set_page_config(page_title="Simulare Imobiliara",layout="wide")
st.title("🏡 Dashboard Interactiv: Piața Imobiliară")

#Creăm un meniu lateral pentru slidere
st.sidebar.header("Parametri Simulare")
dobanda_curenta = st.sidebar.slider("Rata Dobânzii", min_value=0.01, max_value=0.20, value=0.05, step=0.01)
buget_curent = st.sidebar.slider("Buget Mediu Cumpărători (€)", min_value=50000, max_value=200000, value=100000, step=10000)
pasi_simulare = st.sidebar.slider("Pași de Simulat (Luni)", min_value=1, max_value=30, value=1)

# Buton pentru a rula logica
if st.sidebar.button("Rulează Simularea"):
    # 1. Inițializăm modelul cu variabilele din slidere
    model = RealEstateModel(width=10, height=10, num_buyers=50, num_sellers=50, dobanda_pornire=dobanda_curenta,
                            budget=buget_curent)

    # 2. Rulăm modelul pentru numărul de luni ales
    for _ in range(pasi_simulare):
        model.step()

    # 3. Desenăm harta cu agenții actualizați
    fig, ax = plt.subplots(figsize=(6, 6))

    x_buyers = [agent.pos[0] for agent in model.schedule.agents if type(agent).__name__ == "HomeBuyer"]
    y_buyers = [agent.pos[1] for agent in model.schedule.agents if type(agent).__name__ == "HomeBuyer"]

    ax.scatter(x_buyers, y_buyers, c='blue', label='Cumpărători', alpha=0.7, s=100)
    ax.set_xlim(0, model.grid.width)
    ax.set_ylim(0, model.grid.height)
    ax.set_title(f"Harta Agenților (Luna {pasi_simulare})")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()

    # 4. Afișăm graficul în centrul paginii web
    st.pyplot(fig)

    st.success("Simulare executată cu succes!")