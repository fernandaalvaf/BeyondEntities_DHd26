"""
Standalone-Skript zum Exportieren von JSON-Vergleichen nach CSV.
"""
import argparse
import logging
import sys

from config_loader import load_config, get_api_config, get_processing_config
from csv_exporter import export_comparisons_to_csv


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
        description="Exportiert Vergleichsdaten aus JSON-Dateien nach CSV"
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
        default='csv/vergleiche.csv',
        help='Pfad zur Output-CSV-Datei (Standard: csv/vergleiche.csv)'
    )
    
    args = parser.parse_args()
    
    # Logging einrichten
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=" * 60)
        logger.info("Starte CSV-Export von Vergleichsdaten")
        logger.info("=" * 60)
        
        # Konfiguration laden
        logger.info(f"Lade Konfiguration aus: {args.config}")
        config = load_config(args.config)
        
        # Verzeichnisse und Sprachen aus Config
        processing_config = get_processing_config(config)
        api_config = get_api_config(config)
        
        json_dir = args.input_dir or processing_config.get('output_dir', 'output_json')
        languages = api_config.get('languages', {'field1': 'de', 'field2': 'en'})
        
        logger.info(f"JSON-Verzeichnis: {json_dir}")
        logger.info(f"Output-CSV: {args.output}")
        logger.info(f"Sprachen: {languages}")
        
        # Export durchführen
        export_comparisons_to_csv(
            json_dir=json_dir,
            output_csv=args.output,
            languages=languages
        )
        
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
