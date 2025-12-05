"""
Konfigurations-Loader für YAML-Dateien.
"""
import yaml
from pathlib import Path
from typing import Any


def load_config(path: str = "config.yaml") -> dict[str, Any]:
    """
    Lädt die Konfigurationsdatei.
    
    Args:
        path: Pfad zur YAML-Konfigurationsdatei
        
    Returns:
        Dictionary mit der Konfiguration
        
    Raises:
        FileNotFoundError: Wenn die Datei nicht gefunden wird
        yaml.YAMLError: Wenn die YAML-Datei ungültig ist
    """
    config_path = Path(path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        if not config:
            raise ValueError("Konfigurationsdatei ist leer")
            
        # Validiere Hauptsektionen
        required_sections = ['database', 'api', 'processing']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Fehlende Sektion in Konfiguration: {section}")
                
        return config
        
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Fehler beim Parsen der YAML-Datei: {e}")


def get_database_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Extrahiert die Datenbank-Konfiguration.
    
    Args:
        config: Vollständige Konfiguration
        
    Returns:
        Datenbank-Konfiguration
    """
    return config.get('database', {})


def get_api_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Extrahiert die API-Konfiguration.
    
    Args:
        config: Vollständige Konfiguration
        
    Returns:
        API-Konfiguration
    """
    return config.get('api', {})


def get_processing_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Extrahiert die Verarbeitungs-Konfiguration.
    
    Args:
        config: Vollständige Konfiguration
        
    Returns:
        Verarbeitungs-Konfiguration
    """
    return config.get('processing', {})
