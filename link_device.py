import sqlite3

conn = sqlite3.connect('database/antitheft.db')
cursor = conn.cursor()

# Link Danish-windows device to atip@gmail.com (user_id = 24)
cursor.execute("UPDATE devices SET user_id = 24 WHERE device_id = 'Danish-windows'")
conn.commit()

print("Device 'Danish-windows' linked to atip@gmail.com")
print("Refresh your dashboard to see the device!")

conn.close()
