# Gabryscola, la Briscola da riga di comando contro l'intelligenza artificiale.
# Studiata per chi usa uno screen reader e per il display braille.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 08/09/2026: revisione 1 del refactoring generale. Messaggi alla seconda
# persona e senza decorazioni, classifica con le sole trenta migliori e senza
# gli abbandoni, ingressi con dgt e key, controllo degli aggiornamenti, stato
# del match passato al cervello, statistiche del calcolatore a fine match.

import faulthandler
import gc
import math
import sys
import time
from datetime import datetime

from GBUtils import dgt, gestisci_aggiornamento, key

from gestione_dati import (
    NOME_MAX,
    cartella_programma,
    inserisci_in_classifica,
    load_classifica,
    nuova_voce,
    posizione_in_classifica,
    pulisci_nome,
    righe_classifica,
    save_classifica,
)
from motore_briscola import FORFEIT, MotoreBriscola
from suoni import play_event
from version import VERSION

APP_NAME = "gabryscola"
API_RELEASE = "https://api.github.com/repos/GabrieleBattaglia/gabryscola/releases/latest"
PARTITE_MIN = 1
PARTITE_MAX = 11
PAUSA_FRA_PARTITE = 1.5


def _numero(valore):
    """I punti del match, con la virgola dove serve: 1, 1,5, 2."""
    if valore == int(valore):
        return str(int(valore))
    return str(valore).replace(".", ",")


def _conta(n, singolare, plurale):
    return f"{_numero(n)} {singolare if n == 1 else plurale}"


def punti_match(score):
    return score["wins"] + 0.5 * score["ties"]


def frase_traguardo(mancanti, rimaste, nome=None):
    """Quanto manca al traguardo del match, a te se nome e' None, altrimenti a nome."""
    if mancanti <= 0:
        return "Hai raggiunto il traguardo del match." if nome is None else f"{nome} ha raggiunto il traguardo del match."
    necessarie = math.ceil(mancanti)
    if necessarie > rimaste:
        return "Per te la rimonta è impossibile." if nome is None else f"Per {nome} la rimonta è impossibile."
    if necessarie == rimaste:
        if nome is None:
            return f"Devi vincerle tutte: {necessarie} su {rimaste}."
        return f"{nome} deve vincerle tutte: {necessarie} su {rimaste}."
    testo_punti = "mezzo punto" if mancanti == 0.5 else _conta(mancanti, "punto", "punti")
    verbo = "manca" if mancanti <= 1 else "mancano"
    vittorie = _conta(necessarie, "vittoria", "vittorie")
    if nome is None:
        return f"Ti {verbo} {testo_punti}: almeno {vittorie} su {rimaste}."
    return f"A {nome} {verbo} {testo_punti}: almeno {vittorie} su {rimaste}."


def stampa_riepilogo_match(gioco, risultati, numero_partite_match, partite_giocate):
    rimaste = numero_partite_match - partite_giocate
    if rimaste <= 0:
        return
    pc = gioco.giocatore_pc.nome
    pm_umano = punti_match(risultati[gioco.giocatore_umano.nome])
    pm_pc = punti_match(risultati[pc])
    traguardo = numero_partite_match / 2 + 0.5
    play_event("riepilogo")
    print(
        f"Match: tu {_numero(pm_umano)}, {pc} {_numero(pm_pc)}, "
        f"{_conta(rimaste, 'partita rimasta', 'partite rimaste')} su {numero_partite_match}."
    )
    print(frase_traguardo(traguardo - pm_umano, rimaste))
    print(frase_traguardo(traguardo - pm_pc, rimaste, pc))


def _aggiorna_classifica(gioco, vincitore, risultato, punti_totali, numero_partite_match):
    """Decide se il vincitore entra, chiede il nome se serve, salva e legge la classifica."""
    umano = vincitore is gioco.giocatore_umano
    classifica, avviso = load_classifica()
    if avviso:
        print(avviso)
    voce = nuova_voce(
        vincitore.nome, risultato["wins"], risultato["ties"], risultato["losses"], punti_totali, numero_partite_match
    )
    posizione = posizione_in_classifica(classifica, voce)
    if posizione is None:
        print("Il risultato non entra fra i primi trenta.")
        play_event("classifica")
        for riga in righe_classifica(classifica, numero_partite_match):
            print(riga)
        return
    if umano:
        play_event("entra_in_classifica")
        print(f"Entri in classifica al posto {posizione}.")
        nome = ""
        while not nome:
            nome = pulisci_nome(dgt("Il tuo nome: ", kind="s", smin=1, smax=NOME_MAX))
            if not nome:
                print("Serve un nome con almeno una lettera o una cifra.")
        voce["nome"] = nome
        play_event("conferma")
    else:
        print(f"{vincitore.nome} entra in classifica al posto {posizione}.")
    classifica = inserisci_in_classifica(classifica, voce)
    try:
        save_classifica(classifica)
        play_event("salvato")
        print("Classifica salvata.")
    except OSError as e:
        play_event("errore")
        print(f"Classifica non salvata: {e}")
    play_event("classifica")
    for riga in righe_classifica(classifica, numero_partite_match, nuova=voce):
        print(riga)


def avvia_match(gioco, numero_partite_match):
    umano, pc = gioco.giocatore_umano, gioco.giocatore_pc
    print(f"Sfidi {pc.nome} in un match al meglio di {numero_partite_match} partite.")
    gioco._decidi_primo_giocatore_match()
    risultati = {
        umano.nome: {"wins": 0, "ties": 0, "losses": 0},
        pc.nome: {"wins": 0, "ties": 0, "losses": 0},
    }
    punti_totali = {umano.nome: 0, pc.nome: 0}
    di_mano = gioco.primo_giocatore_del_match
    score_umano, score_pc = risultati[umano.nome], risultati[pc.nome]
    for i in range(numero_partite_match):
        print(f"Partita {i + 1}.")
        play_event("nuova_partita")
        gioco.match = {
            "partite": numero_partite_match,
            "vinte_pc": score_pc["wins"],
            "vinte_avv": score_umano["wins"],
            "patte": score_umano["ties"],
            "punti_pc": punti_totali[pc.nome],
            "punti_avv": punti_totali[umano.nome],
        }
        vincitore, punti_u, punti_pc = gioco.gioca_partita(di_mano)
        if vincitore == FORFEIT:
            print("Match abbandonato: non entra in classifica.")
            return
        punti_totali[umano.nome] += punti_u
        punti_totali[pc.nome] += punti_pc
        if vincitore is umano:
            score_umano["wins"] += 1
            score_pc["losses"] += 1
            print(f"Hai vinto la partita {i + 1}.")
            play_event("vittoria_partita")
        elif vincitore is pc:
            score_pc["wins"] += 1
            score_umano["losses"] += 1
            print(f"{pc.nome} ha vinto la partita {i + 1}.")
            play_event("sconfitta_partita")
        else:
            score_umano["ties"] += 1
            score_pc["ties"] += 1
            print(f"La partita {i + 1} è patta.")
            play_event("patta_partita")
        print(
            f"Parziale: {_conta(score_umano['wins'], 'vinta', 'vinte')}, "
            f"{_conta(score_umano['ties'], 'patta', 'patte')}, "
            f"{_conta(score_umano['losses'], 'persa', 'perse')}."
        )
        stampa_riepilogo_match(gioco, risultati, numero_partite_match, i + 1)
        rimaste = numero_partite_match - (i + 1)
        # Chi ha raggiunto il traguardo ha sempre un vantaggio maggiore delle
        # partite rimaste, e viceversa: la condizione sul distacco basta.
        if abs(punti_match(score_umano) - punti_match(score_pc)) > rimaste:
            play_event("match_anticipato")
            print("Il match termina in anticipo: la rimonta è impossibile.")
            break
        di_mano = pc if di_mano is umano else umano
        time.sleep(PAUSA_FRA_PARTITE)
    print("Match terminato.")
    pm_umano, pm_pc = punti_match(score_umano), punti_match(score_pc)
    motivo = ""
    if pm_umano > pm_pc:
        vincitore_match = umano
    elif pm_pc > pm_umano:
        vincitore_match = pc
    else:
        tot_u, tot_pc = punti_totali[umano.nome], punti_totali[pc.nome]
        print(f"Match in parità, {_numero(pm_umano)} a {_numero(pm_pc)}: decidono i punti totali, {tot_u} a {tot_pc}.")
        motivo = " ai punti totali"
        if tot_u > tot_pc:
            vincitore_match = umano
        elif tot_pc > tot_u:
            vincitore_match = pc
        else:
            play_event("match_patta")
            print("Match in patta assoluta, pari anche nei punti totali.")
            return
    if vincitore_match is umano:
        play_event("match_vinto")
        print(f"Hai vinto il match{motivo}.")
    else:
        play_event("match_perso")
        print(f"{pc.nome} ha vinto il match{motivo}.")
    _aggiorna_classifica(
        gioco, vincitore_match, risultati[vincitore_match.nome], punti_totali[vincitore_match.nome], numero_partite_match
    )


def _salva_log(gioco):
    orario = datetime.now()
    percorso = f"{cartella_programma()}/log_gabryscola_{orario.strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(percorso, "w", encoding="utf-8") as f:
            f.write(f"Log del match del {orario.strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("\n".join(gioco.log_partita))
        print(f"Log del match salvato in {percorso}.")
    except OSError as e:
        print(f"Log non salvato: {e}")


def _statistiche_cervello(gioco):
    s = gioco.statistiche_ia
    if not s["decisioni"]:
        return
    play_event("statistiche")
    print(
        f"Il calcolatore ha esaminato {s['mondi']} mondi possibili "
        f"in {s['tempo']:.0f} secondi di riflessione, "
        f"con {s['esatte']} decisioni esatte su {s['decisioni']}."
    )


def main():
    # Se il programma cade per un errore nativo, faulthandler scrive su
    # stderr in quale punto era: senza, un crash lascia solo un codice.
    faulthandler.enable()
    # Python 3.14.5 su Windows e' caduto piu' volte, nelle prove lunghe,
    # durante le raccolte del garbage collector in mezzo alla ricerca del
    # calcolatore. Il gioco non crea cicli di riferimenti, quindi il
    # conteggio dei riferimenti basta e il collector resta spento.
    gc.disable()
    args = [arg.lower() for arg in sys.argv[1:]]
    log_enabled = "logon" in args
    prompt_enabled = "noprompt" not in args
    print(f"Gabryscola {MotoreBriscola.VERSIONE}.")
    play_event("avvio")
    if gestisci_aggiornamento(APP_NAME, VERSION, API_RELEASE):
        play_event("chiusura", sync=True)
        return 0
    if log_enabled:
        print("Modalità log attivata.")
    if not prompt_enabled:
        print("Modalità senza prompt breve attivata.")
    print("Durante il gioco il punto di domanda apre la guida e q abbandona il match.")
    numero_partite = dgt(
        f"Match al meglio di quante partite? Da {PARTITE_MIN} a {PARTITE_MAX}: ",
        kind="i",
        imin=PARTITE_MIN,
        imax=PARTITE_MAX,
    )
    play_event("conferma")
    gioco = MotoreBriscola(nome_giocatore_umano="Tu")
    gioco.log_attivo = log_enabled
    gioco.prompt_attivo = prompt_enabled
    avvia_match(gioco, numero_partite)
    if gioco.log_attivo:
        _salva_log(gioco)
    _statistiche_cervello(gioco)
    play_event("chiusura", sync=True)
    print("Premi un tasto per uscire.", end="", flush=True)
    key()
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
