"""
ExpiryGuard AI — Startup Script
Runs the Flask application and displays accessible network URLs for phone and desktop testing.
Supports both standard HTTP and HTTPS (for phone WebRTC live camera streams).
"""
import sys
import os
from app import app
from routes.connect_routes import get_lan_ip

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

if __name__ == '__main__':
    use_ssl = '--ssl' in sys.argv
    local_ip = get_lan_ip()
    protocol = "https" if use_ssl else "http"

    print("=" * 70)
    print(" 🛡️  EXPIRYGUARD AI — SERVER STARTED SUCCESSFULLY!  🛡️")
    print("=" * 70)
    print(f" ▶ Desktop Access:      {protocol}://localhost:5000")
    print(f" ▶ Mobile Phone Access: {protocol}://{local_ip}:5000" if local_ip else " ▶ Mobile Phone Access: No LAN address detected; QR access is unavailable")
    print("-" * 70)
    print(" 🏪 Store: Gupta Chaat & Stores")
    print(" 🔑 Login Credentials:")
    print("    Username: admin")
    print("    Password: admin 123")
    print("-" * 70)
    print(" 📱 Mobile Scanning Guide:")
    print("    • Standard Mode (HTTP): Tap 'Take Photo / Upload' to snap packaging")
    print("      directly with your phone's native high-resolution camera!")
    print("    • Live camera video on phones requires trusted HTTPS or localhost.")
    print("      --ssl creates a temporary self-signed certificate and may not be trusted by phones.")
    print("=" * 70)

    if use_ssl:
        cert = os.environ.get('SSL_CERT_FILE')
        key = os.environ.get('SSL_KEY_FILE')
        ssl_context = (cert, key) if cert and key else 'adhoc'
        app.run(host='0.0.0.0', port=5000, debug=False, ssl_context=ssl_context)
    else:
        app.run(host='0.0.0.0', port=5000, debug=False)
