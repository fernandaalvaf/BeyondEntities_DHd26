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


class Processor:
    """Verarbeitet Datensätze von der Datenbank über die KI-API."""
    
    def __init__(
        self,
        db_client: DatabaseClient,
        openwebui_client: OpenWebUIClient,
        output_dir: str,
        required_keys: list[str] | None = None
    ):
        """
        Initialisiert den Processor.
        
        Args:
            db_client: Datenbank-Client
            openwebui_client: OpenWebUI-Client
            output_dir: Verzeichnis für Output-Dateien
            required_keys: Erforderliche JSON-Keys zur Validierung
        """
        self.db_client = db_client
        self.openwebui_client = openwebui_client
        self.output_dir = Path(output_dir)
        self.required_keys = required_keys or []
        
        # Erstelle Output-Verzeichnis
        self._ensure_output_dir()
        
    def _ensure_output_dir(self) -> None:
        """Erstellt das Output-Verzeichnis, falls es nicht existiert."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output-Verzeichnis bereit: {self.output_dir}")
    
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
        
        try:
            logger.info(f"Starte Verarbeitung für ID {record_id}")
            
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
            
            # Erstelle Metadaten
            meta_info = {
                "source_id": record_id,
                "languages": list(self.openwebui_client.languages.values())
            }
            
            # Speichere Ergebnis
            self._save_result(record_id, result, meta_info)
            
            logger.info(f"Verarbeitung erfolgreich für ID {record_id}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei Verarbeitung von ID {record_id}: {e}")
            return False
    
    def run(self) -> dict[str, int]:
        """
        Führt die komplette Verarbeitung durch.
        
        Returns:
            Dictionary mit Statistiken: {"total": x, "success": y, "failed": z}
        """
        logger.info("Starte Verarbeitungspipeline")
        
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0
        }
        
        try:
            # Hole Datensätze aus Datenbank
            records = self.db_client.fetch_records()
            stats["total"] = len(records)
            
            if stats["total"] == 0:
                logger.warning("Keine Datensätze zum Verarbeiten gefunden")
                return stats
            
            logger.info(f"Gefundene Datensätze: {stats['total']}")
            
            # Verarbeite jeden Datensatz
            for i, record in enumerate(records, 1):
                logger.info(f"Verarbeite Datensatz {i}/{stats['total']}")
                
                if self._process_record(record):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
            
            # Zusammenfassung
            logger.info(
                f"Verarbeitung abgeschlossen. "
                f"Gesamt: {stats['total']}, "
                f"Erfolgreich: {stats['success']}, "
                f"Fehlgeschlagen: {stats['failed']}"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Kritischer Fehler während der Verarbeitung: {e}")
            raise
