import os
import uuid
from fastapi import FastAPI, WebSocket, Request, Form, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
import base64
import socketio

# Setup the FastAPI application
app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi')
app.mount('/ws', socketio.ASGIApp(sio))

# Generate a new ECIES key pair
def generate_key_pair():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key

# Serialize the public key to PEM format
def serialize_public_key(public_key):
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')

# Generate a shared secret using the private key and the peer's public key
def generate_shared_secret(private_key, peer_public_key):
    shared_key = private_key.exchange(ec.ECDH(), peer_public_key)
    return shared_key

# Step 1: The dapp generates a UUID v4 (Socket.io room ID) and ECIES key pair.
room_id = str(uuid.uuid4())
private_key, public_key = generate_key_pair()

# Save state (in-memory, can be changed to a persistent storage)
state = {
    "room_id": room_id,
    "private_key": private_key,
    "public_key": public_key
}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = f"""
    <html>
        <head>
            <title>Ethereum Mining WebApp</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>Welcome to Ethereum Mining WebApp</h1>
            <p>Room ID: {room_id}</p>
            <p>Public Key:</p>
            <pre>{serialize_public_key(public_key)}</pre>
            <button id="connectButton">Connect MetaMask Wallet</button>

            <script>
                async function connectWallet() {{
                    const deepLink = `https://metamask.app.link/wc?uri=...`; // Replace with actual deep link for MetaMask Mobile
                    window.open(deepLink, "_self");
                }}

                document.getElementById("connectButton").addEventListener("click", connectWallet);
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/connect_wallet")
async def connect_wallet(wallet_address: str = Form(...)):
    # Store the wallet address in session or database as needed
    return {"message": "Wallet connected", "wallet_address": wallet_address}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Process the data received from MetaMask Mobile
            # This would involve handling the public key exchange and establishing the encrypted communication channel
            print(f"Received data from MetaMask Mobile in room {room_id}: {data}")

            # Send response back if necessary
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        print(f"Client disconnected from room {room_id}")

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
