import math
import time
from datetime import datetime
from motore_briscola import MotoreBriscola
from gestione_dati import (
    load_classifica,
    update_and_display_classifica,
    save_classifica,
)


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

    print("\n" + "--- Riepilogo Strategico Match ---")
    print(
        f"Partite giocate: {partite_giocate} di {numero_partite_match}. Partite rimanenti: {partite_rimanenti}."
    )
    punti_target_vittoria = (numero_partite_match / 2.0) + 0.5

    punti_mancanti_umano = punti_target_vittoria - punti_match_umano
    print(
        f"\nSituazione per {gioco.giocatore_umano.nome} (Punti Match: {punti_match_umano}):"
    )
    if punti_mancanti_umano <= 0:
        print("  Sei in una posizione di forte vantaggio. Mantieni la concentrazione!")
    else:
        vittorie_necessarie = math.ceil(punti_mancanti_umano)
        if vittorie_necessarie > partite_rimanenti:
            print("  La rimonta è matematicamente impossibile. Il match è perso.")
        elif vittorie_necessarie == partite_rimanenti:
            print(
                f"  Situazione critica: devi vincerle tutte! Ti servono {vittorie_necessarie} vittorie su {partite_rimanenti} partite."
            )
        else:
            print(
                f"  Per vincere ti servono ancora {punti_mancanti_umano} punti. Un possibile percorso è vincere {vittorie_necessarie} delle prossime {partite_rimanenti} partite."
            )

    punti_mancanti_pc = punti_target_vittoria - punti_match_pc
    print(f"Situazione per {gioco.giocatore_pc.nome} (Punti Match: {punti_match_pc}):")
    if punti_mancanti_pc <= 0:
        print("  È in vantaggio. Bisogna attaccare per recuperare.")
    else:
        vittorie_necessarie_pc = math.ceil(punti_mancanti_pc)
        if vittorie_necessarie_pc > partite_rimanenti:
            print("  La sua rimonta è matematicamente impossibile.")
        else:
            print(
                f"  Gli servono ancora {punti_mancanti_pc} punti. Deve vincere almeno {vittorie_necessarie_pc} delle prossime {partite_rimanenti} partite."
            )
    print("------------------------------------")


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
        print("\n" + "#" * 50)
        print(f"#{'':<19} PARTITA {i + 1} {'':<19}#")
        print("#" * 50)

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
        else:
            risultati[gioco.giocatore_umano.nome]["ties"] += 1
            risultati[gioco.giocatore_pc.nome]["ties"] += 1
            print("\n>> La partita è finita in pareggio! <<")

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

    print("\n" + "=" * 40 + "\nMATCH TERMINATO!\n" + "=" * 40)
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
            f"🎉🎉🎉 {vincitore_match.nome.upper()} HAI VINTO IL MATCH{motivo_vittoria}! 🎉🎉🎉"
        )
        res_vincitore = risultati[vincitore_match.nome]
        classifica = load_classifica()
        classifica_aggiornata = update_and_display_classifica(
            classifica,
            vincitore_match.nome,
            res_vincitore["wins"],
            res_vincitore["ties"],
            res_vincitore["losses"],
            punti_totali[vincitore_match.nome],
        )
        save_classifica(classifica_aggiornata)
        print("\nClassifica salvata. Grazie per aver giocato!")
    else:
        print(
            "Incredibile! Il match è finito in PATTA ASSOLUTA, anche nei punti totali!"
        )


if __name__ == "__main__":
    log_enabled = False
    prompt_enabled = True
    nome_giocatore = ""

    print(f"Gabryscola v{MotoreBriscola.VERSIONE}")
    print(
        "Digita 'logon' per attivare la modalità di debug o 'noprompt' per nascondere i prompt."
    )

    while not nome_giocatore:
        nome_input = input("Inserisci il tuo nome per la sfida: ").strip()

        if nome_input.lower() == "logon":
            log_enabled = True
            print(
                ">>> Modalità LOG attivata. I dati della partita verranno salvati. Reinserisci il tuo nome. <<<"
            )
            continue
        elif nome_input.lower() == "noprompt":
            prompt_enabled = False
            print(
                ">>> Modalità NOPROMPT attivata. I prompt verranno nascosti. Reinserisci il tuo nome. <<<"
            )
            continue

        if not nome_input:
            print("Il nome non può essere vuoto. Riprova.")
        else:
            nome_giocatore = nome_input.title()

    numero_partite = 0
    while True:
        try:
            num_input = input("Match al meglio di quante partite? (1-11): ").strip()
            numero_partite = int(num_input)
            if 1 <= numero_partite <= 11:
                break
            else:
                print("Per favore, inserisci un numero da 1 a 11.")
        except ValueError:
            print("Input non valido. Inserisci un numero.")

    gioco = MotoreBriscola(nome_giocatore_umano=nome_giocatore)
    gioco.log_attivo = log_enabled
    gioco.prompt_attivo = prompt_enabled

    avvia_match(gioco, numero_partite)

    if gioco.log_attivo:
        timestamp_match = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_file = f"log_{gioco.giocatore_umano.nome}_{timestamp_match}.txt"
        with open(nome_file, "w", encoding="utf-8") as f:
            f.write(f"Log Match del {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("=" * 40 + "\n")
            f.write("\n".join(gioco.log_partita))
        print(f"\nLog del match salvato nel file: {nome_file}")

    input("\nPremi Invio per uscire...")
