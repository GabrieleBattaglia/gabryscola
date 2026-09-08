# Gabryscola, l'arena: partite senza console fra due cervelli, per misurarne la forza.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 08/09/2026: nasce con il motore nuovo, per verificarlo con i numeri.

"""L'arena di Gabryscola.

Fa giocare fra loro due configurazioni del motore, oppure due qualsiasi
oggetti con la stessa interfaccia di Cervello, per centinaia di partite,
alternando chi comincia, e conta vittorie, patte, punti e tempi. E' lo
strumento con cui si misura se una modifica al motore lo ha reso piu'
forte, invece di crederlo a orecchio.
Da riga di comando:
    python arena.py --partite 200 --tempo-a 0.1 --tempo-b 0.1 --inferenza-b 0
Ogni opzione con il suffisso a o b riguarda uno dei due giocatori.
"""

import argparse
import gc
import random
import sys
import time

from giocatore import Giocatore
from motore_ia import Cervello
from regole import PUNTI_TOTALI, nuovo_mazzo, punti, vince_primo


def fabbrica_cervello(**opzioni):
    """Restituisce una funzione che crea un Cervello con quelle opzioni."""

    def crea(briscola, mazzo_completo, mano, seme):
        return Cervello(briscola, mazzo_completo, mano, seme=seme, **opzioni)

    return crea


class _Sfidante(Giocatore):
    def __init__(self, nome, fabbrica):
        super().__init__(nome)
        self.fabbrica = fabbrica
        self.cervello = None
        self.decisioni = 0
        self.tempo = 0.0

    def punteggio(self):
        return sum(punti(c) for c in self.mazzetto)


def partita(fabbrica_a, fabbrica_b, comincia_a, rng):
    """Una partita intera fra due fabbriche di cervelli. Restituisce i punti di a e di b."""
    mazzo = nuovo_mazzo()
    rng.shuffle(mazzo.carte)
    completo = nuovo_mazzo().carte[:]
    a = _Sfidante("a", fabbrica_a)
    b = _Sfidante("b", fabbrica_b)
    a.mano = mazzo.pesca(3)
    b.mano = mazzo.pesca(3)
    briscola = mazzo.pesca(1)[0]
    mazzo.carte.insert(0, briscola)
    seme = briscola.seme_nome
    a.cervello = fabbrica_a(briscola, completo, a.mano, rng.randrange(1 << 30))
    b.cervello = fabbrica_b(briscola, completo, b.mano, rng.randrange(1 << 30))
    di_mano = a if comincia_a else b
    while a.mano:
        ordine = (a, b) if di_mano is a else (b, a)
        tavolo = []
        for g in ordine:
            altro = b if g is a else a
            prima = list(tavolo)
            inizio = time.perf_counter()
            carta = g.cervello.scegli(tavolo, g.mano, g.punteggio(), altro.punteggio(), len(mazzo))
            g.tempo += time.perf_counter() - inizio
            g.decisioni += 1
            g.mano.remove(carta)
            tavolo.append(carta)
            g.cervello.carta_giocata(carta, True, prima)
            altro.cervello.carta_giocata(carta, False, prima)
        vincitore = ordine[0] if vince_primo(tavolo[0], tavolo[1], seme) else ordine[1]
        perdente = ordine[1] if vincitore is ordine[0] else ordine[0]
        vincitore.mazzetto.extend(tavolo)
        if len(mazzo) > 0:
            for g in (vincitore, perdente):
                altro = b if g is a else a
                carta = mazzo.pesca(1)[0]
                g.mano.append(carta)
                g.cervello.carta_pescata(carta, True)
                altro.cervello.carta_pescata(carta if carta == briscola else None, False)
        di_mano = vincitore
    return a, b


def torneo(fabbrica_a, fabbrica_b, partite, seme=None, racconta=None):
    """Tante partite alternando chi comincia. Restituisce un dizionario di conteggi."""
    rng = random.Random(seme)
    conti = {
        "partite": 0,
        "vinte_a": 0,
        "vinte_b": 0,
        "patte": 0,
        "punti_a": 0,
        "punti_b": 0,
        "decisioni_a": 0,
        "decisioni_b": 0,
        "tempo_a": 0.0,
        "tempo_b": 0.0,
        "mondi_a": 0,
        "mondi_b": 0,
    }
    for n in range(partite):
        a, b = partita(fabbrica_a, fabbrica_b, comincia_a=(n % 2 == 0), rng=rng)
        pa, pb = a.punteggio(), b.punteggio()
        if pa + pb != PUNTI_TOTALI:
            raise AssertionError(f"punti totali {pa + pb} invece di {PUNTI_TOTALI}")
        conti["partite"] += 1
        conti["punti_a"] += pa
        conti["punti_b"] += pb
        if pa > pb:
            conti["vinte_a"] += 1
        elif pb > pa:
            conti["vinte_b"] += 1
        else:
            conti["patte"] += 1
        for lato, g in (("a", a), ("b", b)):
            conti["decisioni_" + lato] += g.decisioni
            conti["tempo_" + lato] += g.tempo
            statistiche = getattr(g.cervello, "statistiche", None)
            if statistiche:
                conti["mondi_" + lato] += statistiche["mondi"]
        if racconta and (n + 1) % racconta == 0:
            print(righe_riepilogo(conti)[0])
    return conti


def righe_riepilogo(conti):
    """Il riepilogo in frasi corte, per lo screen reader."""
    n = max(1, conti["partite"])
    righe = [
        f"Partite {conti['partite']}: a vince {conti['vinte_a']}, b vince {conti['vinte_b']}, patte {conti['patte']}.",
        f"Quota di a: {100 * (conti['vinte_a'] + 0.5 * conti['patte']) / n:.1f} per cento.",
        f"Punti medi: a {conti['punti_a'] / n:.1f}, b {conti['punti_b'] / n:.1f}.",
    ]
    for lato in "ab":
        decisioni = max(1, conti["decisioni_" + lato])
        righe.append(
            f"Giocatore {lato}: {1000 * conti['tempo_' + lato] / decisioni:.0f} millisecondi "
            f"e {conti['mondi_' + lato] / decisioni:.0f} mondi per decisione."
        )
    return righe


def _argomenti(argv):
    parser = argparse.ArgumentParser(description="Arena di Gabryscola: due cervelli a confronto.")
    parser.add_argument("--partite", type=int, default=100)
    parser.add_argument("--seme", type=int, default=None)
    parser.add_argument("--racconta", type=int, default=20, help="ogni quante partite stampare il parziale")
    for lato in "ab":
        parser.add_argument(f"--tempo-{lato}", type=float, default=0.1)
        parser.add_argument(f"--inferenza-{lato}", type=int, default=1)
        parser.add_argument(f"--profondita-{lato}", type=int, default=None)
    parser.add_argument(
        "--collector-acceso",
        action="store_true",
        help="lascia acceso il garbage collector: e' la prova di accettazione della macchina, vedi il changelog della 4.0.0",
    )
    return parser.parse_args(argv)


def main(argv=None):
    opzioni = _argomenti(argv)
    # Sulla macchina di sviluppo le corse lunghe piene di allocazioni sono
    # cadute con il collector acceso, con tre versioni diverse di Python:
    # le partite non creano cicli, quindi il conteggio dei riferimenti basta
    # e il collector resta spento. Con --collector-acceso si lascia acceso,
    # ed e' il modo di verificare se la macchina e' tornata sana.
    if not opzioni.collector_acceso:
        gc.disable()
    fabbriche = {}
    for lato in "ab":
        fabbriche[lato] = fabbrica_cervello(
            tempo=getattr(opzioni, f"tempo_{lato}"),
            inferenza=bool(getattr(opzioni, f"inferenza_{lato}")),
            profondita_max=getattr(opzioni, f"profondita_{lato}"),
        )
    conti = torneo(fabbriche["a"], fabbriche["b"], opzioni.partite, seme=opzioni.seme, racconta=opzioni.racconta)
    for riga in righe_riepilogo(conti):
        print(riga)
    return 0


if __name__ == "__main__":
    sys.exit(main())
