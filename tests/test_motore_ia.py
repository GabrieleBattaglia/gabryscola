# Gabryscola, prove sul cervello: tabelle, conoscenza, ricerca e utilita' del match.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import random
from itertools import combinations
from math import comb

import arena
import motore_ia as mi
import regole


def _mazzo():
    return regole.nuovo_mazzo().carte


def _idx(carte):
    return tuple(sorted(mi.indice(c) for c in carte))


def test_tabella_delle_prese_coerente_con_le_regole():
    mazzo = _mazzo()
    for seme in range(4):
        nome_seme = mazzo[seme * 10].seme_nome
        tabella = mi.tabella_prese(seme)
        for a in mazzo:
            for b in mazzo:
                if a is not b:
                    assert tabella[mi.indice(a)][mi.indice(b)] == regole.vince_primo(a, b, nome_seme)


def test_utilita_senza_match():
    u = mi.utilita_punti(None)
    assert u[0] == 0 and u[59] == 0 and u[60] == 0.5 and u[61] == 1 and u[120] == 1


def test_utilita_ultima_partita_di_un_match_in_parita():
    match = {"partite": 3, "vinte_pc": 1, "vinte_avv": 1, "patte": 0, "punti_pc": 100, "punti_avv": 140}
    u = mi.utilita_punti(match)
    assert u[61] == 1.0 and u[59] == 0.0
    # Patta: lo spareggio va a chi ha piu' punti totali. Con 60 il calcolatore resta sotto.
    assert u[60] == 0.0
    match["punti_pc"], match["punti_avv"] = 140, 100
    assert mi.utilita_punti(match)[60] == 1.0


def test_utilita_prima_partita_di_un_match_lungo_e_intermedia():
    match = {"partite": 5, "vinte_pc": 0, "vinte_avv": 0, "patte": 0, "punti_pc": 0, "punti_avv": 0}
    u = mi.utilita_punti(match)
    assert 0.5 < u[61] < 1.0
    assert 0.0 < u[59] < 0.5
    assert abs(u[61] + u[59] - 1.0) < 1e-9


def test_la_sfumatura_conserva_la_media_e_l_ordine():
    u = mi._sfuma(mi.utilita_punti(None), 4.0)
    assert all(u[i] <= u[i + 1] + 1e-12 for i in range(120))
    assert 0.4 < u[60] < 0.6


def test_conoscenza_iniziale_uniforme_senza_la_briscola():
    mazzo = _mazzo()
    briscola = mazzo[0]
    mano = mazzo[1:4]
    conoscenza = mi.Conoscenza(mi.indice(briscola), [mi.indice(c) for c in mano])
    assert len(conoscenza.mani) == comb(36, 3)
    assert all(mi.indice(briscola) not in m for m in conoscenza.mani)
    assert all(mi.indice(c) not in m for m in conoscenza.mani for c in mano)


def test_conoscenza_segue_gli_eventi():
    mazzo = _mazzo()
    briscola, mano = mazzo[0], mazzo[1:4]
    giocata, pescata_pc, pescata_avv = mazzo[10], mazzo[11], mazzo[12]
    conoscenza = mi.Conoscenza(mi.indice(briscola), [mi.indice(c) for c in mano], inferenza=False)
    conoscenza.gioca_avversario(mi.indice(giocata), None)
    assert all(len(m) == 2 and mi.indice(giocata) not in m for m in conoscenza.mani)
    assert len(conoscenza.mani) == comb(35, 2)
    conoscenza.pesca_avversario(None)
    assert all(len(m) == 3 for m in conoscenza.mani)
    assert len(conoscenza.mani) == comb(35, 3)
    conoscenza.pesca_pc(mi.indice(pescata_pc))
    assert all(mi.indice(pescata_pc) not in m for m in conoscenza.mani)
    assert len(conoscenza.mani) == comb(34, 3)
    assert abs(sum(conoscenza.mani.values()) - 1.0) < 1e-9
    # La briscola pescata dall'avversario entra in tutte le mani.
    conoscenza.gioca_avversario(mi.indice(pescata_avv), mi.indice(mano[0]))
    conoscenza.pesca_avversario(mi.indice(briscola))
    assert not conoscenza.briscola_nel_mazzo
    assert all(mi.indice(briscola) in m for m in conoscenza.mani)


def test_inferenza_abbassa_le_mani_con_una_scelta_cattiva():
    mazzo = _mazzo()
    c = {(x.valore, x.seme_nome): x for x in mazzo}
    briscola = c[(2, "Spade")]
    mano_pc = [c[(4, "Bastoni")], c[(5, "Bastoni")], c[(6, "Bastoni")]]
    conoscenza = mi.Conoscenza(mi.indice(briscola), [mi.indice(x) for x in mano_pc])
    # Il calcolatore guida con il Re di Coppe; l'avversario risponde con il 2 di Coppe, perdendo.
    guida = c[(10, "Coppe")]
    conoscenza.gioca_pc(mi.indice(guida))
    conoscenza.gioca_avversario(mi.indice(c[(2, "Coppe")]), mi.indice(guida))
    asso = mi.indice(c[(1, "Coppe")])
    liscio = mi.indice(c[(4, "Denari")])
    peso_con_asso = sum(w for m, w in conoscenza.mani.items() if asso in m)
    peso_con_liscio = sum(w for m, w in conoscenza.mani.items() if liscio in m)
    assert peso_con_asso < peso_con_liscio


def _minimax_lento(batte, mp, ma, mazzo, pc_di_mano):
    """Un minimax senza potatura ne' memoria, per verificare quello vero."""
    if not mp:
        return 0
    if pc_di_mano:
        best = -1e9
        for c in mp:
            peggio = 1e9
            for d in ma:
                vince = batte[c][d]
                punti = mi.PUNTI[c] + mi.PUNTI[d]
                nmp, nma, nmz = mi._Ricerca._pesca(tuple(x for x in mp if x != c), tuple(x for x in ma if x != d), mazzo, vince)
                peggio = min(peggio, (punti if vince else 0) + _minimax_lento(batte, nmp, nma, nmz, vince))
            best = max(best, peggio)
        return best
    best = 1e9
    for d in ma:
        meglio = -1e9
        for c in mp:
            vince = not batte[d][c]
            punti = mi.PUNTI[d] + mi.PUNTI[c]
            nmp, nma, nmz = mi._Ricerca._pesca(tuple(x for x in mp if x != c), tuple(x for x in ma if x != d), mazzo, vince)
            meglio = max(meglio, (punti if vince else 0) + _minimax_lento(batte, nmp, nma, nmz, vince))
        best = min(best, meglio)
    return best


def test_la_ricerca_esatta_coincide_con_il_minimax_lento():
    rng = random.Random(5)
    for _ in range(40):
        seme = rng.randrange(4)
        batte = mi.tabella_prese(seme)
        carte = rng.sample(range(40), 10)
        mp, ma, mazzo = tuple(sorted(carte[:3])), tuple(sorted(carte[3:6])), tuple(carte[6:])
        for pc_di_mano in (True, False):
            ricerca = mi._Ricerca(batte, seme, 5)
            lento = _minimax_lento(batte, mp, ma, mazzo, pc_di_mano)
            if pc_di_mano:
                valori = ricerca.radice(mp, ma, mazzo, None)
                assert max(valori.values()) == lento
            else:
                guida = ma[0]
                valori = ricerca.radice(mp, tuple(ma[1:]), mazzo, guida)
                atteso = max(
                    (mi.PUNTI[guida] + mi.PUNTI[c] if not batte[guida][c] else 0)
                    + _minimax_lento(batte, *mi._Ricerca._pesca(tuple(x for x in mp if x != c), tuple(ma[1:]), mazzo, not batte[guida][c]), not batte[guida][c])
                    for c in mp
                )
                assert max(valori.values()) == atteso


def test_nel_finale_il_cervello_prende_il_carico_con_la_briscola():
    mazzo = _mazzo()
    c = {(x.valore, x.seme_nome): x for x in mazzo}
    briscola = c[(4, "Spade")]
    mano_pc = [c[(2, "Spade")], c[(5, "Denari")]]
    completo = mazzo
    cervello = mi.Cervello(briscola, completo, mano_pc, tempo=1.0)
    conoscenza = cervello.conoscenza
    conoscenza.briscola_nel_mazzo = False
    # Tutte le altre carte sono uscite, tranne le due dell'avversario.
    mano_avv = [c[(1, "Coppe")], c[(7, "Bastoni")]]
    for carta in mazzo:
        if carta not in mano_pc and carta not in mano_avv:
            conoscenza.uscite.add(mi.indice(carta))
    conoscenza.n_mano_avv = 2
    conoscenza.mani = {tuple(sorted(mi.indice(x) for x in mano_avv)): 1.0}
    # L'avversario guida con l'Asso di Coppe: con 50 punti il calcolatore vince solo tagliando.
    scelta = cervello.scegli([c[(1, "Coppe")]], mano_pc, 50, 48, 0)
    assert scelta == c[(2, "Spade")]
    assert cervello.statistiche["esatte"] == 1


def test_una_partita_intera_in_arena_fa_centoventi_punti():
    fabbrica = arena.fabbrica_cervello(tempo=0.02)
    a, b = arena.partita(fabbrica, fabbrica, True, random.Random(11))
    assert a.punteggio() + b.punteggio() == regole.PUNTI_TOTALI
    assert len(a.mazzetto) + len(b.mazzetto) == 40
    assert a.cervello.statistiche["decisioni"] >= 15


def test_le_mani_campionate_sono_sempre_coerenti():
    mazzo = _mazzo()
    briscola, mano = mazzo[0], mazzo[1:4]
    conoscenza = mi.Conoscenza(mi.indice(briscola), [mi.indice(c) for c in mano])
    tavolo = [mi.indice(mazzo[20])]
    conoscenza.gioca_avversario(tavolo[0], None)
    mani, pesi, incognite = conoscenza.distribuzione(_idx(mano), tavolo, 2)
    assert len(mani) == len(pesi) == comb(35, 2)
    assert set(incognite) == set(range(40)) - {mi.indice(briscola), tavolo[0]} - set(_idx(mano))
    assert all(set(m) <= set(incognite) for m in mani)
    assert all(m in set(combinations(sorted(incognite), 2)) for m in mani[:50])
