#!/usr/bin/env python3
"""
QR Code Scanner for iOS (Pythonista)
Uses Pythonista's camera and QR code detection
"""

try:
    import photos
    from PIL import Image
    from objc_util import ObjCClass, ObjCInstance
    import ui
    HAS_IOS_CAMERA = True
except ImportError:
    HAS_IOS_CAMERA = False

try:
    import qrcode
    from pyzbar.pyzbar import decode as qr_decode
    HAS_QR_LIB = True
except ImportError:
    HAS_QR_LIB = False

def scan_qr_with_camera():
    """Scan QR code using iOS camera"""
    if not HAS_IOS_CAMERA:
        print("❌ iOS camera not available. This script must run in Pythonista.")
        return None
    
    try:
        # Use Pythonista's camera picker
        print("📷 Opening camera...")
        print("   Point at QR code and tap to capture")
        
        # Take photo
        img = photos.capture_image()
        if img is None:
            print("❌ No image captured")
            return None
        
        # Save to temporary location
        temp_path = 'temp_qr_scan.jpg'
        img.save(temp_path)
        
        # Decode QR code
        if HAS_QR_LIB:
            qr_data = decode_qr_from_image(temp_path)
        else:
            # Alternative: Use iOS built-in QR detection
            qr_data = detect_qr_ios(img)
        
        return qr_data
        
    except Exception as e:
        print(f"❌ Error scanning QR code: {e}")
        return None

def decode_qr_from_image(image_path):
    """Decode QR code from image file"""
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode
        
        img = Image.open(image_path)
        qr_codes = decode(img)
        
        if qr_codes:
            qr_data = qr_codes[0].data.decode('utf-8')
            print(f"✅ QR Code detected: {qr_data}")
            return qr_data
        else:
            print("❌ No QR code found in image")
            return None
            
    except Exception as e:
        print(f"❌ Error decoding QR: {e}")
        return None

def detect_qr_ios(image):
    """Use iOS built-in QR detection (if available)"""
    try:
        import objc_util
        
        # Try to use Vision framework for QR detection
        # This is iOS-native and doesn't require external libraries
        VNDetectBarcodesRequest = ObjCClass('VNDetectBarcodesRequest')
        VNImageRequestHandler = ObjCClass('VNImageRequestHandler')
        
        # Convert PIL image to CIImage
        # This is a simplified version - actual implementation needs more work
        print("⚠️ Using iOS native QR detection...")
        
        # For now, return None and suggest using pyzbar
        print("💡 Install pyzbar for better QR detection:")
        print("   pip install pyzbar")
        return None
        
    except Exception as e:
        print(f"⚠️ iOS native detection not available: {e}")
        return None

def scan_qr_from_photo_library():
    """Scan QR code from photo library"""
    try:
        print("📸 Select image from photo library...")
        img = photos.pick_image()
        
        if img is None:
            print("❌ No image selected")
            return None
        
        # Save temporarily
        temp_path = 'temp_qr_scan.jpg'
        img.save(temp_path)
        
        # Decode
        return decode_qr_from_image(temp_path)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == '__main__':
    print("iOS QR Code Scanner")
    print("=" * 50)
    print()
    print("Select scanning method:")
    print("1. Camera (recommended)")
    print("2. Photo Library")
    print()
    
    choice = input("Choice [1]: ").strip() or '1'
    
    if choice == '1':
        connection_key = scan_qr_with_camera()
    elif choice == '2':
        connection_key = scan_qr_from_photo_library()
    else:
        print("❌ Invalid choice")
        connection_key = None
    
    if connection_key:
        print(f"\n✅ Connection Key: {connection_key}")
        print("\nTo use this key, run:")
        print(f"   python ios_register_device.py --connect-key {connection_key}")
    else:
        print("\n❌ No QR code detected")

