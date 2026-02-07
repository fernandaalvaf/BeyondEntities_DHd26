"""
CSV-Exporter für Triple-Extraktionsergebnisse aus JSON-Dateien.
"""
import csv
import json
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class CSVExporter:
    """Exportiert Triple-Ergebnisse aus JSON-Dateien in CSV."""
    
    def __init__(self, json_dir: str, output_csv: str):
        """
        Initialisiert den CSV-Exporter.
        
        Args:
            json_dir: Verzeichnis mit JSON-Dateien
            output_csv: Pfad zur Output-CSV-Datei
        """
        self.json_dir = Path(json_dir)
        self.output_csv = Path(output_csv)
        
    def collect_triples(self) -> list[dict[str, Any]]:
        """
        Sammelt alle Triple-Daten aus den JSON-Dateien.
        
        Returns:
            Liste von Triple-Einträgen mit aufgelösten Labels
        """
        all_triples = []
        
        # Durchsuche alle JSON-Dateien rekursiv (auch in Unterverzeichnissen)
        json_files = sorted(self.json_dir.rglob("*.json"))
        
        if not json_files:
            logger.warning(f"Keine JSON-Dateien in {self.json_dir} gefunden")
            return all_triples
        
        logger.info(f"Verarbeite {len(json_files)} JSON-Dateien")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extrahiere Metadaten aus quelle
                quelle = data.get('quelle', {})
                datei = quelle.get('datei', json_file.stem)
                source_id = quelle.get('source_id', '')
                verarbeitet = quelle.get('verarbeitet', '')
                original_text = quelle.get('original_text', '')
                
                # Extrahiere Entities und Prädikate
                entities = data.get('entities', {})
                praedikate = data.get('praedikate', {})
                
                # Extrahiere Triples
                triples = data.get('triples', [])
                
                for triple in triples:
                    # Löse Entity- und Prädikat-IDs auf
                    subjekt_id = triple.get('subjekt', '')
                    praedikat_id = triple.get('praedikat', '')
                    objekt_id = triple.get('objekt', '')
                    
                    subjekt_label = entities.get(subjekt_id, {}).get('label', subjekt_id)
                    subjekt_typ = entities.get(subjekt_id, {}).get('typ', '')
                    
                    praedikat_label = praedikate.get(praedikat_id, {}).get('label', praedikat_id)
                    praedikat_normalisiert = ', '.join(praedikate.get(praedikat_id, {}).get('normalisiert_von', []))
                    
                    objekt_label = entities.get(objekt_id, {}).get('label', objekt_id)
                    objekt_typ = entities.get(objekt_id, {}).get('typ', '')
                    
                    triple_entry = {
                        'datei': datei,
                        'source_id': source_id,
                        'verarbeitet': verarbeitet,
                        'subjekt_id': subjekt_id,
                        'subjekt': subjekt_label,
                        'subjekt_typ': subjekt_typ,
                        'praedikat_id': praedikat_id,
                        'praedikat': praedikat_label,
                        'praedikat_normalisiert_von': praedikat_normalisiert,
                        'objekt_id': objekt_id,
                        'objekt': objekt_label,
                        'objekt_typ': objekt_typ,
                        'original_text': original_text
                    }
                    all_triples.append(triple_entry)
                
                logger.debug(f"Verarbeitet: {json_file.name} - {len(triples)} Triples")
                
            except json.JSONDecodeError as e:
                logger.error(f"Fehler beim Parsen von {json_file}: {e}")
            except Exception as e:
                logger.error(f"Fehler bei Verarbeitung von {json_file}: {e}")
        
        logger.info(f"Insgesamt {len(all_triples)} Triples gesammelt")
        return all_triples
    
    def export_to_csv(self) -> None:
        """
        Exportiert die Triple-Daten in eine CSV-Datei.
        """
        triples = self.collect_triples()
        
        if not triples:
            logger.warning("Keine Triple-Daten zum Exportieren vorhanden")
            return
        
        # Sortiere nach Datei/ID
        triples.sort(key=lambda x: (x['datei'], x['subjekt']))
        
        # Erstelle Output-Verzeichnis falls nötig
        self.output_csv.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            'datei',
            'source_id',
            'verarbeitet',
            'subjekt_id',
            'subjekt',
            'subjekt_typ',
            'praedikat_id',
            'praedikat',
            'praedikat_normalisiert_von',
            'objekt_id',
            'objekt',
            'objekt_typ',
            'original_text'
        ]
        
        try:
            with open(self.output_csv, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=fieldnames,
                    delimiter=';',
                    quoting=csv.QUOTE_MINIMAL
                )
                
                writer.writeheader()
                writer.writerows(triples)
            
            logger.info(f"CSV erfolgreich exportiert: {self.output_csv}")
            logger.info(f"Anzahl Zeilen: {len(triples)}")
            
        except IOError as e:
            logger.error(f"Fehler beim Schreiben der CSV-Datei: {e}")
            raise
