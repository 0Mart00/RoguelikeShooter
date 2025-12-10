import asyncio
import time
import logging
import struct
import random
from typing import Dict, Any, Optional

# Import a protokoll modulból
from protocol import (
    decode_message, encode_message, HEADER_SIZE, HEADER_FORMAT,
    MSG_TYPE_CLIENT_MOVE, MSG_TYPE_SERVER_STATE, MSG_TYPE_SERVER_ERROR
)

# --- Konfiguráció ---
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8888
INPUT_SEND_RATE = 20  # Hz (Hányszor küld inputot a kliens/másodperc)
RECONNECT_DELAY = 5   # Másodperc várakozás újracsatlakozás előtt

# --- Logolás beállítása ---
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s | CLIENT | %(levelname)s | %(message)s',
                    datefmt='%H:%M:%S')

class GameClient:
    """A kliens, amely kezeli a hálózati I/O-t és a játékállapotot."""
    def __init__(self):
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.is_connected = False
        self.game_state: Dict[str, Any] = {"players": []}
        self.client_id: str = "N/A" 

    async def connect_forever(self, host: str, port: int):
        """Végtelen ciklus, amely megpróbál csatlakozni és kapcsolatot tartani."""
        while True:
            try:
                logging.info(f"Attempting to connect to {host}:{port}...")
                self.reader, self.writer = await asyncio.open_connection(host, port)
                self.is_connected = True
                logging.info(f"Connected to server!")
                
                # Futtatjuk a kommunikációs loopokat
                # A gather addig fut, amíg valamelyik loop véget nem ér (pl. hiba miatt)
                await asyncio.gather(
                    self.receive_loop(),
                    self.input_loop()
                )
            
            except ConnectionRefusedError:
                logging.error(f"Connection refused. Server might be down.")
            except Exception as e:
                logging.error(f"Connection error: {e}")
            finally:
                self.close()
                logging.info(f"Reconnecting in {RECONNECT_DELAY} seconds...")
                await asyncio.sleep(RECONNECT_DELAY)

    def close(self):
        """Kapcsolat bezárása és takarítás."""
        self.is_connected = False
        if self.writer:
            try:
                self.writer.close()
            except Exception:
                pass
            self.writer = None
        self.reader = None

    async def send_message(self, msg_type: str, data: Optional[Dict[str, Any]] = None):
        """Üzenet küldése a szervernek."""
        if not self.writer or not self.is_connected:
            return
        try:
            encoded_msg = encode_message(msg_type, data)
            self.writer.write(encoded_msg)
            await self.writer.drain()
        except Exception as e:
            # Nem logolunk minden hibát itt, a receive_loop/input_loop majd kezeli a szakadást
            pass
            
    async def receive_loop(self):
        """Folyamatosan fogadja és dekódolja a szerver üzeneteit."""
        while self.is_connected:
            try:
                if not self.reader:
                    break

                # 1. Hossz (header) olvasása
                header_data = await self.reader.readexactly(HEADER_SIZE)
                msg_len, = struct.unpack(HEADER_FORMAT, header_data)
                
                # 2. Üzenet olvasása
                message_data = await self.reader.readexactly(msg_len)
                
                # 3. Üzenet feldolgozása
                message = decode_message(message_data)
                if message:
                    self.process_server_message(message)

            except asyncio.IncompleteReadError:
                logging.warning("Server disconnected (stream ended).")
                break
            except ConnectionResetError:
                logging.warning("Server connection reset.")
                break
            except Exception as e:
                logging.error(f"Error in receive loop: {e}")
                break
        
        # Ha a loop megszakad, jelezzük a disconnectet
        self.close()


    def process_server_message(self, message: Dict[str, Any]):
        """Szerver üzenetek feldolgozása."""
        msg_type = message.get("type")
        payload = message.get("payload", {})

        if msg_type == MSG_TYPE_SERVER_STATE:
            self.game_state = payload
            if self.client_id == "N/A":
                self.client_id = next((p['id'] for p in payload.get('players', []) if 'id' in p), "N/A")
                logging.info(f"Client assigned ID: {self.client_id}")
            self.render_state()
            
        elif msg_type == MSG_TYPE_SERVER_ERROR:
            logging.error(f"Server Error: {payload.get('reason', 'Unknown error')}")

    def render_state(self):
        """A játékállapot megjelenítése (logolás)."""
        if not self.game_state or not self.game_state.get('players'):
            return
        
        # Csak ritkábban logoljunk, hogy ne floodoljuk a konzolt (opcionális)
        # Itt most minden ticknél logol, ahogy az eredetiben
        player_data = self.game_state['players']
        me = next((p for p in player_data if p['id'] == self.client_id), None)
        player_count = len(player_data)
        
        if me:
            pos_info = f"My Position: ({me['x']:.2f}, {me['y']:.2f}) | "
        else:
            pos_info = "Waiting for initial state... | "
            
        logging.info(f"[RENDER] {pos_info}Total Players: {player_count}")


    async def input_loop(self):
        """Input szimulálása és küldése."""
        directions = ["up", "down", "left", "right", "none"]
        current_direction = random.choice(directions)
        last_change_time = time.time()
        
        while self.is_connected:
            try:
                if time.time() - last_change_time > 10.0:
                    current_direction = random.choice(directions)
                    last_change_time = time.time()
                    logging.info(f"Simulated new direction: {current_direction}")

                await self.send_message(MSG_TYPE_CLIENT_MOVE, {"direction": current_direction})
                await asyncio.sleep(1.0 / INPUT_SEND_RATE)
            except Exception:
                break # Ha hiba van, lépjünk ki, a connect_forever majd újraindítja


if __name__ == "__main__":
    client = GameClient()
    try:
        # connect helyett connect_forever-t hívunk
        asyncio.run(client.connect_forever(SERVER_HOST, SERVER_PORT))
    except KeyboardInterrupt:
        logging.info("Client shutting down manually.")
    finally:
        client.close()