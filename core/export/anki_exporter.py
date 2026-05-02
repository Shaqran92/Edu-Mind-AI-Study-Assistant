# core/export/anki_exporter.py
"""
Anki deck exporter for flashcards.
Exports to Anki-compatible format (.apkg or text import format).
"""

import json
import sqlite3
import zipfile
import tempfile
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from utils.logger import get_logger

logger = get_logger("anki_exporter")


@dataclass
class AnkiCard:
    """Represents a card for Anki export."""
    front: str
    back: str
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class AnkiExporter:
    """
    Export flashcards to Anki-compatible formats.
    
    Supports:
    - Text file import format (tab-separated)
    - Basic .apkg format
    
    Example:
        >>> exporter = AnkiExporter("Biology Notes")
        >>> exporter.add_card("What is mitosis?", "Cell division process")
        >>> exporter.export_to_text("biology.txt")
    """
    
    def __init__(self, deck_name: str = "EduMind Export"):
        self.deck_name = deck_name
        self.cards: List[AnkiCard] = []
        self._model_id = int(time.time() * 1000)
        self._deck_id = self._model_id + 1
        logger.info(f"AnkiExporter initialized for deck: {deck_name}")
    
    def add_card(self, front: str, back: str, tags: Optional[List[str]] = None):
        """Add a card to the export."""
        self.cards.append(AnkiCard(front=front, back=back, tags=tags or []))
    
    def add_cards_from_list(self, flashcards: List[Dict[str, str]]):
        """
        Add cards from a list of flashcard dictionaries.
        
        Args:
            flashcards: List of dicts with 'q'/'a' or 'question'/'answer' keys
        """
        for card in flashcards:
            front = card.get('q') or card.get('question', '')
            back = card.get('a') or card.get('answer', '')
            tags = card.get('tags', [])
            
            if front and back:
                self.add_card(front, back, tags)
        
        logger.info(f"Added {len(flashcards)} cards")
    
    def export_to_text(self, filepath: str, include_tags: bool = True) -> str:
        """
        Export cards to tab-separated text file for Anki import.
        
        This is the simplest and most reliable import method.
        Format: front<tab>back<tab>tags
        
        Args:
            filepath: Output file path
            include_tags: Whether to include tags column
        
        Returns:
            Path to the created file
        """
        path = Path(filepath)
        
        with open(path, 'w', encoding='utf-8') as f:
            # Write header comment
            f.write(f"# EduMind Export - {self.deck_name}\n")
            f.write(f"# Cards: {len(self.cards)}\n")
            f.write("# Format: Front\\tBack\\tTags\n")
            f.write("#separator:tab\n")
            f.write("#html:true\n")
            f.write(f"#deck:{self.deck_name}\n")
            f.write("#notetype:Basic\n\n")
            
            for card in self.cards:
                # Escape special characters
                front = self._escape_html(card.front)
                back = self._escape_html(card.back)
                
                if include_tags and card.tags:
                    tags = " ".join(card.tags)
                    f.write(f"{front}\t{back}\t{tags}\n")
                else:
                    f.write(f"{front}\t{back}\n")
        
        logger.info(f"Exported {len(self.cards)} cards to {path}")
        return str(path)
    
    def export_to_csv(self, filepath: str) -> str:
        """
        Export cards to CSV format.
        
        Args:
            filepath: Output file path
        
        Returns:
            Path to the created file
        """
        import csv
        
        path = Path(filepath)
        
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Front', 'Back', 'Tags'])
            
            for card in self.cards:
                writer.writerow([
                    card.front,
                    card.back,
                    ' '.join(card.tags)
                ])
        
        logger.info(f"Exported {len(self.cards)} cards to CSV: {path}")
        return str(path)
    
    def export_to_apkg(self, filepath: str) -> str:
        """
        Export cards to Anki package format (.apkg).
        
        This creates a complete Anki deck that can be imported directly.
        
        Args:
            filepath: Output file path (should end in .apkg)
        
        Returns:
            Path to the created file
        """
        path = Path(filepath)
        if not path.suffix == '.apkg':
            path = path.with_suffix('.apkg')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create the SQLite database
            db_path = Path(tmpdir) / "collection.anki2"
            self._create_anki_db(db_path)
            
            # Create the media file (empty for now)
            media_path = Path(tmpdir) / "media"
            with open(media_path, 'w') as f:
                f.write("{}")
            
            # Create the zip archive
            with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(db_path, "collection.anki2")
                zf.write(media_path, "media")
        
        logger.info(f"Exported {len(self.cards)} cards to APKG: {path}")
        return str(path)
    
    def _create_anki_db(self, db_path: Path):
        """Create the Anki SQLite database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.executescript('''
            CREATE TABLE col (
                id INTEGER PRIMARY KEY,
                crt INTEGER NOT NULL,
                mod INTEGER NOT NULL,
                scm INTEGER NOT NULL,
                ver INTEGER NOT NULL,
                dty INTEGER NOT NULL,
                usn INTEGER NOT NULL,
                ls INTEGER NOT NULL,
                conf TEXT NOT NULL,
                models TEXT NOT NULL,
                decks TEXT NOT NULL,
                dconf TEXT NOT NULL,
                tags TEXT NOT NULL
            );
            
            CREATE TABLE notes (
                id INTEGER PRIMARY KEY,
                guid TEXT NOT NULL,
                mid INTEGER NOT NULL,
                mod INTEGER NOT NULL,
                usn INTEGER NOT NULL,
                tags TEXT NOT NULL,
                flds TEXT NOT NULL,
                sfld TEXT NOT NULL,
                csum INTEGER NOT NULL,
                flags INTEGER NOT NULL,
                data TEXT NOT NULL
            );
            
            CREATE TABLE cards (
                id INTEGER PRIMARY KEY,
                nid INTEGER NOT NULL,
                did INTEGER NOT NULL,
                ord INTEGER NOT NULL,
                mod INTEGER NOT NULL,
                usn INTEGER NOT NULL,
                type INTEGER NOT NULL,
                queue INTEGER NOT NULL,
                due INTEGER NOT NULL,
                ivl INTEGER NOT NULL,
                factor INTEGER NOT NULL,
                reps INTEGER NOT NULL,
                lapses INTEGER NOT NULL,
                left INTEGER NOT NULL,
                odue INTEGER NOT NULL,
                odid INTEGER NOT NULL,
                flags INTEGER NOT NULL,
                data TEXT NOT NULL
            );
            
            CREATE TABLE revlog (
                id INTEGER PRIMARY KEY,
                cid INTEGER NOT NULL,
                usn INTEGER NOT NULL,
                ease INTEGER NOT NULL,
                ivl INTEGER NOT NULL,
                lastIvl INTEGER NOT NULL,
                factor INTEGER NOT NULL,
                time INTEGER NOT NULL,
                type INTEGER NOT NULL
            );
            
            CREATE TABLE graves (
                usn INTEGER NOT NULL,
                oid INTEGER NOT NULL,
                type INTEGER NOT NULL
            );
        ''')
        
        now = int(time.time())
        
        # Model (note type) definition
        model = {
            str(self._model_id): {
                "id": self._model_id,
                "name": "EduMind Basic",
                "type": 0,
                "mod": now,
                "usn": -1,
                "sortf": 0,
                "did": self._deck_id,
                "tmpls": [{
                    "name": "Card 1",
                    "ord": 0,
                    "qfmt": "{{Front}}",
                    "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
                    "did": None
                }],
                "flds": [
                    {"name": "Front", "ord": 0, "sticky": False, "rtl": False, "font": "Arial", "size": 20},
                    {"name": "Back", "ord": 1, "sticky": False, "rtl": False, "font": "Arial", "size": 20}
                ],
                "css": ".card { font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white; }"
            }
        }
        
        # Deck definition
        deck = {
            str(self._deck_id): {
                "id": self._deck_id,
                "name": self.deck_name,
                "mod": now,
                "usn": -1,
                "lrnToday": [0, 0],
                "revToday": [0, 0],
                "newToday": [0, 0],
                "timeToday": [0, 0],
                "collapsed": False,
                "desc": f"Exported from EduMind on {time.strftime('%Y-%m-%d')}"
            }
        }
        
        # Insert collection metadata
        cursor.execute('''
            INSERT INTO col VALUES (1, ?, ?, ?, 11, 0, -1, 0, '{}', ?, ?, '{}', '{}')
        ''', (now, now, now * 1000, json.dumps(model), json.dumps(deck)))
        
        # Insert notes and cards
        for i, card in enumerate(self.cards):
            note_id = now * 1000 + i
            card_id = note_id + 1
            
            guid = hashlib.md5(f"{card.front}{card.back}{i}".encode()).hexdigest()[:10]
            fields = f"{card.front}\x1f{card.back}"
            csum = int(hashlib.sha1(card.front.encode()).hexdigest()[:8], 16)
            tags = " ".join(card.tags) if card.tags else ""
            
            # Insert note
            cursor.execute('''
                INSERT INTO notes VALUES (?, ?, ?, ?, -1, ?, ?, ?, ?, 0, '')
            ''', (note_id, guid, self._model_id, now, tags, fields, card.front[:20], csum))
            
            # Insert card
            cursor.execute('''
                INSERT INTO cards VALUES (?, ?, ?, 0, ?, -1, 0, 0, ?, 0, 0, 0, 0, 0, 0, 0, 0, '')
            ''', (card_id, note_id, self._deck_id, now, i))
        
        conn.commit()
        conn.close()
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('\n', '<br>')
        return text
    
    def get_stats(self) -> Dict[str, Any]:
        """Get export statistics."""
        return {
            "deck_name": self.deck_name,
            "total_cards": len(self.cards),
            "unique_tags": len(set(tag for card in self.cards for tag in card.tags))
        }
