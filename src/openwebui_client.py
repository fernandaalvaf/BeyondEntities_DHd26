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


class Colors:
    """ANSI-Farbcodes für Terminal-Ausgabe."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class OpenWebUIClient:
    """Client für OpenWebUI-API-Aufrufe."""
    
    def __init__(
        self,
        base_url: str,
        endpoint: str,
        model: str,
        system_prompt: str,
        api_key: str | None = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
        retry_delay_seconds: int = 3,
        api_provider: str = "openai"
    ):
        """
        Initialisiert den OpenWebUI-Client.
        
        Args:
            base_url: Basis-URL der API (z.B. "http://localhost:11434")
            endpoint: API-Endpoint (z.B. "/api/chat/completions")
            model: Modellname
            system_prompt: System-/Instruktionsprompt
            api_key: API-Schlüssel für Authentifizierung (optional)
            timeout_seconds: Timeout für API-Aufrufe in Sekunden
            max_retries: Maximale Anzahl von Wiederholungsversuchen
            retry_delay_seconds: Wartezeit zwischen Wiederholungen
            api_provider: API-Provider ("openai", "gemini") - default: "openai"
        """
        self.base_url = base_url.rstrip('/')
        self.endpoint = endpoint
        self.model = model
        self.system_prompt = system_prompt
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.api_provider = api_provider.lower()
        self.full_url = f"{self.base_url}{self.endpoint}"
        self.api_call_counter = 0  # Zähler für API-Aufrufe
        
        # Validiere Provider
        if self.api_provider not in ["openai", "gemini"]:
            raise ValueError(f"Ungültiger API-Provider: {api_provider}. Erlaubt: openai, gemini")
    
    def build_payload(
        self,
        text_data: dict[str, Any],
        granularity: int = 3,
        entity_types: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Erstellt die Request-Payload für die API.
        
        Args:
            text_data: Dictionary mit id und sourcetext
            granularity: Abstraktionslevel (1-5)
            entity_types: Liste erlaubter Entitätstypen
        
        Returns:
            Payload-Dictionary für die API
        """
        # Erstelle den User-Prompt mit dem Text
        sourcetext = text_data.get('sourcetext', '')
        
        # Füge Granularität und Entity-Typen zum Prompt hinzu
        user_prompt = f"""Text:
{sourcetext}

Abstraktionslevel: {granularity}/5"""
        
        if entity_types:
            user_prompt += f"\nErlaubte Entitätstypen: {', '.join(entity_types)}"
        
        # Provider-spezifische Payload-Generierung
        if self.api_provider == "gemini":
            return self._build_gemini_payload(user_prompt)
        else:  # openai (default)
            return self._build_openai_payload(user_prompt)
    
    def _build_openai_payload(self, user_prompt: str) -> dict[str, Any]:
        """
        Erstellt Payload für OpenAI-kompatible APIs.
        
        Args:
            user_prompt: User-Prompt-Text
            
        Returns:
            OpenAI-kompatible Payload
        """
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
            "max_tokens": 8000
        }
        
        return payload
    
    def _build_gemini_payload(self, user_prompt: str) -> dict[str, Any]:
        """
        Erstellt Payload für Google Gemini API.
        
        Args:
            user_prompt: User-Prompt-Text
            
        Returns:
            Gemini-kompatible Payload
        """
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": user_prompt
                        }
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [
                    {
                        "text": self.system_prompt
                    }
                ]
            },
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 65536  # Gemini Maximum
            }
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
            # Gemini API Format
            if self.api_provider == "gemini":
                if "candidates" in response_data and len(response_data["candidates"]) > 0:
                    candidate = response_data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if len(parts) > 0 and "text" in parts[0]:
                            return parts[0]["text"]
            
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
        text_data: dict[str, Any],
        required_keys: list[str] | None = None,
        granularity: int = 3,
        entity_types: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Ruft das Modell auf und gibt den validierten JSON-Output zurück.
        
        Args:
            text_data: Dictionary mit id und sourcetext
            required_keys: Liste der erforderlichen Keys zur Validierung
            granularity: Abstraktionslevel (1-5)
            entity_types: Liste erlaubter Entitätstypen
            
        Returns:
            Parsed und validiertes JSON als Dictionary
            
        Raises:
            RequestException: Nach Ausschöpfen aller Wiederholungsversuche
            ValueError: Bei nicht-parsbarem oder ungültigem JSON
        """
        record_id = text_data.get("id", "unknown")
        
        for attempt in range(1, self.max_retries + 1):
            self.api_call_counter += 1
            
            # Farbige Terminal-Ausgabe für API-Aufruf
            print(f"{Colors.YELLOW}{Colors.BOLD}[API #{self.api_call_counter}]{Colors.RESET} "
                  f"{Colors.YELLOW}API-Aufruf für ID {record_id}, Versuch {attempt}/{self.max_retries}{Colors.RESET}")
            
            try:
                logger.info(f"API-Aufruf #{self.api_call_counter} für ID {record_id}, Versuch {attempt}/{self.max_retries}")
                
                # Payload erstellen
                payload = self.build_payload(text_data, granularity, entity_types)
                
                # Headers und URL vorbereiten (Provider-abhängig)
                headers = {"Content-Type": "application/json"}
                url = self.full_url
                
                if self.api_provider == "gemini":
                    # Gemini: API-Key als Query-Parameter
                    if self.api_key:
                        url = f"{self.full_url}?key={self.api_key}"
                else:
                    # OpenAI: API-Key als Authorization Header
                    if self.api_key:
                        headers["Authorization"] = f"Bearer {self.api_key}"
                
                # API-Aufruf
                response = requests.post(
                    url,
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
                
                # Erfolgreiche Antwort - Grüne Ausgabe
                print(f"{Colors.GREEN}{Colors.BOLD}[API #{self.api_call_counter}]{Colors.RESET} "
                      f"{Colors.GREEN}Erfolgreiche Antwort für ID {record_id}{Colors.RESET}")
                
                logger.info(f"Erfolgreicher API-Aufruf #{self.api_call_counter} für ID {record_id}")
                return result_json
                
            except (RequestException, Timeout) as e:
                # Rote Ausgabe für Netzwerkfehler
                print(f"{Colors.RED}{Colors.BOLD}[API #{self.api_call_counter}]{Colors.RESET} "
                      f"{Colors.RED}Netzwerkfehler bei ID {record_id}, Versuch {attempt}: {str(e)[:100]}{Colors.RESET}")
                
                logger.warning(f"Netzwerkfehler bei ID {record_id}, Versuch {attempt}: {e}")
                if attempt < self.max_retries:
                    logger.info(f"Warte {self.retry_delay_seconds} Sekunden vor erneutem Versuch...")
                    time.sleep(self.retry_delay_seconds)
                else:
                    logger.error(f"Maximale Anzahl Wiederholungen erreicht für ID {record_id}")
                    raise
                    
            except ValueError as e:
                # Rote Ausgabe für Validierungsfehler
                print(f"{Colors.RED}{Colors.BOLD}[API #{self.api_call_counter}]{Colors.RESET} "
                      f"{Colors.RED}Validierungsfehler bei ID {record_id}, Versuch {attempt}: {str(e)[:100]}{Colors.RESET}")
                
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
