# Gabryscola, i suoni: la mappa fra gli eventi del gioco e i preset condivisi.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5, modalita' auto).
# 03/09/2026: la lettura della collezione e' passata ad Acusticator.

"""Collega gli eventi del gioco ai suoni della collezione condivisa.

Fino alla 3.1.0 questo file si leggeva da solo Acu_Collection.json e si
riscriveva la conversione dei volumi, che nella collezione sono scarti
rispetto alla base 0.5 mentre il motore vuole il valore assoluto. Le
stesse quindici righe stavano identiche anche in batnav e in Terminal
Beast: ora quel mestiere lo fa Acusticator, e qui resta soltanto cio' che
e' proprio di Gabryscola, cioe' quale suono va con quale evento.
"""

from GBUtils import Acusticator

EVENT_MAP = {
    "avvio": "gabryscola_avvio",
    "inserimento_nome": "gabryscola_conferma_nome",
    "gioco_carta": "gabryscola_gioca_carta",
    "presa_mia": "gabryscola_presa_giocatore",
    "presa_avversario": "gabryscola_presa_pc",
    "vittoria_partita": "gabryscola_vittoria",
    "sconfitta_partita": "gabryscola_sconfitta",
    "patta_partita": "gabryscola_patta",
    "mostra_classifica": "apertura",
    "chiusura": "gabryscola_chiusura",
    "nuovo_turno": "gabryscola_nuovo_turno",
    "nuova_partita": "partenza",
}


def play_preset_by_name(preset_name, sync=False):
    """Suona un preset della collezione condivisa chiamandolo per nome."""
    return Acusticator.play(preset_name, sync=sync)


def play_event(event_name, sync=False):
    """Suona il preset legato a un evento del gioco."""
    preset_name = EVENT_MAP.get(event_name)
    if not preset_name:
        return False
    return Acusticator.play(preset_name, sync=sync)
