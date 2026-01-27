"""
File-Client für das Lesen von Textdateien aus dem analyze-Verzeichnis.
"""
import logging
from pathlib import Path
from typing import Any, Generator


logger = logging.getLogger(__name__)


class FileClient:
    """Client für das Lesen von Textdateien."""
    
    def __init__(self, input_dir: str):
        """
        Initialisiert den File-Client.
        
        Args:
            input_dir: Verzeichnis mit den zu verarbeitenden Textdateien
        """
        self.input_dir = Path(input_dir)
        
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input-Verzeichnis nicht gefunden: {input_dir}")
        
        if not self.input_dir.is_dir():
            raise ValueError(f"Input-Pfad ist kein Verzeichnis: {input_dir}")
    
    def _read_file(self, file_path: Path) -> str:
        """
        Liest eine Textdatei und gibt den Inhalt zurück.
        
        Args:
            file_path: Pfad zur Textdatei
            
        Returns:
            Inhalt der Datei als String
            
        Raises:
            IOError: Bei Lesefehlern
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                logger.warning(f"Datei ist leer: {file_path}")
                
            return content
            
        except UnicodeDecodeError as e:
            logger.error(f"Encoding-Fehler beim Lesen von {file_path}: {e}")
            raise IOError(f"Konnte Datei nicht lesen (Encoding-Problem): {file_path}")
        except IOError as e:
            logger.error(f"Fehler beim Lesen von {file_path}: {e}")
            raise
    
    def fetch_records(self, filename: str | None = None) -> list[dict[str, Any]]:
        """
        Liest Textdateien und gibt sie als Records zurück.
        
        Args:
            filename: Optional - Name einer spezifischen Datei. 
                     Falls None, werden alle .txt-Dateien im Verzeichnis verarbeitet.
        
        Returns:
            Liste von Dictionaries mit den Feldern:
            - id: Dateiname (ohne Erweiterung)
            - sourcetext: Inhalt der Datei
            
        Raises:
            FileNotFoundError: Wenn die spezifische Datei nicht gefunden wird
            IOError: Bei Lesefehlern
        """
        records = []
        
        if filename:
            # Einzelne Datei verarbeiten
            file_path = self.input_dir / filename
            
            if not file_path.exists():
                raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")
            
            content = self._read_file(file_path)
            
            record = {
                "id": file_path.stem,  # Dateiname ohne Erweiterung
                "sourcetext": content
            }
            records.append(record)
            
            logger.info(f"Datei geladen: {filename}")
            
        else:
            # Alle .txt-Dateien im Verzeichnis verarbeiten
            txt_files = sorted(self.input_dir.glob("*.txt"))
            
            if not txt_files:
                logger.warning(f"Keine .txt-Dateien gefunden in: {self.input_dir}")
                return records
            
            for file_path in txt_files:
                try:
                    content = self._read_file(file_path)
                    
                    record = {
                        "id": file_path.stem,
                        "sourcetext": content
                    }
                    records.append(record)
                    
                except IOError as e:
                    logger.error(f"Überspringe Datei {file_path.name}: {e}")
                    continue
            
            logger.info(f"{len(records)} Datei(en) aus {self.input_dir} geladen")
        
        return records
    
    def __enter__(self):
        """Context Manager: Keine Aktion erforderlich für File-Client."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager: Keine Cleanup-Aktion erforderlich."""
        pass
