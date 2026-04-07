from mesa import Agent

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

    def step(self):
        # Dacă agentul are deja casă, nu mai caută alta (în acest model simplificat)
        if self.has_home:
            return

        # 1. Cumpărătorul se mută pe o celulă vecină (la întâmplare), nu pe una izolată!
        vecini = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        noua_pozitie = self.random.choice(vecini)
        self.model.grid.move_agent(self, noua_pozitie)

        # 1. ANALIZA MEDIULUI (Logicǎ Agenticǎ)
        # Agentul verifică starea "lumii" din model.py
        sentiment = self.model.market_sentiment
        dobanda = self.model.interest_rate

        #2.1 Daca dobanda e sub 3%, cumparam chiar daca indicele bursei e negativ
        if dobanda < LIMITA_DOBANDA_PROFITABILA:
            self.cauta_si_negociaza()
            return

        # 2.2 PROCESUL DE DECIZIE
        # Dacă sentimentul e 'Anxios', cumpărătorul devine precaut și nu cumpără,
        # preferând să păstreze lichiditățile.
        if sentiment == "Anxios" or dobanda > LIMITA_DOBANDA_ACCEPTABILA:
            #print(f"Agent {self.unique_id}: Sentiment negativ. Aștept condiții mai bune.")
            return

        # Dacă dobânda e prea mare (ex: > 8%), creditul e prea scump
        if dobanda > LIMITA_DOBANDA_ACCEPTABILA:
            #print(f"Agent {self.unique_id}: Dobânzi prea mari ({dobanda:.2%}). Pas.")
            return

        # 3. ACȚIUNEA: Căutarea unei locuințe
        self.cauta_si_negociaza()

    def cauta_si_negociaza(self):
        # Scanăm celulele vecine pentru a găsi un vânzător
        celule_vizibile = self.model.grid.get_neighbors(self.pos, moore=True, include_center=True)

        for other in celule_vizibile:
            if type(other).__name__ == "Seller" and not other.is_sold:
                # Verificăm dacă bugetul cumpărătorului acoperă prețul cerut
                if self.budget >= other.price:
                    # --- ACEASTA ESTE LINIA ESENȚIALĂ ---
                    # Raportăm prețul către model înainte ca tranzacția să se finalizeze
                    self.model.preturi_tranzactii_pas_curent.append(other.price)
                    # ------------------------------------

                    self.has_home = True
                    other.is_sold = True

                    # Cumpărătorul se mută pe poziția casei achiziționate
                    self.model.grid.move_agent(self, other.pos)
                    break

class Seller(Agent):
    """
    Agentul Vânzător: Reprezintă oferta.
    Își ajustează prețul în funcție de cât de repede vrea să vândă și de economie.
    """

    def __init__(self, model, price):
        super().__init__(model)
        self.price = price
        self.limit_price = price * 0.75
        self.is_sold = False
        self.time_on_market = 0

    def step(self):
        if self.is_sold:
            return

        self.time_on_market += 1

        # LOGICA DE PREȚ:
        # Scade prețul doar dacă este peste limita minimă
        if self.price > self.limit_price:
            if self.time_on_market > TIMP_ASTEPTARE_VANZATOR or self.model.market_sentiment == "Anxios":
                    self.price *= REDUCERE_PRET_VANZATOR  # Scade cu 1%

        # Dacă economia e în criză (Anxios), mai scade prețul cu încă 1% forțat
        if self.model.market_sentiment == "Anxios":
            self.price *= REDUCERE_PRET_VANZATOR