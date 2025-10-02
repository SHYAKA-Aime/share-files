from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import base64
from urllib.parse import urlparse, parse_qs
import os

# Simple in-memory storage
transactions = []
next_id = 1

# Basic authentication credentials
VALID_USERNAME = "kkteam"
VALID_PASSWORD = "password123"

def load_transactions():
    """Load transactions from JSON file"""
    global transactions, next_id
    try:
        with open('data/processed/transactions.json', 'r') as f:
            transactions = json.load(f)
            next_id = max([t['id'] for t in transactions]) + 1 if transactions else 1
        print(f"Loaded {len(transactions)} transactions")
    except FileNotFoundError:
        print("No transactions file found. Starting with empty list.")
        transactions = []

def save_transactions():
    """Save transactions to JSON file"""
    os.makedirs('data/processed', exist_ok=True)
    with open('data/processed/transactions.json', 'w') as f:
        json.dump(transactions, f, indent=2)

class APIHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests"""
        if not self.authenticate():
            return
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/transactions':
            self.list_transactions()
        elif path.startswith('/transactions/'):
            transaction_id = path.split('/')[-1]
            try:
                transaction_id = int(transaction_id)
                self.get_transaction(transaction_id)
            except ValueError:
                self.send_error_response(400, "Invalid transaction ID")
        else:
            self.send_error_response(404, "Endpoint not found")
    
    def do_POST(self):
        """Handle POST requests"""
        if not self.authenticate():
            return
        
        if self.path == '/transactions':
            self.create_transaction()
        else:
            self.send_error_response(404, "Endpoint not found")
    
    def do_PUT(self):
        """Handle PUT requests"""
        if not self.authenticate():
            return
        
        if self.path.startswith('/transactions/'):
            transaction_id = self.path.split('/')[-1]
            try:
                transaction_id = int(transaction_id)
                self.update_transaction(transaction_id)
            except ValueError:
                self.send_error_response(400, "Invalid transaction ID")
        else:
            self.send_error_response(404, "Endpoint not found")
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        if not self.authenticate():
            return
        
        if self.path.startswith('/transactions/'):
            transaction_id = self.path.split('/')[-1]
            try:
                transaction_id = int(transaction_id)
                self.delete_transaction(transaction_id)
            except ValueError:
                self.send_error_response(400, "Invalid transaction ID")
        else:
            self.send_error_response(404, "Endpoint not found")
    
    def authenticate(self):
        """Check Basic Authentication"""
        auth_header = self.headers.get('Authorization')
        
        if not auth_header:
            self.send_unauthorized()
            return False
        
        try:
            auth_type, auth_string = auth_header.split(' ', 1)
            if auth_type.lower() != 'basic':
                self.send_unauthorized()
                return False
            
            decoded = base64.b64decode(auth_string).decode('utf-8')
            username, password = decoded.split(':', 1)
            
            if username == VALID_USERNAME and password == VALID_PASSWORD:
                return True
            else:
                self.send_unauthorized()
                return False
        except Exception:
            self.send_unauthorized()
            return False
    
    def send_unauthorized(self):
        """Send 401 Unauthorized response"""
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="MoMo API"')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {'error': 'Unauthorized', 'message': 'Invalid credentials'}
        self.wfile.write(json.dumps(response).encode())
    
    def send_json_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def send_error_response(self, status_code, message):
        """Send error response"""
        response = {'error': True, 'message': message}
        self.send_json_response(status_code, response)
    
    def list_transactions(self):
        """GET /transactions - List all transactions"""
        response = {
            'status': 'success',
            'count': len(transactions),
            'data': transactions
        }
        self.send_json_response(200, response)
    
    def get_transaction(self, transaction_id):
        """GET /transactions/{id} - Get single transaction"""
        transaction = next((t for t in transactions if t['id'] == transaction_id), None)
        
        if transaction:
            response = {'status': 'success', 'data': transaction}
            self.send_json_response(200, response)
        else:
            self.send_error_response(404, f"Transaction {transaction_id} not found")
    
    def create_transaction(self):
        """POST /transactions - Create new transaction"""
        global next_id
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            new_transaction = json.loads(post_data.decode('utf-8'))
            
            new_transaction['id'] = next_id
            next_id += 1
            
            transactions.append(new_transaction)
            save_transactions()
            
            response = {
                'status': 'success',
                'message': 'Transaction created successfully',
                'data': new_transaction
            }
            self.send_json_response(201, response)
        except json.JSONDecodeError:
            self.send_error_response(400, "Invalid JSON")
        except Exception as e:
            self.send_error_response(500, str(e))
    
    def update_transaction(self, transaction_id):
        """PUT /transactions/{id} - Update transaction"""
        transaction = next((t for t in transactions if t['id'] == transaction_id), None)
        
        if not transaction:
            self.send_error_response(404, f"Transaction {transaction_id} not found")
            return
        
        try:
            content_length = int(self.headers['Content-Length'])
            put_data = self.rfile.read(content_length)
            update_data = json.loads(put_data.decode('utf-8'))
            
            # Update fields but keep the id
            for key, value in update_data.items():
                if key != 'id':
                    transaction[key] = value
            
            save_transactions()
            
            response = {
                'status': 'success',
                'message': 'Transaction updated successfully',
                'data': transaction
            }
            self.send_json_response(200, response)
        except json.JSONDecodeError:
            self.send_error_response(400, "Invalid JSON")
        except Exception as e:
            self.send_error_response(500, str(e))
    
    def delete_transaction(self, transaction_id):
        """DELETE /transactions/{id} - Delete transaction"""
        global transactions
        
        transaction = next((t for t in transactions if t['id'] == transaction_id), None)
        
        if transaction:
            transactions = [t for t in transactions if t['id'] != transaction_id]
            save_transactions()
            
            response = {
                'status': 'success',
                'message': f'Transaction {transaction_id} deleted successfully'
            }
            self.send_json_response(200, response)
        else:
            self.send_error_response(404, f"Transaction {transaction_id} not found")
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"{self.address_string()} - {format % args}")

def run_server(port=8000):
    """Start the API server"""
    load_transactions()
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, APIHandler)
    
    print(f"\nMoMo SMS Transaction API Server")
    print(f"Running on http://localhost:{port}")
    print(f"Authentication: Basic Auth (username: {VALID_USERNAME}, password: {VALID_PASSWORD})")
    print(f"\nAvailable endpoints:")
    print(f"  GET    /transactions")
    print(f"  GET    /transactions/{{id}}")
    print(f"  POST   /transactions")
    print(f"  PUT    /transactions/{{id}}")
    print(f"  DELETE /transactions/{{id}}")
    print(f"\nPress Ctrl+C to stop the server\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    run_server()
