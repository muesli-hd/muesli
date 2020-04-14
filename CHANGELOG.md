### 2020-04-14

Aktionen werden auf dem UI jetzt als Buttons dargestellt, Links zur Navigation als Links.

### 2019-12-31

* Mails können jetzt auch nur an die anderen Tutoren (nicht nur an Tutoren und Assistenten geschickt) werden.
* Das Feld für Matrikelnummern akzeptiert (clientseitig) nur noch Zahlen, um z.B. zu verhindern, dass dort versehentlich die Uni-ID eingetragen wird.

### 2019-11-25

Hinter einer belegten Übungsgruppe wird jetzt korrekterweise "austreten" (statt fälschlicherweise "wechseln") als Aktion angeboten.

### 2019-09-30

Erklärung zur E-Mail-Adresse auf der "Registrieren"-Seite verbessert.

### 2019-05-24

Es wird angezeigt, an welche Übungsgruppen eine Mail geschickt wird.

### 2019-03-12

Durch das Softwareprakikum bei Prof. Andrzejak haben verschiedenen Gruppen neue
Features dem Müsli hinzugefügt.

##### REST-API

* Enpoints für verschiedene Funktionen des Müsli erstellt
* Rechtesystem für die API erstellt
* Dokumentation für die API
Für weitere Informationen: <link-zum-finalen-pr>

##### GUI-1 Gruppe

* Tooltips implementiert, welche dem Benutzer Aktionen erklären.
* Histogramme für Klausurergebnisse implementiert, sowie ist es möglich 
durch Änderung der Bewertungsformel direkt zu sehen wie die neuen Ergebnisse aussehen
und wie die Notenverteilung sich verändert.
* Selenium Tests implementiert.
* Workflow verbessert und benutzerfreundlicher gestaltet 
(Testate erstellen, Excelexport etc.).

### 2018-09-05
Das MÜSLI läuft ab sofort mit Python Version 3 und nutzt teilweise neuere
Python Module.

### 2017-11-30
Alle Bugs im MÜSLI sind jetzt in den IssueTracker von Github umgezogen. Dort
können gerne weitere programmtechnische Probleme gemeldet werden. Support
für die Installation im Mathematischen Institut gibt es weiterhin über die
unter Kontakt genannte Adresse.

### 2016-02-19
In den nächsten Wochen zieht die Fakultät für Mathematik und Informatik
gemeinsam mit dem IWR in das neu gebaute Mathematikon (INF 205). Aus diesem
Grund wird das MÜSLI um den 10. März teilweise nicht zur Verfügung stehen.

### 2015-09-22
Ab sofort können sich Benutzer ohne Matrikelnummer anmelden, indem sie die
Matrikelnummer 00000 eingeben. Diese muss baldmöglichst nachgetragen werden um
Problemen beim eintragen der Prüfungsergebnisse aus dem Weg zu gehen.

### 2014-08-30
Um Seminare sinnvoller Sortieren zu können werden Übungsgruppen ab sofort nach
Wochentag, Uhrzeit und Kommentarfeld (in dieser Reihenfolge) sortiert. Dadurch
wird ermöglicht, dass Seminare über das Kommentarfeld durchnummeriert werden
können.

### 2012-10-19
Es gibt wieder Korrelationsdiagramme, zumindest für einzelne Testate und die Summe
der Übungszettel. Der Vergleich einzelner Aufgaben wird irgendwann noch implementiert.
Die Links zu den Korrelationsdiagrammen finden sich auf den Vorlesungs- und Übungsgruppenseiten
unter den Testaten.

### 2012-09-22
Man kann jetzt Studenten per Hand in eine Vorlesung eintragen. Dazu gibt es auf
der Seite "Vorlesung bearbeiten" unten einen Link "Student als Teilnehmer eintragen".
Dort kann man durch Angabe der Emailadresse des Studenten diesen in eine Übungsgruppe
eintragen. Dieses Feature ist vor allem gedacht, um Studenten, die die Zulassung
zu einer Klausur in einem früheren Semester erworben haben, in die Vorlesesung
eintragen zu können. Sonst kann man ihnen keine Klausurpunkte eintragen.

### 2012-09-14
Auf der Seite zum Noteneintragen gibt es nun den versprochenen Button, um einzelne
Zeilen abzuspeichern. Damit besteht nichtmehr die Gefahr, beim Eintragen der
Punkteänderung eines Studenten ausversehen alles zu überschreiben.

### 2012-08-17
Von der Seite zum Noteneintragen aus kann man jetzt auch direkt die Punkte der
verlinkten Klausuren korrigieren. Dies ist gedacht, um nach der Klausureinsicht
Arbeitsschritte einzusparen. Die neue Note wird berechnet, aber nicht übertragen.
Dies muss man also noch selber machen. Demnächst wird es noch einen Button geben,
der dies übernehmen kann.

### 2012-07-27
Um mit den neuen Regelungen für Multiple Choice-Aufgaben umgehen zu können, kennt die
Notenberechnung jetzt die Funktion "round3down", die auf Drittelnoten abrundet. Genaueres
findet sich in der Hilfe auf der Seite "Noten eintragen".

### 2012-07-20
Die Seite mit der Punkteübersicht kann jetzt auch von Assistenten für die ganze Vorlesung
angezeigt werden. Der Link findet sich unten auf der Vorlesungsseite. Außerdem kann die
Tabelle durch Klick auf die Spaltenüberschriften nach den unterschiedlichen Werten sortiert
werden.

### 2012-06-29
Neben Zulassung und Anmeldung können zu Klausuren jetzt auch Atteste verwaltet werden. Das
Konzept ist das gleiche wie bei Zulassung und Anmeldung: Man muss die Funktionalität bei
den Einstellungen des Testats freischalten. Danach findet sich beim Punkte-Eintragen der Link
zum Eintragen der Attest-Informationen. Außerdem wird auf der Seite zum Noteneintragen bei
verlinkten Testaten mit Attest der Atteststatus angezeigt.

### 2012-06-19
Auf der Statistikseite zu Testaten kann jetzt eine Tabelle angezeigt werden, die angibt,
wieviele Studenten welche Mindestpunktzahl haben.

### 2012-05-18
Ab jetzt können Übungsaufgaben und Testate gelöscht werden. Aufgaben können gelöscht werden,
wenn kein Punkte eingetragen sind (auch nicht bei bereits ausgetragenen Studenten!). Ein
Testat kann gelöscht werden, wenn es keine Aufgaben mehr hat.

### 2012-04-18
Ab sofort können komplett leere Übungsgruppen gelöscht werden. In der Liste der ausgetretenen
Studenten werden Studenten die aus einer später gelöschten Gruppe ausgetreten sind, mit "gelöschte
Gruppe" angezeigt. Es lässt sich damit nicht mehr feststellen, aus welcher Gruppe sie genau
ausgetreten sind.

### 2012-04-13
Vorlesungen können jetzt mehr als einen Assistenten haben. Weitere Assistenten können momentan
nur die Administratoren hinzufügen (Erreichbar über "Kontakt").

### 2012-03-16
Das Ausrechnen von Noten hat eine Vereinfachung erfahren: Es gibt die zusätzlichen Funktionen
cases1, cases2 und cases3 zum Vergeben von ganzen, halben und drittel Noten. Details finden sich
unter "Hilfe" auf der Seite zum Noteneintragen.

### 2012-03-02
Es ist jetzt möglich, für jede Vorlesung einzustellen, ob die Tutoren Punkte für alle
Übungsgruppen oder nur für ihre eigenen Übungsgruppen eintragen dürfen, oder auch, dass
sie gar keine Punkte eintragen dürfen. Die Option dazu findet sich auf der "Bearbeiten"-Seite
der Vorlesung.

### 2012-02-27
Es gibt eine neue Seite mit Details zur Anmeldung über Präferenzen. Sie enthält Histogramme,
die die Beliebtheit jedes möglichen Termines angeben, sowie eine Übersicht der Fächerverteilung
unter den angemeldeten Studenten. Der Link zu der Seite findet sich auf der "Bearbeiten"-Seite
der Vorlesung.

### 2012-02-02
Die Punkte von Testaten können versteckt werden. Dies bewirkt, dass die Studenten ihre
Punktzahlen in diesem Testat nicht sehen. Die Option findet sich auf der "Bearbeiten"-Seite
des Testats.
