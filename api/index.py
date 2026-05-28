
from http.server import BaseHTTPRequestHandler
import json
import asyncio
import os
import sys

# Ajouter le répertoire parent au chemin pour importer bot.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importez la fonction main et webhook_handler de votre bot.py
from bot import main, webhook_handler

# Initialiser l'application du bot une seule fois
main()

class VercelHandler(BaseHTTPRequestHandler):
    def _send_response(self, status_code, content_type="text/plain", body=""):
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        
        # Simuler une requête pour le webhook_handler
        class MockRequest:
            def __init__(self, data):
                self._json_data = data
                self.method = "POST"

            async def json(self):
                return self._json_data

        try:
            update_data = json.loads(post_data)
            mock_request = MockRequest(update_data)
            
            # Exécuter le webhook_handler de manière asynchrone
            asyncio.run(webhook_handler(mock_request))
            
            self._send_response(200, body="ok")
        except Exception as e:
            self._send_response(500, body=f"Error: {e}")

# Point d'entrée pour Vercel
async def handler(request):
    return await webhook_handler(request)
