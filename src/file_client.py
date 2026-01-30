"""
File-Client für das Lesen von Textdateien und XML-Dateien aus dem analyze-Verzeichnis.
Optimiert TEI-XML für Token-Effizienz durch Extraktion relevanter Metadaten und Brieftext.
"""
import copy
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Generator

logger = logging.getLogger(__name__)

# TEI-Namespace
TEI_NS = {'tei': 'http://www.tei-c.org/ns/1.0'}


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
        Liest eine TEI-XML-Datei und extrahiert Metadaten + Brieftext als optimierten Plaintext.
        
        Extrahiert:
        - Titel, Absender, Empfänger, Datum, Ort aus correspDesc
        - Brieftext bereinigt (ohne Apparatnotizen, Markup)
        
        Args:
            file_path: Pfad zur XML-Datei
            
        Returns:
            Optimierter Plaintext mit Metadaten und Briefinhalt
            
        Raises:
            IOError: Bei Lesefehlern oder Parse-Fehlern
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Prüfe ob TEI-Namespace vorhanden
            is_tei = root.tag.startswith('{http://www.tei-c.org/ns/1.0}') or root.tag == 'TEI'
            
            if is_tei:
                return self._extract_tei_optimized(root, file_path)
            else:
                # Fallback für Nicht-TEI-XML
                return self._extract_xml_fallback(root, file_path)
                
        except ET.ParseError as e:
            logger.error(f"XML-Parse-Fehler in {file_path}: {e}")
            raise IOError(f"Konnte XML-Datei nicht parsen: {file_path}")
        except IOError as e:
            logger.error(f"Fehler beim Lesen von {file_path}: {e}")
            raise
    
    def _extract_tei_optimized(self, root: ET.Element, file_path: Path) -> str:
        """
        Extrahiert optimierten Plaintext aus TEI-XML.
        
        Args:
            root: XML-Root-Element
            file_path: Pfad zur Quelldatei (für Logging)
            
        Returns:
            Formatierter Plaintext mit Metadaten und Brieftext
        """
        ns = TEI_NS
        result_parts = []
        
        # === METADATEN EXTRAHIEREN ===
        
        # Titel aus titleStmt
        title_elem = root.find('.//tei:titleStmt/tei:title', ns)
        if title_elem is not None:
            title_text = self._get_element_text(title_elem)
            # Bereinige Titel (entferne IDs, pagina-Anweisungen)
            title_text = re.sub(r'\d+\s*$', '', title_text).strip()
            if title_text:
                result_parts.append(f"TITEL: {title_text}")
        
        # Korrespondenz-Metadaten aus correspDesc
        corresp_desc = root.find('.//tei:correspDesc', ns)
        if corresp_desc is not None:
            # Absender
            sent_action = corresp_desc.find('tei:correspAction[@type="sent"]', ns)
            if sent_action is not None:
                sender = sent_action.find('tei:persName', ns)
                if sender is not None:
                    sender_name = self._get_element_text(sender).strip()
                    if sender_name:
                        result_parts.append(f"ABSENDER: {sender_name}")
                
                place = sent_action.find('tei:placeName', ns)
                if place is not None:
                    place_name = self._get_element_text(place).strip()
                    if place_name:
                        result_parts.append(f"ORT: {place_name}")
                
                date = sent_action.find('tei:date', ns)
                if date is not None:
                    date_from = date.get('from', '')
                    date_to = date.get('to', '')
                    date_when = date.get('when', '')
                    if date_when:
                        result_parts.append(f"DATUM: {date_when}")
                    elif date_from and date_to:
                        result_parts.append(f"DATUM: {date_from} bis {date_to}")
                    elif date_from:
                        result_parts.append(f"DATUM: {date_from}")
            
            # Empfänger
            received_action = corresp_desc.find('tei:correspAction[@type="received"]', ns)
            if received_action is not None:
                receiver = received_action.find('tei:persName', ns)
                if receiver is not None:
                    receiver_name = self._get_element_text(receiver).strip()
                    if receiver_name:
                        result_parts.append(f"EMPFÄNGER: {receiver_name}")
        
        # === BRIEFTEXT EXTRAHIEREN ===
        
        body = root.find('.//tei:body', ns)
        if body is not None:
            letter_text = self._extract_letter_text(body, ns)
            if letter_text:
                result_parts.append("")  # Leerzeile vor Brieftext
                result_parts.append("BRIEFTEXT:")
                result_parts.append(letter_text)
        
        content = '\n'.join(result_parts)
        
        if not content.strip():
            logger.warning(f"Kein relevanter Inhalt in TEI-XML gefunden: {file_path}")
        else:
            # Log Token-Ersparnis
            original_size = len(ET.tostring(root, encoding='unicode'))
            optimized_size = len(content)
            savings = ((original_size - optimized_size) / original_size) * 100
            logger.info(f"XML optimiert: {file_path.name} - {savings:.1f}% Token-Ersparnis ({original_size} → {optimized_size} Zeichen)")
        
        return content
    
    def _extract_letter_text(self, body: ET.Element, ns: dict) -> str:
        """
        Extrahiert den bereinigten Brieftext aus dem body-Element.
        
        Entfernt:
        - note-Elemente (Apparatnotizen)
        - index-Elemente (Registereinträge)
        - pagina-Anweisungen
        - Übermäßige Whitespace
        
        Args:
            body: TEI body-Element
            ns: Namespace-Dictionary
            
        Returns:
            Bereinigter Brieftext
        """
        # Arbeite mit einer Kopie, um Original nicht zu verändern
        body_copy = copy.deepcopy(body)
        
        # Entferne störende Elemente (Apparatnotizen, Registereinträge, Anker)
        tags_to_remove = ['note', 'index', 'anchor', 'ref']
        for tag in tags_to_remove:
            # Mit TEI-Namespace
            for elem in body_copy.findall(f'.//tei:{tag}', ns):
                parent = self._find_parent(body_copy, elem)
                if parent is not None:
                    # Tail-Text bewahren (Text nach dem Element)
                    if elem.tail:
                        prev = self._find_previous_sibling(parent, elem)
                        if prev is not None:
                            prev.tail = (prev.tail or '') + elem.tail
                        else:
                            parent.text = (parent.text or '') + elem.tail
                    parent.remove(elem)
            # Ohne Namespace (für gemischte Dokumente)
            for elem in body_copy.findall(f'.//{tag}'):
                parent = self._find_parent(body_copy, elem)
                if parent is not None:
                    if elem.tail:
                        prev = self._find_previous_sibling(parent, elem)
                        if prev is not None:
                            prev.tail = (prev.tail or '') + elem.tail
                        else:
                            parent.text = (parent.text or '') + elem.tail
                    parent.remove(elem)
        
        # Extrahiere Text rekursiv mit besserer Struktur
        text = self._extract_text_recursive(body_copy)
        
        # Bereinigungen
        text = re.sub(r'\s+', ' ', text)  # Mehrfache Whitespace
        text = re.sub(r'\?\s*pagina[^?]*\?', '', text)  # <?pagina ...?>
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)  # Leerzeichen vor Satzzeichen
        text = re.sub(r'([.!?])\s+', r'\1\n', text)  # Absätze nach Satzende
        
        return text.strip()
    
    def _extract_text_recursive(self, elem: ET.Element) -> str:
        """Extrahiert Text rekursiv aus einem Element."""
        parts = []
        
        # Text vor Kindelementen
        if elem.text:
            parts.append(elem.text)
        
        # Kindelemente verarbeiten
        for child in elem:
            parts.append(self._extract_text_recursive(child))
            # Tail-Text (nach Kindelement)
            if child.tail:
                parts.append(child.tail)
        
        return ''.join(parts)
    
    def _find_previous_sibling(self, parent: ET.Element, target: ET.Element) -> ET.Element | None:
        """Findet das vorherige Geschwister-Element."""
        prev = None
        for child in parent:
            if child is target:
                return prev
            prev = child
        return None
    
    def _find_parent(self, root: ET.Element, target: ET.Element) -> ET.Element | None:
        """Findet das Elternelement eines Elements."""
        for parent in root.iter():
            for child in parent:
                if child is target:
                    return parent
        return None
    
    def _get_element_text(self, elem: ET.Element) -> str:
        """Extrahiert den gesamten Text eines Elements (inkl. Kinder)."""
        return ''.join(elem.itertext()).strip()
    
    def _extract_xml_fallback(self, root: ET.Element, file_path: Path) -> str:
        """
        Fallback-Extraktion für Nicht-TEI-XML.
        
        Args:
            root: XML-Root-Element
            file_path: Pfad zur Quelldatei
            
        Returns:
            Extrahierter Text
        """
        text_parts = []
        
        # Versuche .//text zu finden
        if self.xml_text_xpath == ".//text":
            for elem in root.iter('text'):
                text_parts.append(self._get_element_text(elem))
        
        # Fallback: allen Text sammeln
        if not text_parts:
            text_parts = [text.strip() for text in root.itertext() if text.strip()]
        
        content = ' '.join(text_parts)
        
        if not content:
            logger.warning(f"Kein Text in XML-Datei gefunden: {file_path}")
            
        return content
    
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
            - source_path: Vollständiger Pfad der Quelldatei (Path-Objekt)
            - relative_path: Relativer Pfad ab input_dir (für Unterverzeichnisse)
            
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
            
            # Berechne relativen Pfad
            try:
                rel_path = file_path.relative_to(self.input_dir)
            except ValueError:
                rel_path = Path(file_path.name)
            
            record = {
                "id": file_path.stem,  # Dateiname ohne Erweiterung
                "sourcetext": content,
                "source_path": file_path,
                "relative_path": rel_path
            }
            records.append(record)
            
            logger.info(f"Datei geladen: {filename}")
            
        else:
            # Alle .txt und .xml-Dateien im Verzeichnis UND Unterverzeichnissen verarbeiten
            txt_files = sorted(self.input_dir.rglob("*.txt"))
            xml_files = sorted(self.input_dir.rglob("*.xml"))
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
                    
                    # Berechne relativen Pfad
                    rel_path = file_path.relative_to(self.input_dir)
                    
                    record = {
                        "id": file_path.stem,
                        "sourcetext": content,
                        "source_path": file_path,
                        "relative_path": rel_path
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
