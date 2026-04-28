import random
import mesa
import yfinance as yf
import ssl
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from agents import HomeBuyer, Seller

# Ignora erorile de certificat SSL la nivel de Python
ssl._create_default_https_context = ssl._create_unverified_context

def get_pret_mediu(model):
    preturi = [a.price for a in model.agents if isinstance(a, Seller) and not a.is_sold]
    return sum(preturi) / len(preturi) if preturi else 0


def get_sp500(model):
    index = min(model.steps, len(model.istoric_sp500) - 1)
    return float(model.istoric_sp500[index])


def get_bursa_locala(model):
    index = min(model.steps, len(model.istoric_bursa_locala) - 1)
    return float(model.istoric_bursa_locala[index])


class RealEstateModel(Model):
    def __init__(self, width, height, num_buyers, num_sellers, dobanda_pornire=0.05, budget=100000):
        # Obligatoriu în Mesa 3.0: apelăm constructorul clasei de bază
        super().__init__()

        self.num_buyers = num_buyers
        self.num_sellers = num_sellers
        self.grid = MultiGrid(width, height, True)
        self.interest_rate = dobanda_pornire

        # Sentimentul este o valoare continuă în intervalul [0, 1]. Pornim de la 0.5 (Neutru)
        self.market_sentiment = 0.5

        self.steps = 0
        self.preturi_tranzactii_pas_curent = []

        # --- INTEGRARE DATE REALE (Yahoo Finance) ---
        print("Se descarcă datele financiare...")
        self.istoric_sp500 = self._descarca_date_reale("^GSPC", 100)
        # --- INTEGRARE DATE REALE (Yahoo Finance) ---
        print("Se descarcă datele financiare...")
        self.istoric_sp500 = self._descarca_date_reale("^GSPC", 100)
        self.istoric_bursa_locala = self._descarca_date_reale("EEM", 100)

        # ADAUGĂ ACESTE DOUĂ LINII PENTRU TESTARE:
        print(f"Test SP500 (primele 5 luni): {self.istoric_sp500[:5]}")
        print(f"Test Bursa (primele 5 luni): {self.istoric_bursa_locala[:5]}")
        self.istoric_bursa_locala = self._descarca_date_reale("EEM", 100)  # Proxy pentru piața locală

        self.datacollector = DataCollector(
            model_reporters={
                "Pret_Mediu_Oferta": get_pret_mediu,
                "SP500": get_sp500,
                "Bursa_Locala": get_bursa_locala,
                "Dobanda": lambda m: m.interest_rate * 100,
                "Sentiment_Piata": lambda m: m.market_sentiment
            }
        )

        # Creare Agenți Cumpărători
        for i in range(self.num_buyers):
            b = HomeBuyer(self, budget, random.choice([0, 1]))
            # (Nu mai este nevoie de self.schedule.add)
            x, y = self.random.randrange(self.grid.width), self.random.randrange(self.grid.height)
            self.grid.place_agent(b, (x, y))

        # Creare Agenți Vânzători
        for i in range(self.num_sellers):
            pret_initial = random.uniform(budget * 0.8, budget * 1.5)
            s = Seller(self, pret_initial)
            # (Nu mai este nevoie de self.schedule.add)
            x, y = self.random.randrange(self.grid.width), self.random.randrange(self.grid.height)
            self.grid.place_agent(s, (x, y))

    def _descarca_date_reale(self, ticker, luni_necesare):
        try:
            # Încercăm să descărcăm datele oficiale
            data = yf.download(ticker, period="10y", interval="1mo", progress=False)

            # Verificăm dacă Yahoo ne-a dat un tabel gol sau blocat
            if data is None or data.empty or 'Close' not in data:
                raise ValueError("Yahoo a blocat cererea (date goale).")

            valori_inchidere = data['Close'].dropna().values.flatten().tolist()

            # Ne asigurăm că avem cel puțin o valoare validă înainte de a o accesa
            if not valori_inchidere:
                raise ValueError("Lista de prețuri este complet goală.")

            if len(valori_inchidere) >= luni_necesare:
                return valori_inchidere[-luni_necesare:]

            return valori_inchidere + [valori_inchidere[-1]] * (luni_necesare - len(valori_inchidere))

        except Exception as e:
            # DACA API-UL PICA SAU DA EROARE DE SSL, GENERĂM DATE REALISTE (BACKUP)
            print(f"API indisponibil pentru {ticker} ({e}). Se folosesc date simulate realiste.")

            start_val = 4000.0 if ticker == "^GSPC" else 12000.0
            istoric_simulat = [start_val]

            for _ in range(luni_necesare - 1):
                # Generăm o fluctuație lunară realistă (între -3% și +3.5%, cu tendință ușor crescătoare)
                fluctuatie = random.uniform(-0.03, 0.035)
                noua_valoare = istoric_simulat[-1] * (1 + fluctuatie)
                istoric_simulat.append(noua_valoare)

            return istoric_simulat

    def step(self):
        self.steps += 1
        self.preturi_tranzactii_pas_curent = []

        # --- ACTUALIZARE SENTIMENT CONTINUU ---
        # Calculăm fluctuația bursei față de luna anterioară pentru a influența sentimentul
        valoare_curenta = get_sp500(self)
        if self.steps > 1:
            val_trecuta = self.istoric_sp500[min(self.steps - 2, len(self.istoric_sp500) - 1)]
            fluctuatie = (valoare_curenta - val_trecuta) / val_trecuta
        else:
            fluctuatie = 0.0

        # Mapăm fluctuația (-5% la +5%) într-o modificare a sentimentului între [0, 1]
        sentiment_brut = 0.5 + (fluctuatie * 10)
        self.market_sentiment = max(0.0, min(1.0, sentiment_brut))

        # NOU ÎN MESA 3.0: Activăm toți agenții într-o ordine aleatorie
        self.agents.shuffle_do("step")

        self.datacollector.collect(self)