# Gabryscola, prova di un match intero senza console: messaggi, classifica e abbandono.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import json
import random
import time

import pytest

import gabryscola
import gestione_dati as gd
import motore_briscola
import suoni


@pytest.fixture
def tavolo_muto(monkeypatch, tmp_path):
    """Niente suoni, niente attese, un umano casuale e la classifica in una cartella vuota."""
    monkeypatch.setattr(suoni, "play_event", lambda *a, **k: False)
    monkeypatch.setattr(motore_briscola, "play_event", lambda *a, **k: False)
    monkeypatch.setattr(gabryscola, "play_event", lambda *a, **k: False)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setattr(gd, "percorso_classifica", lambda: str(tmp_path / "briscola_charts.json"))
    rng = random.Random(4)

    def scelta_casuale(self):
        return self.giocatore_umano.mano.pop(rng.randrange(len(self.giocatore_umano.mano)))

    monkeypatch.setattr(motore_briscola.MotoreBriscola, "_chiedi_carta", scelta_casuale)
    monkeypatch.setattr(gabryscola, "dgt", lambda *a, **k: "  gabry battaglia ")
    return tmp_path


def _gioco():
    gioco = motore_briscola.MotoreBriscola("Tu", tempo_riflessione=0.02)
    gioco.log_attivo = True
    return gioco


def test_un_match_intero_parla_bene_e_salva_la_classifica(tavolo_muto, capsys):
    gioco = _gioco()
    gabryscola.avvia_match(gioco, 1)
    testo = capsys.readouterr().out
    righe = testo.splitlines()
    assert "Match terminato." in righe
    assert all(riga.strip() for riga in righe), "nessuna riga vuota"
    assert not any(">>" in r or "<<" in r or "===" in r or "---" in r for r in righe)
    assert not any(r.startswith("Tu ") for r in righe), "il giocatore non e' un soggetto in terza persona"
    assert any(r.startswith("Giochi: ") for r in righe)
    assert any(r.startswith("Peschi: ") for r in righe)
    assert any(r.startswith("Partita terminata: hai ") for r in righe)
    assert any("ha vinto il match" in r or "Hai vinto il match" in r or "patta assoluta" in r for r in righe)
    percorso = tavolo_muto / "briscola_charts.json"
    if percorso.exists():
        voci = json.loads(percorso.read_text(encoding="utf-8"))
        assert len(voci) == 1
        assert voci[0]["nome"] in ("Gabry Battaglia", gioco.giocatore_pc.nome)
        assert voci[0]["partite_match"] == 1
        assert any(r.startswith("1. ") and ", nuova:" in r for r in righe)
    else:
        assert "patta assoluta" in testo
    assert gioco.statistiche_ia["decisioni"] >= 15
    assert any(riga.startswith("GIOCA ") for riga in gioco.log_partita)


def test_l_abbandono_non_tocca_la_classifica(tavolo_muto, capsys, monkeypatch):
    gioco = _gioco()
    monkeypatch.setattr(motore_briscola.MotoreBriscola, "_chiedi_carta", lambda self: motore_briscola.FORFEIT)
    gabryscola.avvia_match(gioco, 3)
    testo = capsys.readouterr().out
    assert "Match abbandonato: non entra in classifica." in testo
    assert not (tavolo_muto / "briscola_charts.json").exists()


def test_il_riepilogo_del_match_dice_il_vero():
    assert gabryscola.frase_traguardo(0, 1) == "Hai raggiunto il traguardo del match."
    assert gabryscola.frase_traguardo(2, 1, "IA-Bofolu") == "Per IA-Bofolu la rimonta è impossibile."
    assert gabryscola.frase_traguardo(2, 2) == "Devi vincerle tutte: 2 su 2."
    assert gabryscola.frase_traguardo(0.5, 2) == "Ti manca mezzo punto: almeno 1 vittoria su 2."
    assert gabryscola.frase_traguardo(1.5, 3, "IA-Bofolu") == "A IA-Bofolu mancano 1,5 punti: almeno 2 vittorie su 3."
