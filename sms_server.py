#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android SMS Server (Termux Native)
This server sends real SMS using Termux:API.
It includes logging and bulk sending features.

Run:
python sms_server.py
"""

import json
import socket
import time
import os
import sys
import subprocess
import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- SETTINGS ---
PORT = 5000 
LOG_DIR = os.path.expanduser("~/sms_logs")

# Termux API Check
def check_termux_api():
    """Check if Termux:API is installed"""
    if shutil.which("termux-sms-send"):
        print("✅ Termux API found - SMS sending active.")
        return True
    else:
        print("⚠️  WARNING: 'termux-api' package is not installed!")
        print("   Please run: pkg install termux-api")
        return False

HAS_TERMUX_API = check_termux_api()

def send_sms_native(phone_number, message):
    """Send SMS via Termux command line"""
    try:
    
        cmd = ['termux-sms-send', '-n', str(phone_number), str(message)]       
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, "SMS Delivered to Operator"
        else:
            return False, f"Termux Error: {result.stderr}"
            
    except Exception as e:
        return False, str(e)

def send_sms(phone_number, message):
    """Main Sending Function (with logging)"""
    
    if not phone_number or len(phone_number) < 3:
        return False, "Invalid phone number"
    
    if not message:
        return False, "Message is empty"
    
    # Simulation or Real Sending
    if HAS_TERMUX_API:
        success, response = send_sms_native(phone_number, message)
        status_log = "sent" if success else "failed"
    else:
        print(f"📝 [SIM] SMS: {phone_number} -> {message}")
        success = True
        response = "Simulation Mode (No API)"
        status_log = "simulated"

    # Print to console
    if success:
        print(f"✅ SMS Sent: {phone_number}")
    else:
        print(f"❌ SMS Error ({phone_number}): {response}")

    # Log to file
    log_sms(phone_number, message, status_log, response)
    
    return success, response

def log_sms(phone_number, message, status, error=""):
    """Save SMS operation to JSON file"""
    try:
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        
        log_file = os.path.join(LOG_DIR, "sms_history.json")
        
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "phone": phone_number,
            "message": message,
            "status": status,
            "response": error
        }
        
        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                logs = [] # Reset if file is corrupted
        
        logs.append(log_entry)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs[-200:], f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"⚠️  Log error: {e}")

class SMSRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler"""
    
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body)
            
            # --- SINGLE SMS ---
            if self.path == '/api/send_sms':
                phone = data.get('phone_number')
                msg = data.get('message')
                
                success, resp = send_sms(phone, msg)
                
                self._send_json(200, {
                    'success': success,
                    'phone_number': phone,
                    'response': resp
                })
            
            # --- BULK SMS ---
            elif self.path == '/api/send_bulk_sms':
                phones = data.get('phone_numbers', [])
                msg = data.get('message')
                delay = int(data.get('delay_seconds', 2))
                
                if not isinstance(phones, list): phones = [phones]
                
                results = []
                successful = 0
                
                print(f"\n📨 Bulk Sending Started: {len(phones)} numbers")
                
                for i, p in enumerate(phones):
                    success, resp = send_sms(p, msg)
                    if success: successful += 1
                    
                    results.append({'phone': p, 'success': success, 'response': resp})
                    
                    if i < len(phones) - 1:
                        time.sleep(delay)
                
                self._send_json(200, {
                    'success': True,
                    'total': len(phones),
                    'successful': successful,
                    'failed': len(phones) - successful,
                    'results': results
                })

            else:
                self.send_response(404)
                self.end_headers()
        
        except Exception as e:
            self._send_json(500, {'success': False, 'error': str(e)})
    
    def do_GET(self):
        # Status Check
        if self.path == '/api/status':
            self._send_json(200, {
                'status': 'online',
                'device': 'Termux Native',
                'api_available': HAS_TERMUX_API,
                'port': PORT
            })
            
        # Read Logs
        elif self.path == '/api/logs':
            log_file = os.path.join(LOG_DIR, "sms_history.json")
            logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            
            self._send_json(200, {'success': True, 'logs': logs})
            
        else:
            self.send_response(404)
            self.end_headers()

def get_local_ip():
    """Get IP Address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    # Start Server
    try:
        server = HTTPServer(('0.0.0.0', PORT), SMSRequestHandler)
        ip = get_local_ip()
        
        print("\n" + "="*50)
        print("🚀 TERMUX SMS SERVER (PRO MODE)")
        print("="*50)
        print(f"📡 Address : http://{ip}:{PORT}")
        print(f"📂 Logs    : {LOG_DIR}")
        print(f"📱 API     : {'✅ Active' if HAS_TERMUX_API else '❌ Missing (Simulation)'}")
        print("="*50)
        print("You can connect from your computer...\n")
        
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server closed.")
    except OSError as e:
        print(f"\n❌ Port Error: {PORT} port might be in use.")
        print("   Solution: Run 'fuser -k 8080/tcp' and try again.")
