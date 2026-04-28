from mesa import Agent
import random

# --- CONFIGURARE COMPORTAMENT AGENȚI ---
LIMITA_DOBANDA_ACCEPTABILA = 0.08  # 8% (peste asta, agenții nu mai iau credite)
LIMITA_DOBANDA_PROFITABILA = 0.03  # 3% (sub asta, agentii iau credite)
REDUCERE_PRET_VANZATOR = 0.99      # -1% reducere dacă nu se vinde
TIMP_ASTEPTARE_VANZATOR = 3        # Luni după care vânzătorul scade prețul

class HomeBuyer(Agent):
    """
    Agentul Cumpărător: Reprezintă cererea din piață.
    Acesta decide dacă să cumpere, să investească la bursă sau să aștepte.
    """

    def __init__(self, model, budget, risk_appetite):
        super().__init__(model)
        self.budget = budget
        self.risk_appetite = risk_appetite  # 0 = Prudent, 1 = Speculator
        self.has_home = False

        # --- PERSONALITATE AGENT (Valoare Globală +/- Epsilon) ---
        # Unii acceptă maxim 6% dobândă, alții merg până la 10%
        self.limita_dobanda_acceptabila = random.uniform(0.06, 0.10)
        # Pragul de sentiment la care intră în panică (0.2 = foarte greu de speriat, 0.4 = fricos)
        self.prag_panica = random.uniform(0.20, 0.40)

    def step(self):
        # Dacă agentul are deja casă, nu mai caută alta (în acest model simplificat)
        if self.has_home:
            return

        # 1. Cumpărătorul se mută pe o celulă vecină (la întâmplare), nu pe una izolată.
        vecini = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        if vecini:
            self.model.grid.move_agent(self, random.choice(vecini))

        # 1. ANALIZA MEDIULUI (Logicǎ bazatǎ pe agent)
        # Agentul verifică starea "lumii" din model.py
        sentiment = self.model.market_sentiment
        dobanda = self.model.interest_rate

        # Analiza macroeconomică folosind pragurile personale
        # Dacă dobânda e prea mare SAU sentimentul pieței e prea scăzut (sub pragul lui de panică)
        if self.model.interest_rate > self.limita_dobanda_acceptabila or self.model.market_sentiment < self.prag_panica:
            return  # Refuză să cumpere luna aceasta

        # Logica de achiziție
        cell_mates = self.model.grid.get_cell_list_contents([self.pos])
        for other in cell_mates:
            if isinstance(other, Seller) and not other.is_sold:
                if self.budget >= other.price:
                    self.model.preturi_tranzactii_pas_curent.append(other.price)
                    self.has_home = True
                    other.is_sold = True
                    self.model.grid.move_agent(self, other.pos)
                    break

class Seller(Agent):
    """
    Agentul Vânzător: Reprezintă oferta.
    Își ajustează prețul pe baza răbdării personale și a climatului economic.
        """

    def __init__(self, model, price):
        super().__init__(model)
        self.price = price
        self.limit_price = price * 0.75
        self.is_sold = False
        self.time_on_market = 0

        # --- PERSONALITATE AGENT (Valoare Globală +/- Epsilon) ---
        # Unii vânzători așteaptă 2 luni, alții 4 luni până să lase din preț
        self.timp_asteptare_max = random.randint(2, 4)
        # Reducerea variază între -0.5% și -1.5% pe lună
        self.reducere_pret = random.uniform(0.985, 0.995)
        # Pragul la care lasă din preț de disperare din cauza economiei
        self.prag_panica = random.uniform(0.30, 0.50)

    def step(self):
        if self.is_sold:
            return

        self.time_on_market += 1

        # LOGICA DE PREȚ:
        if self.price > self.limit_price:
            # Scade prețul dacă și-a pierdut răbdarea SAU dacă sentimentul general e sub pragul lui de panică
            if self.time_on_market > self.timp_asteptare_max or self.model.market_sentiment < self.prag_panica:
                self.price *= self.reducere_pret