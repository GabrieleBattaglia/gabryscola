# Gabryscola, i suoni: la mappa fra gli eventi del gioco e i preset condivisi.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 03/09/2026: la lettura della collezione e' passata ad Acusticator.
# 08/09/2026: un suono per ogni evento, chi gioca a sinistra e il calcolatore
# a destra, rumori di carte nuovi nella collezione condivisa.

"""Collega gli eventi del gioco ai suoni della collezione condivisa.

Fino alla 3.1.0 questo file si leggeva da solo Acu_Collection.json e si
riscriveva la conversione dei volumi: ora quel mestiere lo fa Acusticator,
e qui resta soltanto cio' che e' proprio di Gabryscola, cioe' quale suono
va con quale evento e da quale lato si sente.
Ogni evento ha un lato: meno uno per chi gioca, che sta a sinistra, piu'
uno per il calcolatore, che sta a destra, zero per cio' che e' di tutti e
due. Il panorama e' quello di Acusticator, che ogni quartina dello score
porta con se': al momento di suonare si aggiunge lo spostamento del lato
al pan di ogni quartina, lasciando com'e' il preset nella collezione, che
vale per tutti i programmi. Manca solo un parametro di play o di preset
che faccia questa somma per conto suo: e' la issue 18 su GBUtils.
"""

from GBUtils import Acusticator

SPOSTAMENTO = 0.6
SINISTRA, CENTRO, DESTRA = -1, 0, 1

EVENTI = {
    "avvio": ("gabryscola_avvio", CENTRO),
    "conferma": ("gabryscola_conferma_nome", CENTRO),
    "mescola": ("mazzo_mescolato", CENTRO),
    "briscola": ("carta_girata", CENTRO),
    "nuova_partita": ("partenza", CENTRO),
    "nuovo_turno": ("gabryscola_nuovo_turno", CENTRO),
    "carta_tu": ("carta_giocata", SINISTRA),
    "carta_pc": ("carta_giocata", DESTRA),
    "pesca_tu": ("carta_pescata", SINISTRA),
    "pesca_pc": ("carta_pescata", DESTRA),
    "presa_tu": ("gabryscola_presa_giocatore", SINISTRA),
    "presa_pc": ("gabryscola_presa_pc", DESTRA),
    "moneta": ("moneta_raccolta", CENTRO),
    "errore": ("errore_secco", CENTRO),
    "domanda": ("campanellino", CENTRO),
    "annullato": ("annullato", CENTRO),
    "vittoria_partita": ("gabryscola_vittoria", SINISTRA),
    "sconfitta_partita": ("gabryscola_sconfitta", DESTRA),
    "patta_partita": ("gabryscola_patta", CENTRO),
    "riepilogo": ("sys_tick_basso", CENTRO),
    "match_anticipato": ("avviso_di_sistema", CENTRO),
    "match_vinto": ("fanfara_retro", SINISTRA),
    "match_perso": ("jingle_missione_fallita", DESTRA),
    "match_patta": ("gabryscola_patta", CENTRO),
    "entra_in_classifica": ("jingle_livello_superato", CENTRO),
    "salvato": ("doppio_tic_conferma", CENTRO),
    "classifica": ("apertura", CENTRO),
    "manuale": ("apertura", CENTRO),
    "statistiche": ("sys_tick_alto", CENTRO),
    "chiusura": ("gabryscola_chiusura", CENTRO),
}


def sposta(score, lato):
    """Sposta verso un lato i panorami numerici di uno score appiattito.

    Lo score che esce da Acusticator.preset e' una lista piatta di quartine:
    nota, durata, panorama, volume. I panorami scritti come stringhe, cioe'
    quelli che scivolano, restano come sono.
    """
    spostato = list(score)
    for i in range(2, len(spostato), 4):
        pan = spostato[i]
        if isinstance(pan, (int, float)):
            spostato[i] = max(-1.0, min(1.0, pan + SPOSTAMENTO * lato))
    return spostato


def play_event(event_name, sync=True):
    """Suona il preset legato a un evento del gioco, dal lato giusto.

    I suoni sono sincroni: ognuno finisce prima che il gioco prosegua,
    cosi' non si accavallano, ognuno ha il suo momento, e nessuno sta
    suonando mentre il calcolatore riflette. Chi vuole tornare subito
    passa sync falso.
    """
    voce = EVENTI.get(event_name)
    if voce is None:
        return False
    nome, lato = voce
    if lato == CENTRO:
        return Acusticator.play(nome, sync=sync)
    score, kind, adsr = Acusticator.preset(nome)
    if not score:
        return False
    Acusticator(sposta(score, lato), kind=kind, adsr=adsr, sync=sync)
    return True
