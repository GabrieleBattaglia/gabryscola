import random
from collections import namedtuple

Carta = namedtuple("Carta", ["id", "nome", "valore", "seme_nome", "seme_id", "desc_breve"])

class Mazzo:
    PUNTI_BRISCOLA = {1: 11, 3: 10, 10: 4, 9: 3, 8: 2}
    _SEMI_ITALIANI = ["Bastoni", "Spade", "Coppe", "Denari"]
    _VALORI_ITALIANI = [("Asso", 1), ('2', 2), ('3', 3), ('4', 4), ('5', 5), ('6', 6), ('7', 7), ("Fante", 8), ("Cavallo", 9), ("Re", 10)]
    _VALORI_DESCRIZIONE = {1: 'A', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: '0'}
    _SEMI_DESCRIZIONE = {"Bastoni": 'B', "Spade": 'S', "Coppe": 'C', "Denari": 'D'}

    def __init__(self):
        self.carte = []
        self._costruisci_mazzo()

    def _costruisci_mazzo(self):
        self.carte = []
        for id_seme, nome_seme in enumerate(self._SEMI_ITALIANI, 1):
            for nome_valore, valore_num in self._VALORI_ITALIANI:
                desc_val = self._VALORI_DESCRIZIONE.get(valore_num, '?')
                desc_seme = self._SEMI_DESCRIZIONE.get(nome_seme, '?')
                desc_breve = f"{desc_val}{desc_seme}"
                nome_completo = f"{nome_valore} di {nome_seme}"
                self.carte.append(Carta(
                    id=valore_num * 10 + id_seme,
                    nome=nome_completo,
                    valore=valore_num,
                    seme_nome=nome_seme,
                    seme_id=id_seme,
                    desc_breve=desc_breve
                ))

    def mescola_mazzo(self):
        random.shuffle(self.carte)

    def pesca(self, quante=1):
        return [self.carte.pop(0) for _ in range(min(quante, len(self.carte)))]

    def __len__(self):
        return len(self.carte)
