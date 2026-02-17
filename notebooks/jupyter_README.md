# Jupyter-Notebooks – Kurzinfo und Nutzung

## Was ist ein Jupyter-Notebook?
Ein [Jupyter-Notebook](https://docs.jupyter.org/en/latest/) ist ein interaktives Dokument, in dem sich Text (Markdown), Code und Ausgaben (Tabellen, Grafiken) kombinieren lassen. Sie können Zellen einzeln ausführen und Ergebnisse direkt sehen.

## API‑Keys und LLM‑Provider (Kontext)
Die Notebooks greifen auf externe LLM‑Provider (z.B. [Gemini](https://aistudio.google.com/) oder [ChatAI](https://chat-ai.academiccloud.de/)) zu. Dafür benötigen Sie einen persönlichen API‑Key, der in der API‑Konfiguration eingetragen wird. Ohne gültigen API‑Key funktionieren die Abfragen nicht. Bewahren Sie den Schlüssel sicher auf und teilen Sie ihn niemals öffentlich.

## Provider (Kurzüberblick)
- **[Gemini (Google)](https://aistudio.google.com/):** Nutzung über den Google‑API‑Key; Base‑URL wird im Notebook automatisch gesetzt.
- **[ChatAI (AcademicCloud)](https://chat-ai.academiccloud.de/):** Nutzung mit AcademicCloud‑Key; Base‑URL ist im Notebook hinterlegt.

Tipp: Achten Sie darauf, dass der ausgewählte Provider zum Modell passt (Provider‑Konflikt wird vom Notebook geprüft).

## Notebooks in diesem Projekt
- `notebooks/Triple_Extraktion_Colab.ipynb`: Für [Google Colab](https://colab.research.google.com/) (Colab-spezifische Funktionen).
- `notebooks/Triple_Extraktion_jupyterhub.ipynb`: Für JupyterHub/Standard‑Jupyter (keine Colab‑Features).

## Nutzung in Google Colab
1. Öffnen Sie das Notebook in [Google Colab](https://colab.research.google.com/).
2. Führen Sie die Setup‑Zelle aus (installiert Abhängigkeiten).
3. Füllen Sie die API‑Konfiguration aus.
4. Laden Sie Dateien hoch und starten Sie die Verarbeitung.
5. Visualisieren Sie die Ergebnisse und laden Sie das ZIP herunter.

## Nutzung in JupyterHub / Standard‑Jupyter
1. Öffnen Sie das Notebook.
2. Führen Sie die Zelle „Abhängigkeiten installieren“ aus.
3. Führen Sie die Setup‑Zelle aus.
4. Füllen Sie die API‑Konfiguration aus.
5. Laden Sie Dateien manuell in `triple-jupyterhub/uploads` hoch.
6. Führen Sie die Zelle „Dateien vorbereiten“ aus (scannt Uploads).
7. Starten Sie die Verarbeitung.
8. Führen Sie Visualisierung/Download aus.

## Hinweise
- **API‑Key** niemals öffentlich teilen.
- Grafiken: In JupyterHub werden PNGs via Matplotlib erzeugt (keine Chrome‑Abhängigkeit).
- Bei fehlenden Paketen die Installationszelle erneut ausführen.

## Lokal ausführen
Sie können die Notebooks auch lokal ausführen, wenn [Jupyter](https://docs.jupyter.org/en/latest/) installiert ist.

Einsteiger‑Schritt‑für‑Schritt:
1. Öffnen Sie das Projektverzeichnis auf Ihrem Rechner.
2. Erstellen Sie eine virtuelle Umgebung (empfohlen). Wenn Sie damit noch nicht vertraut sind, sehen Sie hier eine kurze Einführung: https://docs.python.org/3/tutorial/venv.html
3. Starten Sie Jupyter Notebook oder JupyterLab. Eine einfache Einführung dazu finden Sie hier: https://jupyter.org/install
4. Öffnen Sie das gewünschte Notebook im Browser.
5. Führen Sie die Installationszelle im Notebook aus.
6. Führen Sie die Setup‑Zelle aus und arbeiten Sie sich Zelle für Zelle vor.

Checkliste Installation (lokal):
- [ ] Virtuelle Umgebung aktiviert (siehe https://docs.python.org/3/tutorial/venv.html)
- [ ] Jupyter installiert und startet (siehe https://jupyter.org/install)
- [ ] Installationszelle im Notebook ausgeführt
- [ ] API‑Key in der Konfiguration gesetzt
- [ ] Testlauf ohne Fehler

Hinweis: Falls Sie lokal PNG‑Export via Kaleido nutzen möchten, stellen Sie sicher, dass die nötigen Systemabhängigkeiten (z.B. Chrome) verfügbar sind. Die Matplotlib‑Variante (`notebooks/Triple_Extraktion_jupyterhub.ipynb`) funktioniert ohne Chrome.
