"""
Datenbank-Client für den Zugriff auf Beschreibungsdaten.
"""
import logging
from typing import Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)


class DatabaseClient:
    """Client für Datenbankzugriffe."""
    
    def __init__(
        self,
        driver: str,
        host: str,
        port: int,
        user: str,
        password: str,
        name: str,
        query: str
    ):
        """
        Initialisiert den Datenbank-Client.
        
        Args:
            driver: Datenbanktyp (z.B. 'postgresql', 'mysql', 'sqlite')
            host: Datenbank-Host
            port: Datenbank-Port
            user: Benutzername
            password: Passwort
            name: Datenbankname
            query: SQL-Query zum Abrufen der Datensätze
        """
        self.driver = driver
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.name = name
        self.query = query
        self.engine: Engine | None = None
        
    def _create_connection_string(self) -> str:
        """
        Erstellt den Connection-String basierend auf den Konfigurationsparametern.
        
        Returns:
            Connection-String für SQLAlchemy
        """
        if self.driver == "sqlite":
            # Für SQLite wird nur der Datenbankname (Dateipfad) benötigt
            return f"sqlite:///{self.name}"
        else:
            # Für andere Datenbanken (PostgreSQL, MySQL, etc.)
            return f"{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    def connect(self) -> None:
        """
        Stellt eine Verbindung zur Datenbank her.
        
        Raises:
            SQLAlchemyError: Bei Verbindungsfehlern
        """
        try:
            connection_string = self._create_connection_string()
            self.engine = create_engine(connection_string)
            
            # Test-Verbindung
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                
            logger.info(f"Verbindung zur Datenbank erfolgreich: {self.driver}://{self.host}:{self.port}/{self.name}")
            
        except SQLAlchemyError as e:
            logger.error(f"Fehler beim Verbinden zur Datenbank: {e}")
            raise SQLAlchemyError(f"Datenbankverbindung fehlgeschlagen: {e}")
    
    def disconnect(self) -> None:
        """Schließt die Datenbankverbindung."""
        if self.engine:
            self.engine.dispose()
            logger.info("Datenbankverbindung geschlossen")
    
    def fetch_records(self) -> list[dict[str, Any]]:
        """
        Führt die konfigurierte Query aus und gibt die Datensätze zurück.
        
        Returns:
            Liste von Dictionaries mit den Feldern:
            - id: Datensatz-ID
            - sourcetext: Textinhalt
            
        Raises:
            SQLAlchemyError: Bei Fehlern während der Abfrage
            ValueError: Wenn keine Engine initialisiert wurde
        """
        if not self.engine:
            raise ValueError("Keine Datenbankverbindung. Bitte zuerst connect() aufrufen.")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(self.query))
                
                # Konvertiere Ergebnisse in Liste von Dictionaries
                records = []
                for row in result:
                    record = {
                        "id": row.id,
                        "sourcetext": row.sourcetext
                    }
                    records.append(record)
                
                logger.info(f"{len(records)} Datensätze aus der Datenbank abgerufen")
                return records
                
        except SQLAlchemyError as e:
            logger.error(f"Fehler beim Abrufen der Datensätze: {e}")
            raise SQLAlchemyError(f"Datenbankabfrage fehlgeschlagen: {e}")
        except AttributeError as e:
            logger.error(f"Query liefert nicht die erwarteten Felder: {e}")
            raise ValueError(
                f"Die Query muss die Felder 'id' und 'sourcetext' "
                f"zurückgeben. Fehler: {e}"
            )
    
    def __enter__(self):
        """Context Manager: Verbindung öffnen."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager: Verbindung schließen."""
        self.disconnect()
