# Gabryscola, i dati: la classifica su disco e i nomi dell'intelligenza artificiale.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 08/09/2026: la classifica vive accanto al programma, si salva su file
# temporaneo con copia di riserva, tiene solo le trenta migliori per lunghezza
# di match e alla lettura scarta le voci senza tutti i campi. Chi entra e a
# che posto lo decide qui, non chi stampa.

"""La classifica di Gabryscola.

Una voce per ogni match concluso con un vincitore, umano o calcolatore, che
sia fra le trenta migliori dei match della stessa lunghezza. L'ordine e' per
quota di vittorie sulle partite decise e poi per punti totali. Un match
abbandonato non e' concluso e non lascia traccia.
Il modulo non stampa: restituisce liste di righe gia' pensate per la lettura
con lo screen reader e per il display braille, e solleva OSError quando il
disco non collabora, cosi' che chi chiama lo dica a modo suo.
"""

import json
import os
import random
import sys
from datetime import date

CLASSIFICA_NOME = "briscola_charts.json"
CLASSIFICA_MAX_VOCI = 30
CAMPI_VOCE = ("nome", "wins", "ties", "losses", "punti_totali", "partite_match", "data")
CAMPI_NUMERICI = ("wins", "ties", "losses", "punti_totali", "partite_match")
NOME_MAX = 20


def cartella_programma():
    """La cartella dell'eseguibile compilato, oppure quella del sorgente."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def percorso_classifica():
    return os.path.join(cartella_programma(), CLASSIFICA_NOME)


def generate_ai_name():
    """Un nome pronunciabile per il calcolatore, per esempio IA-Fofolu."""
    consonanti = "BCDFGHJKLMNPQRSTVWXYZ"
    vocali = "AEIOU"
    lettere = []
    for _ in range(3):
        lettere.append(random.choice(consonanti))
        lettere.append(random.choice(vocali))
    return "IA-" + "".join(lettere).lower().title()


def pulisci_nome(nome):
    """Toglie i caratteri di controllo e gli spazi ai bordi, e accorcia."""
    testo = "".join(ch for ch in str(nome) if ch.isprintable()).strip()
    return testo[:NOME_MAX].title()


def _voce_valida(voce):
    if not isinstance(voce, dict):
        return False
    if any(campo not in voce for campo in CAMPI_VOCE):
        return False
    if not isinstance(voce["nome"], str) or not isinstance(voce["data"], str):
        return False
    for campo in CAMPI_NUMERICI:
        valore = voce[campo]
        if isinstance(valore, bool) or not isinstance(valore, int) or valore < 0:
            return False
    return True


def _leggi(percorso):
    """Legge un file della classifica. Solleva OSError o ValueError."""
    with open(percorso, encoding="utf-8") as f:
        dati = json.load(f)
    if not isinstance(dati, list):
        raise ValueError("il contenuto non e' una lista di voci")
    return [voce for voce in dati if _voce_valida(voce)]


def load_classifica():
    """Restituisce la classifica e un avviso, vuoto se e' andato tutto bene.

    Un file assente e' normale, e' la prima partita. Un file illeggibile
    non viene toccato: si prova la copia di riserva, e se manca anche quella
    si riparte da vuoto dicendolo.
    """
    percorso = percorso_classifica()
    if not os.path.exists(percorso):
        return [], ""
    try:
        return _leggi(percorso), ""
    except (OSError, ValueError) as e:
        avviso = f"La classifica non si legge: {e}."
    riserva = percorso + ".bak"
    if os.path.exists(riserva):
        try:
            return _leggi(riserva), avviso + " Uso la copia di riserva."
        except (OSError, ValueError):
            pass
    return [], avviso + " Riparto da una classifica vuota."


def save_classifica(classifica):
    """Scrive su file temporaneo e sostituisce, tenendo la copia di riserva.

    Solleva OSError se il disco non collabora: chi chiama lo dice all'utente.
    """
    percorso = percorso_classifica()
    temporaneo = percorso + ".tmp"
    with open(temporaneo, "w", encoding="utf-8") as f:
        json.dump(classifica, f, indent=4, ensure_ascii=False)
    if os.path.exists(percorso):
        os.replace(percorso, percorso + ".bak")
    os.replace(temporaneo, percorso)


def chiave_ordinamento(voce):
    """Prima la quota di vittorie sulle partite decise, poi i punti totali."""
    vinte, perse = voce["wins"], voce["losses"]
    decise = vinte + perse
    quota = vinte / decise if decise else 0.0
    return (quota, voce["punti_totali"])


def classifica_per_match(classifica, partite_match):
    """Le voci dei match di quella lunghezza, dalla migliore alla peggiore.

    L'ordinamento e' stabile: a parita' di chiave resta davanti chi c'era
    prima, quindi un risultato nuovo non scavalca mai uno uguale gia' in
    classifica.
    """
    voci = [voce for voce in classifica if voce["partite_match"] == partite_match]
    voci.sort(key=chiave_ordinamento, reverse=True)
    return voci


def nuova_voce(nome, wins, ties, losses, punti_totali, partite_match):
    return {
        "nome": nome,
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "punti_totali": punti_totali,
        "partite_match": partite_match,
        "data": date.today().strftime("%d/%m/%Y"),
    }


def posizione_in_classifica(classifica, voce):
    """La posizione, da uno, che la voce otterrebbe; None se non entra."""
    chiave = chiave_ordinamento(voce)
    davanti = sum(
        1
        for altra in classifica_per_match(classifica, voce["partite_match"])
        if chiave_ordinamento(altra) >= chiave
    )
    posizione = davanti + 1
    return posizione if posizione <= CLASSIFICA_MAX_VOCI else None


def inserisci_in_classifica(classifica, voce):
    """Aggiunge la voce e taglia la sua lunghezza di match alle trenta migliori.

    Restituisce la classifica nuova, senza toccare quella ricevuta.
    """
    altre = [v for v in classifica if v["partite_match"] != voce["partite_match"]]
    stesse = classifica_per_match([*classifica, voce], voce["partite_match"])
    return altre + stesse[:CLASSIFICA_MAX_VOCI]


def _conta(n, singolare, plurale):
    return f"{n} {singolare if n == 1 else plurale}"


def righe_classifica(classifica, partite_match, nuova=None):
    """Le righe da leggere, due frasi corte per ogni voce.

    La voce appena entrata, se passata, viene segnalata come nuova.
    """
    voci = classifica_per_match(classifica, partite_match)
    righe = [f"Classifica dei match al meglio di {partite_match}."]
    if not voci:
        righe.append("Ancora nessun risultato.")
        return righe
    for posizione, voce in enumerate(voci, 1):
        marca = ", nuova" if voce is nuova else ""
        righe.append(
            f"{posizione}. {voce['nome']}{marca}: "
            f"{_conta(voce['wins'], 'vinta', 'vinte')}, "
            f"{_conta(voce['ties'], 'patta', 'patte')}, "
            f"{_conta(voce['losses'], 'persa', 'perse')}."
        )
        righe.append(f"{_conta(voce['punti_totali'], 'punto', 'punti')}, il {voce['data']}.")
    return righe
