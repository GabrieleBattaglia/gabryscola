# Changelog - Gabryscola

Tutti i cambiamenti e le novità introdotte nelle versioni di Gabryscola.
Il changelog nasce con la versione 4.0.0. Per le versioni precedenti il resoconto sta nella cronologia dei commit e nelle release pubblicate su GitHub.

## [4.0.0] - 2026-09-08

Revisione 1 del refactoring generale del parco software, con il motore del calcolatore riscritto da zero.

### Aggiunto
- **Un calcolatore nuovo.** Non guarda mai le tue carte: sa esattamente quello che sai tu, cioè le carte uscite, la briscola scoperta e le carte che ha pescato, e su questo tiene la distribuzione di probabilità di tutte le mani che puoi avere. A ogni carta che giochi aggiorna le probabilità, anche ragionando su cosa avrebbe fatto un giocatore attento con ogni mano possibile. Per decidere esamina molti mondi possibili, coerenti con quello che sa, e in ciascuno gioca le mani successive contro un avversario perfetto, scegliendo la carta che gli dà la maggiore probabilità di vincere la partita. Nelle ultime cinque mani la ricerca arriva in fondo, e dalle quattro carte nel mazzo in giù il gioco è esatto. Ha due secondi di riflessione per carta.
- **Il peso del match.** Il calcolatore sa come sta andando il match: se gli basta una patta gioca per la patta, se gli serve la vittoria rischia, e tiene conto dello spareggio sui punti totali.
- **Un suono per ogni cosa.** Ogni evento del gioco ha il suo suono, dal mazzo che si mescola alla classifica salvata. Quello che fai tu si sente a sinistra, quello che fa il calcolatore a destra, il resto al centro. Quattro rumori di carte nuovi nella collezione condivisa: la carta giocata, la carta pescata, la briscola girata e il mazzo mescolato.
- **La guida.** Il punto di domanda, durante il gioco, apre il manuale a pagine. È il file manuale.txt, che viaggia anche dentro l'eseguibile.
- **Controllo degli aggiornamenti** all'avvio del programma compilato, con gestisci_aggiornamento di GBUtils, come negli altri programmi del parco.
- **Statistiche del calcolatore** a fine match: quanti mondi ha esaminato, in quanti secondi, e quante decisioni sono state esatte.
- **L'arena** (arena.py): fa giocare fra loro due configurazioni del motore per centinaia di partite e conta vittorie, punti e tempi. È così che si è misurato il motore nuovo. Con i due secondi per carta del gioco, in media 260 mondi e un secondo e tre decimi per decisione, ha battuto il motore della 3.1.1 per 26 partite a 13 su quaranta, con una patta, e 63 punti di media contro 57. Con un decimo di secondo per carta il margine scende a 54 partite contro 45 su cento. L'inferenza sul comportamento, a parità di tempo, ha vinto 106 partite a 88 su duecento contro il motore senza inferenza, con sei patte. Il motore usa il tempo che ha: se una passata di ricerca finisce presto ne fa una più profonda sugli stessi mondi.
- **Una contromisura per la macchina di sviluppo.** Nelle prove lunghe l'interprete è caduto più volte con errori che il codice non può produrre, e allo stesso modo con Python 3.13.15, 3.14.5 e 3.14.7: la memoria viene corrotta dalla macchina sotto carico, un i9-13900KF con il BIOS del 2022, e le raccolte del garbage collector e il thread audio la fanno affiorare. Il gioco non crea cicli di riferimenti, quindi il collector resta spento durante la riflessione del calcolatore e nel programma, e faulthandler è acceso così un crash lascia scritto dov'era. L'arena ha l'opzione --collector-acceso, che è la prova di accettazione della macchina dopo l'aggiornamento del BIOS.
- **Prove automatiche** in tests, trentaquattro, su regole, classifica, conoscenza del calcolatore, ricerca e un match intero senza console.
- I file per compilare e distribuire: gabryscola.spec, con la collezione dei suoni e la guida dentro l'eseguibile (issue 3), e zip_maker.py.

### Modificato
- **I messaggi ti parlano.** Il giocatore resta "Tu", ma le frasi sono alla seconda persona: giochi, peschi, vinci la mano. Niente righe vuote, niente decorazioni con maggiore e minore, niente nomi in maiuscolo letti lettera per lettera. Il punteggio di fine partita e il parziale del match sono frasi corte. Quando vince il calcolatore lo dice con il verbo giusto.
- **Il riepilogo del match** dice che il traguardo è stato raggiunto invece di due frasi sbagliate, e dice quante partite mancano con i numeri e le parole al singolare o al plurale giusti.
- **La classifica.** Entrano solo le trenta migliori per ogni lunghezza di match, e il file salvato coincide con quella mostrata. Il nome ti viene chiesto solo se entri davvero, con dgt, e viene ripulito dai caratteri di controllo. Un match abbandonato non entra e non regala più al calcolatore un primo posto con il cento per cento. La classifica viene letta a frasi, due righe corte per voce, con la voce nuova segnalata.
- **La classifica su disco** vive accanto al programma, non nella cartella da cui lo lanci; si salva su file temporaneo con sostituzione atomica e copia di riserva; alla lettura si tengono solo le voci complete, e un file rotto non azzera più tutto in silenzio: si usa la copia di riserva e lo si dice. Le ventidue voci del formato vecchio, che non comparivano in nessuna classifica, sono state tolte.
- **Il sorteggio iniziale** a carte di pari valore decide con la moneta, invece di dare sempre la mano a te.
- **L'abbandono** si conferma con un tasto singolo, come il resto del gioco. Il numero di partite si chiede con dgt.
- Il mazzo è quello condiviso di GBUtils, come in pokermachine: la copia locale carte.py è stata cancellata. Le regole della briscola, cioè punti, gerarchia di presa e chi vince la mano, stanno nel modulo regole.py, separato dal mazzo. Le Coppe restano abbreviate con la C sul prompt braille, tramite il parametro nuovo di Mazzo V6.1.0.
- Le opzioni logon e noprompt si cercano solo fra gli argomenti veri della riga di comando. Il log del match si salva accanto al programma.
- Tutti i moduli portano l'intestazione con gli autori nel formato del parco software, e l'attribuzione mostrata all'avvio nomina ClaudIA.
- Il codice passa il validatore ruff con la configurazione di progetto in ruff.toml.

### Rimosso
- Il motore precedente, ia_perfetta.py, con le sue euristiche a pesi fissi e il tracker che deduceva un vuoto di seme inesistente.
- I file di lavoro rimasti nel repository: il log di un match di marzo 2026, un file di test vuoto e il piano di miglioramento dell'intelligenza artificiale, i cui tre punti sono assorbiti dal motore nuovo.
