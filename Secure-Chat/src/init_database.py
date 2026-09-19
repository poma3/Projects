import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

#xóa bảng cũ
cursor.execute("DROP TABLE IF EXISTS Client")

#tạo bảng Client để lưu username, password (hash), salt, OTP secret
cursor.execute("""
    CREATE TABLE Client (
        Username text primary key,
        Password text,
        Salt text,
        Otp_secret text
    );
""")

conn.commit()
conn.close()
print("Database 'users.db' đã được tạo thành công!")