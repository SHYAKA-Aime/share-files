#!/usr/bin/env python3

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import base64
from urllib.parse import urlparse, parse_qs
import os

# Simple in-memory storage
transactions = []
next_id = 1

def load_transactions():
    """Load transactions from JSON file"""
    global transactions, next_id
    try:
        with open('data/processed/transactions.json', 'r') as f:
            transactions = json.load(f)
            next_id = max([t.get('id', 0) for t in transactions], default=0) + 1
        print(f"Loaded {len(transactions)} transactions from JSON")
    except FileNotFoundError:
        print("No transactions file found. Starting with empty list.")
        transactions = []
    except Exception as e:
        print(f"Error loading transactions: {e}")
        transactions = []

def save_transactions():
    """Save transactions to JSON file"""
    try:
        os.makedirs('data/processed', exist_ok=True)
        with open('data/processed/transactions.json', 'w') as f:
            json.dump(transactions, f, indent=2)
    except Exception as e:
        print(f"Error saving transactions: {e}")

class AuthHandler:
    """Handles Basic Authentication"""
    
    def __init__(self, valid_credentials):
        self.valid_credentials = valid_credentials
    
    def authenticate(self, auth_header):
        """Validate Basic Auth credentials"""
        if not auth_header or not auth_header.startswith('Basic '):
            return False, None
        
        try:
            encoded = auth_header.split('Basic ')[1]
            decoded = base64.b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':', 1)
            
            if username in self.valid_credentials:
                if self.valid_credentials[username] == password:
                    return True, username
            return False, None
        except Exception:
            return False, None

class TransactionAPIHandler(BaseHTTPRequestHandler):
    """REST API Handler for MoMo Transaction System"""
    
    auth = AuthHandler({
        'admin': 'password123',
        'user1': 'mypassword',
        'testuser': 'test123'
    })
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"{self.address_string()} - {format % args}")
    
    def _send_json(self, status_code, data):
        """Helper to send JSON responses"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def _send_unauthorized(self):
        """Send 401 response"""
        self.send_response(401)
        self.send_header('Content-Type', 'application/json')
        self.send_header('WWW-Authenticate', 'Basic realm="MoMo Transaction API"')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error = {
            'error': 'Unauthorized',
            'message': 'Invalid or missing credentials',
            'code': 401
        }
        self.wfile.write(json.dumps(error).encode())
    
    def _check_auth(self):
        """Check if request is authenticated"""
        auth_header = self.headers.get('Authorization')
        is_valid, username = self.auth.authenticate(auth_header)
        
        if not is_valid:
            self._send_unauthorized()
            return False, None
        return True, username
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        
        is_authenticated, username = self._check_auth()
        if not is_authenticated:
            return
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        if path == '/transactions':
            limit = query_params.get('limit', [None])[0]
            offset = query_params.get('offset', [0])[0]
            
            try:
                offset = int(offset)
                result_transactions = transactions[offset:]
                
                if limit:
                    limit = int(limit)
                    result_transactions = result_transactions[:limit]
                
                self._send_json(200, {
                    'success': True,
                    'count': len(result_transactions),
                    'total': len(transactions),
                    'transactions': result_transactions
                })
            except ValueError:
                self._send_json(400, {
                    'error': 'Bad Request',
                    'message': 'Invalid limit or offset parameter',
                    'code': 400
                })
        
        elif path.startswith('/transactions/'):
            try:
                transaction_id = int(path.split('/')[-1])
                
                for t in transactions:
                    if t.get("id") == transaction_id:
                        self._send_json(200, {
                            'success': True,
                            'transaction': t
                        })
                        return
                
                self._send_json(404, {
                    'error': 'Not Found',
                    'message': f'Transaction with ID {transaction_id} not found',
                    'code': 404
                })
            
            except ValueError:
                self._send_json(400, {
                    'error': 'Bad Request',
                    'message': 'Invalid transaction ID format',
                    'code': 400
                })
        
        else:
            self._send_json(404, {
                'error': 'Not Found',
                'message': 'Endpoint not found',
                'code': 404
            })
    
    def do_POST(self):
        """Handle POST requests to create new transaction"""
        global next_id
        
        is_authenticated, username = self._check_auth()
        if not is_authenticated:
            return
        
        if self.path == '/transactions':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self._send_json(400, {
                        'error': 'Bad Request',
                        'message': 'Empty request body',
                        'code': 400
                    })
                    return
                
                post_data = self.rfile.read(content_length)
                new_transaction = json.loads(post_data.decode())
                
                if not new_transaction.get('body'):
                    self._send_json(400, {
                        'error': 'Bad Request',
                        'message': 'Transaction body is required',
                        'code': 400
                    })
                    return
                
                new_transaction['id'] = next_id
                next_id += 1
                
                transactions.append(new_transaction)
                save_transactions()
                
                self._send_json(201, {
                    'success': True,
                    'message': 'Transaction created successfully',
                    'transaction': new_transaction
                })
            
            except json.JSONDecodeError:
                self._send_json(400, {
                    'error': 'Bad Request',
                    'message': 'Invalid JSON format',
                    'code': 400
                })
            except Exception as e:
                self._send_json(500, {
                    'error': 'Internal Server Error',
                    'message': str(e),
                    'code': 500
                })
        else:
            self._send_json(404, {
                'error': 'Not Found',
                'message': 'Endpoint not found',
                'code': 404
            })
    
    def do_PUT(self):
        """Handle PUT requests to update transaction"""
        
        is_authenticated, username = self._check_auth()
        if not is_authenticated:
            return
        
        if self.path.startswith('/transactions/'):
            try:
                transaction_id = int(self.path.split('/')[-1])
                
                for t in transactions:
                    if t.get('id') == transaction_id:
                        content_length = int(self.headers.get('Content-Length', 0))
                        if content_length == 0:
                            self._send_json(400, {
                                'error': 'Bad Request',
                                'message': 'Empty request body',
                                'code': 400
                            })
                            return
                        
                        put_data = self.rfile.read(content_length)
                        update_data = json.loads(put_data.decode())
                        
                        update_data.pop('id', None)
                        
                        t.update(update_data)
                        save_transactions()
                        
                        self._send_json(200, {
                            'success': True,
                            'message': 'Transaction updated successfully',
                            'transaction': t
                        })
                        return
                
                self._send_json(404, {
                    'error': 'Not Found',
                    'message': f'Transaction with ID {transaction_id} not found',
                    'code': 404
                })
            
            except (ValueError, json.JSONDecodeError):
                self._send_json(400, {
                    'error': 'Bad Request',
                    'message': 'Invalid request format',
                    'code': 400
                })
            except Exception as e:
                self._send_json(500, {
                    'error': 'Internal Server Error',
                    'message': str(e),
                    'code': 500
                })
        else:
            self._send_json(404, {
                'error': 'Not Found',
                'message': 'Endpoint not found',
                'code': 404
            })
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        
        is_authenticated, username = self._check_auth()
        if not is_authenticated:
            return
        
        if self.path.startswith('/transactions/'):
            try:
                transaction_id = int(self.path.split('/')[-1])
                
                for i, t in enumerate(transactions):
                    if t.get('id') == transaction_id:
                        deleted = transactions.pop(i)
                        save_transactions()
                        
                        self._send_json(200, {
                            'success': True,
                            'message': 'Transaction deleted successfully',
                            'transaction': deleted
                        })
                        return
                
                self._send_json(404, {
                    'error': 'Not Found',
                    'message': f'Transaction with ID {transaction_id} not found',
                    'code': 404
                })
            
            except ValueError:
                self._send_json(400, {
                    'error': 'Bad Request',
                    'message': 'Invalid transaction ID format',
                    'code': 400
                })
            except Exception as e:
                self._send_json(500, {
                    'error': 'Internal Server Error',
                    'message': str(e),
                    'code': 500
                })
        else:
            self._send_json(404, {
                'error': 'Not Found',
                'message': 'Endpoint not found',
                'code': 404
            })

def run_server(port=8000):
    """Start the API server"""
    load_transactions()
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, TransactionAPIHandler)
    
    print(f"\nMoMo Transaction API Server")
    print(f"Running on: http://localhost:{port}")
    print(f"Authentication: Basic Auth Required")
    print(f"Loaded: {len(transactions)} transactions")
    print(f"\nAvailable endpoints:")
    print(f"  GET    /transactions")
    print(f"  GET    /transactions/{{id}}")
    print(f"  POST   /transactions")
    print(f"  PUT    /transactions/{{id}}")
    print(f"  DELETE /transactions/{{id}}")
    print(f"\nServer running... (Press Ctrl+C to stop)\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        httpd.shutdown()

if __name__ == '__main__':
    run_server(port=8000)
