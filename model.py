import random
import mesa
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from agents import HomeBuyer, Seller

#---- Configurare Parametri Economici ----
VALOARE_INITIALA_BVB = 1000.0
VALOARE_INITIALA_SP500 = 4000.0
PRAG_CRIZA_BURSA = -0.02
CRESTERE_DOBANDA_CRIZA = 0.002
VOLATILITATE_MAXIMA = 0.05

# Funcții care simulează comportamentul pieței de capital
# Dacă dobânda crește, bursa tinde să scadă ușor, cu mici variații aleatorii.
def get_sp500(model):
    # O valoare de bază imaginară de 4000 puncte
    fluctuatie = random.uniform(-0.02, 0.03) # Între -2% și +3% pe lună
    impact_dobanda = model.interest_rate * 1000
    return 4000 * (1 + fluctuatie) - impact_dobanda

def get_bursa_locala(model):
    # O valoare de bază imaginară de 12000 puncte (ex: Indicele BET)
    fluctuatie = random.uniform(-0.03, 0.04)
    impact_dobanda = model.interest_rate * 3000
    return 12000 * (1 + fluctuatie) - impact_dobanda

class RealEstateModel(Model):
    """
    Modelul principal care gestionează piața imobiliară,
    indicatorii macroeconomici și bursa.
    """

    # Definim steps la nivel de clasă pentru a evita eroarea de tip object
    steps = 0

    def __init__(self, **kwargs):
        # Extragem valorile pentru noi, în siguranță
        # 1. EXTRAGEM (ȘI ȘTERGEM) toți parametrii din kwargs ca să nu avem erori cu Mesa
        width = kwargs.pop("width", 10)
        height = kwargs.pop("height", 10)
        num_buyers = kwargs.pop("num_buyers", 50)
        num_sellers = kwargs.pop("num_sellers", 50)
        dobanda_pornire = kwargs.pop("dobanda_pornire", 0.05)
        avg_budget = kwargs.pop("budget", 100000)  # Extragem și noul parametru budget

        super().__init__(**kwargs)

        # 2. Inițializarea Spațiului (Harta orașului)
        self.grid = MultiGrid(width, height, torus=True)
        self.space = self.grid  # Referință pentru componentele de vizualizare
        self.steps = 0

        # 3. Parametri Macroeconomici Inițiali
        self.interest_rate = dobanda_pornire       # Folosim valoarea primită ca argument
        self.stock_index = VALOARE_INITIALA_BVB    # Bursa Locală (ex: BET)
        self.sp500_index = VALOARE_INITIALA_SP500  # Bursa Internațională
        self.market_sentiment = "Optimist"
        self.preturi_tranzactii_pas_curent = []  # stocăm tranzacțiile din luna curentă

        #4. Extragere date pentru raport
        self.datacollector = DataCollector(
            model_reporters= {
                "Pret_Mediu_Oferta": lambda m: m.get_pret_mediu(m),
                "SP500": get_sp500,
                "Bursa_Locala": get_bursa_locala,
                "Dobanda": lambda m: m.interest_rate,
                "Sentiment": lambda m: 1 if m.market_sentiment == "Optimist" else 0,
                "Tranzactii_Noi": lambda m: len(m.preturi_tranzactii_pas_curent),
                "Tranzactii_Totale": lambda m: len([a for a in m.agents if type(a).__name__ == "Seller" and a.is_sold])
            }
        )
        # 5.1. PLASARE CUMPĂRĂTORI
        for i in range(num_buyers):
            buget_indiv = avg_budget * random.uniform(0.7, 1.3)
            buyer = HomeBuyer(self, buget_indiv, random.random())
            self.grid.place_agent(buyer, (self.random.randrange(width), self.random.randrange(height)))

        # 5.2 PLASARE VÂNZĂTORI
        for i in range(num_sellers):
            price = random.randint(80000, 130000)
            seller = Seller(self, price)
            self.grid.place_agent(seller, (self.random.randrange(width), self.random.randrange(height)))

        self.datacollector.collect(self)

    def get_pret_mediu(self, model):
        preturi = [a.price for a in model.agents if isinstance(a,Seller) and not a .is_sold]
        return sum(preturi) / len(preturi) if preturi else 0

    def step(self):
        """
        Avansează simularea cu un pas (echivalentul unei luni).
        """
        self.steps += 1
        self.preturi_tranzactii_pas_curent = []

        # Dinamica Bursei (Random Walk)
        change_intl = random.uniform(-VOLATILITATE_MAXIMA, VOLATILITATE_MAXIMA)
        self.sp500_index *= (1 + change_intl)
        self.market_sentiment = "Anxios" if change_intl < PRAG_CRIZA_BURSA else "Optimist"

        # Dinamica Dobânzii Automate (Slider-ul va putea suprascrie asta)
        if self.market_sentiment == "Anxios":
            self.interest_rate += CRESTERE_DOBANDA_CRIZA

        self.interest_rate = max(0.01, min(0.20, self.interest_rate))

        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

        # --- F. RAPORTARE ÎN CONSOLĂ ---
        #self.afiseaza_raport()

    def afiseaza_raport(self):
        print(f"\n--- LUNA {self.steps} | Sentiment: {self.market_sentiment} ---")
        print(f"S&P 500: {self.sp500_index:.2f} | Bursa Locala: {self.stock_index:.2f}")
        print(f"Dobânda: {self.interest_rate:.2%}")

        # Numărăm câte case s-au vândut
        sold_count = sum(1 for a in self.agents if isinstance(a, Seller) and a.is_sold)
        print(f"Tranzacții totale: {sold_count}")