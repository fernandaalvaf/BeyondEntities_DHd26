"""
Processor-Modul für die Verarbeitung der Datensätze.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from db_client import DatabaseClient
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
    """Verarbeitet Datensätze von der Datenbank über die KI-API."""
    
    def __init__(
        self,
        db_client: DatabaseClient,
        openwebui_client: OpenWebUIClient,
        output_dir: str,
        required_keys: list[str] | None = None,
        skip_existing: bool = False,
        update_metadata: bool = False
    ):
        """
        Initialisiert den Processor.
        
        Args:
            db_client: Datenbank-Client
            openwebui_client: OpenWebUI-Client
            output_dir: Verzeichnis für Output-Dateien
            required_keys: Erforderliche JSON-Keys zur Validierung
            skip_existing: Wenn True, werden IDs mit existierenden JSON-Dateien übersprungen
            update_metadata: Wenn True, werden nur Metadaten in existierenden Dateien aktualisiert
        """
        self.db_client = db_client
        self.openwebui_client = openwebui_client
        self.output_dir = Path(output_dir)
        self.required_keys = required_keys or []
        self.skip_existing = skip_existing
        self.update_metadata = update_metadata
        
        # Erstelle Output-Verzeichnis
        self._ensure_output_dir()
        
    def _ensure_output_dir(self) -> None:
        """Erstellt das Output-Verzeichnis, falls es nicht existiert."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output-Verzeichnis bereit: {self.output_dir}")
    
    def _update_json_metadata(self, record_id: int, field1: str, field2: str) -> bool:
        """
        Aktualisiert die Metadaten in einer existierenden JSON-Datei.
        
        Args:
            record_id: ID des Datensatzes
            field1: Text aus field1
            field2: Text aus field2
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        output_file = self.output_dir / f"{record_id}.json"
        
        if not output_file.exists():
            logger.warning(f"JSON-Datei für ID {record_id} nicht gefunden - überspringe")
            return False
        
        try:
            # Lade existierende JSON-Datei
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Aktualisiere oder füge original_texts hinzu
            if 'meta' not in data:
                data['meta'] = {}
            
            data['meta']['original_texts'] = {
                self.openwebui_client.languages['field1']: field1,
                self.openwebui_client.languages['field2']: field2
            }
            
            # Speichere aktualisierte Datei
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Metadaten aktualisiert für ID {record_id}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Fehler beim Parsen von {output_file}: {e}")
            return False
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Metadaten für ID {record_id}: {e}")
            return False
    
    def _save_result(self, record_id: int, result: dict[str, Any], meta_info: dict[str, Any]) -> None:
        """
        Speichert das Ergebnis als JSON-Datei.
        
        Args:
            record_id: ID des Datensatzes
            result: Verarbeitetes JSON-Ergebnis
            meta_info: Zusätzliche Metadaten
        """
        output_file = self.output_dir / f"{record_id}.json"
        
        # Kombiniere Ergebnis mit Metadaten
        output_data = {
            **result,
            "meta": meta_info
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Ergebnis gespeichert: {output_file}")
            
        except IOError as e:
            logger.error(f"Fehler beim Speichern der Datei {output_file}: {e}")
            raise
    
    def _process_record(self, record: dict[str, Any]) -> bool:
        """
        Verarbeitet einen einzelnen Datensatz.
        
        Args:
            record: Datensatz mit id und Beschreibungen
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        record_id = record.get("id")
        field1 = record.get("field1", "")
        field2 = record.get("field2", "")
        
        # Update-Metadata Modus: Nur Metadaten in existierenden Dateien aktualisieren
        if self.update_metadata:
            print(f"{Colors.CYAN}Aktualisiere Metadaten für ID {record_id}...{Colors.RESET}")
            return self._update_json_metadata(record_id, field1, field2)
        
        try:
            logger.info(f"Starte Verarbeitung für ID {record_id}")
            
            # Zeitstempel vor Verarbeitung
            start_time = datetime.now()
            
            # Bereite Beschreibungen für API-Aufruf vor
            descriptions = {
                "id": record_id,
                "field1": record.get("field1", ""),
                "field2": record.get("field2", "")
            }
            
            # Rufe KI-API auf
            result = self.openwebui_client.call_model(
                descriptions=descriptions,
                required_keys=self.required_keys
            )
            
            # Zeitstempel nach Verarbeitung
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Erstelle Metadaten mit Zeitinformationen und Originaltexten
            meta_info = {
                "source_id": record_id,
                "languages": list(self.openwebui_client.languages.values()),
                "original_texts": {
                    self.openwebui_client.languages['field1']: descriptions.get('field1', ''),
                    self.openwebui_client.languages['field2']: descriptions.get('field2', '')
                },
                "execution_date": start_time.isoformat(),
                "execution_time_seconds": round(execution_time, 2)
            }
            
            # Speichere Ergebnis
            self._save_result(record_id, result, meta_info)
            
            logger.info(f"Verarbeitung erfolgreich für ID {record_id} ({execution_time:.2f}s)")
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei Verarbeitung von ID {record_id}: {e}")
            return False
    
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
            print(f"{Colors.BLUE}{Colors.BOLD}STARTE VERARBEITUNG{Colors.RESET}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
        logger.info("Starte Verarbeitungspipeline")
        
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        failed_ids = []  # Liste für fehlgeschlagene IDs
        
        try:
            # Hole Datensätze aus Datenbank
            records = self.db_client.fetch_records()
            stats["total"] = len(records)
            
            if stats["total"] == 0:
                print(f"{Colors.RED}Keine Datensätze zum Verarbeiten gefunden{Colors.RESET}")
                logger.warning("Keine Datensätze zum Verarbeiten gefunden")
                return stats
            
            print(f"{Colors.CYAN}Gefundene Datensätze: {stats['total']}{Colors.RESET}")
            logger.info(f"Gefundene Datensätze: {stats['total']}")
            
            if self.update_metadata:
                print(f"{Colors.CYAN}Update-Modus: Aktualisiere original_texts in existierenden JSON-Dateien{Colors.RESET}")
                logger.info("Update-Modus: Aktualisiere original_texts in existierenden JSON-Dateien")
            elif self.skip_existing:
                print(f"{Colors.CYAN}Skip-Modus aktiv: Existierende JSON-Dateien werden übersprungen{Colors.RESET}")
                logger.info("Skip-Modus aktiv: Existierende JSON-Dateien werden übersprungen")
            
            # Verarbeite jeden Datensatz
            for i, record in enumerate(records, 1):
                record_id = record.get("id")
                output_file = self.output_dir / f"{record_id}.json"
                
                # Im Update-Modus: Überspringe nur fehlende Dateien
                if self.update_metadata:
                    if not output_file.exists():
                        print(f"{Colors.YELLOW}⊘ Überspringe ID {record_id} - JSON-Datei existiert nicht{Colors.RESET}")
                        logger.info(f"Überspringe Datensatz {i}/{stats['total']} (ID {record_id}) - Datei existiert nicht")
                        stats["skipped"] += 1
                        continue
                # Im Normal-Modus: Prüfe ob Datei bereits existiert
                elif self.skip_existing and output_file.exists():
                    print(f"{Colors.GREEN}✓ Überspringe ID {record_id} - Datei existiert bereits{Colors.RESET}")
                    logger.info(f"Überspringe Datensatz {i}/{stats['total']} (ID {record_id}) - Datei existiert bereits")
                    stats["skipped"] += 1
                    continue
                
                print(f"\n{Colors.CYAN}--- Datensatz {i}/{stats['total']} (ID {record_id}) ---{Colors.RESET}")
                logger.info(f"Verarbeite Datensatz {i}/{stats['total']}")
                
                if self._process_record(record):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                    failed_ids.append(record_id)
            
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
            
            # Extra-Log für fehlgeschlagene IDs
            if failed_ids:
                print(f"\n{Colors.RED}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
                print(f"{Colors.RED}{Colors.BOLD}FEHLGESCHLAGENE IDs (nach {self.openwebui_client.max_retries} Versuchen):{Colors.RESET}")
                print(f"{Colors.RED}Anzahl: {len(failed_ids)}{Colors.RESET}")
                print(f"{Colors.RED}IDs: {', '.join(map(str, failed_ids))}{Colors.RESET}")
                print(f"{Colors.RED}{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
                
                logger.error("=" * 60)
                logger.error("FEHLGESCHLAGENE IDs (nach 3 Versuchen):")
                logger.error(f"Anzahl: {len(failed_ids)}")
                logger.error(f"IDs: {', '.join(map(str, failed_ids))}")
                logger.error("=" * 60)
            
            return stats
            
        except Exception as e:
            logger.error(f"Kritischer Fehler während der Verarbeitung: {e}")
            raise
