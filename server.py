import http.server
import socketserver
import json
import os
import sys
from urllib.parse import urlparse, parse_qs

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
from db_handler import get_all_policies
from trigger_notification import update_status_manually
from scraper import run_scraper
from chat_engine import answer_question

PORT = 8080
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")

class PolicyTrackerAPIHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "OK")
        self.end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == "/api/policies":
            try:
                policies = get_all_policies()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(policies).encode('utf-8'))
            except Exception as e:
                self.send_error_response(500, f"Database error: {str(e)}")
        else:
            # Serve static files from the dist/ folder
            # If path doesn't exist or is a route (like React Router), serve index.html
            local_path = os.path.join(PUBLIC_DIR, parsed_path.path.lstrip("/"))
            
            # If it's a directory or doesn't have an extension, default to index.html (React routing SPA)
            if not os.path.exists(local_path) or os.path.isdir(local_path):
                local_path = os.path.join(PUBLIC_DIR, "index.html")
            
            # Check if index.html exists, if not serve a simple fallback message
            if not os.path.exists(local_path):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>AI Regulation Tracker Server Running</h1><p>Please build the frontend using 'npm run build' or access '/api/policies' for JSON data.</p>")
                return
                
            # Content type mapping
            content_type = "text/html"
            if local_path.endswith(".js"):
                content_type = "application/javascript"
            elif local_path.endswith(".css"):
                content_type = "text/css"
            elif local_path.endswith(".png"):
                content_type = "image/png"
            elif local_path.endswith(".jpg") or local_path.endswith(".jpeg"):
                content_type = "image/jpeg"
            elif local_path.endswith(".svg"):
                content_type = "image/svg+xml"
            elif local_path.endswith(".json"):
                content_type = "application/json"
                
            try:
                with open(local_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error_response(500, f"Static serve error: {str(e)}")

    def do_POST(self):
        parsed_path = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""

        if parsed_path.path == "/api/policies/update-status":
            try:
                params = json.loads(body_data)
                policy_id = params.get("policy_id")
                new_status = params.get("status")
                
                if not policy_id or not new_status:
                    self.send_error_response(400, "Missing 'policy_id' or 'status' parameters")
                    return
                
                success = update_status_manually(policy_id, new_status)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": success}).encode('utf-8'))
            except Exception as e:
                self.send_error_response(500, f"Error processing update: {str(e)}")
                
        elif parsed_path.path == "/api/policies/scrape":
            try:
                updates = run_scraper()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                
                response_payload = {
                    "success": True,
                    "updated_count": len(updates),
                    "updates": [
                        {
                            "policy_id": u[0]["policy_id"],
                            "policy_name": u[0]["policy_name"],
                            "old_status": u[1],
                            "new_status": u[2]
                        } for u in updates
                    ]
                }
                self.wfile.write(json.dumps(response_payload).encode('utf-8'))
            except Exception as e:
                self.send_error_response(500, f"Scrape error: {str(e)}")
        elif parsed_path.path == "/api/chat":
            try:
                params = json.loads(body_data)
                user_message = params.get("message", "")
                
                response_message = answer_question(user_message)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"response": response_message}).encode('utf-8'))
            except Exception as e:
                self.send_error_response(500, f"Chat error: {str(e)}")
        else:
            self.send_error_response(404, "Endpoint not found")

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))

import threading
import time

def background_scraper_loop():
    print("[Background Scraper] Periodic updater thread active.")
    # Run a scrape 5 seconds after startup to ensure fresh data
    time.sleep(5)
    while True:
        print("[Background Scraper] Beginning scheduled policy updates...")
        try:
            from scraper import run_scraper
            run_scraper()
            print("[Background Scraper] Scheduled update successfully completed.")
        except Exception as e:
            print(f"[Background Scraper] Scheduled policy update failed: {e}")
        # Run every 30 minutes (1800 seconds)
        time.sleep(1800)

def run_server():
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    
    # Start periodic background updates
    scraper_thread = threading.Thread(target=background_scraper_loop, daemon=True)
    scraper_thread.start()
    
    handler = PolicyTrackerAPIHandler
    
    # Allow address reuse to prevent "address already in use" errors during quick restarts
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Server started on port {PORT}")
        print(f"API endpoints available at: http://localhost:{PORT}/api/policies")
        print(f"Static web files served from: {PUBLIC_DIR}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    run_server()
