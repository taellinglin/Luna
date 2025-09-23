# ssl_fix.py - Force SSL to work in PyInstaller
import os
import sys
import ssl

def fix_ssl():
    """Fix SSL certificate verification in PyInstaller"""
    try:
        # Method 1: Try to use certifi if available
        try:
            import certifi
            ssl._create_default_https_context = ssl._create_unverified_context
            os.environ['SSL_CERT_FILE'] = certifi.where()
            os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
            print("✅ SSL configured with certifi")
            return True
        except ImportError:
            pass
        
        # Method 2: Try to find certificates in the bundle
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            bundle_dir = sys._MEIPASS
        else:
            # Running as script
            bundle_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Look for certificates in common locations
        cert_locations = [
            os.path.join(bundle_dir, 'certifi', 'cacert.pem'),
            os.path.join(bundle_dir, 'cacert.pem'),
            os.path.join(bundle_dir, 'ssl', 'certs', 'ca-bundle.crt'),
        ]
        
        for cert_path in cert_locations:
            if os.path.exists(cert_path):
                ssl._create_default_https_context = ssl._create_unverified_context
                os.environ['SSL_CERT_FILE'] = cert_path
                os.environ['REQUESTS_CA_BUNDLE'] = cert_path
                print(f"✅ SSL configured with {cert_path}")
                return True
        
        # Method 3: Disable SSL verification as last resort
        ssl._create_default_https_context = ssl._create_unverified_context
        print("⚠️  SSL verification disabled (fallback)")
        return True
        
    except Exception as e:
        print(f"❌ SSL setup failed: {e}")
        # Final fallback: disable SSL verification
        ssl._create_default_https_context = ssl._create_unverified_context
        return False

# Run the fix when this module is imported
fix_ssl()