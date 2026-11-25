# SnackMorph — benchmark di sviluppo v1

Il benchmark usa il codice candidato con `SnackMorph_compatibility.patch` già applicata. Non modifica gli algoritmi di produzione. I generatori indipendenti definiscono geometrie continue e maschere discrete; il codice di valutazione richiama le routine di SnackMorph. Il campionamento JPEG è quello nativo delle immagini generate; la scala è nota in mm/pixel (non calibrata sul diametro da misurare). Si usa l'asse noto solo per orientare i profili dopo la predizione. L'abbinamento a massima IoU è globale uno-a-uno; gli oggetti senza sovrapposizione sono non abbinati e ricevono Dice/IoU zero. Gli errori dimensionali sono condizionati ai risultati disponibili; riportare sempre anche i fallimenti. Non confondere osservazioni dello stesso gruppo con replicati indipendenti. Il colore riguarda la mediana Lab non corretta dei soli oggetti uniformi, non le misure di una fotocamera reale. La selezione del corpo replica l'algoritmo originale. Non si stima Pk/Le per forme non adatte al modello; non si valuta ancora un classificatore automatico di idoneità del modello.

VOX: griglia nativa, nessun ricampionamento, impostazioni legacy, connettività 6, percorso SciPy senza acceleratori opzionali, confronto ROI fornita vs automatica. Il riferimento di porosità è discreto e definisce l'esterno come complemento della ROI; il software esclude dall'esterno i voxel ad alta attenuazione (possibile divergenza in presenza del supporto). Il confronto del numero di componenti usa componenti connesse, non watershed. Gli spessori nominali continui di sfere/canali/lamelle sono confrontati sui voxel di intersezione dei pori o delle pareti in regioni specificate: riportare la copertura e non attribuire la differenza soltanto all'algoritmo di spessore, perché include rasterizzazione e segmentazione. Il benchmark non copre ancora i descrittori MIL/Euler/superficie/watershed, i profili cromatici e la convergenza spaziale.

## Esecuzione (PowerShell dalla radice del repository)

Copia i file di questo pacchetto nelle cartelle corrispondenti. Se vuoi usare un ambiente nuovo:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-tested.txt -r validation/generators/requirements.txt -e '.[test]'
$python = '.\.venv\Scripts\python.exe'
& $python validation/generators/generate_jpeg.py --out validation_data/JPEG
& $python validation/generators/generate_vox.py --out validation_data/VOX
& $python validation/check_dataset.py validation_data
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& $python validation/run_benchmark.py --data validation_data --out results/development_v1
& $python validation/summarize_benchmark.py results/development_v1
Compress-Archive -Path results/development_v1/* -DestinationPath SnackMorph_development_results.zip -Force
```

Se interrotto, ripetere il comando di benchmark con la stessa versione del codice, stesso dataset, stessa configurazione e stesso output; i casi con DONE non vengono rieseguiti (inclusi i fallimenti, da conservare). Usare una nuova directory se si cambia qualunque impostazione. `--pilot` esegue solo quattro JPEG clean e cinque VOX clean (solo sviluppo), `--mode jpeg` o `--mode vox` permette esecuzioni separate con output distinti. Non usare `--pilot` per il test. Il programma rifiuta il test senza un piano JSON approvato, con hash del codice uguali a `environment.json`, criteri non vuoti e `approved=true`. Tale piano va definito dopo lo sviluppo e prima di misurare il test; non è ancora disponibile. Il flag non è un meccanismo di cecità crittografica. Il dataset è deterministico, non contiene scansioni reali. Non pubblicare i dati di test o tarare sui loro risultati.

`jpeg_metrics.csv` e `jpeg_widths.csv`: risultati per oggetto e posizione; `jpeg_log.csv`: errori e abbinamenti per immagine. `vox_metrics.csv`: risultati per volume e ROI; `vox_log.csv`: errori del file e warning. `descriptive_errors.csv`: statistiche per famiglia e variante (porosità in punti percentuali, lunghezze in mm o µm come dal nome). Le statistiche sono descrittive, non intervalli inferenziali. Il log VOX può essere OK anche se una modalità ROI è fallita; usare lo stato delle singole righe. Le immagini/volumi non vengono inclusi nel pacchetto risultati, perché rigenerabili. Non mescolare output pilot e sviluppo completo.
