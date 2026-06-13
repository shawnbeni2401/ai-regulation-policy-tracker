import http.server
import json
import os
import sys
from urllib.parse import urlparse

# Add tools directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

from db_handler import get_all_policies
from trigger_notification import update_status_manually
from scraper import run_scraper
from chat_engine import answer_question

class handler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for deployment
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
            self.send_error_response(404, "Endpoint not found")

    def do_POST(self):
        parsed_path = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""
        
        if parsed_path.path == "/api/policies/scrape":
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
                
        elif parsed_path.path == "/api/policies/update-status":
            try:
                params = json.loads(post_data)
                policy_id = params.get("policy_id")
                new_status = params.get("status")
                
                if not policy_id or not new_status:
                    self.send_error_response(400, "Missing 'policy_id' or 'status'")
                    return
                
                success = update_status_manually(policy_id, new_status)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": success}).encode('utf-8'))
            except Exception as e:
                self.send_error_response(500, f"Status update error: {str(e)}")
                
        elif parsed_path.path == "/api/chat":
            try:
                params = json.loads(post_data)
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
