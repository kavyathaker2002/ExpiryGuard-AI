import socket
import io
import qrcode
import ipaddress
import os
from flask import Blueprint, jsonify, send_file, request

connect_bp = Blueprint('connect', __name__)

def get_lan_ip():
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(('192.0.2.1', 9))
        ip = sock.getsockname()[0]
        if not ip.startswith('127.'):
            return ip
    except Exception:
        pass
    finally:
        if sock:
            sock.close()
    try:
        candidates = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_DGRAM)
        for candidate in candidates:
            ip = candidate[4][0]
            if not ip.startswith(('127.', '169.254.')):
                return ip
    except OSError:
        pass
    return None

def get_phone_base_url():
    """Build a phone URL from an explicit public URL or a detected LAN IP."""
    from urllib.parse import urlsplit
    configured = os.environ.get('PUBLIC_APP_URL', '').strip().rstrip('/')
    if configured:
        parsed = urlsplit(configured)
        if parsed.scheme in {'http', 'https'} and parsed.hostname and not parsed.username and not parsed.password:
            return configured
        return None
    host = urlsplit(f"//{request.host}").hostname
    try:
        address = ipaddress.ip_address(host or '')
        if not address.is_loopback and not address.is_unspecified:
            return f"{request.scheme}://{request.host}"
    except ValueError:
        pass
    ip = get_lan_ip()
    if not ip:
        return None
    port = os.environ.get('PORT', request.environ.get('SERVER_PORT', '5000'))
    return f"{request.scheme}://{ip}:{port}"

@connect_bp.route('/api/phone-connect/info')
def phone_connect_info():
    url = get_phone_base_url()
    if not url:
        return jsonify({'available': False, 'url': None, 'message': 'No network-accessible LAN address was detected.'})
    from urllib.parse import urlparse
    parsed = urlparse(url)
    ip = parsed.hostname
    port = str(parsed.port or (443 if parsed.scheme == 'https' else 80))
    protocol = parsed.scheme
    return jsonify({
        "ip": ip,
        "port": port,
        "protocol": protocol,
        "url": url,
        "available": True
    })

@connect_bp.route('/api/phone-connect/qr-code')
def phone_qr_code():
    base_url = get_phone_base_url()
    if not base_url:
        return jsonify({'error': 'No network-accessible LAN address was detected.'}), 503
    mobile_url = f"{base_url}/login"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(mobile_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#9D174D", back_color="#FFF5F7")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@connect_bp.route('/download-apk')
@connect_bp.route('/download/apk')
def download_apk():
    """Serves the installable native Android APK file."""
    static_apk = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'ExpiryGuard_AI.apk')
    if os.path.exists(static_apk):
        target = static_apk
    else:
        target = os.path.join(os.path.expanduser('~'), 'Desktop', 'ExpiryGuard_AI.apk')
    if not os.path.exists(target):
        return jsonify({'error': 'APK file not found on server.'}), 404
    return send_file(
        target,
        mimetype='application/vnd.android.package-archive',
        as_attachment=True,
        download_name='ExpiryGuard_AI.apk'
    )
