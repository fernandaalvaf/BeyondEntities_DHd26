"""
Haupt-Einstiegspunkt für die Beschreibungsverarbeitung.
"""
import argparse
import logging
import sys
from pathlib import Path

from config_loader import load_config, get_database_config, get_api_config, get_processing_config
from db_client import DatabaseClient
from openwebui_client import OpenWebUIClient
from processor import Processor


def setup_logging(log_file: str = "logs/processing.log") -> None:
    """
    Konfiguriert das Logging-System.
    
    Args:
        log_file: Pfad zur Log-Datei
    """
    # Erstelle logs-Verzeichnis falls nötig
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Konfiguriere Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_prompt(prompt_file: str = "prompt.txt") -> str:
    """
    Lädt den System-/Instruktionsprompt aus einer Datei.
    
    Args:
        prompt_file: Pfad zur Prompt-Datei
        
    Returns:
        Prompt-Text als String
        
    Raises:
        FileNotFoundError: Wenn die Prompt-Datei nicht gefunden wird
    """
    prompt_path = Path(prompt_file)
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt-Datei nicht gefunden: {prompt_file}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt = f.read().strip()
    
    if not prompt:
        raise ValueError("Prompt-Datei ist leer")
    
    return prompt


def main() -> int:
    """
    Hauptfunktion.
    
    Returns:
        Exit-Code (0 = Erfolg, 1 = Fehler)
    """
    # Argument-Parser
    parser = argparse.ArgumentParser(
        description="Verarbeitet Beschreibungen über OpenWebUI-API"
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Pfad zur Konfigurationsdatei (Standard: config.yaml)'
    )
    parser.add_argument(
        '--prompt',
        type=str,
        default='prompt.txt',
        help='Pfad zur Prompt-Datei (Standard: prompt.txt)'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default='logs/processing.log',
        help='Pfad zur Log-Datei (Standard: logs/processing.log)'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Überspringe IDs, für die bereits JSON-Dateien existieren. Nützlich zum Fortsetzen unterbrochener Verarbeitungen oder für inkrementelle Updates.'
    )
    parser.add_argument(
        '--update-metadata',
        action='store_true',
        help='Aktualisiere nur die Metadaten (original_texts) in existierenden JSON-Dateien, ohne die KI-API aufzurufen. Nützlich zum Nachtragen fehlender Originaltexte.'
    )
    
    args = parser.parse_args()
    
    # Logging einrichten
    setup_logging(args.log_file)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=" * 60)
        logger.info("Starte Beschreibungsverarbeitung")
        logger.info("=" * 60)
        
        # 1. Konfiguration laden
        logger.info(f"Lade Konfiguration aus: {args.config}")
        config = load_config(args.config)
        
        # 2. Prompt laden
        logger.info(f"Lade Prompt aus: {args.prompt}")
        system_prompt = load_prompt(args.prompt)
        
        # 3. Komponenten initialisieren
        db_config = get_database_config(config)
        api_config = get_api_config(config)
        processing_config = get_processing_config(config)
        
        logger.info("Initialisiere Datenbank-Client")
        db_client = DatabaseClient(
            driver=db_config['driver'],
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            name=db_config['name'],
            query=db_config['query']
        )
        
        logger.info("Initialisiere OpenWebUI-Client")
        openwebui_client = OpenWebUIClient(
            base_url=api_config['base_url'],
            endpoint=api_config['endpoint'],
            model=api_config['model'],
            system_prompt=system_prompt,
            languages=api_config.get('languages', {'field1': 'unknown', 'field2': 'unknown'}),
            api_key=api_config.get('api_key'),
            timeout_seconds=api_config.get('timeout_seconds', 60),
            max_retries=api_config.get('max_retries', 3),
            retry_delay_seconds=api_config.get('retry_delay_seconds', 3)
        )
        
        logger.info("Initialisiere Processor")
        processor = Processor(
            db_client=db_client,
            openwebui_client=openwebui_client,
            output_dir=processing_config['output_dir'],
            required_keys=processing_config.get('required_keys', []),
            skip_existing=args.skip_existing,
            update_metadata=args.update_metadata
        )
        
        # 4. Verarbeitung durchführen
        with db_client:  # Context Manager für Verbindungsmanagement
            stats = processor.run()
        
        # 5. Zusammenfassung
        logger.info("=" * 60)
        logger.info("Verarbeitung abgeschlossen")
        logger.info(f"Gesamt: {stats['total']}")
        logger.info(f"Erfolgreich: {stats['success']}")
        logger.info(f"Übersprungen: {stats['skipped']}")
        logger.info(f"Fehlgeschlagen: {stats['failed']}")
        logger.info("=" * 60)
        
        # Exit-Code basierend auf Erfolg
        if stats['failed'] > 0:
            logger.warning(f"{stats['failed']} Datensätze konnten nicht verarbeitet werden")
            return 1
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Datei nicht gefunden: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Konfigurationsfehler: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
