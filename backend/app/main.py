from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Optional, Set
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import random
from datetime import datetime

class Character(BaseModel):
    id: int
    name: str
    hp: int
    damage: int
    speed: int
    armor: int
    imageUrl: str

app = FastAPI()

# In-memory storage with default characters
characters: List[Character] = [
    Character(
        id=1,
        name="Eldric the Wise",
        hp=250,
        damage=120,
        speed=45,
        armor=40,
        imageUrl="/src/assets/chisu.png"
    ),
    Character(
        id=2,
        name="Thora Ironshield",
        hp=400,
        damage=95,
        speed=55,
        armor=120,
        imageUrl="/src/assets/chisu.png"
    ),
    Character(
        id=3,
        name="Sylvanas Swiftshadow",
        hp=350,
        damage=140,
        speed=95,
        armor=65,
        imageUrl="/src/assets/chisu.png"
    )
]
next_id = 4

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.is_generating = False
        print("WebSocket Manager initialized")

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast_characters(self):
        if not self.active_connections:
            return
        
        print(f"Broadcasting to {len(self.active_connections)} connections")
        for connection in self.active_connections:
            try:
                await connection.send_json({"characters": [char.dict() for char in characters]})
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                pass

manager = ConnectionManager()

# Character generation functions
FANTASY_PREFIXES = ["Brave", "Swift", "Mighty", "Wise", "Shadow", "Storm", "Iron", "Fire", "Frost", "Thunder"]
FANTASY_SUFFIXES = ["walker", "blade", "heart", "soul", "fist", "shield", "master", "slayer", "hunter", "sage"]

def generate_character() -> Character:
    global next_id
    random_prefix = random.choice(FANTASY_PREFIXES)
    random_suffix = random.choice(FANTASY_SUFFIXES)
    
    character = Character(
        id=next_id,
        name=f"{random_prefix} {random_suffix}",
        hp=random.randint(250, 400),
        damage=random.randint(50, 150),
        speed=random.randint(30, 100),
        armor=random.randint(20, 150),
        imageUrl="/src/assets/chisu.png"
    )
    next_id += 1
    return character

async def auto_generate_characters():
    print("Starting auto-generation loop")
    while manager.is_generating:
        if len(characters) < 1000:  # Limit to prevent memory issues
            character = generate_character()
            characters.append(character)
            print(f"Generated new character: {character.name} (ID: {character.id})")
            await manager.broadcast_characters()
        await asyncio.sleep(1)  # Generate every second
    print("Auto-generation loop stopped")

# CORS configuration
origins = [
    "http://localhost:5173",
    "ws://localhost:5173",
    "http://localhost:8000",
    "ws://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("New WebSocket connection request")
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received WebSocket message: {data}")
            if "action" in data:
                if data["action"] == "start_generation":
                    print("Starting character generation")
                    manager.is_generating = True
                    asyncio.create_task(auto_generate_characters())
                elif data["action"] == "stop_generation":
                    print("Stopping character generation")
                    manager.is_generating = False
            await manager.broadcast_characters()
    except WebSocketDisconnect:
        print("WebSocket disconnected due to client disconnect")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}

@app.get("/characters", response_model=List[Character])
def get_characters():
    return characters

@app.post("/characters", response_model=Character)
def create_character(character: Character):
    global next_id
    character.id = next_id
    next_id += 1
    characters.append(character)
    return character

@app.put("/characters/{character_id}", response_model=Character)
def update_character(character_id: int, updated_character: Character):
    for i, char in enumerate(characters):
        if char.id == character_id:
            updated_character.id = character_id  # Ensure ID remains the same
            characters[i] = updated_character
            return updated_character
    raise HTTPException(status_code=404, detail="Character not found")

@app.delete("/characters/{character_id}")
def delete_character(character_id: int):
    for i, char in enumerate(characters):
        if char.id == character_id:
            characters.pop(i)
            return {"message": "Character deleted"}
    raise HTTPException(status_code=404, detail="Character not found")