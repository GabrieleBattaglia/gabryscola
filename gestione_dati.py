import json
import random
from datetime import date

CLASSIFICA_FILE = "briscola_charts.json"
CLASSIFICA_MAX_VOCI = 30


def generate_ai_name():
    consonanti = "BCDFGHJKLMNPQRSTVWXYZ"
    vocali = "AEIOU"
    c1, c2, c3 = (
        random.choice(consonanti),
        random.choice(consonanti),
        random.choice(consonanti),
    )
    v1, v2, v3 = random.choice(vocali), random.choice(vocali), random.choice(vocali)
    random_part = f"{c1}{v1}{c2}{v2}{c3}{v3}"
    formatted_part = random_part.lower().title()
    return f"IA-{formatted_part}"


def load_classifica():
    try:
        with open(CLASSIFICA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_classifica(classifica):
    with open(CLASSIFICA_FILE, "w") as f:
        json.dump(classifica, f, indent=4)


def update_and_display_classifica(
    classifica, winner_name, wins, ties, losses, total_points, partite_match
):
    new_entry = {
        "nome": winner_name,
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "punti_totali": total_points,
        "partite_match": partite_match,
        "data": date.today().strftime("%d/%m/%Y"),
    }
    classifica.append(new_entry)

    classifica_filtrata = [
        e for e in classifica if e.get("partite_match") == partite_match
    ]

    def get_sort_key(entry):
        w = entry.get("wins", 0)
        l = entry.get("losses", 0)
        p = entry.get("punti_totali", 0)
        tot = w + l
        win_rate = (w / tot) if tot > 0 else 0.0
        return (win_rate, p)

    classifica_filtrata.sort(key=get_sort_key, reverse=True)
    classifica_filtrata = classifica_filtrata[:CLASSIFICA_MAX_VOCI]

    print(f"\nClassifica Match al meglio di {partite_match}")
    print(f"{'Pos.':<5}{'Nome':<20}{'Risultato (V-P-S)':<20}{'Punti Tot.':<12}{'Data'}")
    for i, entry in enumerate(classifica_filtrata, 1):
        pos = f"{i}."
        nome = entry.get("nome", "N/D")
        w = entry.get("wins", 0)
        t = entry.get("ties", 0)
        l = entry.get("losses", 0)
        match_score_str = f"{w}-{t}-{l}"
        punti = entry.get("punti_totali", 0)
        data_partita = entry.get("data", "N/D")
        print(f"{pos:<5}{nome:<20}{match_score_str:<20}{punti:<12}{data_partita}")
    return classifica

