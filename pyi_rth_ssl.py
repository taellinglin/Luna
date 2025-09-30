# pyi_rth_ssl.py - SSL runtime hook for PyInstaller
import os
import sys


# This is a minimal runtime hook that doesn't require file operations
def setup_ssl():
    """Basic SSL setup that works without file dependencies"""
    try:
        # Set basic SSL environment variables
        ssl_paths = [getattr(sys, "_MEIPASS", ""), os.path.dirname(sys.executable), "."]

        for path in ssl_paths:
            if path:
                cert_path = os.path.join(path, "certifi", "cacert.pem")
                if os.path.exists(cert_path):
                    os.environ["SSL_CERT_FILE"] = cert_path
                    os.environ["REQUESTS_CA_BUNDLE"] = cert_path
                    break
    except Exception:
        # If SSL setup fails, continue without it
        pass


# Run the setup
setup_ssl()
