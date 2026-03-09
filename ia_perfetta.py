from carte import Mazzo


class IAPerfetta:
    @staticmethod
    def _determina_vincitore_mano_logica(carta1, carta2, briscola_seme):
        """Restituisce 1 se vince carta1 (giocata per prima), 2 se vince carta2 (giocata per seconda)"""
        c1_briscola = carta1.seme_nome == briscola_seme
        c2_briscola = carta2.seme_nome == briscola_seme

        def valore_comparativo(carta):
            return Mazzo.PUNTI_BRISCOLA.get(carta.valore, 0) * 10 + carta.valore

        if c1_briscola and not c2_briscola:
            return 1
        if not c1_briscola and c2_briscola:
            return 2

        if c1_briscola and c2_briscola or carta1.seme_nome == carta2.seme_nome:
            if valore_comparativo(carta1) > valore_comparativo(carta2):
                return 1
            else:
                return 2
        return 1

    @staticmethod
    def _punti(carta):
        return Mazzo.PUNTI_BRISCOLA.get(carta.valore, 0)

    @classmethod
    def _minimax(
        cls,
        mano_pc,
        mano_umano,
        briscola_seme,
        turno_pc,
        punti_pc,
        punti_umano,
        depth,
        alpha,
        beta,
    ):
        if not mano_pc and not mano_umano:
            return punti_pc

        best_score = -float("inf") if turno_pc else float("inf")

        if turno_pc:
            for c_pc in mano_pc:
                max_score_per_c_pc = float("inf")
                for c_umano in mano_umano:
                    vincitore = cls._determina_vincitore_mano_logica(
                        c_pc, c_umano, briscola_seme
                    )
                    punti_presi = cls._punti(c_pc) + cls._punti(c_umano)

                    nuovi_punti_pc = (
                        punti_pc + punti_presi if vincitore == 1 else punti_pc
                    )
                    nuovi_punti_umano = (
                        punti_umano + punti_presi if vincitore == 2 else punti_umano
                    )
                    nuova_mano_pc = [c for c in mano_pc if c != c_pc]
                    nuova_mano_umano = [c for c in mano_umano if c != c_umano]
                    nuovo_turno_pc = vincitore == 1

                    score = cls._minimax(
                        nuova_mano_pc,
                        nuova_mano_umano,
                        briscola_seme,
                        nuovo_turno_pc,
                        nuovi_punti_pc,
                        nuovi_punti_umano,
                        depth - 1,
                        alpha,
                        beta,
                    )
                    max_score_per_c_pc = min(max_score_per_c_pc, score)

                best_score = max(best_score, max_score_per_c_pc)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
            return best_score
        else:
            best_score = float("inf")
            for c_umano in mano_umano:
                min_score_per_c_umano = -float("inf")
                for c_pc in mano_pc:
                    vincitore = cls._determina_vincitore_mano_logica(
                        c_umano, c_pc, briscola_seme
                    )
                    punti_presi = cls._punti(c_umano) + cls._punti(c_pc)

                    nuovi_punti_pc = (
                        punti_pc + punti_presi if vincitore == 2 else punti_pc
                    )
                    nuovi_punti_umano = (
                        punti_umano + punti_presi if vincitore == 1 else punti_umano
                    )
                    nuova_mano_pc = [c for c in mano_pc if c != c_pc]
                    nuova_mano_umano = [c for c in mano_umano if c != c_umano]
                    nuovo_turno_pc = vincitore == 2

                    score = cls._minimax(
                        nuova_mano_pc,
                        nuova_mano_umano,
                        briscola_seme,
                        nuovo_turno_pc,
                        nuovi_punti_pc,
                        nuovi_punti_umano,
                        depth - 1,
                        alpha,
                        beta,
                    )
                    min_score_per_c_umano = max(min_score_per_c_umano, score)

                best_score = min(best_score, min_score_per_c_umano)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            return best_score

    @classmethod
    def _risolvi_endgame(
        cls,
        mano_pc,
        carte_umano,
        tavolo,
        briscola_seme,
        punti_pc,
        punti_umano,
        turno_pc,
    ):
        if tavolo:
            carta_avversario = tavolo[0]
            best_carta = None
            best_score = -float("inf")

            for c_pc in mano_pc:
                vincitore = cls._determina_vincitore_mano_logica(
                    carta_avversario, c_pc, briscola_seme
                )
                punti_presi = cls._punti(carta_avversario) + cls._punti(c_pc)
                nuovi_punti_pc = punti_pc + punti_presi if vincitore == 2 else punti_pc
                nuovi_punti_umano = (
                    punti_umano + punti_presi if vincitore == 1 else punti_umano
                )

                nuova_mano_pc = [c for c in mano_pc if c != c_pc]
                nuova_mano_umano = list(carte_umano)
                nuovo_turno_pc = vincitore == 2

                score = cls._minimax(
                    nuova_mano_pc,
                    nuova_mano_umano,
                    briscola_seme,
                    nuovo_turno_pc,
                    nuovi_punti_pc,
                    nuovi_punti_umano,
                    len(nuova_mano_pc) * 2,
                    -float("inf"),
                    float("inf"),
                )

                if score > best_score:
                    best_score = score
                    best_carta = c_pc
            return best_carta
        else:
            best_carta = None
            best_score = -float("inf")

            for c_pc in mano_pc:
                min_score_for_c_pc = float("inf")
                for c_umano in carte_umano:
                    vincitore = cls._determina_vincitore_mano_logica(
                        c_pc, c_umano, briscola_seme
                    )
                    punti_presi = cls._punti(c_pc) + cls._punti(c_umano)

                    nuovi_punti_pc = (
                        punti_pc + punti_presi if vincitore == 1 else punti_pc
                    )
                    nuovi_punti_umano = (
                        punti_umano + punti_presi if vincitore == 2 else punti_umano
                    )
                    nuova_mano_pc = [c for c in mano_pc if c != c_pc]
                    nuova_mano_umano = [c for c in carte_umano if c != c_umano]
                    nuovo_turno_pc = vincitore == 1

                    score = cls._minimax(
                        nuova_mano_pc,
                        nuova_mano_umano,
                        briscola_seme,
                        nuovo_turno_pc,
                        nuovi_punti_pc,
                        nuovi_punti_umano,
                        len(nuova_mano_pc) * 2,
                        -float("inf"),
                        float("inf"),
                    )
                    min_score_for_c_pc = min(min_score_for_c_pc, score)

                if min_score_for_c_pc > best_score:
                    best_score = min_score_for_c_pc
                    best_carta = c_pc
            return best_carta

    @classmethod
    def scegli_carta(
        cls,
        briscola,
        tavolo,
        mano_pc,
        mazzo_completo,
        carte_uscite,
        punti_pc,
        punti_umano,
    ):
        def is_briscola(c):
            return c.seme_nome == briscola.seme_nome

        carte_incognite = list(set(mazzo_completo) - carte_uscite - set(mano_pc))

        if (
            len(carte_incognite) <= 3
            and len(mano_pc) == len(carte_incognite)
            and len(carte_incognite) > 0
        ):
            turno_pc = len(tavolo) == 0
            carta_scelta = cls._risolvi_endgame(
                mano_pc,
                carte_incognite,
                tavolo,
                briscola.seme_nome,
                punti_pc,
                punti_umano,
                turno_pc,
            )
            if carta_scelta:
                return carta_scelta

        mosse_valutate = []
        punti_mancanti_vittoria = 61 - punti_pc

        if tavolo:
            carta_avversario = tavolo[0]
            for carta_da_giocare in mano_pc:
                vincitore_idx = cls._determina_vincitore_mano_logica(
                    carta_avversario, carta_da_giocare, briscola.seme_nome
                )
                vincitore = "PC" if vincitore_idx == 2 else "UMANO"

                punti_mano = cls._punti(carta_avversario) + cls._punti(carta_da_giocare)

                if vincitore == "PC" and (punti_pc + punti_mano >= 61):
                    return carta_da_giocare

                valore = punti_mano if vincitore == "PC" else -punti_mano

                if vincitore == "PC":
                    if (
                        is_briscola(carta_da_giocare)
                        and not is_briscola(carta_avversario)
                        and punti_mano < 10
                    ):
                        valore -= 20
                else:
                    valore -= cls._punti(carta_da_giocare) * 5

                mosse_valutate.append((valore, carta_da_giocare))
            _, carta_scelta = max(mosse_valutate, key=lambda x: x[0])
            return carta_scelta
        else:
            num_carte_incognite = len(carte_incognite)
            briscole_incognite = [c for c in carte_incognite if is_briscola(c)]

            for carta_da_giocare in mano_pc:
                punti_da_rischiare = cls._punti(carta_da_giocare)
                valore_atteso_punti = 0
                vittorie_stimate = 0

                if num_carte_incognite > 0:
                    for carta_avv_potenziale in carte_incognite:
                        vincitore_idx = cls._determina_vincitore_mano_logica(
                            carta_da_giocare, carta_avv_potenziale, briscola.seme_nome
                        )
                        vincitore = "PC" if vincitore_idx == 1 else "UMANO"
                        punti_mano = punti_da_rischiare + cls._punti(
                            carta_avv_potenziale
                        )
                        if vincitore == "PC":
                            valore_atteso_punti += punti_mano
                            vittorie_stimate += 1
                        else:
                            valore_atteso_punti -= punti_mano
                    valore_medio_punti = valore_atteso_punti / num_carte_incognite
                    prob_vittoria = vittorie_stimate / num_carte_incognite
                else:
                    valore_medio_punti, prob_vittoria = punti_da_rischiare, 1.0

                rischio = 0
                if (
                    punti_da_rischiare > 0
                    and not is_briscola(carta_da_giocare)
                    and num_carte_incognite > 0
                ):
                    prob_di_essere_briscolata = (
                        len(briscole_incognite) / num_carte_incognite
                    )
                    if punti_mancanti_vittoria <= 10:
                        rischio = prob_di_essere_briscolata * punti_da_rischiare * 100
                    else:
                        rischio = prob_di_essere_briscolata * punti_da_rischiare * 30

                costo_opportunita = 0
                if is_briscola(carta_da_giocare) and punti_da_rischiare > 3:
                    costo_opportunita = (punti_da_rischiare + 5) * (
                        len(carte_incognite) / 10
                    )

                VANTAGGIO_MANO_SUCCESSIVA = 1.5
                valore_tattico = (
                    (1 - prob_vittoria) * VANTAGGIO_MANO_SUCCESSIVA
                    - prob_vittoria * VANTAGGIO_MANO_SUCCESSIVA
                )
                valore_finale = (
                    valore_medio_punti - rischio - costo_opportunita + valore_tattico
                )

                mosse_valutate.append((valore_finale, carta_da_giocare))
            _, carta_scelta = max(mosse_valutate, key=lambda x: x[0])
            return carta_scelta
