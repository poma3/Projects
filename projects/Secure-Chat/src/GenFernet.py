from cryptography.fernet import Fernet

key = Fernet.generate_key() #hàm này sinh ra chuỗi ngẫu nhiên(32byte) được encode base64, đây là chìa khóa

with open("secret.key", "wb") as f:   #wb là write binary
    f.write(key)

print("Đã tạo file secret.key cho mã hóa đầu cuối")