# Gabryscola, le regole della briscola: punti, gerarchia, presa e mazzo.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 08/09/2026: nasce con la revisione 1 del refactoring generale. Raccoglie cio'
# che fino alla 3.1.1 stava in carte.py, una copia locale del Mazzo di GBUtils.

"""Le regole della briscola, separate dal mazzo che le gioca.

Il mazzo italiano da quaranta carte e' quello di GBUtils, con tipo_francese
falso. La tabella dei punti non appartiene al mazzo: con le stesse carte si
giocano scopa e tressette, che contano in modo diverso. Per questo sta qui,
insieme alla gerarchia di presa e alla regola che decide chi vince la mano.
GBUtils abbrevia le Coppe con la O, perche' la C e' gia' dei Cuori. Le carte
segnate in braille di Gabriele hanno sempre usato la C, e dalla V6.1.0 Mazzo
accetta le lettere dei semi come parametro: qui si passa quella.
"""

from GBUtils import Mazzo

# Punti di presa: asso undici, tre dieci, re quattro, cavallo tre, fante due.
PUNTI_BRISCOLA = {1: 11, 3: 10, 10: 4, 9: 3, 8: 2}
# Gerarchia di presa: asso, tre, re, cavallo, fante, poi dal sette al due.
FORZA = {1: 10, 3: 9, 10: 8, 9: 7, 8: 6, 7: 5, 6: 4, 5: 3, 4: 2, 2: 1}
# Lettere dei semi sul display braille, dove differiscono da quelle di GBUtils.
LETTERE_SEMI = {"Coppe": "C"}
PUNTI_TOTALI = 120
PUNTI_PER_VINCERE = 61


def punti(carta):
    """Punti che la carta porta a chi la prende."""
    return PUNTI_BRISCOLA.get(carta.valore, 0)


def forza(carta):
    """Posizione della carta nella gerarchia di presa, dieci per l'asso."""
    return FORZA[carta.valore]


def vince_primo(prima, seconda, seme_briscola):
    """Vero se la carta giocata per prima vince la mano sulla seconda.

    Una briscola batte sempre una carta di altro seme. A parita' di seme,
    briscola compresa, vince la carta piu' alta nella gerarchia. Con due
    semi diversi e nessuna briscola vince chi ha giocato per primo.
    """
    prima_briscola = prima.seme_nome == seme_briscola
    seconda_briscola = seconda.seme_nome == seme_briscola
    if prima_briscola != seconda_briscola:
        return prima_briscola
    if prima.seme_nome == seconda.seme_nome:
        return forza(prima) > forza(seconda)
    return True


def nuovo_mazzo():
    """Il mazzo italiano di GBUtils, con le lettere dei semi del braille.

    Le carte escono dalla coda del mazzo di GBUtils, quindi chi vuole una
    carta pescata per ultima, come la briscola, la inserisce in testa.
    """
    return Mazzo(tipo_francese=False, lettere_semi=LETTERE_SEMI)
