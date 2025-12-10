import json
import struct
import time
from typing import Dict, Any, List, Optional

# --- Konstansok és Konfiguráció ---
# 4 bájtos kis-endian ('<I') egész szám a csomag hosszának tárolására.
HEADER_FORMAT = '<I' 
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
ENCODING = 'utf-8'

# Üzenettípusok (Client -> Server)
MSG_TYPE_CLIENT_MOVE = "MOVE"  # Játékos mozgási szándékot küld

# Üzenettípusok (Server -> Client)
MSG_TYPE_SERVER_STATE = "STATE"  # Teljes játéktér állapotának broadcastolása
MSG_TYPE_SERVER_ERROR = "ERROR"  # Hiba, pl. rate limit
MSG_TYPE_SERVER_ACK = "ACK"    # Általános nyugtázás

# --- Adatmodellek ---

class PlayerState:
    """Egy játékos pillanatnyi állapotát tároló adatosztály."""
    def __init__(self, player_id: str):
        self.id: str = player_id
        self.x: float = 0.0
        self.y: float = 0.0
        self.vx: float = 0.0 # Velocity (sebesség) x
        self.vy: float = 0.0 # Velocity (sebesség) y
        self.last_update_time: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Konvertálás szótárrá hálózati küldéshez."""
        return {
            "id": self.id,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "vx": round(self.vx, 2),
            "vy": round(self.vy, 2)
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'PlayerState':
        """Szótárból való visszaállítás."""
        state = PlayerState(data['id'])
        state.x = data.get('x', 0.0)
        state.y = data.get('y', 0.0)
        state.vx = data.get('vx', 0.0)
        state.vy = data.get('vy', 0.0)
        return state

# --- Protokollréteg funkciói ---

def encode_message(msg_type: str, data: Optional[Dict[str, Any]] = None) -> bytes:
    """
    Üzenet kódolása bájtokká a hálózaton való küldéshez.
    Formátum: [4-byte hossz] [JSON tartalom]
    """
    if data is None:
        data = {}
        
    message = {
        "type": msg_type,
        "payload": data
    }
    
    # 1. JSON szerializálás
    json_data = json.dumps(message)
    message_bytes = json_data.encode(ENCODING)
    
    # 2. Hossz előtag (header) hozzáadása
    # struct.pack: C-struktúrák szerint csomagolja be az adatot
    header = struct.pack(HEADER_FORMAT, len(message_bytes))
    
    return header + message_bytes

def decode_message(data: bytes) -> Optional[Dict[str, Any]]:
    """
    Bájtok dekódolása üzenetté.
    """
    try:
        json_data = data.decode(ENCODING)
        message = json.loads(json_data)
        
        # Validálás
        if 'type' not in message or 'payload' not in message:
            raise ValueError("Invalid message format: missing 'type' or 'payload'")
            
        return message
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:
        print(f"ERROR: Failed to decode message: {e}")
        return None

# Az ismétlődő kód itt a struct.pack/unpack és a JSON.
# Ezeket a funkciókat (encode_message, decode_message) hoztuk létre a tisztaság érdekében.