# SnackMorph: preparazione GitHub per SoftwareX

Fonte editoriale: Guide for Authors di SoftwareX (copia fornita) e template Original Software Publication v6, marzo 2026. La rivista richiede repository GitHub pubblico, README.md ben documentato, LICENSE.txt/Licence.txt contenente una licenza legale riconosciuta e sorgenti nella directory src/. Il modello C1–C8 non va alterato nelle intestazioni. Per Word si devono incorporare le figure nel file e seguire il template; limite 4000 parole e 6 figure. Il repository pubblico è indispensabile per il fork editoriale. Non pubblicare prima del consenso dei titolari dei diritti.

## 1. Preparazione privata
1. Accedi a https://github.com/new con il tuo account (o l'organizzazione del gruppo, se approvato).
2. Repository name: SnackMorph (provvisorio). Description: Python tools for automated multi-scale characterisation of expanded snacks. Visibility: Private. Non inizializzare con README, .gitignore o licenza: sono già presenti file di progetto e la scelta della licenza è pendente.
3. Scarica ed estrai SnackMorph_GitHub_candidate.zip. Apri un terminale dentro la cartella SnackMorph_repository_candidate. Verifica il contenuto, soprattutto i diritti sul codice, i dati, l'assenza di chiavi/percorsi privati e i riferimenti al notebook. Non includere i dati sperimentali grezzi o gli archivi grandi.
4. Installa Git se necessario (https://git-scm.com/downloads) e autentica GitHub con GitHub CLI o tramite il sistema di autenticazione proposto; non inserire password o token nei file.

```sh
git init -b main
git add .
git diff --cached --stat
git status
git commit -m "Prepare SnackMorph research software candidate"
git remote add origin https://github.com/TUO_ACCOUNT/SnackMorph.git
git push -u origin main
```
Sostituisci TUO_ACCOUNT con l'identificativo reale. Se Git richiede nome/email, imposta i dati che desideri rendere visibili nei commit (puoi usare l'indirizzo noreply fornito da GitHub). Non usare `--force`. Alternativa senza terminale: in GitHub apri il repository > Add file > Upload files, carica i file e le cartelle estratti, non lo ZIP; verifica anche le cartelle nascoste (.github) e .gitignore. Usa il terminale per preservare meglio la struttura.

## 2. Completamento scientifico e tecnico prima di rendere pubblico
- Approvare nome, licenza e titolari dei diritti. MIT/BSD-3-Clause/Apache-2.0 sono opzioni permissive da discutere; GPL comporta condizioni di copyleft. Non viene assegnata alcuna licenza automaticamente. Inserire il testo integrale della licenza approvata in LICENSE.txt, eliminare LICENSE_PENDING.md. Controllare anche le licenze delle dipendenze e i diritti sui dati (distinti dalla licenza software).
- Completare mapping indipendente di tutte le JPEG, batch, interfaccia, integrazione esplicita del riscalamento JPEG/VOX, test scientifici e manuale. Il codice candidato incorpora il modulo CT fisico e una correzione del manifest e del ramo statistico contestato; non riproduce ancora il workflow finale completo.
- Eseguire i test in un ambiente pulito e verificare Actions su GitHub. Correggere i warning delle dipendenze solo dopo regression testing. Congelare codice e criteri prima di usare le geometrie test.
- Completare README con istruzioni di installazione, utilizzo, input/output, esempi, limiti, contatto, versione e citazione. Aggiungere eventuali CONTRIBUTING.md, CHANGELOG.md e CITATION.cff con autori/DOI veri (non inventati).
- Depositare dati sintetici e dati sperimentali condivisibili in un archivio dati appropriato (es. Zenodo o Mendeley Data) con versione, DOI e condizioni di riuso; mantenere nel repository generatori, istruzioni e piccoli esempi. Mai caricare i VOX sperimentali da 14 GB nel repository Git: GitHub limita i file normali a 100 MiB. Eventuali restrizioni documentate nel Data availability statement.

## 3. Release da citare nel paper
Dopo consenso e verifica, creare commit finale e tag (esempio, non ancora esistente):
```sh
git add .
git commit -m "Prepare SoftwareX submission release"
git tag -a v1.0.0 -m "SoftwareX submission version"
git push origin main
git push origin v1.0.0
```
Aprire GitHub > Releases > Draft a new release, selezionare il tag e descrivere dipendenze, funzionalità, limiti, istruzioni, dati dimostrativi e test. Non chiamarla v1.0.0 se il team non l'ha approvata: usare l'identificativo definitivo concordato. Impostare il repository pubblico solo dopo autorizzazione (Settings > General > Danger Zone > Change repository visibility). Verificare da una finestra anonima accesso a README.md, LICENSE.txt, src/ e al tag. Usare in C2 un URL immutabile a tag/commit GitHub, ad es. https://github.com/TUO_ACCOUNT/SnackMorph/tree/v1.0.0; in C1 la stessa versione, non quella di un altro commit. Non usare un archivio DOI al posto del link GitHub richiesto. Aggiornare C3–C8 secondo docs/SOFTWAREX_METADATA.md. Zenodo può archiviare la release e fornire un DOI complementare, utile ma non sostitutivo.

## 4. Stato al momento
Repository candidato locale, non creato né pubblicato su GitHub. Nessun titolare, licenza o indirizzo inventato. CI predisposta non ancora eseguita su GitHub. 8 test locali superati; i test indipendenti di accuratezza non sono ancora stati eseguiti. Non caricare il manoscritto, le note private o i risultati riservati in un repo pubblico senza consenso.
