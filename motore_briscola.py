# Gabryscola, il motore delle regole: la partita, le mani e chi le vince.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 08/09/2026: mazzo di GBUtils con la briscola in testa perche' si pesca dalla
# coda, cervello nuovo alimentato dagli eventi della partita, messaggi alla
# seconda persona quando il soggetto e' chi gioca, moneta a parita' nel
# sorteggio, tasto singolo per l'abbandono, guida con il punto di domanda.

"""Le regole in movimento: una partita di briscola a due, mano per mano.

Il motore distribuisce, chiede la carta a chi gioca, la chiede al cervello
per il calcolatore, decide chi prende e fa pescare. Il cervello riceve ogni
evento visibile della partita, e mai la carta pescata dall'avversario, a
meno che non sia la briscola scoperta.
"""

import os
import random
import sys
import time

from GBUtils import key, manuale

from gestione_dati import generate_ai_name
from giocatore import Giocatore
from motore_ia import TEMPO_PREDEFINITO, Cervello
from regole import nuovo_mazzo, punti, vince_primo
from suoni import play_event
from version import AUTHOR, DATE, VERSION

FORFEIT = "FORFEIT"
GUIDA = "manuale.txt"
CARTE_IN_MANO = 3
CHIAVI_STATISTICHE = ("decisioni", "mondi", "tempo", "esatte")


class MotoreBriscola:
    VERSIONE = f"{VERSION} del {DATE}, di {AUTHOR}"

    def __init__(self, nome_giocatore_umano, tempo_riflessione=TEMPO_PREDEFINITO):
        self.mazzo_completo = nuovo_mazzo().carte[:]
        self.mazzo = nuovo_mazzo()
        self.giocatore_umano = Giocatore(nome_giocatore_umano)
        self.giocatore_pc = Giocatore(generate_ai_name())
        self.briscola = None
        self.tavolo = []
        self.primo_giocatore_del_match = None
        self.log_attivo = False
        self.prompt_attivo = True
        self.log_partita = []
        self.tempo_riflessione = tempo_riflessione
        self.ia = None
        self.match = None
        self.statistiche_ia = dict.fromkeys(CHIAVI_STATISTICHE, 0)

    @staticmethod
    def _valore_sorteggio(carta):
        return punti(carta) * 10 + carta.valore

    def _log(self, messaggio):
        if self.log_attivo:
            self.log_partita.append(messaggio)

    def _decidi_primo_giocatore_match(self):
        pc = self.giocatore_pc.nome
        print("Si decide chi inizia il match.")
        mazzo_temp = nuovo_mazzo()
        mazzo_temp.mescola_mazzo()
        carta_umano = mazzo_temp.pesca(1)[0]
        play_event("pesca_tu")
        print(f"Hai pescato: {carta_umano.nome}.")
        carta_pc = mazzo_temp.pesca(1)[0]
        play_event("pesca_pc")
        print(f"{pc} ha pescato: {carta_pc.nome}.")
        valore_umano = self._valore_sorteggio(carta_umano)
        valore_pc = self._valore_sorteggio(carta_pc)
        if valore_umano == valore_pc:
            play_event("moneta")
            print("Carte di pari valore: decide la moneta.")
            primo = random.choice([self.giocatore_umano, self.giocatore_pc])
        elif valore_umano > valore_pc:
            primo = self.giocatore_umano
        else:
            primo = self.giocatore_pc
        self.primo_giocatore_del_match = primo
        if primo is self.giocatore_umano:
            print("Inizi tu la prima partita.")
        else:
            print(f"Inizia {pc} la prima partita.")
        time.sleep(0.5)

    def _reset_e_prepara_partita(self):
        self.mazzo = nuovo_mazzo()
        play_event("mescola")
        self.mazzo.mescola_mazzo()
        self.giocatore_umano.mano, self.giocatore_umano.mazzetto = [], []
        self.giocatore_pc.mano, self.giocatore_pc.mazzetto = [], []
        self.giocatore_umano.mano = self.mazzo.pesca(CARTE_IN_MANO)
        self.giocatore_pc.mano = self.mazzo.pesca(CARTE_IN_MANO)
        self.briscola = self.mazzo.pesca(1)[0]
        # GBUtils pesca dalla coda: in testa la briscola esce per ultima.
        self.mazzo.carte.insert(0, self.briscola)
        play_event("briscola")
        print(f"La briscola è: {self.briscola.nome}.")
        self._log(f"BRISCOLA {self.briscola.desc_breve}")
        self.ia = Cervello(
            self.briscola, self.mazzo_completo, self.giocatore_pc.mano, tempo=self.tempo_riflessione
        )

    def _prompt(self):
        if not self.prompt_attivo:
            return "> "
        carte_rimaste = len(self.mazzo)
        tavolo_breve = self.tavolo[0].desc_breve if self.tavolo else "-"
        punti_tuoi = self.giocatore_umano.calcola_punteggio()
        punti_pc = self.giocatore_pc.calcola_punteggio()
        mano_breve = " ".join(c.desc_breve for c in self.giocatore_umano.mano)
        return f"R{carte_rimaste} B{self.briscola.desc_breve} T{tavolo_breve} P{punti_tuoi}/{punti_pc} - C {mano_breve} > "

    @staticmethod
    def _percorso_guida():
        """La guida sta accanto ai sorgenti, e dentro l'eseguibile quando e' compilato."""
        base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, GUIDA)

    def _mostra_guida(self):
        play_event("manuale")
        try:
            manuale(nf=self._percorso_guida(), nome="Guida di Gabryscola")
        except (OSError, ValueError) as e:
            print(f"Guida non disponibile: {e}")

    def _chiedi_carta(self):
        """La carta scelta da chi gioca, oppure FORFEIT se abbandona."""
        mano = self.giocatore_umano.mano
        print("Hai in mano: " + ". ".join(c.nome for c in mano) + ".")
        prompt = self._prompt()
        while True:
            print(prompt, end="", flush=True)
            scelta = key()
            print(scelta if scelta.isprintable() else "")
            if scelta.lower() == "q" or scelta == "\x1b":
                play_event("domanda")
                print("Abbandoni il match? Premi s per confermare, un altro tasto per continuare: ", end="", flush=True)
                conferma = key()
                print(conferma if conferma.isprintable() else "")
                if conferma.lower() == "s":
                    return FORFEIT
                play_event("annullato")
                print("Abbandono annullato, si continua.")
                continue
            if scelta in ("?", "h"):
                self._mostra_guida()
                continue
            if scelta.isdigit() and 1 <= int(scelta) <= len(mano):
                return mano.pop(int(scelta) - 1)
            play_event("errore")
            print(f"Tasto non valido: un numero da 1 a {len(mano)} gioca la carta, q abbandona, ? apre la guida.")

    def _annuncia_presa(self, vincitore, presi):
        if vincitore is self.giocatore_umano:
            play_event("presa_tu")
            print(f"Vinci la mano e prendi {presi} punti." if presi else "Vinci la mano, senza punti.")
        else:
            play_event("presa_pc")
            nome = self.giocatore_pc.nome
            print(f"{nome} vince la mano e prende {presi} punti." if presi else f"{nome} vince la mano, senza punti.")

    def _pesca(self, vincitore, perdente):
        for giocatore in (vincitore, perdente):
            carta = self.mazzo.pesca(1)[0]
            giocatore.mano.append(carta)
            e_briscola = carta == self.briscola
            if giocatore is self.giocatore_pc:
                self.ia.carta_pescata(carta, True)
                play_event("pesca_pc")
                if e_briscola:
                    print(f"{self.giocatore_pc.nome} pesca la briscola.")
            else:
                self.ia.carta_pescata(carta if e_briscola else None, False)
                play_event("pesca_tu")
                print(f"Peschi: {carta.nome}." + (" È la briscola." if e_briscola else ""))

    def _accumula_statistiche(self):
        for chiave in CHIAVI_STATISTICHE:
            self.statistiche_ia[chiave] += self.ia.statistiche[chiave]

    def gioca_partita(self, giocatore_di_mano):
        """Una partita intera. Restituisce vincitore, punti tuoi e punti del calcolatore."""
        self._reset_e_prepara_partita()
        umano, pc = self.giocatore_umano, self.giocatore_pc
        if giocatore_di_mano is umano:
            print("Inizia la partita: giochi per primo.")
        else:
            print(f"Inizia la partita: gioca per primo {pc.nome}.")
        self._log(f"INIZIO_PARTITA MANO_A {giocatore_di_mano.nome}")
        mano_n = 1
        while umano.mano:
            print(f"Mano {mano_n}.")
            play_event("nuovo_turno")
            self._log(f"MANO {mano_n}")
            self._log("MANO_IA " + " ".join(c.desc_breve for c in pc.mano))
            self.tavolo = []
            giocatori = (umano, pc) if giocatore_di_mano is umano else (pc, umano)
            for giocatore in giocatori:
                tavolo_prima = list(self.tavolo)
                if giocatore is umano:
                    carta = self._chiedi_carta()
                    if carta == FORFEIT:
                        return FORFEIT, 0, 0
                    print(f"Giochi: {carta.nome}.")
                    play_event("carta_tu")
                else:
                    carta = self.ia.scegli(
                        self.tavolo, pc.mano, pc.calcola_punteggio(), umano.calcola_punteggio(), len(self.mazzo), self.match
                    )
                    pc.mano.remove(carta)
                    print(f"{pc.nome} gioca: {carta.nome}.")
                    play_event("carta_pc")
                self._log(f"GIOCA {giocatore.nome} {carta.desc_breve}")
                self.tavolo.append(carta)
                self.ia.carta_giocata(carta, giocatore is pc, tavolo_prima)
            vincitore = giocatori[0] if vince_primo(self.tavolo[0], self.tavolo[1], self.briscola.seme_nome) else giocatori[1]
            perdente = giocatori[1] if vincitore is giocatori[0] else giocatori[0]
            presi = sum(punti(c) for c in self.tavolo)
            vincitore.mazzetto.extend(self.tavolo)
            self._annuncia_presa(vincitore, presi)
            self._log(f"PRENDE {vincitore.nome} PUNTI {presi}")
            if len(self.mazzo) > 0:
                self._pesca(vincitore, perdente)
            giocatore_di_mano = vincitore
            mano_n += 1
        self._accumula_statistiche()
        punti_umano = umano.calcola_punteggio()
        punti_pc = pc.calcola_punteggio()
        print(f"Partita terminata: hai {punti_umano} punti, {pc.nome} {punti_pc}.")
        self._log(f"FINALE {umano.nome} {punti_umano} {pc.nome} {punti_pc}")
        if punti_umano > punti_pc:
            return umano, punti_umano, punti_pc
        if punti_umano == punti_pc:
            return None, punti_umano, punti_pc
        return pc, punti_umano, punti_pc
