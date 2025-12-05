"""
OpenWebUI-Client für die Kommunikation mit der KI-API.
"""
import json
import logging
import time
from typing import Any
import requests
from requests.exceptions import RequestException, Timeout


logger = logging.getLogger(__name__)


class OpenWebUIClient:
    """Client für OpenWebUI-API-Aufrufe."""
    
    def __init__(
        self,
        base_url: str,
        endpoint: str,
        model: str,
        system_prompt: str,
        languages: dict[str, str],
        api_key: str | None = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
        retry_delay_seconds: int = 3
    ):
        """
        Initialisiert den OpenWebUI-Client.
        
        Args:
            base_url: Basis-URL der API (z.B. "http://localhost:11434")
            endpoint: API-Endpoint (z.B. "/api/chat/completions")
            model: Modellname
            system_prompt: System-/Instruktionsprompt
            languages: Dictionary mit Sprachen-ISO-Codes (field1, field2, field3)
            api_key: API-Schlüssel für Authentifizierung (optional)
            timeout_seconds: Timeout für API-Aufrufe in Sekunden
            max_retries: Maximale Anzahl von Wiederholungsversuchen
            retry_delay_seconds: Wartezeit zwischen Wiederholungen
        """
        self.base_url = base_url.rstrip('/')
        self.endpoint = endpoint
        self.model = model
        self.system_prompt = system_prompt
        self.languages = languages
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.full_url = f"{self.base_url}{self.endpoint}"
    
    def build_payload(self, descriptions: dict[str, Any]) -> dict[str, Any]:
        """
        Erstellt die Request-Payload für die API.
        
        Args:
            descriptions: Dictionary mit id und Beschreibungen
                         (Schlüssel: "id", "field1", "field2")
        
        Returns:
            Payload-Dictionary für die API
        """
        # Erstelle den User-Prompt mit den zwei Beschreibungen und Sprachen
        lang1 = self.languages.get('field1', 'unknown')
        lang2 = self.languages.get('field2', 'unknown')
        
        user_prompt = f"""Beschreibung ({lang1}): {descriptions.get('field1', '')}

Beschreibung ({lang2}): {descriptions.get('field2', '')}"""
        
        # Payload-Struktur für OpenWebUI / OpenAI-kompatible APIs
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.1,  # Niedrige Temperatur für konsistentere Outputs
            "max_tokens": 2000
        }
        
        return payload
    
    def _extract_model_output(self, response_data: dict[str, Any]) -> str:
        """
        Extrahiert den eigentlichen Modell-Output aus der API-Antwort.
        
        Args:
            response_data: Parsed JSON-Antwort der API
            
        Returns:
            Modell-Output als String
            
        Raises:
            ValueError: Wenn das erwartete Format nicht gefunden wird
        """
        try:
            # Standard OpenAI-kompatibles Format
            if "choices" in response_data and len(response_data["choices"]) > 0:
                choice = response_data["choices"][0]
                if "message" in choice:
                    return choice["message"].get("content", "")
                elif "text" in choice:
                    return choice["text"]
            
            # Alternatives Format
            if "response" in response_data:
                return response_data["response"]
            
            raise ValueError("Unbekanntes API-Antwortformat")
            
        except (KeyError, IndexError) as e:
            raise ValueError(f"Fehler beim Extrahieren des Modell-Outputs: {e}")
    
    def _clean_json_output(self, output: str) -> str:
        """
        Bereinigt den Modell-Output, indem Markdown-Code-Blöcke entfernt werden.
        
        Args:
            output: Roher Modell-Output
            
        Returns:
            Bereinigter JSON-String
        """
        # Entferne Markdown-Code-Blöcke (```json ... ``` oder ``` ... ```)
        output = output.strip()
        
        # Prüfe auf ```json am Anfang
        if output.startswith("```json"):
            output = output[7:]  # Entferne ```json
        elif output.startswith("```"):
            output = output[3:]  # Entferne ```
        
        # Prüfe auf ``` am Ende
        if output.endswith("```"):
            output = output[:-3]  # Entferne ```
        
        return output.strip()
    
    def validate_json(self, data: dict[str, Any], required_keys: list[str] | None = None) -> None:
        """
        Validiert das JSON-Output gegen erwartete Schlüssel.
        
        Args:
            data: Zu validierendes Dictionary
            required_keys: Liste der erforderlichen Top-Level-Keys
            
        Raises:
            ValueError: Wenn erforderliche Keys fehlen
        """
        if not required_keys:
            return
        
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            raise ValueError(
                f"Fehlende erforderliche Schlüssel im JSON-Output: {', '.join(missing_keys)}"
            )
        
        logger.debug(f"JSON-Validierung erfolgreich: Alle erforderlichen Keys vorhanden")
    
    def call_model(
        self,
        descriptions: dict[str, Any],
        required_keys: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Ruft das Modell auf und gibt den validierten JSON-Output zurück.
        
        Args:
            descriptions: Dictionary mit id und Beschreibungen
            required_keys: Liste der erforderlichen Keys zur Validierung
            
        Returns:
            Parsed und validiertes JSON als Dictionary
            
        Raises:
            RequestException: Nach Ausschöpfen aller Wiederholungsversuche
            ValueError: Bei nicht-parsbarem oder ungültigem JSON
        """
        record_id = descriptions.get("id", "unknown")
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"API-Aufruf für ID {record_id}, Versuch {attempt}/{self.max_retries}")
                
                # Payload erstellen
                payload = self.build_payload(descriptions)
                
                # Headers vorbereiten
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                # API-Aufruf
                response = requests.post(
                    self.full_url,
                    json=payload,
                    timeout=self.timeout_seconds,
                    headers=headers
                )
                
                # Status-Code prüfen
                response.raise_for_status()
                
                # Response parsen
                response_data = response.json()
                
                # Modell-Output extrahieren
                model_output = self._extract_model_output(response_data)
                
                # Bereinige Modell-Output (entferne Markdown-Code-Blöcke)
                cleaned_output = self._clean_json_output(model_output)
                
                # JSON parsen
                try:
                    result_json = json.loads(cleaned_output.strip())
                except json.JSONDecodeError as e:
                    raise ValueError(f"Modell-Output ist kein gültiges JSON: {e}\nOutput: {cleaned_output[:200]}")
                
                # JSON validieren
                self.validate_json(result_json, required_keys)
                
                logger.info(f"Erfolgreicher API-Aufruf für ID {record_id}")
                return result_json
                
            except (RequestException, Timeout) as e:
                logger.warning(f"Netzwerkfehler bei ID {record_id}, Versuch {attempt}: {e}")
                if attempt < self.max_retries:
                    logger.info(f"Warte {self.retry_delay_seconds} Sekunden vor erneutem Versuch...")
                    time.sleep(self.retry_delay_seconds)
                else:
                    logger.error(f"Maximale Anzahl Wiederholungen erreicht für ID {record_id}")
                    raise
                    
            except ValueError as e:
                logger.warning(f"Validierungsfehler bei ID {record_id}, Versuch {attempt}: {e}")
                if attempt < self.max_retries:
                    logger.info(f"Warte {self.retry_delay_seconds} Sekunden vor erneutem Versuch...")
                    time.sleep(self.retry_delay_seconds)
                else:
                    logger.error(f"Maximale Anzahl Wiederholungen erreicht für ID {record_id}")
                    raise
            
            except Exception as e:
                logger.error(f"Unerwarteter Fehler bei ID {record_id}: {e}")
                raise
        
        # Sollte nie erreicht werden, da die Schleife entweder return oder raise ausführt
        raise RuntimeError(f"Unerwarteter Zustand nach Retry-Schleife für ID {record_id}")
