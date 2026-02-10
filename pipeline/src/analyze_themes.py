#!/usr/bin/env python3
"""
Themen- und Begriffsanalyse für Triple-Extraktionsergebnisse.

Analysiert JSON-Dateien aus dem output_json-Verzeichnis und erstellt
Statistiken über wiederkehrende Entitäten, Prädikate und Konzepte (Themen).
"""
import argparse
import csv
import json
import logging
import sys
from collections import Counter
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class ThemeAnalyzer:
    """Analysiert JSON-Dateien und erstellt Statistiken über Themen und Begriffe."""
    
    def __init__(self, json_dir: str):
        """
        Initialisiert den Theme-Analyzer.
        
        Args:
            json_dir: Verzeichnis mit JSON-Dateien (rekursive Suche)
        """
        self.json_dir = Path(json_dir)
        
        # Counter für verschiedene Statistiken
        self.entity_types: Counter = Counter()
        self.entity_labels: Counter = Counter()
        self.praedikat_labels: Counter = Counter()
        self.entities_by_type: dict[str, Counter] = {}
        
        # Metadaten
        self.file_count = 0
        self.triple_count = 0
        self.entity_count = 0
        self.praedikat_count = 0
    
    def analyze(self) -> bool:
        """
        Führt die Analyse aller JSON-Dateien durch.
        
        Returns:
            True bei Erfolg, False wenn keine Dateien gefunden
        """
        json_files = sorted(self.json_dir.rglob("*.json"))
        
        if not json_files:
            logger.warning(f"Keine JSON-Dateien in {self.json_dir} gefunden")
            return False
        
        logger.info(f"Analysiere {len(json_files)} JSON-Dateien...")
        
        for json_file in json_files:
            self._process_file(json_file)
        
        self.file_count = len(json_files)
        return True
    
    def _process_file(self, json_file: Path) -> None:
        """
        Verarbeitet eine einzelne JSON-Datei.
        
        Args:
            json_file: Pfad zur JSON-Datei
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Fehler beim Lesen von {json_file}: {e}")
            return
        
        # Entitäten verarbeiten
        entities = data.get('entities', {})
        for entity_id, entity_data in entities.items():
            label = entity_data.get('label', '')
            typ = entity_data.get('typ', 'Unbekannt')
            
            # Zähle nach Typ
            self.entity_types[typ] += 1
            
            # Zähle Labels global
            self.entity_labels[label] += 1
            
            # Zähle Labels nach Typ
            if typ not in self.entities_by_type:
                self.entities_by_type[typ] = Counter()
            self.entities_by_type[typ][label] += 1
            
            self.entity_count += 1
        
        # Prädikate verarbeiten
        praedikate = data.get('praedikate', {})
        for praedikat_id, praedikat_data in praedikate.items():
            label = praedikat_data.get('label', '')
            self.praedikat_labels[label] += 1
            self.praedikat_count += 1
        
        # Triples zählen
        triples = data.get('triples', [])
        self.triple_count += len(triples)
    
    def get_top_entities_by_type(self, entity_type: str, top_n: int = 20) -> list[tuple[str, int]]:
        """
        Gibt die häufigsten Entitäten eines bestimmten Typs zurück.
        
        Args:
            entity_type: Der Entitätstyp (z.B. "Konzept", "Person")
            top_n: Anzahl der Top-Einträge
            
        Returns:
            Liste von (label, count) Tupeln
        """
        if entity_type in self.entities_by_type:
            return self.entities_by_type[entity_type].most_common(top_n)
        return []
    
    def print_statistics(self, top_n: int = 20) -> None:
        """
        Gibt formatierte Statistiken im Terminal aus.
        
        Args:
            top_n: Anzahl der Top-Einträge für Listen
        """
        # Überschrift
        print("\n" + "=" * 70)
        print("  THEMEN- UND BEGRIFFSANALYSE - TRIPLE-EXTRAKTOR")
        print("=" * 70)
        
        # Übersichtsstatistik
        print(f"\n{'ÜBERSICHT':^70}")
        print("-" * 70)
        print(f"  Analysierte Dateien:    {self.file_count:>8}")
        print(f"  Entitäten gesamt:       {self.entity_count:>8}")
        print(f"  Prädikate gesamt:       {self.praedikat_count:>8}")
        print(f"  Triples gesamt:         {self.triple_count:>8}")
        
        # Entitäten nach Typ
        print(f"\n{'ENTITÄTEN NACH TYP':^70}")
        print("-" * 70)
        if self.entity_types:
            max_type_count = max(self.entity_types.values())
            for typ, count in self.entity_types.most_common():
                bar = "█" * min(int(count / max_type_count * 30), 30)
                print(f"  {typ:<20} {count:>6}  {bar}")
        
        # Top Listen
        self._print_top_list("TOP KONZEPTE (THEMEN)", self.get_top_entities_by_type("Konzept", top_n))
        self._print_top_list("TOP PERSONEN", self.get_top_entities_by_type("Person", top_n))
        self._print_top_list("TOP ORTE", self.get_top_entities_by_type("Ort", top_n))
        self._print_top_list("TOP WERKE", self.get_top_entities_by_type("Werk", top_n))
        
        print("\n" + "=" * 70)
        print("  Analyse abgeschlossen")
        print("=" * 70 + "\n")
    
    def _print_top_list(self, title: str, items: list[tuple[str, int]]) -> None:
        """
        Gibt eine formatierte Top-Liste aus.
        
        Args:
            title: Titel der Liste
            items: Liste von (label, count) Tupeln
        """
        if not items:
            return
        
        print(f"\n{title:^70}")
        print("-" * 70)
        
        max_count = max(count for _, count in items) if items else 1
        
        for i, (label, count) in enumerate(items, 1):
            # Label kürzen wenn zu lang
            display_label = label[:45] + "..." if len(label) > 48 else label
            bar_width = int(count / max_count * 20)
            bar = "█" * bar_width
            print(f"  {i:>3}. {display_label:<48} {count:>4}  {bar}")
    
    def export_to_csv(self, output_path: str) -> None:
        """
        Exportiert die Statistiken in eine CSV-Datei.
        
        Args:
            output_path: Pfad zur Output-CSV-Datei
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            
            # Header
            writer.writerow(['kategorie', 'typ', 'label', 'anzahl'])
            
            # Entitäten nach Typ
            for typ, counter in self.entities_by_type.items():
                for label, count in counter.most_common():
                    writer.writerow(['entitaet', typ, label, count])
            
            # Prädikate
            for label, count in self.praedikat_labels.most_common():
                writer.writerow(['praedikat', '', label, count])
        
        logger.info(f"Statistiken exportiert nach: {output_file}")


def main():
    """Hauptfunktion mit CLI-Interface."""
    parser = argparse.ArgumentParser(
        description="Analysiert JSON-Dateien und erstellt Themen-/Begriffsstatistiken.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python src/analyze_themes.py
  python src/analyze_themes.py --input-dir output_json/JeanPaul_1809 --top 30
  python src/analyze_themes.py --output csv/theme_statistics.csv
        """
    )
    
    parser.add_argument(
        '--input-dir',
        type=str,
        default='output_json',
        help='Verzeichnis mit JSON-Dateien (default: output_json)'
    )
    
    parser.add_argument(
        '--top',
        type=int,
        default=20,
        help='Anzahl der Top-Einträge in Listen (default: 20)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Optionaler Pfad für CSV-Export der Statistiken'
    )
    
    args = parser.parse_args()
    
    # Analyzer initialisieren und ausführen
    analyzer = ThemeAnalyzer(args.input_dir)
    
    if not analyzer.analyze():
        sys.exit(1)
    
    # Statistiken ausgeben
    analyzer.print_statistics(top_n=args.top)
    
    # Optional: CSV exportieren
    if args.output:
        analyzer.export_to_csv(args.output)


if __name__ == '__main__':
    main()
