# Gabryscola, prove sulle regole e sul mazzo condiviso.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import regole


def _carte():
    mazzo = regole.nuovo_mazzo()
    return {(c.valore, c.seme_nome): c for c in mazzo.carte}


def test_il_mazzo_ha_quaranta_carte_e_centoventi_punti():
    mazzo = regole.nuovo_mazzo()
    assert len(mazzo.carte) == 40
    assert len({c.id for c in mazzo.carte}) == 40
    assert sum(regole.punti(c) for c in mazzo.carte) == regole.PUNTI_TOTALI


def test_le_coppe_si_abbreviano_con_la_c():
    coppe = [c for c in regole.nuovo_mazzo().carte if c.seme_nome == "Coppe"]
    assert len(coppe) == 10
    assert all(c.desc_breve.endswith("C") for c in coppe)
    asso = next(c for c in coppe if c.valore == 1)
    assert asso.desc_breve == "AC"


def test_due_mazzi_hanno_le_stesse_carte():
    primo = regole.nuovo_mazzo().carte
    secondo = regole.nuovo_mazzo().carte
    assert primo == secondo


def test_la_briscola_batte_gli_altri_semi():
    c = _carte()
    assert regole.vince_primo(c[(2, "Spade")], c[(1, "Coppe")], "Spade")
    assert not regole.vince_primo(c[(1, "Coppe")], c[(2, "Spade")], "Spade")


def test_a_pari_seme_vince_la_gerarchia():
    c = _carte()
    assert regole.vince_primo(c[(1, "Coppe")], c[(3, "Coppe")], "Spade")
    assert not regole.vince_primo(c[(3, "Coppe")], c[(1, "Coppe")], "Spade")
    assert regole.vince_primo(c[(8, "Spade")], c[(7, "Spade")], "Spade")
    assert regole.vince_primo(c[(3, "Denari")], c[(10, "Denari")], "Spade")


def test_semi_diversi_senza_briscola_vince_il_primo():
    c = _carte()
    assert regole.vince_primo(c[(2, "Coppe")], c[(1, "Denari")], "Spade")


def test_forza_e_punti():
    c = _carte()
    assert regole.forza(c[(1, "Bastoni")]) == 10
    assert regole.forza(c[(2, "Bastoni")]) == 1
    assert regole.punti(c[(1, "Bastoni")]) == 11
    assert regole.punti(c[(3, "Bastoni")]) == 10
    assert regole.punti(c[(7, "Bastoni")]) == 0
