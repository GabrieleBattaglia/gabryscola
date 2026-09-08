# Gabryscola, il giocatore: nome, carte in mano e mazzetto delle prese.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 08/09/2026: i punti si leggono da regole, non piu' dal mazzo.

from regole import punti


class Giocatore:
    def __init__(self, nome):
        self.nome = nome
        self.mano = []
        self.mazzetto = []

    def calcola_punteggio(self):
        return sum(punti(carta) for carta in self.mazzetto)
