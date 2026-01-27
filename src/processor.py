"""
Processor-Modul für die Verarbeitung der Datensätze.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Union

import networkx as nx
import plotly.graph_objects as go

from db_client import DatabaseClient
from file_client import FileClient
from openwebui_client import OpenWebUIClient


logger = logging.getLogger(__name__)


class Colors:
    """ANSI-Farbcodes für Terminal-Ausgabe."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class Processor:
    """Verarbeitet Datensätze von Dateien oder Datenbank über die KI-API."""
    
    def __init__(
        self,
        data_client: Union[DatabaseClient, FileClient],
        openwebui_client: OpenWebUIClient,
        output_dir: str,
        required_keys: list[str] | None = None,
        skip_existing: bool = False,
        update_metadata: bool = False,
        granularity: int = 3,
        source_type: str = 'file',
        filename: str | None = None,
        entity_types: list[str] | None = None
    ):
        """
        Initialisiert den Processor.
        
        Args:
            data_client: Datenbank- oder File-Client
            openwebui_client: OpenWebUI-Client
            output_dir: Verzeichnis für Output-Dateien
            required_keys: Erforderliche JSON-Keys zur Validierung
            skip_existing: Wenn True, werden bereits verarbeitete Dateien übersprungen
            update_metadata: Wenn True, werden nur Metadaten in existierenden Dateien aktualisiert
            granularity: Abstraktionslevel für Triple-Extraktion (1-5)
            source_type: 'file' oder 'db'
            filename: Spezifischer Dateiname (nur bei source_type='file')
            entity_types: Liste erlaubter Entitätstypen
        """
        self.data_client = data_client
        self.openwebui_client = openwebui_client
        self.output_dir = Path(output_dir)
        self.required_keys = required_keys or []
        self.skip_existing = skip_existing
        self.update_metadata = update_metadata
        self.granularity = granularity
        self.source_type = source_type
        self.filename = filename
        self.entity_types = entity_types or []
        
        # Erstelle Output-Verzeichnis
        self._ensure_output_dir()
        
    def _ensure_output_dir(self) -> None:
        """Erstellt das Output-Verzeichnis, falls es nicht existiert."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output-Verzeichnis bereit: {self.output_dir}")
    
    def _generate_timestamp_filename(self, record_id: str | int) -> str:
        """
        Generiert einen Timestamp-basierten Dateinamen.
        
        Args:
            record_id: ID des Datensatzes
            
        Returns:
            Dateiname im Format YYYYMMDD-HHMMSS-{source}.json
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"{timestamp}-{self.source_type}.json"
    
    def _update_json_metadata(self, filename: str, sourcetext: str) -> bool:
        """
        Aktualisiert die Metadaten in einer existierenden JSON-Datei.
        
        Args:
            filename: Name der JSON-Datei
            sourcetext: Ursprünglicher Textinhalt
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        output_file = self.output_dir / filename
        
        if not output_file.exists():
            logger.warning(f"JSON-Datei {filename} nicht gefunden - überspringe")
            return False
        
        try:
            # Lade existierende JSON-Datei
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Aktualisiere oder füge original_text hinzu
            if 'quelle' not in data:
                data['quelle'] = {}
            
            data['quelle']['original_text'] = sourcetext
            
            # Speichere aktualisierte Datei
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Metadaten aktualisiert für {filename}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Fehler beim Parsen von {output_file}: {e}")
            return False
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Metadaten für {filename}: {e}")
            return False
    
    def _generate_plantuml(self, result: dict[str, Any]) -> str:
        """
        Generiert PlantUML-Code für die Triples.
        
        Args:
            result: JSON-Ergebnis mit entities, praedikate, triples
            
        Returns:
            PlantUML-Code als String
        """
        entities = result.get('entities', {})
        praedikate = result.get('praedikate', {})
        triples = result.get('triples', [])
        
        lines = ["@startuml", ""]
        
        # Skinparam für bessere Darstellung
        lines.append("skinparam defaultTextAlignment center")
        lines.append("skinparam objectBorderColor #333333")
        lines.append("skinparam objectBackgroundColor #FEFECE")
        lines.append("skinparam arrowColor #333333")
        lines.append("")
        
        # Entity-Typ zu PlantUML-Farbe Mapping
        type_colors = {
            "Person": "#ADD8E6",      # Hellblau
            "Ort": "#90EE90",         # Hellgrün
            "Werk": "#FFB6C1",        # Hellrosa
            "Institution": "#DDA0DD", # Pflaume
            "Ereignis": "#F0E68C",    # Khaki
            "Konzept": "#E6E6FA",     # Lavendel
            "Zeitpunkt": "#FFDAB9",   # Pfirsich
            "Sonstiges": "#D3D3D3"    # Hellgrau
        }
        
        # Definiere Objekte für alle Entitäten
        for entity_id, entity_data in entities.items():
            label = entity_data.get('label', entity_id)
            typ = entity_data.get('typ', 'Sonstiges')
            color = type_colors.get(typ, "#D3D3D3")
            # Escape Anführungszeichen und Sonderzeichen
            safe_label = label.replace('"', '\\"').replace('\n', ' ')
            lines.append(f'object "{safe_label}" as {entity_id} {color}')
        
        lines.append("")
        
        # Definiere Relationen
        for triple in triples:
            subjekt_id = triple.get('subjekt', '')
            praedikat_id = triple.get('praedikat', '')
            objekt_id = triple.get('objekt', '')
            
            # Hole Prädikat-Label
            praedikat_label = praedikate.get(praedikat_id, {}).get('label', praedikat_id)
            safe_praedikat = praedikat_label.replace('"', '\\"').replace('\n', ' ')
            
            lines.append(f'{subjekt_id} --> {objekt_id} : "{safe_praedikat}"')
        
        lines.append("")
        lines.append("@enduml")
        
        return "\n".join(lines)
    
    def _generate_interactive_graph(self, result: dict[str, Any]) -> str:
        """
        Generiert einen interaktiven Netzwerkgraph mit plotly.
        
        Args:
            result: JSON-Ergebnis mit entities, praedikate, triples
            
        Returns:
            HTML-Code des interaktiven Graphen
        """
        entities = result.get('entities', {})
        praedikate = result.get('praedikate', {})
        triples = result.get('triples', [])
        
        # Erstelle NetworkX-Graph
        G = nx.DiGraph()
        
        # Füge Knoten hinzu mit Attributen
        for entity_id, entity_data in entities.items():
            G.add_node(
                entity_id,
                label=entity_data.get('label', entity_id),
                typ=entity_data.get('typ', 'Sonstiges')
            )
        
        # Füge Kanten hinzu
        for triple in triples:
            subjekt_id = triple.get('subjekt', '')
            objekt_id = triple.get('objekt', '')
            praedikat_id = triple.get('praedikat', '')
            praedikat_label = praedikate.get(praedikat_id, {}).get('label', praedikat_id)
            
            if subjekt_id in G.nodes and objekt_id in G.nodes:
                G.add_edge(subjekt_id, objekt_id, label=praedikat_label)
        
        # Layout berechnen (spring layout für bessere Verteilung)
        pos = nx.spring_layout(G, k=1, iterations=50, seed=42)
        
        # Entity-Typ zu Farbe Mapping
        type_colors = {
            "Person": "#ADD8E6",
            "Ort": "#90EE90",
            "Werk": "#FFB6C1",
            "Institution": "#DDA0DD",
            "Ereignis": "#F0E68C",
            "Konzept": "#E6E6FA",
            "Zeitpunkt": "#FFDAB9",
            "Sonstiges": "#D3D3D3"
        }
        
        # Erstelle Edge Traces
        edge_traces = []
        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_label = edge[2].get('label', '')
            
            # Edge line
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=2, color='#888'),
                hoverinfo='text',
                hovertext=edge_label,
                showlegend=False
            )
            edge_traces.append(edge_trace)
            
            # Edge label (Mittelpunkt)
            mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
            edge_label_trace = go.Scatter(
                x=[mid_x],
                y=[mid_y],
                mode='text',
                text=[edge_label],
                textposition='middle center',
                textfont=dict(size=9, color='#555'),
                hoverinfo='skip',
                showlegend=False
            )
            edge_traces.append(edge_label_trace)
        
        # Gruppiere Knoten nach Typ für Legend
        node_traces_by_type = {}
        
        for node_id in G.nodes():
            node_data = G.nodes[node_id]
            typ = node_data.get('typ', 'Sonstiges')
            label = node_data.get('label', node_id)
            x, y = pos[node_id]
            color = type_colors.get(typ, '#D3D3D3')
            
            if typ not in node_traces_by_type:
                node_traces_by_type[typ] = {
                    'x': [],
                    'y': [],
                    'text': [],
                    'hovertext': [],
                    'color': color
                }
            
            node_traces_by_type[typ]['x'].append(x)
            node_traces_by_type[typ]['y'].append(y)
            node_traces_by_type[typ]['text'].append(label)
            node_traces_by_type[typ]['hovertext'].append(f"{label}<br>Typ: {typ}<br>ID: {node_id}")
        
        # Erstelle Node Traces pro Typ
        node_traces = []
        for typ, data in node_traces_by_type.items():
            node_trace = go.Scatter(
                x=data['x'],
                y=data['y'],
                mode='markers+text',
                marker=dict(
                    size=20,
                    color=data['color'],
                    line=dict(width=2, color='#333')
                ),
                text=data['text'],
                textposition='top center',
                textfont=dict(size=10),
                hoverinfo='text',
                hovertext=data['hovertext'],
                name=typ,
                showlegend=True
            )
            node_traces.append(node_trace)
        
        # Kombiniere alle Traces
        fig = go.Figure(data=edge_traces + node_traces)
        
        # Layout
        fig.update_layout(
            title=dict(
                text='Triple-Netzwerk (Interaktiv)',
                x=0.5,
                xanchor='center',
                font=dict(size=20)
            ),
            showlegend=True,
            legend=dict(
                title='Entitätstypen',
                yanchor='top',
                y=0.99,
                xanchor='left',
                x=0.01
            ),
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=60),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            height=800
        )
        
        # Exportiere als HTML-String
        return fig.to_html(include_plotlyjs='cdn', full_html=True)
    
    def _save_result(self, filename: str, result: dict[str, Any], meta_info: dict[str, Any]) -> None:
        """
        Speichert das Ergebnis als JSON-Datei.
        
        Args:
            filename: Name der Output-Datei
            result: Verarbeitetes JSON-Ergebnis
            meta_info: Zusätzliche Metadaten
        """
        output_file = self.output_dir / filename
        
        # Generiere PlantUML-Code
        plantuml_code = self._generate_plantuml(result)
        
        # Kombiniere Ergebnis mit Metadaten und PlantUML
        output_data = {
            **result,
            "plantuml": plantuml_code,
            "quelle": meta_info
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Ergebnis gespeichert: {output_file}")
            
            # Speichere PlantUML als separate .puml-Datei
            puml_file = output_file.with_suffix('.puml')
            with open(puml_file, 'w', encoding='utf-8') as f:
                f.write(plantuml_code)
            
            logger.info(f"PlantUML-Diagramm gespeichert: {puml_file}")
            
            # Generiere und speichere interaktiven Netzwerkgraph
            html_graph = self._generate_interactive_graph(result)
            html_file = output_file.with_suffix('.html')
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_graph)
            
            logger.info(f"Interaktiver Graph gespeichert: {html_file}")
            
        except IOError as e:
            logger.error(f"Fehler beim Speichern der Datei {output_file}: {e}")
            raise
    
    def _process_record(self, record: dict[str, Any], counter: int) -> tuple[bool, str]:
        """
        Verarbeitet einen einzelnen Datensatz.
        
        Args:
            record: Datensatz mit id und sourcetext
            counter: Laufende Nummer für die Ausgabedatei
            
        Returns:
            Tuple (Erfolg: bool, Dateiname: str)
        """
        record_id = record.get("id")
        sourcetext = record.get("sourcetext", "")
        
        # Generiere Dateinamen
        filename = self._generate_timestamp_filename(record_id)
        
        # Update-Metadata Modus: Nur Metadaten in existierenden Dateien aktualisieren
        if self.update_metadata:
            print(f"{Colors.CYAN}Aktualisiere Metadaten für {filename}...{Colors.RESET}")
            success = self._update_json_metadata(filename, sourcetext)
            return (success, filename)
        
        try:
            logger.info(f"Starte Verarbeitung für ID {record_id}")
            
            # Zeitstempel vor Verarbeitung
            start_time = datetime.now()
            
            # Bereite Text für API-Aufruf vor
            text_data = {
                "id": record_id,
                "sourcetext": sourcetext
            }
            
            # Rufe KI-API auf mit Granularität und Entity-Typen
            result = self.openwebui_client.call_model(
                text_data=text_data,
                required_keys=self.required_keys,
                granularity=self.granularity,
                entity_types=self.entity_types
            )
            
            # Zeitstempel nach Verarbeitung
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Erstelle Metadaten
            meta_info = {
                "datei": str(record_id) if self.source_type == 'file' else None,
                "source_id": record_id if self.source_type == 'db' else None,
                "verarbeitet": start_time.isoformat(),
                "ausfuehrungszeit_sekunden": round(execution_time, 2),
                "modell": self.openwebui_client.model,
                "api_provider": self.openwebui_client.api_provider,
                "original_text": sourcetext
            }
            
            # Entferne None-Werte
            meta_info = {k: v for k, v in meta_info.items() if v is not None}
            
            # Speichere Ergebnis
            self._save_result(filename, result, meta_info)
            
            logger.info(f"Verarbeitung erfolgreich für ID {record_id} ({execution_time:.2f}s)")
            return (True, filename)
            
        except Exception as e:
            logger.error(f"Fehler bei Verarbeitung von ID {record_id}: {e}")
            return (False, filename)
    
    def run(self) -> dict[str, int]:
        """
        Führt die komplette Verarbeitung durch.
        
        Returns:
            Dictionary mit Statistiken: {"total": x, "success": y, "failed": z, "skipped": w}
        """
        print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
        if self.update_metadata:
            print(f"{Colors.BLUE}{Colors.BOLD}METADATEN-UPDATE MODUS{Colors.RESET}")
        else:
            print(f"{Colors.BLUE}{Colors.BOLD}STARTE TRIPLE-EXTRAKTION{Colors.RESET}")
            print(f"{Colors.CYAN}Granularität (Abstraktionslevel): {self.granularity}/5{Colors.RESET}")
            print(f"{Colors.CYAN}Quelle: {self.source_type}{Colors.RESET}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
        logger.info("Starte Verarbeitungspipeline")
        
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        failed_records = []  # Liste für fehlgeschlagene Records
        
        try:
            # Hole Datensätze (aus Dateien oder Datenbank)
            if self.source_type == 'file' and hasattr(self.data_client, 'fetch_records'):
                records = self.data_client.fetch_records(filename=self.filename)
            else:
                records = self.data_client.fetch_records()
                
            stats["total"] = len(records)
            
            if stats["total"] == 0:
                print(f"{Colors.RED}Keine Datensätze zum Verarbeiten gefunden{Colors.RESET}")
                logger.warning("Keine Datensätze zum Verarbeiten gefunden")
                return stats
            
            print(f"{Colors.CYAN}Gefundene Datensätze: {stats['total']}{Colors.RESET}")
            logger.info(f"Gefundene Datensätze: {stats['total']}")
            
            if self.update_metadata:
                print(f"{Colors.CYAN}Update-Modus: Aktualisiere Metadaten in existierenden JSON-Dateien{Colors.RESET}")
                logger.info("Update-Modus: Aktualisiere Metadaten in existierenden JSON-Dateien")
            elif self.skip_existing:
                print(f"{Colors.CYAN}Skip-Modus aktiv: Existierende JSON-Dateien werden übersprungen{Colors.RESET}")
                logger.info("Skip-Modus aktiv: Existierende JSON-Dateien werden übersprungen")
            
            # Verarbeite jeden Datensatz
            for i, record in enumerate(records, 1):
                record_id = record.get("id")
                
                # Generiere vorläufigen Dateinamen zum Prüfen
                temp_filename = self._generate_timestamp_filename(record_id)
                output_file = self.output_dir / temp_filename
                
                # Skip-Logik (vereinfacht, da Timestamp-Namen Kollisionen unwahrscheinlich macht)
                # Im Update-Modus: Keine Skip-Logik
                # Im Normal-Modus mit skip_existing: Wird durch Timestamp-Namen praktisch verhindert
                
                print(f"\n{Colors.CYAN}--- Datensatz {i}/{stats['total']} (ID {record_id}) ---{Colors.RESET}")
                logger.info(f"Verarbeite Datensatz {i}/{stats['total']}")
                
                success, filename = self._process_record(record, i)
                
                if success:
                    stats["success"] += 1
                    print(f"{Colors.GREEN}✓ Erfolgreich gespeichert: {filename}{Colors.RESET}")
                else:
                    stats["failed"] += 1
                    failed_records.append(str(record_id))
                    print(f"{Colors.RED}✗ Fehlgeschlagen: {record_id}{Colors.RESET}")
            
            # Zusammenfassung
            print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
            print(f"{Colors.BLUE}{Colors.BOLD}VERARBEITUNG ABGESCHLOSSEN{Colors.RESET}")
            print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
            print(f"{Colors.CYAN}Gesamt: {stats['total']}{Colors.RESET}")
            print(f"{Colors.GREEN}✓ Erfolgreich: {stats['success']}{Colors.RESET}")
            if stats['skipped'] > 0:
                print(f"{Colors.GREEN}⊘ Übersprungen: {stats['skipped']}{Colors.RESET}")
            if stats['failed'] > 0:
                print(f"{Colors.RED}✗ Fehlgeschlagen: {stats['failed']}{Colors.RESET}")
            print(f"{Colors.BLUE}Gesamte API-Aufrufe: {self.openwebui_client.api_call_counter}{Colors.RESET}")
            print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
            
            logger.info(
                f"Verarbeitung abgeschlossen. "
                f"Gesamt: {stats['total']}, "
                f"Erfolgreich: {stats['success']}, "
                f"Übersprungen: {stats['skipped']}, "
                f"Fehlgeschlagen: {stats['failed']}"
            )
            
            # Extra-Log für fehlgeschlagene Records
            if failed_records:
                print(f"\n{Colors.RED}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
                print(f"{Colors.RED}{Colors.BOLD}FEHLGESCHLAGENE RECORDS (nach {self.openwebui_client.max_retries} Versuchen):{Colors.RESET}")
                print(f"{Colors.RED}Anzahl: {len(failed_records)}{Colors.RESET}")
                print(f"{Colors.RED}IDs: {', '.join(failed_records)}{Colors.RESET}")
                print(f"{Colors.RED}{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
                
                logger.error("=" * 60)
                logger.error("FEHLGESCHLAGENE RECORDS:")
                logger.error(f"Anzahl: {len(failed_records)}")
                logger.error(f"IDs: {', '.join(failed_records)}")
                logger.error("=" * 60)
            
            return stats
            
        except Exception as e:
            logger.error(f"Kritischer Fehler während der Verarbeitung: {e}")
            raise
