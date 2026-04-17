# 🏡 Simulare Agent-Based: Piața Imobiliară

Acest proiect reprezintă un laborator de simulare a pieței imobiliare, dezvoltat în Python. Folosind modelarea bazată pe agenți (Agent-Based Modeling - ABM), proiectul studiază interacțiunile dintre cumpărători și vânzători și modul în care factorii macroeconomici (precum rata dobânzii, sentimentul pieței, bursa locală și internațională) influențează tranzacțiile și evoluția prețurilor.

## 🛠️ Tehnologii Utilizate
* **Python 3.12**
* **Mesa:** Motorul principal pentru simularea multi-agent.
* **Streamlit:** Pentru interfața web (Dashboard interactiv).
* **Matplotlib & Seaborn:** Pentru procesarea datelor și generarea graficelor statistice.
* **Docker:** Pentru containerizarea aplicației și izolarea mediului de rulare.

## 📁 Structura Proiectului

Proiectul este organizat în module clare și decuplate:

* **🧠 Nucleul Simulării:**
  * `agents.py` - Definește clasele și comportamentul actorilor (HomeBuyer și Seller).
  * `model.py` - Gestionează mediul de simulare, aplică regulile macroeconomice la fiecare pas și colectează datele.
* **🖥️ Interfețele Vizuale:**
  * `web_animation.py` - Dashboard-ul web modern (Streamlit) cu indicatoare live (KPIs) pentru vizualizare dinamică.
  * `animation.py` - Versiunea locală (Matplotlib) pentru rulare și testare rapidă pe mașina gazdă.
* **📊 Generatoare de Rapoarte:**
  * `generator_reports.py` - Script unificat care rulează automat o analiză macroeconomică pe termen lung (5 ani) și un experiment comparativ (Batch Run), exportând graficele finale (.png).
* **⚙️ Infrastructură:**
  * `Dockerfile` & `requirements.txt` - Configurațiile pentru construirea automată a mediului izolat.

## 🚀 Cum se rulează proiectul

Aplicația poate fi rulată complet izolat folosind Docker.

### 1. Construirea imaginii (Build)
Deschideți un terminal în folderul proiectului și rulați:
```bash
docker build -t simulare-imobiliara .
```

### 2. Rularea Dashboard-ului Interactiv Web
Pentru a accesa interfața cu slidere și animații în timp real, rulați comanda de mai jos și deschideți browserul la http://localhost:8501 :
```bash
docker run -p 8501:8501 simulare-imobiliara
```
### 3. Generarea Graficelor pentru Disertație
Pentru a rula experimentele de fundal și a exporta automat graficele .png pe unitatea locală, rulați:
```bash
docker run -v ${PWD}:/app simulare-imobiliara python generator_reports.py
```

