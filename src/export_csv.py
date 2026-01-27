"""
Standalone-Skript zum Exportieren von JSON-Triples nach CSV.
"""
import argparse
import logging
import sys

from config_loader import load_config, get_processing_config
from csv_exporter import CSVExporter


def setup_logging() -> None:
    """Konfiguriert das Logging-System."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def main() -> int:
    """
    Hauptfunktion.
    
    Returns:
        Exit-Code (0 = Erfolg, 1 = Fehler)
    """
    parser = argparse.ArgumentParser(
        description="Exportiert Triple-Daten aus JSON-Dateien nach CSV"
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Pfad zur Konfigurationsdatei (Standard: config.yaml)'
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        help='Verzeichnis mit JSON-Dateien (überschreibt Config)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='csv/triples.csv',
        help='Pfad zur Output-CSV-Datei (Standard: csv/triples.csv)'
    )
    
    args = parser.parse_args()
    
    # Logging einrichten
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=" * 60)
        logger.info("Starte CSV-Export von Triple-Daten")
        logger.info("=" * 60)
        
        # Konfiguration laden
        logger.info(f"Lade Konfiguration aus: {args.config}")
        config = load_config(args.config)
        
        # Verzeichnisse aus Config
        processing_config = get_processing_config(config)
        
        json_dir = args.input_dir or processing_config.get('output_dir', 'output_json')
        
        logger.info(f"JSON-Verzeichnis: {json_dir}")
        logger.info(f"Output-CSV: {args.output}")
        
        # Export durchführen
        exporter = CSVExporter(
            json_dir=json_dir,
            output_csv=args.output
        )
        exporter.export_to_csv()
        
        logger.info("=" * 60)
        logger.info("CSV-Export erfolgreich abgeschlossen")
        logger.info("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Datei nicht gefunden: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
