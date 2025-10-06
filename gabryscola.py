# GABRYSCOLA - by Gabriele Battaglia and Gemini 2.5 Pro
# Data di concepimento 1 ottobre 2025

import random, datetime
import time
import json
import math
from datetime import date
from collections import namedtuple

# --- Costanti e Funzioni Globali ---
CLASSIFICA_FILE = "briscola_charts.json"
CLASSIFICA_MAX_VOCI = 30
LOG_FILE = "briscola_log.txt"

def generate_ai_name():
    consonanti = "BCDFGHJKLMNPQRSTVWXYZ"; vocali = "AEIOU"
    c1 = random.choice(consonanti); c2 = random.choice(consonanti); c3 = random.choice(consonanti)
    v1 = random.choice(vocali); v2 = random.choice(vocali); v3 = random.choice(vocali)
    random_part = f"{c1}{v1}{c2}{v2}{c3}{v3}"; formatted_part = random_part.lower().title()
    return f"IA-{formatted_part}"

# --- Funzioni di Gestione Classifica ---
def load_classifica():
    try:
        with open(CLASSIFICA_FILE, 'r') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return []

def save_classifica(classifica):
    with open(CLASSIFICA_FILE, 'w') as f: json.dump(classifica, f, indent=4)

def update_and_display_classifica(classifica, winner_name, wins, ties, losses, total_points):
    new_entry = {
        "nome": winner_name, "wins": wins, "ties": ties, "losses": losses,
        "punti_totali": total_points, "data": date.today().strftime("%d/%m/%Y")
    }
    classifica.append(new_entry)
    
    def get_sort_key(entry):
        w = entry.get('wins', 0); t = entry.get('ties', 0); l = entry.get('losses', 0)
        p = entry.get('punti_totali', 0)
        match_points = (w * 1.0) + (t * 0.5)
        return (match_points, w, -l, p)

    classifica.sort(key=get_sort_key, reverse=True)
    classifica = classifica[:CLASSIFICA_MAX_VOCI]
    
    print("\n" + "="*72); print(" " * 30 + "CLASSIFICA" + " " * 32); print("="*72)
    print(f"{'Pos.':<5}{'Nome':<20}{'Risultato (V-P-S)':<20}{'Punti Tot.':<12}{'Data'}"); print("-" * 72)
    for i, entry in enumerate(classifica, 1):
        pos = f"{i}."
        nome = entry.get('nome', 'N/D')
        w = entry.get('wins', 0); t = entry.get('ties', 0); l = entry.get('losses', 0)
        match_score_str = f"{w}-{t}-{l}"
        punti = entry.get('punti_totali', 0)
        data_partita = entry.get('data', 'N/D')
        print(f"{pos:<5}{nome:<20}{match_score_str:<20}{punti:<12}{data_partita}")
    print("-" * 72)
    return classifica

class Mazzo:
    import random; from collections import namedtuple
    Carta = namedtuple("Carta", ["id", "nome", "valore", "seme_nome", "seme_id", "desc_breve"])
    PUNTI_BRISCOLA = {1: 11, 3: 10, 10: 4, 9: 3, 8: 2}
    _SEMI_ITALIANI = ["Bastoni", "Spade", "Coppe", "Denari"]
    _VALORI_ITALIANI = [("Asso", 1), ('2', 2), ('3', 3), ('4', 4), ('5', 5), ('6', 6), ('7', 7), ("Fante", 8), ("Cavallo", 9), ("Re", 10)]
    _VALORI_DESCRIZIONE = {1: 'A', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: '0'}
    _SEMI_DESCRIZIONE = {"Bastoni": 'B', "Spade": 'S', "Coppe": 'C', "Denari": 'D'}
    def __init__(self): self.carte = []; self._costruisci_mazzo()
    def _costruisci_mazzo(self):
        self.carte = []
        for id_seme, nome_seme in enumerate(self._SEMI_ITALIANI, 1):
            for nome_valore, valore_num in self._VALORI_ITALIANI:
                desc_val = self._VALORI_DESCRIZIONE.get(valore_num, '?'); desc_seme = self._SEMI_DESCRIZIONE.get(nome_seme, '?')
                desc_breve = f"{desc_val}{desc_seme}"; nome_completo = f"{nome_valore} di {nome_seme}"
                self.carte.append(self.Carta(id=valore_num*10+id_seme, nome=nome_completo, valore=valore_num, seme_nome=nome_seme, seme_id=id_seme, desc_breve=desc_breve))
    def mescola_mazzo(self): self.random.shuffle(self.carte)
    def pesca(self, quante=1): return [self.carte.pop(0) for _ in range(min(quante, len(self.carte)))]
    def __len__(self): return len(self.carte)

class Giocatore:
    def __init__(self, nome): self.nome = nome; self.mano = []; self.mazzetto = []
    def calcola_punteggio(self): return sum(Mazzo.PUNTI_BRISCOLA.get(carta.valore, 0) for carta in self.mazzetto)

class Briscola:
    VERSIONE = "1.1.3 del 5 ottobre 2025 by Gabriele Battaglia (IZ4APU) & AI"

    def __init__(self, nome_giocatore_umano):
        self.mazzo_completo = Mazzo().carte[:]
        self.mazzo = Mazzo()
        self.giocatore_umano = Giocatore(nome_giocatore_umano)
        self.giocatore_pc = Giocatore(generate_ai_name())
        self.briscola = None; self.tavolo = []; self.carte_uscite = set()
        self.primo_giocatore_del_match = None
        self.log_attivo = False
        self.prompt_attivo = True
        self.log_partita = []
    def _get_valore_comparativo(self, carta): return Mazzo.PUNTI_BRISCOLA.get(carta.valore, 0) * 10 + carta.valore

    def _log(self, messaggio):
        """Se la modalità log è attiva, aggiunge un messaggio alla lista."""
        if self.log_attivo:
            self.log_partita.append(messaggio)
    def _decidi_primo_giocatore_match(self):
        print("\n--- Si decide chi inizia il match ---")
        mazzo_temp = Mazzo(); mazzo_temp.mescola_mazzo()
        carta_umano = mazzo_temp.pesca(1)[0]; print(f"{self.giocatore_umano.nome} hai pescato: {carta_umano.nome}")
        carta_pc = mazzo_temp.pesca(1)[0]; print(f"{self.giocatore_pc.nome} ha pescato: {carta_pc.nome}")
        if self._get_valore_comparativo(carta_umano) >= self._get_valore_comparativo(carta_pc):
            self.primo_giocatore_del_match = self.giocatore_umano; print(f"Hai la carta più alta, inizi tu la prima partita!")
        else:
            self.primo_giocatore_del_match = self.giocatore_pc; print(f"{self.giocatore_pc.nome} ha la carta più alta, inizia lui.")
        print("-------------------------------------\n"); time.sleep(.5)

    def _reset_e_prepara_partita(self):
        self.mazzo = Mazzo(); self.mazzo.mescola_mazzo()
        self.giocatore_umano.mano, self.giocatore_umano.mazzetto = [], []
        self.giocatore_pc.mano, self.giocatore_pc.mazzetto = [], []
        self.carte_uscite = set()
        self.giocatore_umano.mano = self.mazzo.pesca(3); self.giocatore_pc.mano = self.mazzo.pesca(3)
        self.briscola = self.mazzo.pesca(1)[0]; self.mazzo.carte.append(self.briscola)
        print(f"La carta Briscola è: {self.briscola.nome}")
        self._log(f"BRISCOLA {self.briscola.desc_breve}") # <-- AGGIUNGI QUESTA RIGA

    def _stampa_prompt_giocatore(self):
        mano_estesa_str = "Tu hai: "+". ".join([c.nome for c in self.giocatore_umano.mano]) + "."
        print(mano_estesa_str)
        if self.prompt_attivo:
            carte_rimaste = len(self.mazzo); briscola_breve = self.briscola.desc_breve
            tavolo_breve = self.tavolo[0].desc_breve if self.tavolo else "-"
            punti_tuoi = self.giocatore_umano.calcola_punteggio(); punti_pc = self.giocatore_pc.calcola_punteggio()
            punti_str = f"{punti_tuoi}/{punti_pc}"; mano_str = " ".join([c.desc_breve for c in self.giocatore_umano.mano])
            prompt = f"R{carte_rimaste} B{briscola_breve} T{tavolo_breve} P{punti_str} - C {mano_str} > "
        else:
            prompt = "> " # Se noprompt è attivo, mostra solo un cursore

        while True:
            try:
                scelta = input(prompt)
                
                if scelta.strip() == "":
                    conferma = input("Sei sicuro di voler abbandonare il match? (s/n): ").lower().strip()
                    if conferma == 's':
                        return "FORFEIT"
                    else:
                        print("Abbandono annullato. Continua a giocare.")
                        # Se noprompt è attivo, ristampa il cursore per chiarezza
                        if not self.prompt_attivo: print("> ", end="")
                        continue

                scelta_idx = int(scelta) - 1
                if 0 <= scelta_idx < len(self.giocatore_umano.mano): return self.giocatore_umano.mano.pop(scelta_idx)
                else: print(f"Scelta non valida. Inserisci un numero tra 1 e {len(self.giocatore_umano.mano)}")
            except (ValueError, IndexError): print("Input non valido. Inserisci il numero della carta che vuoi giocare.")
    def _determina_vincitore_mano(self, carta1, giocatore1, carta2, giocatore2):
        c1_briscola = carta1.seme_nome == self.briscola.seme_nome; c2_briscola = carta2.seme_nome == self.briscola.seme_nome
        if c1_briscola and not c2_briscola: return giocatore1
        if not c1_briscola and c2_briscola: return giocatore2
        if c1_briscola and c2_briscola or carta1.seme_nome == carta2.seme_nome:
            return giocatore1 if self._get_valore_comparativo(carta1) > self._get_valore_comparativo(carta2) else giocatore2
        return giocatore1
    
    def _scelta_computer_maestro(self):
        mano_pc = self.giocatore_pc.mano; is_briscola = lambda c: c.seme_nome == self.briscola.seme_nome; punti_carta = lambda c: Mazzo.PUNTI_BRISCOLA.get(c.valore, 0)
        if self.tavolo:
            carta_avversario = self.tavolo[0]; mosse_valutate = []
            for carta_da_giocare in mano_pc:
                vincitore = self._determina_vincitore_mano(carta_avversario, self.giocatore_umano, carta_da_giocare, self.giocatore_pc)
                punti_mano = punti_carta(carta_avversario) + punti_carta(carta_da_giocare)
                valore = punti_mano if vincitore == self.giocatore_pc else -punti_mano
                if vincitore == self.giocatore_pc:
                    if is_briscola(carta_da_giocare) and not is_briscola(carta_avversario) and punti_mano < 10: valore -= 20
                else: valore -= punti_carta(carta_da_giocare) * 5
                mosse_valutate.append((valore, carta_da_giocare))
            _, carta_scelta = max(mosse_valutate, key=lambda x: x[0])
        else:
            carte_incognite = list(set(self.mazzo_completo) - self.carte_uscite - set(mano_pc)); num_carte_incognite = len(carte_incognite)
            briscole_incognite = [c for c in carte_incognite if is_briscola(c)]; mosse_valutate = []
            for carta_da_giocare in mano_pc:
                punti_da_rischiare = punti_carta(carta_da_giocare); valore_atteso_punti = 0; vittorie_stimate = 0
                if num_carte_incognite > 0:
                    for carta_avv_potenziale in carte_incognite:
                        vincitore = self._determina_vincitore_mano(carta_da_giocare, self.giocatore_pc, carta_avv_potenziale, self.giocatore_umano)
                        punti_mano = punti_da_rischiare + punti_carta(carta_avv_potenziale)
                        if vincitore == self.giocatore_pc: valore_atteso_punti += punti_mano; vittorie_stimate += 1
                        else: valore_atteso_punti -= punti_mano
                    valore_medio_punti = valore_atteso_punti / num_carte_incognite; prob_vittoria = vittorie_stimate / num_carte_incognite
                else: valore_medio_punti, prob_vittoria = punti_da_rischiare, 1.0
                rischio = 0
                if punti_da_rischiare > 0 and not is_briscola(carta_da_giocare) and num_carte_incognite > 0:
                    prob_di_essere_briscolata = len(briscole_incognite) / num_carte_incognite
                    rischio = prob_di_essere_briscolata * punti_da_rischiare * 30
                costo_opportunita = 0
                if is_briscola(carta_da_giocare) and punti_da_rischiare > 3: costo_opportunita = (punti_da_rischiare + 5) * (len(self.mazzo) / 10)
                VANTAGGIO_MANO_SUCCESSIVA = 1.5
                valore_tattico = (1 - prob_vittoria) * VANTAGGIO_MANO_SUCCESSIVA - prob_vittoria * VANTAGGIO_MANO_SUCCESSIVA
                valore_finale = valore_medio_punti - rischio - costo_opportunita + valore_tattico
                mosse_valutate.append((valore_finale, carta_da_giocare))
            _, carta_scelta = max(mosse_valutate, key=lambda x: x[0])
        mano_pc.remove(carta_scelta)
        return carta_scelta

    # Sostituisci interamente la funzione gioca_partita

    def gioca_partita(self, giocatore_di_mano):
        self._reset_e_prepara_partita()
        print(f"\n--- Inizia la partita! Il primo a giocare è {giocatore_di_mano.nome}. ---")
        self._log(f"INIZIO_PARTITA MANO_A {giocatore_di_mano.nome}")
        
        mano_n = 1
        while len(self.giocatore_umano.mazzetto) + len(self.giocatore_pc.mazzetto) < 40:
            print(f"\n--- Mano n.{mano_n} ---")
            self._log(f"\nMANO {mano_n}")

            # MODIFICA per LOGON: rendi la mano IA sempre visibile nel log
            mano_pc_log = " ".join([c.desc_breve for c in self.giocatore_pc.mano])
            self._log(f"MANO_IA {mano_pc_log}")
            
            # Stampa a video lo stato normale (mano coperta)
            print(f"{self.giocatore_pc.nome} ha {len(self.giocatore_pc.mano)} carte in mano.")
            
            self.tavolo = []
            giocatori = (self.giocatore_umano, self.giocatore_pc) if giocatore_di_mano == self.giocatore_umano else (self.giocatore_pc, self.giocatore_umano)
            
            for giocatore in giocatori:
                carta = self._stampa_prompt_giocatore() if giocatore == self.giocatore_umano else self._scelta_computer_maestro()
                
                if carta == "FORFEIT": return "FORFEIT", 0, 0

                print(f"{giocatore.nome} gioca: {carta.nome}")
                self._log(f"GIOCA {giocatore.nome} {carta.desc_breve}")
                self.tavolo.append(carta)

            vincitore_mano = self._determina_vincitore_mano(self.tavolo[0], giocatori[0], self.tavolo[1], giocatori[1])
            punti_presi = sum(Mazzo.PUNTI_BRISCOLA.get(c.valore, 0) for c in self.tavolo)
            vincitore_mano.mazzetto.extend(self.tavolo); self.carte_uscite.update(self.tavolo)
            
            print(f"{vincitore_mano.nome} vince la mano e prende {punti_presi} punti.")
            self._log(f"PRENDE {vincitore_mano.nome} PUNTI {punti_presi}")

            if len(self.mazzo) > 0:
                perdente_mano = giocatori[1] if vincitore_mano == giocatori[0] else giocatori[0]
                vincitore_mano.mano.extend(self.mazzo.pesca(1)); perdente_mano.mano.extend(self.mazzo.pesca(1))
            
            giocatore_di_mano = vincitore_mano
            mano_n += 1
        
        punti_umano = self.giocatore_umano.calcola_punteggio(); punti_pc = self.giocatore_pc.calcola_punteggio()
        print("\n" + "="*40 + "\nPARTITA TERMINATA!\n" + "="*40); print(f"PUNTEGGIO PARTITA:\n   - {self.giocatore_umano.nome}: {punti_umano} punti\n   - {self.giocatore_pc.nome}: {punti_pc} punti")
        self._log(f"\nFINALE {self.giocatore_umano.nome} {punti_umano} - {self.giocatore_pc.nome} {punti_pc}")
        
        if punti_umano > 60: return (self.giocatore_umano, punti_umano, punti_pc)
        elif punti_umano == 60: return (None, punti_umano, punti_pc)
        else: return (self.giocatore_pc, punti_umano, punti_pc)
    def _stampa_riepilogo_match(self, risultati, punti_totali, numero_partite_match, partite_giocate):
        partite_rimanenti = numero_partite_match - partite_giocate
        if partite_rimanenti <= 0: return
        score_umano = risultati[self.giocatore_umano.nome]; score_pc = risultati[self.giocatore_pc.nome]
        punti_match_umano = (score_umano['wins'] * 1.0) + (score_umano['ties'] * 0.5)
        punti_match_pc = (score_pc['wins'] * 1.0) + (score_pc['ties'] * 0.5)
        print("\n" + "--- Riepilogo Strategico Match ---"); print(f"Partite giocate: {partite_giocate} di {numero_partite_match}. Partite rimanenti: {partite_rimanenti}.")
        punti_target_vittoria = (numero_partite_match / 2.0) + 0.5
        punti_mancanti_umano = punti_target_vittoria - punti_match_umano
        print(f"\nSituazione per {self.giocatore_umano.nome} (Punti Match: {punti_match_umano}):")
        if punti_mancanti_umano <= 0: print("  Sei in una posizione di forte vantaggio. Mantieni la concentrazione!")
        else:
            vittorie_necessarie = math.ceil(punti_mancanti_umano)
            if vittorie_necessarie > partite_rimanenti: print("  La rimonta è matematicamente impossibile. Il match è perso.")
            elif vittorie_necessarie == partite_rimanenti: print(f"  Situazione critica: devi vincerle tutte! Ti servono {vittorie_necessarie} vittorie su {partite_rimanenti} partite.")
            else: print(f"  Per vincere ti servono ancora {punti_mancanti_umano} punti. Un possibile percorso è vincere {vittorie_necessarie} delle prossime {partite_rimanenti} partite.")
        punti_mancanti_pc = punti_target_vittoria - punti_match_pc
        print(f"Situazione per {self.giocatore_pc.nome} (Punti Match: {punti_match_pc}):")
        if punti_mancanti_pc <= 0: print("  È in vantaggio. Bisogna attaccare per recuperare.")
        else:
            vittorie_necessarie_pc = math.ceil(punti_mancanti_pc)
            if vittorie_necessarie_pc > partite_rimanenti: print("  La sua rimonta è matematicamente impossibile.")
            else: print(f"  Gli servono ancora {punti_mancanti_pc} punti. Deve vincere almeno {vittorie_necessarie_pc} delle prossime {partite_rimanenti} partite.")
        print("------------------------------------")

    def avvia_match(self, numero_partite_match):
        print(f"Benvenuto a Gabryscola v{self.VERSIONE}"); print(f"Oggi {self.giocatore_umano.nome} sfida {self.giocatore_pc.nome} in un match al meglio di {numero_partite_match} partite!")
        self._decidi_primo_giocatore_match()
        risultati = {self.giocatore_umano.nome: {'wins': 0, 'ties': 0, 'losses': 0}, self.giocatore_pc.nome: {'wins': 0, 'ties': 0, 'losses': 0}}
        punti_totali = {self.giocatore_umano.nome: 0, self.giocatore_pc.nome: 0}
        giocatore_di_mano_corrente = self.primo_giocatore_del_match
        
        for i in range(numero_partite_match):
            print("\n" + "#"*50); print(f"#{'':<19} PARTITA {i+1} {'':<19}#"); print("#"*50)
            
            vincitore_partita, punti_u, punti_pc = self.gioca_partita(giocatore_di_mano_corrente)
            
            # NUOVA FUNZIONALITÀ: Gestisce l'abbandono
            if vincitore_partita == "FORFEIT":
                print("\nMatch abbandonato dall'utente.")
                risultati[self.giocatore_pc.nome]['wins'] = numero_partite_match # Assegna la vittoria a tavolino all'IA
                break

            punti_totali[self.giocatore_umano.nome] += punti_u; punti_totali[self.giocatore_pc.nome] += punti_pc
            if vincitore_partita:
                vincitore_nome = vincitore_partita.nome
                perdente_nome = self.giocatore_pc.nome if vincitore_partita == self.giocatore_umano else self.giocatore_umano.nome
                risultati[vincitore_nome]['wins'] += 1; risultati[perdente_nome]['losses'] += 1
                print(f"\n>> {vincitore_nome} vince la partita {i+1}! <<")
            else:
                risultati[self.giocatore_umano.nome]['ties'] += 1; risultati[self.giocatore_pc.nome]['ties'] += 1
                print("\n>> La partita è finita in pareggio! <<")

            score_umano = risultati[self.giocatore_umano.nome]; score_pc = risultati[self.giocatore_pc.nome]
            print(f"Risultato parziale (V-P-S): {self.giocatore_umano.nome} {score_umano['wins']}-{score_umano['ties']}-{score_umano['losses']} vs {self.giocatore_pc.nome} {score_pc['wins']}-{score_pc['ties']}-{score_pc['losses']}")
            
            self._stampa_riepilogo_match(risultati, punti_totali, numero_partite_match, i + 1)
            
            punti_match_umano = (score_umano['wins'] * 1.0) + (score_umano['ties'] * 0.5)
            punti_match_pc = (score_pc['wins'] * 1.0) + (score_pc['ties'] * 0.5)
            partite_rimanenti = numero_partite_match - (i + 1)

            # FIX BUG: La logica di fine anticipata ora è corretta e coerente con il riepilogo
            punti_target_vittoria = (numero_partite_match / 2.0) + 0.5
            if punti_match_umano >= punti_target_vittoria or punti_match_pc >= punti_target_vittoria:
                 if abs(punti_match_umano - punti_match_pc) > partite_rimanenti:
                    print("\nIl match termina in anticipo: la rimonta è matematicamente impossibile.")
                    break

            giocatore_di_mano_corrente = self.giocatore_pc if giocatore_di_mano_corrente == self.giocatore_umano else self.giocatore_umano
            time.sleep(1.5)

        print("\n" + "="*40 + "\nMATCH TERMINATO!\n" + "="*40)
        score_umano = risultati[self.giocatore_umano.nome]; score_pc = risultati[self.giocatore_pc.nome]
        punti_match_umano = (score_umano['wins'] * 1.0) + (score_umano['ties'] * 0.5)
        punti_match_pc = (score_pc['wins'] * 1.0) + (score_pc['ties'] * 0.5)
        vincitore_match = None; motivo_vittoria = ""
        if punti_match_umano > punti_match_pc: vincitore_match = self.giocatore_umano
        elif punti_match_pc > punti_match_umano: vincitore_match = self.giocatore_pc
        else:
            punti_u = punti_totali[self.giocatore_umano.nome]; punti_pc = punti_totali[self.giocatore_pc.nome]
            print(f"Il match è in parità di punteggio ({punti_match_umano}-{punti_match_pc}). Si decide ai punti totali ({punti_u}-{punti_pc}).")
            if punti_u > punti_pc: vincitore_match = self.giocatore_umano; motivo_vittoria = " (vittoria ai punti)"
            elif punti_pc > punti_u: vincitore_match = self.giocatore_pc; motivo_vittoria = " (vittoria ai punti)"
        if vincitore_match:
            print(f"🎉🎉🎉 {vincitore_match.nome.upper()} HAI VINTO IL MATCH{motivo_vittoria}! 🎉🎉🎉")
            res_vincitore = risultati[vincitore_match.nome]
            classifica = load_classifica()
            classifica_aggiornata = update_and_display_classifica(classifica, vincitore_match.nome, res_vincitore['wins'], res_vincitore['ties'], res_vincitore['losses'], punti_totali[vincitore_match.nome])
            save_classifica(classifica_aggiornata)
            print("\nClassifica salvata. Grazie per aver giocato!")
        else: print("Incredibile! Il match è finito in PATTA ASSOLUTA, anche nei punti totali!")

# Sostituisci l'intero blocco if __name__ == "__main__" con questo

if __name__ == "__main__":
    log_enabled = False
    prompt_enabled = True
    nome_giocatore = ""

    print(f"Gabryscola v{Briscola.VERSIONE}")
    print("Digita 'logon' per attivare la modalità di debug o 'noprompt' per nascondere i prompt.")

    while not nome_giocatore:
        nome_input = input("Inserisci il tuo nome per la sfida: ").strip()
        
        if nome_input.lower() == 'logon':
            log_enabled = True
            print(">>> Modalità LOG attivata. I dati della partita verranno salvati. Reinserisci il tuo nome. <<<")
            continue
        elif nome_input.lower() == 'noprompt':
            prompt_enabled = False
            print(">>> Modalità NOPROMPT attivata. I prompt verranno nascosti. Reinserisci il tuo nome. <<<")
            continue
        
        if not nome_input:
            print("Il nome non può essere vuoto. Riprova.")
        else:
            nome_giocatore = nome_input.title()

    numero_partite = 0
    while True:
        try:
            num_input = input("Match al meglio di quante partite? (1-11): ").strip()
            numero_partite = int(num_input)
            if 1 <= numero_partite <= 11: break
            else: print("Per favore, inserisci un numero da 1 a 11.")
        except ValueError: print("Input non valido. Inserisci un numero.")
            
    gioco = Briscola(nome_giocatore_umano=nome_giocatore)
    gioco.log_attivo = log_enabled
    gioco.prompt_attivo = prompt_enabled

    gioco.avvia_match(numero_partite_match=numero_partite)
    
    # RIPRISTINATO il salvataggio del log qui, alla fine del match
    if gioco.log_attivo:
        timestamp_match = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_file = f"log_{gioco.giocatore_umano.nome}_{timestamp_match}.txt"
        with open(nome_file, 'w', encoding='utf-8') as f:
            f.write(f"Log Match del {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("="*40 + "\n")
            f.write('\n'.join(gioco.log_partita))
        print(f"\nLog del match salvato nel file: {nome_file}")

    input("\nPremi Invio per uscire...")