"""
File-Client für das Lesen von Textdateien und XML-Dateien aus dem analyze-Verzeichnis.
"""
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Generator
logger = logging.getLogger(__name__)


class FileClient:
    """Client für das Lesen von Textdateien und XML-Dateien."""
    
    def __init__(self, input_dir: str, xml_text_xpath: str = ".//text"):
        """
        Initialisiert den File-Client.
        
        Args:
            input_dir: Verzeichnis mit den zu verarbeitenden Dateien (txt, xml)
            xml_text_xpath: XPath-Ausdruck für Text-Extraktion aus XML (default: .//text)
        """
        self.input_dir = Path(input_dir)
        self.xml_text_xpath = xml_text_xpath
        
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
    
    def _read_xml_file(self, file_path: Path) -> str:
        """
        Liest eine XML-Datei und extrahiert den Text.
        
        Args:
            file_path: Pfad zur XML-Datei
            
        Returns:
            Extrahierter Text aus XML als String
            
        Raises:
            IOError: Bei Lesefehlern oder Parse-Fehlern
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extrahiere Text basierend auf xpath
            # Für einfache Fälle: sammle allen Text
            text_parts = []
            
            # Wenn xpath .//text ist, suche nach <text> Tags
            if self.xml_text_xpath == ".//text":
                for elem in root.iter('text'):
                    if elem.text:
                        text_parts.append(elem.text.strip())
            else:
                # Fallback: Sammle allen Text im Dokument
                text_parts = [text.strip() for text in root.itertext() if text.strip()]
            
            content = ' '.join(text_parts)
            
            if not content:
                logger.warning(f"Kein Text in XML-Datei gefunden: {file_path}")
                
            return content
            
        except ET.ParseError as e:
            logger.error(f"XML-Parse-Fehler in {file_path}: {e}")
            raise IOError(f"Konnte XML-Datei nicht parsen: {file_path}")
        except IOError as e:
            logger.error(f"Fehler beim Lesen von {file_path}: {e}")
            raise
    
    def fetch_records(self, filename: str | None = None) -> list[dict[str, Any]]:
        """
        Liest Textdateien oder XML-Dateien und gibt sie als Records zurück.
        
        Args:
            filename: Optional - Name einer spezifischen Datei (.txt oder .xml). 
                     Falls None, werden alle .txt und .xml-Dateien im Verzeichnis verarbeitet.
        
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
            
            # Bestimme Format und lese entsprechend
            if file_path.suffix.lower() == '.xml':
                content = self._read_xml_file(file_path)
            else:
                content = self._read_file(file_path)
            
            record = {
                "id": file_path.stem,  # Dateiname ohne Erweiterung
                "sourcetext": content
            }
            records.append(record)
            
            logger.info(f"Datei geladen: {filename}")
            
        else:
            # Alle .txt und .xml-Dateien im Verzeichnis verarbeiten
            txt_files = sorted(self.input_dir.glob("*.txt"))
            xml_files = sorted(self.input_dir.glob("*.xml"))
            all_files = txt_files + xml_files
            
            if not all_files:
                logger.warning(f"Keine .txt oder .xml-Dateien gefunden in: {self.input_dir}")
                return records
            
            for file_path in all_files:
                try:
                    # Bestimme Format und lese entsprechend
                    if file_path.suffix.lower() == '.xml':
                        content = self._read_xml_file(file_path)
                    else:
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
