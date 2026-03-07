import json
import random
from datetime import date

CLASSIFICA_FILE = "briscola_charts.json"
CLASSIFICA_MAX_VOCI = 30

def generate_ai_name():
    consonanti = "BCDFGHJKLMNPQRSTVWXYZ"
    vocali = "AEIOU"
    c1, c2, c3 = random.choice(consonanti), random.choice(consonanti), random.choice(consonanti)
    v1, v2, v3 = random.choice(vocali), random.choice(vocali), random.choice(vocali)
    random_part = f"{c1}{v1}{c2}{v2}{c3}{v3}"
    formatted_part = random_part.lower().title()
    return f"IA-{formatted_part}"

def load_classifica():
    try:
        with open(CLASSIFICA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_classifica(classifica):
    with open(CLASSIFICA_FILE, 'w') as f:
        json.dump(classifica, f, indent=4)

def update_and_display_classifica(classifica, winner_name, wins, ties, losses, total_points):
    new_entry = {
        "nome": winner_name,
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "punti_totali": total_points,
        "data": date.today().strftime("%d/%m/%Y")
    }
    classifica.append(new_entry)
    
    def get_sort_key(entry):
        w = entry.get('wins', 0)
        t = entry.get('ties', 0)
        l = entry.get('losses', 0)
        p = entry.get('punti_totali', 0)
        match_points = (w * 1.0) + (t * 0.5)
        return (match_points, w, -l, p)

    classifica.sort(key=get_sort_key, reverse=True)
    classifica = classifica[:CLASSIFICA_MAX_VOCI]
    
    print("\n" + "="*72)
    print(" " * 30 + "CLASSIFICA" + " " * 32)
    print("="*72)
    print(f"{'Pos.':<5}{'Nome':<20}{'Risultato (V-P-S)':<20}{'Punti Tot.':<12}{'Data'}")
    print("-" * 72)
    for i, entry in enumerate(classifica, 1):
        pos = f"{i}."
        nome = entry.get('nome', 'N/D')
        w = entry.get('wins', 0)
        t = entry.get('ties', 0)
        l = entry.get('losses', 0)
        match_score_str = f"{w}-{t}-{l}"
        punti = entry.get('punti_totali', 0)
        data_partita = entry.get('data', 'N/D')
        print(f"{pos:<5}{nome:<20}{match_score_str:<20}{punti:<12}{data_partita}")
    print("-" * 72)
    return classifica