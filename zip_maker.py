# Gabryscola, utilita': prepara l'archivio per la distribuzione.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 08/09/2026: primo chiamante, il mestiere sta in crea_archivio_release di GBUtils.

"""Comprime il risultato di PyInstaller in un solo archivio.

Tutto il mestiere sta in GBUtils, cosi' la regola sulle esclusioni e' una
sola per tutti i progetti. Qui resta soltanto il nome di Gabryscola.
Gabryscola si compila in un file unico, quindi dentro dist c'e' soltanto
l'eseguibile: la collezione dei suoni e la guida, dichiarate nei datas
dello spec, viaggiano dentro di lui e non vanno cercate accanto.
Si lasciano fuori la classifica e la sua copia di riserva, che nascono
giocando accanto all'eseguibile e conterrebbero le tue partite.
"""

import sys

from GBUtils import crea_archivio_release

FUORI = ["briscola_charts.json", "briscola_charts.json.bak"]


def main():
    try:
        crea_archivio_release("gabryscola", cartella_dist="dist", escludi=FUORI)
    except (FileNotFoundError, OSError) as e:
        print(f"Archivio non creato: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
