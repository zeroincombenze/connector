Questo modulo abilita l'importazione dati da file csv. I file csv devono essere
presenti in una cartella dichiarata nella configurazione della dorsale.

La prima riga del file csv deve contenere le etichette di campo. L'utente può associare
l'etichetta del campo ad un campo interno di Odoo; l'utente può anche dichiarare una
funzione di conversione da eseguire.

Se l'utente dichiara una versione di Odoo di controparte, l'associazione tra i campi
della version corrente e quella dichiarata verrò caricata.

Se il file csv contiene la colonna "id", il valore di questa colonna sarà usato per
evitare duplicazioni di dati. Senza questa colonna sarà usato il numero di riga.

