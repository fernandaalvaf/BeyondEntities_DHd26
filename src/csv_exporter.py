"""
CSV-Exporter für Vergleichsergebnisse aus JSON-Dateien.
"""
import csv
import json
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class CSVExporter:
    """Exportiert Vergleichsergebnisse aus JSON-Dateien in CSV."""
    
    def __init__(self, json_dir: str, output_csv: str, languages: dict[str, str]):
        """
        Initialisiert den CSV-Exporter.
        
        Args:
            json_dir: Verzeichnis mit JSON-Dateien
            output_csv: Pfad zur Output-CSV-Datei
            languages: Dictionary mit Sprachen (field1, field2)
        """
        self.json_dir = Path(json_dir)
        self.output_csv = Path(output_csv)
        self.languages = languages
        
    def collect_comparisons(self) -> list[dict[str, Any]]:
        """
        Sammelt alle Vergleichsdaten aus den JSON-Dateien.
        
        Returns:
            Liste von Vergleichseinträgen
        """
        all_comparisons = []
        
        # Durchsuche alle JSON-Dateien
        json_files = sorted(self.json_dir.glob("*.json"))
        
        if not json_files:
            logger.warning(f"Keine JSON-Dateien in {self.json_dir} gefunden")
            return all_comparisons
        
        logger.info(f"Verarbeite {len(json_files)} JSON-Dateien")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extrahiere ID aus meta oder Dateinamen
                source_id = data.get('meta', {}).get('source_id', json_file.stem)
                
                # Extrahiere Vergleiche
                vergleiche = data.get('vergleich', [])
                
                for vergleich in vergleiche:
                    comparison = {
                        'id': source_id,
                        'konzept_field1': vergleich.get(f'konzept_{self.languages["field1"]}', ''),
                        'konzept_field2': vergleich.get(f'konzept_{self.languages["field2"]}', ''),
                        'similarity': vergleich.get('similarity', ''),
                        'abweichung': vergleich.get('abweichung', ''),
                        'beschreibung': vergleich.get('beschreibung', '')
                    }
                    all_comparisons.append(comparison)
                
                logger.debug(f"Verarbeitet: {json_file.name} - {len(vergleiche)} Vergleiche")
                
            except json.JSONDecodeError as e:
                logger.error(f"Fehler beim Parsen von {json_file}: {e}")
            except Exception as e:
                logger.error(f"Fehler bei Verarbeitung von {json_file}: {e}")
        
        logger.info(f"Insgesamt {len(all_comparisons)} Vergleiche gesammelt")
        return all_comparisons
    
    def export_to_csv(self) -> None:
        """
        Exportiert die Vergleichsdaten in eine CSV-Datei.
        """
        comparisons = self.collect_comparisons()
        
        if not comparisons:
            logger.warning("Keine Vergleichsdaten zum Exportieren vorhanden")
            return
        
        # Erstelle Output-Verzeichnis falls nötig
        self.output_csv.parent.mkdir(parents=True, exist_ok=True)
        
        # Dynamische Header basierend auf Sprachen
        lang1 = self.languages['field1']
        lang2 = self.languages['field2']
        
        fieldnames = [
            'id',
            f'konzept_{lang1}',
            f'konzept_{lang2}',
            'similarity',
            'abweichung',
            'beschreibung'
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
                
                for comparison in comparisons:
                    # Mappe die Felder auf die Header
                    row = {
                        'id': comparison['id'],
                        f'konzept_{lang1}': comparison['konzept_field1'],
                        f'konzept_{lang2}': comparison['konzept_field2'],
                        'similarity': comparison['similarity'],
                        'abweichung': comparison['abweichung'],
                        'beschreibung': comparison['beschreibung']
                    }
                    writer.writerow(row)
            
            logger.info(f"CSV erfolgreich exportiert: {self.output_csv}")
            logger.info(f"Anzahl Zeilen: {len(comparisons)}")
            
        except IOError as e:
            logger.error(f"Fehler beim Schreiben der CSV-Datei: {e}")
            raise


def export_comparisons_to_csv(
    json_dir: str,
    output_csv: str,
    languages: dict[str, str]
) -> None:
    """
    Convenience-Funktion zum Exportieren von Vergleichen nach CSV.
    
    Args:
        json_dir: Verzeichnis mit JSON-Dateien
        output_csv: Pfad zur Output-CSV-Datei
        languages: Dictionary mit Sprachen (field1, field2)
    """
    exporter = CSVExporter(json_dir, output_csv, languages)
    exporter.export_to_csv()
