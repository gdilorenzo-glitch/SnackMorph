# Benchmark di sviluppo v2 (candidato, non release)

Non cambia il dataset `benchmark-data-v1` né i generatori. Non usare il gruppo test.
- JPEG: `--candidate` usa `width_normals(method="subpixel")` con contorno 0.5 della maschera interpolata, passo <=0.25 px; il default resta legacy. Non cambia segmentazione o asse, quindi non risolve le mancate associazioni.
- VOX: `known` e `automatic` mantengono esattamente le modalità precedenti. `known_midpoint` confronta una soglia intermedia fra mediane delle classi Otsu su dati grezzi, con sigma 0.5; le due modifiche sono congiunte, non una prova causale. `axial_envelope` è un candidato per sezioni assiali convesse, materiale più brillante del supporto separato in Z. Non usare quando cuneo e colla sono a contatto; non recupera vuoti terminali non osservabili. Non è un algoritmo generico per qualsiasi geometria.
- `known` aggiunge lo spessore su maschere vere (diagnostica numerica, non una nuova stima da immagini). I descrittori legacy restano invariati.
- Il benchmark originale non contiene un cuneo e uno strato di colla a contatto con il campione. `run_fixture_diagnostic.py` genera separatamente sei sezioni idealizzate a tre orientamenti, con/senza blur e rumore. Misura Dice separato per ROI, colla e cuneo, perdita del campione e contaminazione da supporto. È una diagnostica 2D con geometria e intensità ipotetiche, non una validazione 3D, né una ricostruzione del portacampione reale. Per il benchmark realistico servono geometria, intensità e maschere annotate di sezioni reali.

Esecuzione (ambiente ufficiale, dataset già disponibile):
```
python validation/run_benchmark.py --data validation_data --out results/development_v2 --split development --candidate
python validation/summarize_benchmark.py results/development_v2
python validation/run_fixture_diagnostic.py --out results/development_v2/fixture_diagnostic
```
Non riusare la directory v1. Il notebook Colab scarica lo stesso asset GitHub e verifica SHA-256, blocca commit e dipendenze. Confrontare separatamente gli indicatori di v1 e v2; le modalità aggiuntive non sostituiscono le legacy. La modalità subpixel è ora selezionabile nel CLI con --width-method subpixel; la modalità legacy resta il default. I risultati finali sono nell’archivio di audit; le modalità VOX alternative restano esplorative.
