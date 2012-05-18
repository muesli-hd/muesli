# -*- coding: utf-8 -*-
#
# utils.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2012, Matthias Kuemmerer <matthias (at) matthias-k.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

changelog=u"""
====2012-05-18
concerns:assistants
Ab jetzt können Übungsaufgaben und Testate gelöscht werden. Aufgaben können gelöscht werden,
wenn kein Punkte eingetragen sind (auch nicht bei bereits ausgetragenen Studenten!). Ein
Testat kann gelöscht werden, wenn es keine Aufgaben mehr hat.

====2012-04-18
concerns:assistants
Ab sofort können komplett leere Übungsgruppen gelöscht werden. In der Liste der ausgetretenen
Studenten werden Studenten die aus einer später gelöschten Gruppe ausgetreten sind, mit "gelöschte
Gruppe" angezeigt. Es lässt sich damit nicht mehr feststellen, aus welcher Gruppe sie genau
ausgetreten sind.

====2012-04-13
concerns:assistants
Vorlesungen können jetzt mehr als einen Assistenten haben. Weitere Assistenten können momentan
nur die Administratoren hinzufügen (Erreichbar über "Kontakt").

====2012-03-16
concerns:assistants
Das Ausrechnen von Noten hat eine Vereinfachung erfahren: Es gibt die zusätzlichen Funktionen
cases1, cases2 und cases3 zum Vergeben von ganzen, halben und drittel Noten. Details finden sich
unter "Hilfe" auf der Seite zum Noteneintragen.

====2012-03-02
concerns:assistants
Es ist jetzt möglich, für jede Vorlesung einzustellen, ob die Tutoren Punkte für alle
Übungsgruppen oder nur für ihre eigenen Übungsgruppen eintragen dürfen, oder auch, dass
sie gar keine Punkte eintragen dürfen. Die Option dazu findet sich auf der "Bearbeiten"-Seite
der Vorlesung.

====2012-02-27
concerns:assistants
Es gibt eine neue Seite mit Details zur Anmeldung über Präferenzen. Sie enthält Histogramme,
die die Beliebtheit jedes möglichen Termines angeben, sowie eine Übersicht der Fächerverteilung
unter den angemeldeten Studenten. Der Link zu der Seite findet sich auf der "Bearbeiten"-Seite
der Vorlesung.

====2012-02-02
concerns:assistants
Die Punkte von Testaten können versteckt werden. Dies bewirkt, dass die Studenten ihre
Punktzahlen in diesem Testat nicht sehen. Die Option findet sich auf der "Bearbeiten"-Seite
des Testats.
"""