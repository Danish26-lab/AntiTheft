#!/usr/bin/env python3
"""
QR Code Scanner for Device Registration
Supports scanning QR codes from camera or image files
"""

import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import cv2
    import numpy as np
    from pyzbar import pyzbar
    HAS_QR_SCANNER = True
except ImportError:
    HAS_QR_SCANNER = False

def scan_qr_from_camera():
    """Scan QR code using webcam"""
    if not HAS_QR_SCANNER:
        print("❌ QR scanner not available. Install requirements:")
        print("   pip install opencv-python pyzbar")
        return None
    
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot access camera")
            return None
        
        print("📷 Camera opened. Point at QR code...")
        print("   Press 'Q' to quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Decode QR codes
            qr_codes = pyzbar.decode(frame)
            
            # Draw bounding box around QR codes
            for qr in qr_codes:
                points = qr.polygon
                if len(points) == 4:
                    pts = np.array(points, dtype=np.int32)
                    cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
                
                qr_data = qr.data.decode('utf-8')
                qr_type = qr.type
                
                cv2.putText(frame, f'{qr_type}: {qr_data[:30]}...', 
                           (points[0].x, points[0].y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Display frame
            cv2.imshow('QR Code Scanner - Press Q to quit', frame)
            
            # Check for QR code
            if qr_codes:
                qr_data = qr_codes[0].data.decode('utf-8')
                print(f"\n✅ QR Code detected: {qr_data}")
                cap.release()
                cv2.destroyAllWindows()
                return qr_data
            
            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        return None
        
    except Exception as e:
        print(f"❌ Error scanning QR code: {e}")
        return None

def scan_qr_from_image(image_path):
    """Scan QR code from image file"""
    if not HAS_QR_SCANNER:
        print("❌ QR scanner not available. Install requirements:")
        print("   pip install opencv-python pyzbar")
        return None
    
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Cannot read image: {image_path}")
            return None
        
        qr_codes = pyzbar.decode(image)
        if qr_codes:
            qr_data = qr_codes[0].data.decode('utf-8')
            print(f"✅ QR Code found: {qr_data}")
            return qr_data
        else:
            print("❌ No QR code found in image")
            return None
            
    except Exception as e:
        print(f"❌ Error scanning image: {e}")
        return None

def scan_qr_from_clipboard():
    """Try to scan QR code from clipboard image (Windows/Linux)"""
    # This is a placeholder - platform-specific clipboard image reading
    # would need platform-specific libraries
    print("❌ Clipboard QR scanning not yet implemented")
    print("   Please use camera scanner or save QR code as image")
    return None

if __name__ == '__main__':
    print("QR Code Scanner")
    print("=" * 50)
    print()
    
    if len(sys.argv) > 1:
        # Scan from image file
        image_path = sys.argv[1]
        connection_key = scan_qr_from_image(image_path)
    else:
        # Scan from camera
        connection_key = scan_qr_from_camera()
    
    if connection_key:
        print(f"\n✅ Connection Key: {connection_key}")
        print("\nTo use this key, run:")
        print(f"   python register_device.py --connect-key {connection_key}")
    else:
        print("\n❌ No QR code detected")

