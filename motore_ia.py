# Gabryscola, il cervello del calcolatore: conoscenza esatta, inferenza e ricerca.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 08/09/2026: riscritto da zero nella revisione 1 del refactoring generale.
# Sostituisce ia_perfetta.py, che aveva euristiche a pesi fissi e un tracker
# con una deduzione falsa.

"""Il motore decisionale di Gabryscola.

Il calcolatore sa esattamente cio' che sa il suo avversario: le carte
uscite, la briscola scoperta in fondo al mazzo, le carte che ha pescato. Non
guarda mai la mano dell'altro. Su questa conoscenza tiene la distribuzione
di probabilita' di tutte le mani che l'avversario puo' avere, aggiornata a
ogni carta che vede giocare e a ogni pescata: con le sole deduzioni certe,
piu', se attiva, l'inferenza sul comportamento razionale, che abbassa il
peso delle mani in cui la carta giocata sarebbe stata una scelta cattiva.
Per decidere campiona molti mondi completi coerenti con la conoscenza,
cioe' mano avversaria e ordine del mazzo, risolve ciascuno con minimax e
potatura alfa beta contro un avversario che gioca perfettamente, e sceglie
la carta che massimizza l'utilita' attesa: la probabilita' di vincere la
partita, pesata dallo stato del match, e in subordine i punti. Nelle ultime
cinque mani la ricerca arriva in fondo, e dalle quattro carte nel mazzo in
giu' i mondi possibili si enumerano tutti, quindi il gioco e' esatto. Prima
la ricerca si ferma a una profondita' data e stima il resto con una
valutazione statica; se la passata ha usato poco del tempo di riflessione
se ne fa una piu' profonda sugli stessi mondi, e il numero di mondi
esaminati lo decide il tempo.
Le carte qui dentro sono numeri da 0 a 39: seme per dieci piu' valore meno
uno. Punti, forze e prese sono tabelle precalcolate.
"""

import gc
import math
import random
import time
from functools import cache
from itertools import combinations, permutations

from regole import FORZA, PUNTI_BRISCOLA, PUNTI_PER_VINCERE, PUNTI_TOTALI

N_CARTE = 40
TUTTE = tuple(range(N_CARTE))
PUNTI = tuple(PUNTI_BRISCOLA.get(i % 10 + 1, 0) for i in range(N_CARTE))
FORZE = tuple(FORZA[i % 10 + 1] for i in range(N_CARTE))
SEMI = tuple(i // 10 for i in range(N_CARTE))

TEMPO_PREDEFINITO = 2.0
MONDI_MINIMI = 8
MONDI_MASSIMI = 400
# Se una passata ha usato meno di questa frazione del tempo, se ne tenta una
# piu' profonda, che vale solo se arriva ad almeno tanti mondi. Con un
# decimo di secondo per carta il motore ha usato in media meno di meta' del
# tempo con la soglia a tre decimi: a meta' lo sfrutta quasi tutto.
FRAZIONE_PER_APPROFONDIRE = 0.5
MONDI_MINIMI_PROFONDI = 40
# Sotto questo numero di mondi possibili si enumerano tutti, in ordine casuale.
MONDI_ENUMERABILI = 150
# Inferenza sul comportamento: quanto pesa un punto di utilita' persa, e il
# peso sotto cui nessuna mano scende per il solo comportamento.
BETA_INFERENZA = 0.2
PESO_MINIMO = 0.02
# Valutazione statica all'orizzonte della ricerca.
PESO_FORZA = 0.035
PESO_MANO = 0.02
# Incertezza della stima, in punti, per ogni mano oltre l'orizzonte.
INCERTEZZA_BASE = 1.5
INCERTEZZA_PER_MANO = 1.2

_TABELLE_PRESE = {}


def indice(carta):
    """Il numero da 0 a 39 di una Carta di GBUtils."""
    return (carta.seme_id - 1) * 10 + carta.valore - 1


def tabella_prese(seme_briscola):
    """batte[a][b] e' vero se a, giocata per prima, vince la mano su b."""
    tabella = _TABELLE_PRESE.get(seme_briscola)
    if tabella is None:
        tabella = []
        for a in TUTTE:
            riga = []
            for b in TUTTE:
                a_briscola = SEMI[a] == seme_briscola
                b_briscola = SEMI[b] == seme_briscola
                if a_briscola != b_briscola:
                    riga.append(a_briscola)
                elif SEMI[a] == SEMI[b]:
                    riga.append(FORZE[a] > FORZE[b])
                else:
                    riga.append(True)
            tabella.append(tuple(riga))
        tabella = tuple(tabella)
        _TABELLE_PRESE[seme_briscola] = tabella
    return tabella


# --- Il peso del match ---


@cache
def _prob_vittoria_match(partite_rimaste, distacco, spareggio):
    """Probabilita' di vincere il match con partite rimaste alla pari.

    distacco e' vittorie del calcolatore meno quelle dell'avversario, in
    mezzi punti; spareggio e' la probabilita' di vincere lo spareggio sui
    punti totali se il match finisse in parita'.
    """
    if partite_rimaste == 0:
        if distacco > 0:
            return 1.0
        if distacco < 0:
            return 0.0
        return spareggio
    return 0.5 * _prob_vittoria_match(partite_rimaste - 1, distacco + 2, spareggio) + 0.5 * _prob_vittoria_match(
        partite_rimaste - 1, distacco - 2, spareggio
    )


def utilita_punti(match=None):
    """Utilita' di ogni punteggio finale del calcolatore, da 0 a 120.

    Senza match: uno per la vittoria, mezzo per la patta, zero per la
    sconfitta. Con il match, che e' un dizionario con partite, vinte_pc,
    vinte_avv, patte, punti_pc e punti_avv, e' la probabilita' di vincere
    il match dopo questa partita, spareggio sui punti totali compreso.
    """
    utilita = []
    for punti in range(PUNTI_TOTALI + 1):
        if punti >= PUNTI_PER_VINCERE:
            esito = 1.0
        elif punti * 2 == PUNTI_TOTALI:
            esito = 0.5
        else:
            esito = 0.0
        if match is None:
            utilita.append(esito)
            continue
        giocate = match["vinte_pc"] + match["vinte_avv"] + match["patte"]
        rimaste = max(0, match["partite"] - giocate - 1)
        distacco = 2 * (match["vinte_pc"] - match["vinte_avv"]) + int(4 * esito) - 2
        margine = match["punti_pc"] - match["punti_avv"] + 2 * punti - PUNTI_TOTALI
        spareggio = 1.0 if margine > 0 else (0.0 if margine < 0 else 0.5)
        utilita.append(_prob_vittoria_match(rimaste, distacco, spareggio))
    return utilita


def _sfuma(utilita, incertezza):
    """Media l'utilita' con una campana normale larga incertezza punti."""
    if incertezza <= 0:
        return list(utilita)
    raggio = int(3 * incertezza) + 1
    pesi = [math.exp(-0.5 * (k / incertezza) ** 2) for k in range(-raggio, raggio + 1)]
    n = len(utilita)
    sfumata = []
    for v in range(n):
        somma = peso = 0.0
        for k, w in zip(range(-raggio, raggio + 1), pesi, strict=True):
            u = v + k
            if 0 <= u < n:
                somma += w * utilita[u]
                peso += w
        sfumata.append(somma / peso)
    return sfumata


def _interpola(tabella, x):
    if x <= 0:
        return tabella[0]
    ultimo = len(tabella) - 1
    if x >= ultimo:
        return tabella[ultimo]
    base = int(x)
    frazione = x - base
    return tabella[base] * (1 - frazione) + tabella[base + 1] * frazione


# --- La conoscenza ---


class Conoscenza:
    """Cio' che il calcolatore sa, e la distribuzione della mano avversaria.

    Le mani sono tuple ordinate di carte, con un peso ciascuna. All'inizio
    tutte le terne di carte non viste hanno lo stesso peso. Ogni carta che
    l'avversario gioca elimina le mani che non la contengono; ogni pescata
    dell'avversario allarga le mani con una carta incognita del mazzo; ogni
    pescata del calcolatore elimina le mani che contengono la carta pescata.
    La briscola scoperta non sta in nessuna mano finche' resta nel mazzo.
    """

    def __init__(self, briscola, mano_pc, inferenza=True):
        self.briscola = briscola
        self.seme_briscola = SEMI[briscola]
        self.briscola_nel_mazzo = True
        self.uscite = set()
        self.viste_pc = set(mano_pc)
        self.inferenza = inferenza
        self.batte = tabella_prese(self.seme_briscola)
        self.n_mano_avv = len(mano_pc)
        self.mani = self._uniforme(self.n_mano_avv)

    def incognite(self):
        """Le carte che possono stare nella mano avversaria o nel mazzo."""
        return [
            c
            for c in TUTTE
            if c not in self.uscite and c not in self.viste_pc and not (c == self.briscola and self.briscola_nel_mazzo)
        ]

    def _uniforme(self, n_carte):
        return dict.fromkeys(combinations(self.incognite(), n_carte), 1.0)

    def _normalizza(self):
        if not self.mani:
            self.mani = self._uniforme(self.n_mano_avv)
        massimo = max(self.mani.values())
        soglia = massimo * 1e-7
        self.mani = {m: w for m, w in self.mani.items() if w >= soglia}
        totale = sum(self.mani.values())
        for m in self.mani:
            self.mani[m] /= totale

    def gioca_pc(self, carta):
        self.uscite.add(carta)

    def gioca_avversario(self, carta, guida_pc):
        """L'avversario ha giocato carta; guida_pc e' la carta del calcolatore sul tavolo, o None."""
        self.uscite.add(carta)
        nuove = {}
        for mano, peso in self.mani.items():
            if carta not in mano:
                continue
            if self.inferenza:
                peso *= self._verosimiglianza(carta, mano, guida_pc)
            resto = tuple(x for x in mano if x != carta)
            nuove[resto] = nuove.get(resto, 0.0) + peso
        self.n_mano_avv -= 1
        self.mani = nuove
        self._normalizza()

    def pesca_pc(self, carta):
        self.viste_pc.add(carta)
        if carta == self.briscola:
            self.briscola_nel_mazzo = False
        self.mani = {m: w for m, w in self.mani.items() if carta not in m}
        self._normalizza()

    def pesca_avversario(self, carta=None):
        """L'avversario ha pescato: carta e' nota solo quando e' la briscola."""
        if carta is not None and carta == self.briscola:
            self.briscola_nel_mazzo = False
            self.mani = {tuple(sorted((*m, carta))): w for m, w in self.mani.items()}
        else:
            incognite = self.incognite()
            nuove = {}
            for mano, peso in self.mani.items():
                scelte = [d for d in incognite if d not in mano]
                if not scelte:
                    continue
                quota = peso / len(scelte)
                for d in scelte:
                    nuova = tuple(sorted((*mano, d)))
                    nuove[nuova] = nuove.get(nuova, 0.0) + quota
            self.mani = nuove
        self.n_mano_avv += 1
        self._normalizza()

    def _utilita_razionale(self, carta, guida):
        """Quanto conviene, a un giocatore razionale, giocare carta adesso."""
        briscola = SEMI[carta] == self.seme_briscola
        if guida is None:
            utilita = -0.8 * PUNTI[carta] - 0.1 * FORZE[carta]
            if briscola:
                utilita -= 3 + 0.5 * FORZE[carta]
            return utilita
        vince = not self.batte[guida][carta]
        if vince:
            utilita = PUNTI[guida] + PUNTI[carta]
            if briscola and SEMI[guida] != self.seme_briscola:
                utilita -= 2 + 0.5 * FORZE[carta]
            return utilita
        utilita = -PUNTI[carta] - 0.2 * FORZE[carta]
        if briscola:
            utilita -= 5
        return utilita

    def _verosimiglianza(self, carta, mano, guida):
        """Quanto e' credibile che, con quella mano, si sia scelta carta."""
        utilita = {x: self._utilita_razionale(x, guida) for x in mano}
        migliore = max(utilita.values())
        return max(PESO_MINIMO, math.exp(BETA_INFERENZA * (utilita[carta] - migliore)))

    def distribuzione(self, mano_pc, tavolo, n_avv):
        """Mani avversarie possibili adesso e i loro pesi, piu' le carte incognite.

        Filtra le mani incoerenti con lo stato di gioco autorevole, che chi
        chiama passa per intero: e' la rete di sicurezza contro qualunque
        sfasatura fra gli eventi ricevuti e la partita vera.
        """
        vietate = set(self.uscite) | set(mano_pc) | set(tavolo)
        if self.briscola_nel_mazzo:
            vietate.add(self.briscola)
        incognite = [c for c in TUTTE if c not in vietate and c not in self.viste_pc]
        mani = [m for m in self.mani if len(m) == n_avv and not (set(m) & vietate)]
        if not mani:
            mani = list(combinations(incognite, n_avv))
            pesi = [1.0] * len(mani)
        else:
            pesi = [self.mani[m] for m in mani]
        return mani, pesi, incognite


# --- La ricerca ---


class _Ricerca:
    """Minimax con potatura alfa beta su un mondo determinato.

    Il valore di uno stato sono i punti futuri del calcolatore. La tabella
    delle trasposizioni ricorda i valori esatti e i limiti trovati con la
    potatura.
    """

    def __init__(self, batte, seme_briscola, profondita):
        self.batte = batte
        self.seme_briscola = seme_briscola
        self.profondita = profondita
        self.tt = {}

    @staticmethod
    def _pesca(mano_pc, mano_avv, mazzo, pc_vince):
        if not mazzo:
            return mano_pc, mano_avv, mazzo
        if pc_vince:
            mano_pc = (*mano_pc, mazzo[0])
            mano_avv = (*mano_avv, mazzo[1])
        else:
            mano_avv = (*mano_avv, mazzo[0])
            mano_pc = (*mano_pc, mazzo[1])
        return tuple(sorted(mano_pc)), tuple(sorted(mano_avv)), mazzo[2:]

    def _forza_mano(self, mano):
        forza = 0.0
        for c in mano:
            if SEMI[c] == self.seme_briscola:
                forza += 3 + 0.5 * FORZE[c]
            elif PUNTI[c] >= 10:
                forza += 1.5
            elif PUNTI[c] > 0:
                forza += 0.5
            else:
                forza += 0.3
        return forza

    def _valuta(self, mano_pc, mano_avv, mazzo, pc_di_mano):
        """Stima statica dei punti futuri del calcolatore all'orizzonte."""
        rimasti = sum(PUNTI[c] for c in mano_pc) + sum(PUNTI[c] for c in mano_avv) + sum(PUNTI[c] for c in mazzo)
        if rimasti == 0:
            return 0.0
        quota = 0.5 + PESO_FORZA * (self._forza_mano(mano_pc) - self._forza_mano(mano_avv))
        quota += -PESO_MANO if pc_di_mano else PESO_MANO
        return rimasti * min(0.92, max(0.08, quota))

    def radice(self, mano_pc, mano_avv, mazzo, guida):
        """Il valore minimax di ogni carta giocabile, come dizionario."""
        batte = self.batte
        prof = self.profondita - 1
        valori = {}
        if guida is not None:
            for c in mano_pc:
                vince = not batte[guida][c]
                punti = PUNTI[guida] + PUNTI[c]
                resto = tuple(x for x in mano_pc if x != c)
                mp, ma, mz = self._pesca(resto, mano_avv, mazzo, vince)
                valori[c] = (punti if vince else 0) + self._mm(mp, ma, mz, vince, prof, -1e9, 1e9)
            return valori
        for c in mano_pc:
            resto = tuple(x for x in mano_pc if x != c)
            peggio = 1e9
            for d in mano_avv:
                vince = batte[c][d]
                punti = PUNTI[c] + PUNTI[d]
                resto_avv = tuple(x for x in mano_avv if x != d)
                mp, ma, mz = self._pesca(resto, resto_avv, mazzo, vince)
                presi = punti if vince else 0
                v = presi + self._mm(mp, ma, mz, vince, prof, -1e9, peggio - presi)
                if v < peggio:
                    peggio = v
            valori[c] = peggio
        return valori

    def _mm(self, mano_pc, mano_avv, mazzo, pc_di_mano, prof, a, b):
        if not mano_pc:
            return 0.0
        if prof == 0:
            return self._valuta(mano_pc, mano_avv, mazzo, pc_di_mano)
        chiave = (mano_pc, mano_avv, len(mazzo), pc_di_mano, prof)
        voce = self.tt.get(chiave)
        if voce is not None:
            v, tipo = voce
            if tipo == 0 or (tipo == 1 and v >= b) or (tipo == 2 and v <= a):
                return v
        a0, b0 = a, b
        batte = self.batte
        pesca = self._pesca
        # Il valore di un nodo e' i punti presi in questa mano piu' quelli
        # del seguito: i limiti passati al seguito vanno spostati dei punti
        # presi, altrimenti la potatura taglia rami buoni.
        if pc_di_mano:
            best = -1e9
            for c in mano_pc:
                resto = tuple(x for x in mano_pc if x != c)
                peggio = 1e9
                for d in mano_avv:
                    vince = batte[c][d]
                    presi = PUNTI[c] + PUNTI[d] if vince else 0
                    resto_avv = tuple(x for x in mano_avv if x != d)
                    mp, ma, mz = pesca(resto, resto_avv, mazzo, vince)
                    v = presi + self._mm(mp, ma, mz, vince, prof - 1, a - presi, min(b, peggio) - presi)
                    if v < peggio:
                        peggio = v
                        if peggio <= a:
                            break
                if peggio > best:
                    best = peggio
                    if best > a:
                        a = best
                        if a >= b:
                            break
        else:
            best = 1e9
            for d in mano_avv:
                resto_avv = tuple(x for x in mano_avv if x != d)
                meglio = -1e9
                for c in mano_pc:
                    vince = not batte[d][c]
                    presi = PUNTI[d] + PUNTI[c] if vince else 0
                    resto = tuple(x for x in mano_pc if x != c)
                    mp, ma, mz = pesca(resto, resto_avv, mazzo, vince)
                    v = presi + self._mm(mp, ma, mz, vince, prof - 1, max(a, meglio) - presi, b - presi)
                    if v > meglio:
                        meglio = v
                        if meglio >= b:
                            break
                if meglio < best:
                    best = meglio
                    if best < b:
                        b = best
                        if b <= a:
                            break
        tipo = 2 if best <= a0 else (1 if best >= b0 else 0)
        self.tt[chiave] = (best, tipo)
        return best


# --- Il cervello ---


class Cervello:
    """Il giocatore artificiale di una partita.

    Si crea a carte distribuite, con la briscola scoperta e la mano del
    calcolatore, e riceve gli eventi della partita: ogni carta giocata da
    chiunque e ogni pescata. Quando tocca al calcolatore, scegli restituisce
    la carta da giocare. Chi lo usa passa sempre oggetti Carta di GBUtils.
    Non riceve mai la carta pescata dall'avversario, tranne quando e' la
    briscola scoperta, che vedono tutti: se gli arriva un'altra la ignora.
    """

    def __init__(self, briscola, mazzo_completo, mano_pc, tempo=TEMPO_PREDEFINITO, inferenza=True, profondita_max=None, seme=None):
        self.carte = {indice(c): c for c in mazzo_completo}
        self.briscola = indice(briscola)
        self.seme_briscola = SEMI[self.briscola]
        self.conoscenza = Conoscenza(self.briscola, [indice(c) for c in mano_pc], inferenza)
        self.tempo = tempo
        self.profondita_max = profondita_max
        self.rng = random.Random(seme)
        self.statistiche = {"decisioni": 0, "mondi": 0, "tempo": 0.0, "esatte": 0}

    def carta_giocata(self, carta, di_pc, tavolo_prima):
        """Una carta e' finita sul tavolo; tavolo_prima e' cio' che c'era gia'."""
        c = indice(carta)
        if di_pc:
            self.conoscenza.gioca_pc(c)
        else:
            guida = indice(tavolo_prima[0]) if tavolo_prima else None
            self.conoscenza.gioca_avversario(c, guida)

    def carta_pescata(self, carta, di_pc):
        """Qualcuno ha pescato. Per l'avversario conta solo se e' la briscola."""
        if di_pc:
            self.conoscenza.pesca_pc(indice(carta))
            return
        c = indice(carta) if carta is not None else None
        self.conoscenza.pesca_avversario(c if c == self.briscola else None)

    @staticmethod
    def _profondita(mani_rimaste, carte_mazzo):
        """Quante mani guardare avanti: tutte nel finale, di meno all'inizio.

        Il tempo di riflessione decide poi quanti mondi si esaminano a quella
        profondita'. I valori vengono dalle misure sull'arena: a inizio
        partita tre mani costano un millisecondo e mezzo per mondo, cinque
        mani a mazzo quasi vuoto una trentina.
        """
        if mani_rimaste <= 5:
            return mani_rimaste
        if carte_mazzo <= 8:
            return 5
        if carte_mazzo <= 18:
            return 4
        return 3

    def scegli(self, tavolo, mano_pc, punti_pc, punti_avv, carte_mazzo, match=None):
        """La carta migliore da giocare adesso.

        Durante la ricerca il garbage collector ciclico resta spento. La
        ricerca non crea cicli, quindi il conteggio dei riferimenti basta a
        liberare tutto, e Python 3.14.5 su Windows e' caduto piu' volte
        nelle prove lunghe proprio durante le raccolte fatte in mezzo a
        milioni di piccole tuple: con il collector spento cento partite
        sono passate dove quattro corse su quattro erano cadute.
        """
        if len(mano_pc) == 1:
            return mano_pc[0]
        collettore_attivo = gc.isenabled()
        gc.disable()
        try:
            return self._scegli(tavolo, mano_pc, punti_pc, punti_avv, carte_mazzo, match)
        finally:
            if collettore_attivo:
                gc.enable()

    def _scegli(self, tavolo, mano_pc, punti_pc, punti_avv, carte_mazzo, match):
        inizio = time.perf_counter()
        mp = tuple(sorted(indice(c) for c in mano_pc))
        tavolo_idx = [indice(c) for c in tavolo]
        guida = tavolo_idx[0] if tavolo_idx else None
        n_avv = len(mp) - len(tavolo_idx)
        mani, pesi, incognite = self.conoscenza.distribuzione(mp, tavolo_idx, n_avv)
        mani_rimaste = len(mp) + carte_mazzo // 2
        profondita = self._profondita(mani_rimaste, carte_mazzo)
        tetto = mani_rimaste if self.profondita_max is None else min(mani_rimaste, self.profondita_max)
        profondita = min(profondita, tetto)
        utilita_base = utilita_punti(match)
        coda = (self.briscola,) if self.conoscenza.briscola_nel_mazzo else ()
        batte = tabella_prese(self.seme_briscola)
        mondi = self._mondi(mani, pesi, incognite, n_avv)
        scadenza = inizio + self.tempo
        contesto = (mondi, mp, guida, coda, batte, punti_pc, utilita_base, mani_rimaste, scadenza)
        esito = self._esamina(profondita, *contesto)
        # Se la passata ha usato poco tempo, se ne fa una piu' profonda sugli
        # stessi mondi, e la si tiene solo se ha esaminato abbastanza mondi.
        while profondita < tetto and time.perf_counter() - inizio < self.tempo * FRAZIONE_PER_APPROFONDIRE:
            tentativo = self._esamina(profondita + 1, *contesto)
            if tentativo[2] < min(len(mondi), MONDI_MINIMI_PROFONDI):
                break
            esito = tentativo
            profondita += 1
        somma_utilita, somma_punti, valutati, _ = esito
        casuale = {c: self.rng.random() for c in mp}
        scelta = max(mp, key=lambda c: (somma_utilita[c], somma_punti[c], casuale[c]))
        durata = time.perf_counter() - inizio
        self.statistiche["decisioni"] += 1
        self.statistiche["mondi"] += valutati
        self.statistiche["tempo"] += durata
        if profondita >= mani_rimaste:
            self.statistiche["esatte"] += 1
        return self.carte[scelta]

    def _esamina(self, profondita, mondi, mp, guida, coda, batte, punti_pc, utilita_base, mani_rimaste, scadenza):
        """Una passata sui mondi a quella profondita'. Restituisce le somme e quanti mondi ha visto."""
        incertezza = 0.0 if profondita >= mani_rimaste else INCERTEZZA_BASE + INCERTEZZA_PER_MANO * (mani_rimaste - profondita)
        utilita = _sfuma(utilita_base, incertezza)
        somma_utilita = dict.fromkeys(mp, 0.0)
        somma_punti = dict.fromkeys(mp, 0.0)
        peso_totale = 0.0
        valutati = 0
        for mano_avv, ordine, peso in mondi:
            ricerca = _Ricerca(batte, self.seme_briscola, profondita)
            valori = ricerca.radice(mp, mano_avv, (*ordine, *coda), guida)
            for c, v in valori.items():
                finale = punti_pc + v
                somma_utilita[c] += peso * _interpola(utilita, finale)
                somma_punti[c] += peso * finale
            peso_totale += peso
            valutati += 1
            if valutati >= MONDI_MINIMI and time.perf_counter() > scadenza:
                break
        return somma_utilita, somma_punti, valutati, peso_totale

    def _mondi(self, mani, pesi, incognite, n_avv):
        """I mondi da esaminare: enumerati tutti se sono pochi, altrimenti campionati."""
        k = len(incognite) - n_avv
        possibili = len(mani) * math.factorial(k) if k <= 6 else float("inf")
        if possibili <= MONDI_ENUMERABILI:
            totale = sum(pesi)
            mondi = []
            for mano, peso in zip(mani, pesi, strict=True):
                resto = [c for c in incognite if c not in mano]
                for ordine in permutations(resto):
                    mondi.append((mano, ordine, peso / totale / math.factorial(k)))
            self.rng.shuffle(mondi)
            return mondi
        return self._campiona(mani, pesi, incognite)

    def _campiona(self, mani, pesi, incognite):
        rng = self.rng
        mondi = []
        for mano in rng.choices(mani, pesi, k=MONDI_MASSIMI):
            resto = [c for c in incognite if c not in mano]
            rng.shuffle(resto)
            mondi.append((mano, tuple(resto), 1.0))
        return mondi
