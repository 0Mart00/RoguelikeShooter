import asyncio
import time
import logging
import uuid
import struct # <-- Ez az import kell a struct.unpack-hez!
from typing import Dict, Optional, Tuple, Any

# Import a protokoll modulból: Ezt a sort érdemes ellenőrizni!
from protocol import (
    PlayerState, 
    encode_message, 
    decode_message, 
    HEADER_SIZE, 
    HEADER_FORMAT, # <-- Ennek itt kell lennie!
    MSG_TYPE_CLIENT_MOVE, 
    MSG_TYPE_SERVER_STATE, 
    MSG_TYPE_SERVER_ERROR
)

# --- Konfiguráció ---
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8888
TICK_RATE = 60  # Hz
TICK_INTERVAL = 1.0 / TICK_RATE  # Secundumonkénti frissítés

# Rate Limiting
MAX_MESSAGES_PER_SECOND = 10 
TOKEN_REFILL_RATE = MAX_MESSAGES_PER_SECOND
MAX_TOKENS = 3 * MAX_MESSAGES_PER_SECOND # Burst limit

# --- Logolás beállítása ---
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s | SERVER | %(levelname)s | %(message)s',
                    datefmt='%H:%M:%S')

class RateLimiter:
    """Egyszerű Token Bucket implementáció."""
    def __init__(self, max_tokens: float, refill_rate: float):
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens = max_tokens
        self.last_refill = time.time()

    def consume(self, amount: float = 1.0) -> bool:
        """Megpróbál token-t fogyasztani. True, ha sikeres."""
        now = time.time()
        time_passed = now - self.last_refill
        
        # Tokenek újratöltése
        self.tokens = min(self.max_tokens, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False

class PlayerConnection:
    """Egyetlen klienskapcsolatot és annak állapotát kezelő osztály."""
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, server: 'GameServer'):
        self.reader = reader
        self.writer = writer
        self.server = server
        self.player_id: str = str(uuid.uuid4())
        self.addr: Tuple[str, int] = writer.get_extra_info('peername')
        self.limiter = RateLimiter(MAX_TOKENS, TOKEN_REFILL_RATE)
        self.state: PlayerState = PlayerState(self.player_id)
        
        logging.info(f"New connection established: ID={self.player_id} from {self.addr[0]}")

    async def handle_read(self):
        """Bejövő üzenetek folyamatos olvasása a klienstől."""
        try:
            # Hozzáadjuk az állapotot a szerver központi állapotkezelőjéhez
            self.server.players[self.player_id] = self.state

            while True:
                # 1. Hossz (header) olvasása
                header_data = await self.reader.readexactly(HEADER_SIZE)
                
                # struct.unpack: ITT VAN FELHASZNÁLVA A HEADER_FORMAT
                msg_len, = struct.unpack(HEADER_FORMAT, header_data)

                # 2. Üzenet olvasása a jelzett hossznak megfelelően
                message_data = await self.reader.readexactly(msg_len)
                
                # 3. Rate Limiting ellenőrzése
                if not self.limiter.consume():
                    await self.send_error("Rate limit exceeded. Too many messages.")
                    logging.warning(f"Rate limit hit for ID={self.player_id} ({self.addr[0]}).")
                    continue
                    
                # 4. Üzenet feldolgozása
                message = decode_message(message_data)
                if message:
                    await self.server.process_message(self.player_id, message)

        except asyncio.IncompleteReadError:
            logging.info(f"Client disconnected gracefully: ID={self.player_id}")
        except ConnectionResetError:
            logging.info(f"Client disconnected abruptly: ID={self.player_id}")
        except Exception as e:
            logging.error(f"Error in PlayerConnection {self.player_id}: {e}")
        finally:
            self.server.remove_player(self.player_id)

    async def send_message(self, msg_type: str, data: Optional[Dict[str, Any]] = None):
        """Üzenet kódolása és küldése a kliensnek."""
        try:
            encoded_msg = encode_message(msg_type, data)
            self.writer.write(encoded_msg)
            await self.writer.drain()
        except ConnectionResetError:
            pass
        except Exception as e:
            logging.error(f"Error sending message to {self.player_id}: {e}")
            self.server.remove_player(self.player_id)

    async def send_error(self, message: str):
        """Hibajelzés küldése a kliensnek."""
        await self.send_message(MSG_TYPE_SERVER_ERROR, {"reason": message})


class GameServer:
    """A fő játékszerver, amely a loop-ot és a központi állapotot kezeli."""
    def __init__(self):
        self.players: Dict[str, PlayerState] = {}
        self.connections: Dict[str, PlayerConnection] = {}
        self.is_running = False
        self.last_tick_time = time.time()
        self.server_start_time = time.time()

    async def start(self):
        """A szerver indítása és a fő feladatok ütemezése."""
        self.is_running = True
        
        server = await asyncio.start_server(
            self.handle_client, SERVER_HOST, SERVER_PORT
        )
        
        asyncio.create_task(self.game_loop())
        
        addr = server.sockets[0].getsockname()
        logging.info(f"GameServer running on {addr}")
        
        async with server:
            await server.serve_forever()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Callback új klienskapcsolat esetén."""
        connection = PlayerConnection(reader, writer, self)
        self.connections[connection.player_id] = connection
        asyncio.create_task(connection.handle_read())

    def remove_player(self, player_id: str):
        """Játékos eltávolítása a központi állapotból és a kapcsolatok közül."""
        if player_id in self.connections:
            self.connections[player_id].writer.close()
            del self.connections[player_id]
        if player_id in self.players:
            del self.players[player_id]
        logging.info(f"Player removed: ID={player_id}. Current active players: {len(self.players)}")

    async def process_message(self, player_id: str, message: Dict[str, Any]):
        """Bejövő üzenetek feldolgozása a kliensektől."""
        msg_type = message.get("type")
        payload = message.get("payload", {})
        
        player_state = self.players.get(player_id)
        if not player_state:
            return
            
        if msg_type == MSG_TYPE_CLIENT_MOVE:
            speed = 10.0 
            direction = payload.get("direction", "none") 
            
            player_state.vx = 0.0
            player_state.vy = 0.0
            
            if direction == "up":
                player_state.vy = -speed
            elif direction == "down":
                player_state.vy = speed
            elif direction == "left":
                player_state.vx = -speed
            elif direction == "right":
                player_state.vx = speed
            
            player_state.last_update_time = time.time()
            logging.debug(f"Player {player_id[:4]} moved: ({player_state.vx}, {player_state.vy})")

    def update_game_state(self, delta_time: float):
        """A fő játéklogika, amely minden tick-ben lefut."""
        for player_id, state in self.players.items():
            state.x += state.vx * delta_time
            state.y += state.vy * delta_time
            
    async def broadcast_state(self):
        """Minden csatlakoztatott kliensnek elküldi a teljes játékállapotot."""
        all_states = [state.to_dict() for state in self.players.values()]
        state_message = encode_message(MSG_TYPE_SERVER_STATE, {"players": all_states})
        
        tasks = []
        for conn in self.connections.values():
            conn.writer.write(state_message) 
            tasks.append(conn.writer.drain())

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def game_loop(self):
        """A szerver fő, ismétlődő tick loop-ja (pl. 60 Hz)."""
        logging.info(f"Starting Game Loop at {TICK_RATE} Hz.")
        
        while self.is_running:
            start_time = time.time()
            delta_time = start_time - self.last_tick_time
            self.last_tick_time = start_time
            
            self.update_game_state(delta_time)
            await self.broadcast_state()

            elapsed_time = time.time() - start_time
            sleep_time = TICK_INTERVAL - elapsed_time
            
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    try:
        server = GameServer()
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logging.info("Server shutting down due to KeyboardInterrupt.")
    except Exception as e:
        logging.error(f"Unhandled server exception: {e}")