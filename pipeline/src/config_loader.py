"""
Konfigurations-Loader für YAML-Dateien.
"""
import os
import yaml
from pathlib import Path
from typing import Any


# Mapping: Umgebungsvariable → (Profilname, config-Key)
ENV_KEY_MAP: dict[str, tuple[str, str]] = {
    "CHATAI_API_KEY":     ("chatai",     "api_key"),
    "GEMINI_API_KEY":     ("gemini",     "api_key"),
    "OPENAI_API_KEY":     ("openai",     "api_key"),
    "ANTHROPIC_API_KEY":  ("anthropic",  "api_key"),
    "MISTRAL_API_KEY":    ("mistral",    "api_key"),
    "OPENROUTER_API_KEY": ("openrouter", "api_key"),
}


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
        required_sections = ['api', 'processing']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Fehlende Sektion in Konfiguration: {section}")
                
        # ENV-Variablen überschreiben API-Keys (Docker / CI)
        _apply_env_overrides(config)

        return config
        
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Fehler beim Parsen der YAML-Datei: {e}")


def _apply_env_overrides(config: dict[str, Any]) -> None:
    """
    Überschreibt API-Keys in der Konfiguration mit Werten aus
    Umgebungsvariablen (z. B. aus docker/.env).
    Nur gesetzte Variablen werden übernommen.
    """
    profiles = config.get('api', {}).get('profiles', {})
    for env_var, (profile_name, key) in ENV_KEY_MAP.items():
        value = os.environ.get(env_var)
        if value and profile_name in profiles:
            profiles[profile_name][key] = value


def get_database_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Extrahiert die Datenbank-Konfiguration.
    
    Args:
        config: Vollständige Konfiguration
        
    Returns:
        Datenbank-Konfiguration
    """
    return config.get('database', {})


def get_active_profiles(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    Gibt alle Profile zurück, bei denen active: true gesetzt ist.

    Args:
        config: Vollständige Konfiguration

    Returns:
        Dict von Profilname → Profilkonfiguration (nur aktive Profile)

    Raises:
        ValueError: Wenn keine aktiven Profile gefunden werden
    """
    profiles = config.get('api', {}).get('profiles', {})
    active = {
        name: cfg
        for name, cfg in profiles.items()
        if cfg.get('active', True)  # Standard: true für Abwärtskompatibilität
    }
    if not active:
        raise ValueError(
            "Keine aktiven API-Profile gefunden. "
            "Bitte mindestens ein Profil in config.yaml auf 'active: true' setzen."
        )
    return active


def get_api_config(config: dict[str, Any], profile_name: str | None = None) -> dict[str, Any]:
    """
    Extrahiert die API-Konfiguration für ein bestimmtes Profil.

    Args:
        config: Vollständige Konfiguration
        profile_name: Name des gewünschten Profils. Falls None, wird
                      'active_profile' aus der Config genutzt (Legacy-Fallback).

    Returns:
        API-Konfiguration des gewählten Profils

    Raises:
        ValueError: Wenn das Profil nicht existiert oder nicht aktiv ist
    """
    api_config = config.get('api', {})
    profiles = api_config.get('profiles', {})

    # Profil explizit übergeben (interaktive Auswahl oder --profile Flag)
    if profile_name:
        if profile_name not in profiles:
            raise ValueError(
                f"Unbekanntes API-Profil: '{profile_name}'. "
                f"Verfügbare Profile: {', '.join(profiles.keys())}"
            )
        return profiles[profile_name]

    # Legacy-Fallback: active_profile in config.yaml
    if 'active_profile' in api_config and profiles:
        active = api_config['active_profile']
        if active not in profiles:
            raise ValueError(
                f"Unbekanntes API-Profil: '{active}'. "
                f"Verfügbare Profile: {', '.join(profiles.keys())}"
            )
        return profiles[active]

    # Letzter Fallback: direkte API-Konfiguration (alte Struktur ohne profiles)
    return api_config


def get_processing_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Extrahiert die Verarbeitungs-Konfiguration.
    
    Args:
        config: Vollständige Konfiguration
        
    Returns:
        Verarbeitungs-Konfiguration
    """
    return config.get('processing', {})


def get_extraction_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Extrahiert die Extraktions-Konfiguration.
    
    Args:
        config: Vollständige Konfiguration
        
    Returns:
        Extraktions-Konfiguration
    """
    return config.get('extraction', {})


def get_files_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Extrahiert die Datei-Konfiguration.
    
    Args:
        config: Vollständige Konfiguration
        
    Returns:
        Datei-Konfiguration
    """
    return config.get('files', {})
