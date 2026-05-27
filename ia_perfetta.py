"""Motore IA avanzato per Briscola.
Architettura a 3 livelli:
1. Inferenza bayesiana sulle carte dell'avversario (_Tracker)
2. Simulazione Monte Carlo per apertura e medio-gioco
3. Minimax con alpha-beta pruning per l'endgame a informazione perfetta
"""
from carte import Mazzo
import random

_PT = Mazzo.PUNTI_BRISCOLA
_FZ = {1: 10, 3: 9, 10: 8, 9: 7, 8: 6, 7: 5, 6: 4, 5: 3, 4: 2, 2: 1}
_N_MC = 300
_N_MC_TRANS = 600


def _p(c):
    """Punti briscola della carta."""
    return _PT.get(c.valore, 0)


def _f(c):
    """Forza gerarchica (10=Asso ... 1=Due)."""
    return _FZ[c.valore]


def _vp(c1, c2, bs):
    """True se c1 (prima giocata) batte c2. bs = seme briscola."""
    b1, b2 = c1.seme_nome == bs, c2.seme_nome == bs
    if b1 != b2:
        return b1
    if b1 and b2 or c1.seme_nome == c2.seme_nome:
        return _f(c1) > _f(c2)
    return True


def _risposta_simulata(c_leader, mano_avv, bs):
    """Simula la risposta strategica dell'avversario nel Monte Carlo.
    L'avversario massimizza la propria utilità: vince se conviene,
    altrimenti minimizza i punti regalati."""
    migliore, mu = None, -1e9
    for ca in mano_avv:
        vince = not _vp(c_leader, ca, bs)
        pp = _p(c_leader) + _p(ca)
        if vince:
            u = pp * 2
            # Penalizza spreco briscola su piatti scarsi
            if ca.seme_nome == bs and c_leader.seme_nome != bs:
                u -= (_p(ca) + _f(ca)) * 1.5
                if pp < 4:
                    u -= 12
            u += 3
        else:
            u = -_p(ca) * 3 - _f(ca) * 0.1
        if u > mu:
            mu, migliore = u, ca
    return migliore


# --- Livello 1: Inferenza Bayesiana ---
class _Tracker:
    """Mantiene pesi di probabilità per ogni carta incognita
    e li aggiorna osservando le giocate dell'avversario."""
    def __init__(self, bs):
        self.bs = bs
        self._w = {}
        self._void = {}
        self._no_br = 0.0

    def osserva(self, carta, tavolo_prima, incognite, mazzo_attivo):
        """Aggiorna i pesi dopo una giocata dell'avversario."""
        if tavolo_prima:
            ct = tavolo_prima[0]
            pp = _p(ct) + _p(carta)
            if carta.seme_nome != ct.seme_nome:
                # Void nel seme richiesto
                self._void[ct.seme_nome] = self._void.get(ct.seme_nome, 0) + 3
                # Non ha usato briscola su piatto ricco
                if carta.seme_nome != self.bs and pp >= 4:
                    self._no_br += 1.5
            elif _p(carta) == 0 and _p(ct) > 0 and not _vp(carta, ct, self.bs):
                # Liscio perdente stesso seme: non ha carte più forti di quel seme
                for c in incognite:
                    if c.seme_nome == carta.seme_nome and _f(c) > _f(carta):
                        self._w[c.id] = self._w.get(c.id, 1.0) * 0.35
        else:
            # L'avversario ha guidato con un liscio: meno probabile che abbia Asso/3 del seme
            if _p(carta) == 0:
                for c in incognite:
                    if c.seme_nome == carta.seme_nome and _p(c) >= 10:
                        self._w[c.id] = self._w.get(c.id, 1.0) * 0.6
        self._applica(incognite, mazzo_attivo)
        # Decadimento evidenze se il mazzo è attivo (l'avversario pesca)
        if mazzo_attivo:
            for s in list(self._void):
                self._void[s] = max(0, self._void[s] - 1)
            self._no_br = max(0.0, self._no_br - 0.5)

    def _applica(self, incognite, mazzo_attivo):
        """Ricalcola pesi sulle carte incognite basandosi sulle evidenze."""
        for c in incognite:
            w = self._w.get(c.id, 1.0)
            ev = self._void.get(c.seme_nome, 0)
            if ev > 0:
                r = max(0.1, 1.0 - ev * 0.15) if mazzo_attivo else (0.01 if ev >= 2 else 0.15)
                w = min(w, r)
            if c.seme_nome == self.bs and self._no_br > 0:
                w = min(w, max(0.05, 1.0 - self._no_br * 0.2))
            self._w[c.id] = w

    def campiona(self, incognite, n_carte, n):
        """Genera n mani casuali pesate di n_carte carte dalle incognite."""
        if n_carte <= 0 or not incognite:
            return [[] for _ in range(n)]
        n_carte = min(n_carte, len(incognite))
        pesi = [max(0.01, self._w.get(c.id, 1.0)) for c in incognite]
        risultati = []
        for _ in range(n):
            pool, pw = list(incognite), list(pesi)
            mano = []
            for _ in range(n_carte):
                if not pool:
                    break
                t = sum(pw)
                r = random.random() * t if t > 0 else 0
                acc, idx = 0.0, 0
                for j in range(len(pw)):
                    acc += pw[j]
                    if acc >= r:
                        idx = j
                        break
                mano.append(pool.pop(idx))
                pw.pop(idx)
            risultati.append(mano)
        return risultati


# --- Livello 3: Risolutore Endgame (Minimax con Alpha-Beta) ---
class _Endgame:
    """Risolve le ultime mani (mazzo vuoto) a informazione perfetta
    con minimax e alpha-beta pruning."""
    @staticmethod
    def risolvi(mp, mu, tavolo, bs, pp, pu):
        if not mp:
            return None
        if tavolo:
            return _Endgame._rispondi(mp, mu, tavolo[0], bs, pp, pu)
        return _Endgame._guida(mp, mu, bs, pp, pu)

    @staticmethod
    def _rispondi(mp, mu, ca, bs, pp, pu):
        """PC risponde alla carta ca dell'avversario."""
        best, bc = -999, None
        for c in mp:
            v = not _vp(ca, c, bs)
            pt = _p(ca) + _p(c)
            npp, npu = (pp + pt, pu) if v else (pp, pu + pt)
            rp = [x for x in mp if x is not c]
            s = _Endgame._mm(rp, list(mu), bs, v, npp, npu, -999, 999)
            if s > best:
                best, bc = s, c
        return bc

    @staticmethod
    def _guida(mp, mu, bs, pp, pu):
        """PC guida la mano: sceglie la carta che massimizza il punteggio nel caso peggiore."""
        best, bc = -999, None
        for c in mp:
            worst = 999
            for cu in mu:
                v = _vp(c, cu, bs)
                pt = _p(c) + _p(cu)
                npp, npu = (pp + pt, pu) if v else (pp, pu + pt)
                rp = [x for x in mp if x is not c]
                ru = [x for x in mu if x is not cu]
                s = _Endgame._mm(rp, ru, bs, v, npp, npu, -999, 999)
                worst = min(worst, s)
                if worst <= best:
                    break
            if worst > best:
                best, bc = worst, c
        return bc

    @staticmethod
    def _mm(mp, mu, bs, tpc, pp, pu, a, b):
        """Minimax ricorsivo con pruning. Restituisce punti PC attesi."""
        if not mp and not mu:
            return pp
        if tpc:
            # PC guida (massimizza), avversario risponde (minimizza)
            best = -999
            for c in mp:
                worst = 999
                for cu in mu:
                    v = _vp(c, cu, bs)
                    pt = _p(c) + _p(cu)
                    npp, npu = (pp + pt, pu) if v else (pp, pu + pt)
                    s = _Endgame._mm(
                        [x for x in mp if x is not c],
                        [x for x in mu if x is not cu],
                        bs, v, npp, npu, a, b)
                    worst = min(worst, s)
                    if worst <= a:
                        break
                best = max(best, worst)
                a = max(a, best)
                if b <= a:
                    break
            return best
        else:
            # Avversario guida (minimizza), PC risponde (massimizza)
            best = 999
            for cu in mu:
                bft = -999
                for c in mp:
                    v = not _vp(cu, c, bs)
                    pt = _p(cu) + _p(c)
                    npp, npu = (pp + pt, pu) if v else (pp, pu + pt)
                    s = _Endgame._mm(
                        [x for x in mp if x is not c],
                        [x for x in mu if x is not cu],
                        bs, v, npp, npu, a, b)
                    bft = max(bft, s)
                    if bft >= b:
                        break
                best = min(best, bft)
                b = min(b, best)
                if b <= a:
                    break
            return best


# --- Classe Principale ---
class IAPerfetta:
    """Motore decisionale IA per la Briscola.
    Crea un'istanza per partita. Chiama osserva_giocata_umano dopo ogni mano
    e scegli_carta quando è il turno del PC."""
    def __init__(self, briscola, mazzo_completo):
        self.briscola = briscola
        self.bs = briscola.seme_nome
        self.mazzo_completo = list(mazzo_completo)
        self.tracker = _Tracker(self.bs)

    def osserva_giocata_umano(self, carta, tavolo_prima, incognite, mazzo_attivo):
        """Registra la giocata dell'umano per aggiornare l'inferenza bayesiana."""
        self.tracker.osserva(carta, tavolo_prima, incognite, mazzo_attivo)

    def scegli_carta(self, tavolo, mano_pc, carte_uscite, punti_pc, punti_umano, carte_mazzo):
        """Sceglie la carta migliore da giocare."""
        if len(mano_pc) == 1:
            return mano_pc[0]
        incognite = [c for c in self.mazzo_completo
                     if c not in carte_uscite and c not in mano_pc and c not in tavolo]
        # Endgame: mazzo vuoto → minimax esatto
        if carte_mazzo == 0 and incognite:
            risultato = _Endgame.risolvi(
                mano_pc, incognite, tavolo, self.bs, punti_pc, punti_umano)
            if risultato:
                return risultato
        # Medio-gioco
        if tavolo:
            return self._risposta(mano_pc, tavolo[0], punti_pc, punti_umano, carte_mazzo, incognite)
        return self._guida_mc(mano_pc, incognite, punti_pc, punti_umano, carte_mazzo)

    # --- Livello 2a: Valutazione Risposta (PC secondo a giocare) ---
    def _risposta(self, mano_pc, carta_avv, punti_pc, punti_umano, carte_mazzo, incognite):
        """Valuta ogni carta come risposta e sceglie la migliore."""
        best, bc = -1e9, None
        br_mano = sum(1 for c in mano_pc if c.seme_nome == self.bs)
        for c in mano_pc:
            vince = not _vp(carta_avv, c, self.bs)
            pp = _p(carta_avv) + _p(c)
            if vince:
                # Vittoria immediata della partita
                if punti_pc + pp >= 61:
                    return c
                s = pp * 2.0
                if pp >= 10:
                    s += 5
                # Costo uso briscola per tagliare
                if c.seme_nome == self.bs and carta_avv.seme_nome != self.bs:
                    costo = _p(c) + 5
                    s -= costo * (2.5 if pp < 4 else (1.2 if pp < 8 else 0.3))
                    if br_mano <= 1:
                        s -= 10
                # Preferisci vincere con carte meno preziose
                s -= _p(c) * 0.3
                # Bonus posizionale: avere la mano
                s += 2.5
            else:
                s = -pp
                # Penalizza il sacrificio di semi con Asso/3 in mano
                ha_forte = any(x for x in mano_pc
                               if x is not c and x.seme_nome == c.seme_nome and _p(x) >= 10)
                if ha_forte:
                    s -= 2
            if s > best:
                best, bc = s, c
        return bc

    # --- Livello 2b: Valutazione Guida con Monte Carlo (PC primo a giocare) ---
    def _guida_mc(self, mano_pc, incognite, punti_pc, punti_umano, carte_mazzo):
        """Valuta ogni carta di apertura con simulazione Monte Carlo."""
        n_sim = _N_MC_TRANS if carte_mazzo <= 5 else _N_MC
        dim_avv = len(mano_pc)
        campioni = self.tracker.campiona(incognite, dim_avv, n_sim)
        br_incognite = sum(1 for c in incognite if c.seme_nome == self.bs)
        punteggi = {}
        for c in mano_pc:
            totale = 0.0
            for mano_avv in campioni:
                if not mano_avv:
                    continue
                ca = _risposta_simulata(c, mano_avv, self.bs)
                if ca is None:
                    continue
                vince = _vp(c, ca, self.bs)
                pp = _p(c) + _p(ca)
                totale += pp if vince else -pp
            mc = totale / max(1, n_sim)
            adj = 0.0
            pc = _p(c)
            # Rischio Asso/3 non-briscola: probabilità di essere tagliato
            if pc >= 10 and c.seme_nome != self.bs and br_incognite > 0:
                prob = min(0.95, br_incognite * dim_avv / max(1, len(incognite)))
                adj -= pc * prob * 2.5
            # Costo briscola come guida: pesato dalla fase
            if c.seme_nome == self.bs:
                adj -= (pc + 4) * max(0.5, len(incognite) / 15.0)
            # Bonus lisci non-briscola
            if pc == 0 and c.seme_nome != self.bs:
                adj += 4
                # Esca: liscio dello stesso seme dove ho Asso/3
                for alt in mano_pc:
                    if alt is not c and alt.seme_nome == c.seme_nome and _p(alt) >= 10:
                        adj += 6
                        break
                # Bonus seme esaurito di carte pericolose
                if not any(x for x in incognite if x.seme_nome == c.seme_nome and _p(x) > 0):
                    adj += 3
            # Fase partita: conservativo in vantaggio, aggressivo in svantaggio
            diff = punti_pc - punti_umano
            if diff > 20 and pc > 0:
                adj -= 4
            elif diff < -20 and mc > 0:
                adj += 3
            punteggi[c.id] = mc + adj
        return max(mano_pc, key=lambda c: punteggi.get(c.id, -999))
