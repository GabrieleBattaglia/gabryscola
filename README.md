# Gabryscola

La briscola a due, da riga di comando, contro il calcolatore. Studiata per essere del tutto fruibile con uno screen reader e comoda sul display braille: ogni evento viene detto a parole e ha un suono, con chi gioca a sinistra e il calcolatore a destra, e il prompt di gioco sta in una riga corta.

Il calcolatore non guarda mai le carte dell'avversario. Sa esattamente cio' che sa lui, tiene la distribuzione di probabilita' di tutte le mani possibili e decide esaminando molti mondi coerenti con quella conoscenza, risolvendo ciascuno con minimax contro un avversario perfetto. Nelle ultime mani il gioco e' esatto.

La guida completa e' in `manuale.txt`, e si apre durante il gioco con il punto di domanda. Le novita' di ogni versione sono in `CHANGELOG.md`.

## Avvio dal sorgente

Serve Python 3 con i pacchetti di `requirements.txt` e la libreria condivisa GBUtils, raggiungibile da Python, con accanto la sua collezione dei suoni `Acu_Collection.json`.

```bash
python gabryscola.py
```

Con `logon` sulla riga di comando si salva il log del match, con `noprompt` sparisce il prompt breve.

## Strumenti

- `arena.py` fa giocare fra loro due configurazioni del motore per centinaia di partite e conta vittorie, punti e tempi: e' il modo di misurare se una modifica lo ha reso piu' forte.
- `tests` contiene le prove automatiche, da lanciare con `python -m pytest tests`.
- `gabryscola.spec` e `zip_maker.py` compilano e impacchettano la release.

Autori: Gabriele Battaglia (IZ4APU) & ClaudIA.
