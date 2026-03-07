from carte import Mazzo

class Giocatore:
    def __init__(self, nome):
        self.nome = nome
        self.mano = []
        self.mazzetto = []

    def calcola_punteggio(self):
        return sum(Mazzo.PUNTI_BRISCOLA.get(carta.valore, 0) for carta in self.mazzetto)