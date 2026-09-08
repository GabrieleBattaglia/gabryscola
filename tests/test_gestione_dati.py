# Gabryscola, prove sulla classifica: lettura, salvataggio, ingresso e taglio.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import json

import pytest

import gestione_dati as gd


@pytest.fixture
def classifica_in(tmp_path, monkeypatch):
    percorso = tmp_path / "briscola_charts.json"
    monkeypatch.setattr(gd, "percorso_classifica", lambda: str(percorso))
    return percorso


def _voce(nome, wins, losses, punti, partite=3, ties=0):
    return gd.nuova_voce(nome, wins, ties, losses, punti, partite)


def test_file_assente_e_normale(classifica_in):
    assert gd.load_classifica() == ([], "")


def test_salva_e_rilegge_con_copia_di_riserva(classifica_in):
    gd.save_classifica([_voce("Gabry", 2, 1, 190)])
    gd.save_classifica([_voce("Gabry", 2, 1, 190), _voce("Altro", 1, 2, 150)])
    classifica, avviso = gd.load_classifica()
    assert avviso == ""
    assert [v["nome"] for v in classifica] == ["Gabry", "Altro"]
    riserva = json.loads(classifica_in.with_suffix(".json.bak").read_text(encoding="utf-8"))
    assert [v["nome"] for v in riserva] == ["Gabry"]


def test_file_rotto_usa_la_riserva_e_lo_dice(classifica_in):
    gd.save_classifica([_voce("Gabry", 2, 1, 190)])
    gd.save_classifica([_voce("Gabry", 2, 1, 190)])
    classifica_in.write_text("{ rotto", encoding="utf-8")
    classifica, avviso = gd.load_classifica()
    assert [v["nome"] for v in classifica] == ["Gabry"]
    assert "riserva" in avviso


def test_file_rotto_senza_riserva_riparte_da_vuoto(classifica_in):
    classifica_in.write_text("[1, 2", encoding="utf-8")
    classifica, avviso = gd.load_classifica()
    assert classifica == []
    assert "vuota" in avviso


def test_le_voci_del_formato_vecchio_vengono_scartate(classifica_in):
    vecchia = {"nome": "IA-Xihexi", "wins": 6, "ties": 0, "losses": 0, "punti_totali": 0, "data": "04/10/2025"}
    classifica_in.write_text(json.dumps([vecchia, _voce("Buona", 1, 0, 70), "spazzatura", {"nome": 3}]), encoding="utf-8")
    classifica, _ = gd.load_classifica()
    assert [v["nome"] for v in classifica] == ["Buona"]


def test_ordine_per_quota_di_vittorie_e_poi_punti():
    classifica = [_voce("A", 2, 1, 200), _voce("B", 3, 0, 150), _voce("C", 2, 1, 210), _voce("D", 1, 0, 70, partite=1)]
    nomi = [v["nome"] for v in gd.classifica_per_match(classifica, 3)]
    assert nomi == ["B", "C", "A"]


def test_la_posizione_rispetta_chi_era_gia_dentro():
    classifica = [_voce("A", 2, 1, 200)]
    uguale = _voce("Nuovo", 2, 1, 200)
    assert gd.posizione_in_classifica(classifica, uguale) == 2
    migliore = _voce("Nuovo", 3, 0, 100)
    assert gd.posizione_in_classifica(classifica, migliore) == 1


def test_oltre_le_trenta_non_si_entra_e_si_taglia():
    classifica = [_voce(f"G{i}", 2, 1, 300 - i) for i in range(gd.CLASSIFICA_MAX_VOCI)]
    peggiore = _voce("Ultimo", 2, 1, 100)
    assert gd.posizione_in_classifica(classifica, peggiore) is None
    # Undici voci hanno almeno 290 punti, e a parita' resta davanti chi c'era.
    buona = _voce("Buona", 2, 1, 290)
    assert gd.posizione_in_classifica(classifica, buona) == 12
    nuova = gd.inserisci_in_classifica(classifica, buona)
    assert len(nuova) == gd.CLASSIFICA_MAX_VOCI
    assert "Buona" in [v["nome"] for v in nuova]
    assert f"G{gd.CLASSIFICA_MAX_VOCI - 1}" not in [v["nome"] for v in nuova]
    assert len(classifica) == gd.CLASSIFICA_MAX_VOCI


def test_il_taglio_non_tocca_le_altre_lunghezze_di_match():
    classifica = [_voce(f"G{i}", 2, 1, 300 - i) for i in range(gd.CLASSIFICA_MAX_VOCI)] + [_voce("Cinque", 3, 0, 250, partite=5)]
    nuova = gd.inserisci_in_classifica(classifica, _voce("Buona", 2, 1, 290))
    assert "Cinque" in [v["nome"] for v in nuova]


def test_pulisci_nome_toglie_i_caratteri_di_controllo():
    assert gd.pulisci_nome("\x12eferendum  ") == "Eferendum"
    assert gd.pulisci_nome("   ") == ""
    assert len(gd.pulisci_nome("a" * 50)) == gd.NOME_MAX


def test_righe_leggibili_con_la_voce_nuova_segnalata():
    voce = _voce("Gabry", 2, 1, 190)
    righe = gd.righe_classifica([_voce("Altro", 1, 2, 150), voce], 3, nuova=voce)
    assert righe[0] == "Classifica dei match al meglio di 3."
    assert righe[1].startswith("1. Gabry, nuova: 2 vinte, 0 patte, 1 persa.")
    assert righe[2].startswith("190 punti, il ")
    assert all(len(r) <= 60 for r in righe)


def test_nome_del_calcolatore():
    nome = gd.generate_ai_name()
    assert nome.startswith("IA-") and len(nome) == 9
