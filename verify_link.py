import sqlite3

conn = sqlite3.connect('database/antitheft.db')
cursor = conn.cursor()

device = cursor.execute("SELECT device_id, name, user_id FROM devices WHERE device_id = 'Danish-windows'").fetchone()
if device:
    print(f"Device: {device[0]}")
    print(f"Name: {device[1]}")
    print(f"User ID: {device[2]}")
    
    if device[2] == 24:
        print("\n[SUCCESS] Device is linked to atip@gmail.com!")
    else:
        print(f"\n[INFO] Device is linked to user ID {device[2]}")

conn.close()
