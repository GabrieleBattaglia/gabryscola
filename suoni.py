import os
import json
import GBUtils
from GBUtils import Acusticator
DEFAULT_VOL = 0.5
_db = {}
try:
    gbutils_dir = os.path.dirname(GBUtils.__file__)
    db_path = os.path.join(gbutils_dir, "Acu_Collection.json")
    with open(db_path, "r", encoding="utf-8") as f:
        _db = json.load(f)
except Exception:
    pass
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
    "nuova_partita": "partenza"
}
def play_preset_by_name(preset_name, sync=False):
    try:
        preset_data = _db.get(preset_name)
        if not preset_data:
            return
        score_flat = []
        for q in preset_data["score"]:
            note, dur, pan, vol_delta = q
            vol = max(0.0, min(1.0, DEFAULT_VOL + vol_delta))
            score_flat.extend([note, dur, pan, vol])
        Acusticator(score_flat, kind=preset_data["kind"], adsr=preset_data["adsr"], sync=sync)
    except Exception:
        pass
def play_event(event_name, sync=False):
    preset_name = EVENT_MAP.get(event_name)
    if preset_name:
        play_preset_by_name(preset_name, sync=sync)
