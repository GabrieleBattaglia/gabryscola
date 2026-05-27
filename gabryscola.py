import math
import time
import sys
from datetime import datetime
from motore_briscola import MotoreBriscola
from gestione_dati import (
    load_classifica,
    update_and_display_classifica,
    save_classifica,
)
from suoni import play_event


def stampa_riepilogo_match(
    gioco, risultati, punti_totali, numero_partite_match, partite_giocate
):
    partite_rimanenti = numero_partite_match - partite_giocate
    if partite_rimanenti <= 0:
        return

    score_umano = risultati[gioco.giocatore_umano.nome]
    score_pc = risultati[gioco.giocatore_pc.nome]
    punti_match_umano = (score_umano["wins"] * 1.0) + (score_umano["ties"] * 0.5)
    punti_match_pc = (score_pc["wins"] * 1.0) + (score_pc["ties"] * 0.5)
    punti_target_vittoria = (numero_partite_match / 2.0) + 0.5

    def fmt(v):
        return int(v) if v % 1 == 0 else v

    print(
        f"\nMatch: {gioco.giocatore_umano.nome} {fmt(punti_match_umano)} - "
        f"{gioco.giocatore_pc.nome} {fmt(punti_match_pc)} "
        f"(rimaste {partite_rimanenti} di {numero_partite_match})"
    )

    punti_mancanti_umano = punti_target_vittoria - punti_match_umano
    if punti_mancanti_umano <= 0:
        msg_umano = "In forte vantaggio, mantieni la concentrazione."
    else:
        vittorie_necessarie = math.ceil(punti_mancanti_umano)
        if vittorie_necessarie > partite_rimanenti:
            msg_umano = "Rimonta matematicamente impossibile."
        elif vittorie_necessarie == partite_rimanenti:
            msg_umano = f"Devi vincerle tutte ({vittorie_necessarie} su {partite_rimanenti})."
        else:
            msg_umano = (
                f"Mancano {fmt(punti_mancanti_umano)} punti (almeno {vittorie_necessarie} "
                f"vittorie su {partite_rimanenti} partite)."
            )
    print(f"  {gioco.giocatore_umano.nome}: {msg_umano}")

    punti_mancanti_pc = punti_target_vittoria - punti_match_pc
    if punti_mancanti_pc <= 0:
        msg_pc = "In vantaggio, attacca per recuperare."
    else:
        vittorie_necessarie_pc = math.ceil(punti_mancanti_pc)
        if vittorie_necessarie_pc > partite_rimanenti:
            msg_pc = "Rimonta matematicamente impossibile."
        elif vittorie_necessarie_pc == partite_rimanenti:
            msg_pc = f"Deve vincerle tutte ({vittorie_necessarie_pc} su {partite_rimanenti})."
        else:
            msg_pc = (
                f"Mancano {fmt(punti_mancanti_pc)} punti (almeno {vittorie_necessarie_pc} "
                f"vittorie su {partite_rimanenti} partite)."
            )
    print(f"  {gioco.giocatore_pc.nome}: {msg_pc}")



def avvia_match(gioco, numero_partite_match):
    print(f"Benvenuto a Gabryscola v{MotoreBriscola.VERSIONE}")
    print(
        f"Oggi {gioco.giocatore_umano.nome} sfida {gioco.giocatore_pc.nome} in un match al meglio di {numero_partite_match} partite!"
    )
    gioco._decidi_primo_giocatore_match()

    risultati = {
        gioco.giocatore_umano.nome: {"wins": 0, "ties": 0, "losses": 0},
        gioco.giocatore_pc.nome: {"wins": 0, "ties": 0, "losses": 0},
    }
    punti_totali = {gioco.giocatore_umano.nome: 0, gioco.giocatore_pc.nome: 0}
    giocatore_di_mano_corrente = gioco.primo_giocatore_del_match

    for i in range(numero_partite_match):
        print(f"\nPartita {i + 1}")

        play_event("nuova_partita")

        vincitore_partita, punti_u, punti_pc = gioco.gioca_partita(
            giocatore_di_mano_corrente
        )

        if vincitore_partita == "FORFEIT":
            print("\nMatch abbandonato dall'utente.")
            risultati[gioco.giocatore_pc.nome]["wins"] = numero_partite_match
            break

        punti_totali[gioco.giocatore_umano.nome] += punti_u
        punti_totali[gioco.giocatore_pc.nome] += punti_pc

        if vincitore_partita:
            vincitore_nome = vincitore_partita.nome
            perdente_nome = (
                gioco.giocatore_pc.nome
                if vincitore_partita == gioco.giocatore_umano
                else gioco.giocatore_umano.nome
            )
            risultati[vincitore_nome]["wins"] += 1
            risultati[perdente_nome]["losses"] += 1
            print(f"\n>> {vincitore_nome} vince la partita {i + 1}! <<")
            if vincitore_partita == gioco.giocatore_umano:
                play_event("vittoria_partita")
            else:
                play_event("sconfitta_partita")
        else:
            risultati[gioco.giocatore_umano.nome]["ties"] += 1
            risultati[gioco.giocatore_pc.nome]["ties"] += 1
            print("\n>> La partita è finita in pareggio! <<")
            play_event("patta_partita")

        score_umano = risultati[gioco.giocatore_umano.nome]
        score_pc = risultati[gioco.giocatore_pc.nome]
        print(
            f"Risultato parziale (V-P-S): {gioco.giocatore_umano.nome} {score_umano['wins']}-{score_umano['ties']}-{score_umano['losses']} vs {gioco.giocatore_pc.nome} {score_pc['wins']}-{score_pc['ties']}-{score_pc['losses']}"
        )

        stampa_riepilogo_match(
            gioco, risultati, punti_totali, numero_partite_match, i + 1
        )

        punti_match_umano = (score_umano["wins"] * 1.0) + (score_umano["ties"] * 0.5)
        punti_match_pc = (score_pc["wins"] * 1.0) + (score_pc["ties"] * 0.5)
        partite_rimanenti = numero_partite_match - (i + 1)

        punti_target_vittoria = (numero_partite_match / 2.0) + 0.5
        if (
            punti_match_umano >= punti_target_vittoria
            or punti_match_pc >= punti_target_vittoria
        ):
            if abs(punti_match_umano - punti_match_pc) > partite_rimanenti:
                print(
                    "\nIl match termina in anticipo: la rimonta è matematicamente impossibile."
                )
                break

        giocatore_di_mano_corrente = (
            gioco.giocatore_pc
            if giocatore_di_mano_corrente == gioco.giocatore_umano
            else gioco.giocatore_umano
        )
        time.sleep(1.5)

    print("\nMatch terminato!")

    score_umano = risultati[gioco.giocatore_umano.nome]
    score_pc = risultati[gioco.giocatore_pc.nome]
    punti_match_umano = (score_umano["wins"] * 1.0) + (score_umano["ties"] * 0.5)
    punti_match_pc = (score_pc["wins"] * 1.0) + (score_pc["ties"] * 0.5)
    vincitore_match = None
    motivo_vittoria = ""

    if punti_match_umano > punti_match_pc:
        vincitore_match = gioco.giocatore_umano
    elif punti_match_pc > punti_match_umano:
        vincitore_match = gioco.giocatore_pc
    else:
        punti_u = punti_totali[gioco.giocatore_umano.nome]
        punti_pc = punti_totali[gioco.giocatore_pc.nome]
        print(
            f"Il match è in parità di punteggio ({punti_match_umano}-{punti_match_pc}). Si decide ai punti totali ({punti_u}-{punti_pc})."
        )
        if punti_u > punti_pc:
            vincitore_match = gioco.giocatore_umano
            motivo_vittoria = " (vittoria ai punti)"
        elif punti_pc > punti_u:
            vincitore_match = gioco.giocatore_pc
            motivo_vittoria = " (vittoria ai punti)"

    if vincitore_match:
        print(
            f"{vincitore_match.nome.upper()} hai vinto il match{motivo_vittoria}!"
        )

        res_vincitore = risultati[vincitore_match.nome]
        classifica = load_classifica()

        classifica_filtrata = [
            e for e in classifica if e.get("partite_match") == numero_partite_match
        ]

        def get_sort_key(entry):
            w = entry.get("wins", 0)
            l = entry.get("losses", 0)
            p = entry.get("punti_totali", 0)
            tot = w + l
            win_rate = (w / tot) if tot > 0 else 0.0
            return (win_rate, p)

        classifica_filtrata.sort(key=get_sort_key, reverse=True)

        entra_in_classifica = False
        if len(classifica_filtrata) < 30:
            entra_in_classifica = True
        else:
            w = res_vincitore["wins"]
            l = res_vincitore["losses"]
            p = punti_totali[vincitore_match.nome]
            tot = w + l
            new_win_rate = (w / tot) if tot > 0 else 0.0
            new_key = (new_win_rate, p)

            last_entry = classifica_filtrata[-1]
            lw = last_entry.get("wins", 0)
            ll = last_entry.get("losses", 0)
            lp = last_entry.get("punti_totali", 0)
            ltot = lw + ll
            last_win_rate = (lw / ltot) if ltot > 0 else 0.0
            last_key = (last_win_rate, lp)

            if new_key > last_key:
                entra_in_classifica = True

        nome_salvataggio = vincitore_match.nome
        if vincitore_match == gioco.giocatore_umano and entra_in_classifica:
            play_event("inserimento_nome")
            nome_input = ""
            while not nome_input:
                nome_input = input(
                    "Complimenti, sei in classifica! Inserisci il tuo nome: "
                ).strip()
                if not nome_input:
                    print("Il nome non può essere vuoto. Riprova.")
            nome_salvataggio = nome_input.title()

        play_event("mostra_classifica")
        classifica_aggiornata = update_and_display_classifica(
            classifica,
            nome_salvataggio,
            res_vincitore["wins"],
            res_vincitore["ties"],
            res_vincitore["losses"],
            punti_totali[vincitore_match.nome],
            numero_partite_match,
        )
        save_classifica(classifica_aggiornata)
        print("\nClassifica salvata. Grazie per aver giocato!")
    else:
        print(
            "Incredibile! Il match è finito in PATTA ASSOLUTA, anche nei punti totali!"
        )


if __name__ == "__main__":
    args = [arg.lower() for arg in sys.argv]
    log_enabled = "logon" in args
    prompt_enabled = "noprompt" not in args

    print(f"Gabryscola v{MotoreBriscola.VERSIONE}")
    play_event("avvio")
    if log_enabled:
        print(">>> Modalità LOG attivata. <<<")
    if not prompt_enabled:
        print(">>> Modalità NOPROMPT attivata. <<<")

    numero_partite = 0
    while True:
        try:
            num_input = input("Match al meglio di quante partite? (1-11): ").strip()
            numero_partite = int(num_input)
            if 1 <= numero_partite <= 11:
                play_event("inserimento_nome")
                break
            else:
                print("Per favore, inserisci un numero da 1 a 11.")
        except ValueError:
            print("Input non valido. Inserisci un numero.")

    gioco = MotoreBriscola(nome_giocatore_umano="Tu")
    gioco.log_attivo = log_enabled
    gioco.prompt_attivo = prompt_enabled

    avvia_match(gioco, numero_partite)

    if gioco.log_attivo:
        timestamp_match = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_file = f"log_{gioco.giocatore_umano.nome}_{timestamp_match}.txt"
        with open(nome_file, "w", encoding="utf-8") as f:
            f.write(f"Log Match del {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("\n".join(gioco.log_partita))
        print(f"\nLog del match salvato nel file: {nome_file}")

    play_event("chiusura", sync=True)
    input("\nPremi Invio per uscire...")
