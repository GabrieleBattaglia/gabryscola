import time
from carte import Mazzo
from giocatore import Giocatore
from ia_perfetta import IAPerfetta
from gestione_dati import generate_ai_name
from GBUtils import key

class MotoreBriscola:
    VERSIONE = "2.0.0 del 7 marzo 2026 by Gabriele Battaglia (IZ4APU) & Stella (Gemini)"

    def __init__(self, nome_giocatore_umano):
        self.mazzo_completo = Mazzo().carte[:]
        self.mazzo = Mazzo()
        self.giocatore_umano = Giocatore(nome_giocatore_umano)
        self.giocatore_pc = Giocatore(generate_ai_name())
        self.briscola = None
        self.tavolo = []
        self.carte_uscite = set()
        self.primo_giocatore_del_match = None
        self.log_attivo = False
        self.prompt_attivo = True
        self.log_partita = []

    def _get_valore_comparativo(self, carta):
        return Mazzo.PUNTI_BRISCOLA.get(carta.valore, 0) * 10 + carta.valore

    def _log(self, messaggio):
        if self.log_attivo:
            self.log_partita.append(messaggio)

    def _decidi_primo_giocatore_match(self):
        print("\n--- Si decide chi inizia il match ---")
        mazzo_temp = Mazzo()
        mazzo_temp.mescola_mazzo()
        carta_umano = mazzo_temp.pesca(1)[0]
        print(f"{self.giocatore_umano.nome} hai pescato: {carta_umano.nome}")
        carta_pc = mazzo_temp.pesca(1)[0]
        print(f"{self.giocatore_pc.nome} ha pescato: {carta_pc.nome}")
        
        if self._get_valore_comparativo(carta_umano) >= self._get_valore_comparativo(carta_pc):
            self.primo_giocatore_del_match = self.giocatore_umano
            print(f"Hai la carta più alta, inizi tu la prima partita!")
        else:
            self.primo_giocatore_del_match = self.giocatore_pc
            print(f"{self.giocatore_pc.nome} ha la carta più alta, inizia lui.")
        print("-------------------------------------\n")
        time.sleep(.5)

    def _reset_e_prepara_partita(self):
        self.mazzo = Mazzo()
        self.mazzo.mescola_mazzo()
        self.giocatore_umano.mano, self.giocatore_umano.mazzetto = [], []
        self.giocatore_pc.mano, self.giocatore_pc.mazzetto = [], []
        self.carte_uscite = set()
        self.giocatore_umano.mano = self.mazzo.pesca(3)
        self.giocatore_pc.mano = self.mazzo.pesca(3)
        self.briscola = self.mazzo.pesca(1)[0]
        self.mazzo.carte.append(self.briscola)
        print(f"La carta Briscola è: {self.briscola.nome}")
        self._log(f"BRISCOLA {self.briscola.desc_breve}")

    def _stampa_prompt_giocatore(self):
        mano_estesa_str = "Tu hai: " + ". ".join([c.nome for c in self.giocatore_umano.mano]) + "."
        print(mano_estesa_str)
        if self.prompt_attivo:
            carte_rimaste = len(self.mazzo)
            briscola_breve = self.briscola.desc_breve
            tavolo_breve = self.tavolo[0].desc_breve if self.tavolo else "-"
            punti_tuoi = self.giocatore_umano.calcola_punteggio()
            punti_pc = self.giocatore_pc.calcola_punteggio()
            punti_str = f"{punti_tuoi}/{punti_pc}"
            mano_str = " ".join([c.desc_breve for c in self.giocatore_umano.mano])
            prompt = f"R{carte_rimaste} B{briscola_breve} T{tavolo_breve} P{punti_str} - C {mano_str} > "
        else:
            prompt = "> "

        while True:
            try:
                print(prompt, end="", flush=True)
                scelta = key()
                print(scelta)
                
                if scelta.lower() == 'q' or scelta == '\x1b':
                    conferma = input("\nSei sicuro di voler abbandonare il match? (s/n): ").lower().strip()
                    if conferma == 's':
                        return "FORFEIT"
                    else:
                        print("Abbandono annullato. Continua a giocare.")
                        continue

                scelta_idx = int(scelta) - 1
                if 0 <= scelta_idx < len(self.giocatore_umano.mano):
                    return self.giocatore_umano.mano.pop(scelta_idx)
                else:
                    print(f"\nScelta non valida. Inserisci un numero tra 1 e {len(self.giocatore_umano.mano)}")
            except (ValueError, IndexError):
                print("\nInput non valido. Premi il numero della carta che vuoi giocare, o 'q' per abbandonare.")

    def _determina_vincitore_mano(self, carta1, giocatore1, carta2, giocatore2):
        c1_briscola = carta1.seme_nome == self.briscola.seme_nome
        c2_briscola = carta2.seme_nome == self.briscola.seme_nome
        if c1_briscola and not c2_briscola:
            return giocatore1
        if not c1_briscola and c2_briscola:
            return giocatore2
        if c1_briscola and c2_briscola or carta1.seme_nome == carta2.seme_nome:
            return giocatore1 if self._get_valore_comparativo(carta1) > self._get_valore_comparativo(carta2) else giocatore2
        return giocatore1

    def gioca_partita(self, giocatore_di_mano):
        self._reset_e_prepara_partita()
        print(f"\n--- Inizia la partita! Il primo a giocare è {giocatore_di_mano.nome}. ---")
        self._log(f"INIZIO_PARTITA MANO_A {giocatore_di_mano.nome}")
        
        mano_n = 1
        while len(self.giocatore_umano.mazzetto) + len(self.giocatore_pc.mazzetto) < 40:
            print(f"\n--- Mano n.{mano_n} ---")
            self._log(f"\nMANO {mano_n}")

            mano_pc_log = " ".join([c.desc_breve for c in self.giocatore_pc.mano])
            self._log(f"MANO_IA {mano_pc_log}")
            print(f"{self.giocatore_pc.nome} ha {len(self.giocatore_pc.mano)} carte in mano.")
            
            self.tavolo = []
            giocatori = (self.giocatore_umano, self.giocatore_pc) if giocatore_di_mano == self.giocatore_umano else (self.giocatore_pc, self.giocatore_umano)
            
            for giocatore in giocatori:
                if giocatore == self.giocatore_umano:
                    carta = self._stampa_prompt_giocatore()
                else:
                    carta = IAPerfetta.scegli_carta(
                        self.briscola, 
                        self.tavolo, 
                        self.giocatore_pc.mano, 
                        self.mazzo_completo, 
                        self.carte_uscite, 
                        self.giocatore_pc.calcola_punteggio(), 
                        self.giocatore_umano.calcola_punteggio()
                    )
                    self.giocatore_pc.mano.remove(carta)
                
                if carta == "FORFEIT":
                    return "FORFEIT", 0, 0

                print(f"{giocatore.nome} gioca: {carta.nome}")
                self._log(f"GIOCA {giocatore.nome} {carta.desc_breve}")
                self.tavolo.append(carta)

            vincitore_mano = self._determina_vincitore_mano(self.tavolo[0], giocatori[0], self.tavolo[1], giocatori[1])
            punti_presi = sum(Mazzo.PUNTI_BRISCOLA.get(c.valore, 0) for c in self.tavolo)
            vincitore_mano.mazzetto.extend(self.tavolo)
            self.carte_uscite.update(self.tavolo)
            
            print(f"{vincitore_mano.nome} vince la mano e prende {punti_presi} punti.")
            self._log(f"PRENDE {vincitore_mano.nome} PUNTI {punti_presi}")

            if len(self.mazzo) > 0:
                perdente_mano = giocatori[1] if vincitore_mano == giocatori[0] else giocatori[0]
                vincitore_mano.mano.extend(self.mazzo.pesca(1))
                perdente_mano.mano.extend(self.mazzo.pesca(1))
            
            giocatore_di_mano = vincitore_mano
            mano_n += 1
        
        punti_umano = self.giocatore_umano.calcola_punteggio()
        punti_pc = self.giocatore_pc.calcola_punteggio()
        print("\n" + "="*40 + "\nPARTITA TERMINATA!\n" + "="*40)
        print(f"PUNTEGGIO PARTITA:\n   - {self.giocatore_umano.nome}: {punti_umano} punti\n   - {self.giocatore_pc.nome}: {punti_pc} punti")
        self._log(f"\nFINALE {self.giocatore_umano.nome} {punti_umano} - {self.giocatore_pc.nome} {punti_pc}")
        
        if punti_umano > 60:
            return (self.giocatore_umano, punti_umano, punti_pc)
        elif punti_umano == 60:
            return (None, punti_umano, punti_pc)
        else:
            return (self.giocatore_pc, punti_umano, punti_pc)