import socket, ssl, threading, sqlite3, hashlib, pyotp, secrets

host = '0.0.0.0'
port = 8080
clients = []

def get_db():
    return sqlite3.connect("users.db", check_same_thread = False) #false là để cho phép dùng connection ở luồng khác

def handle_client(client_sock, addr):
    print(f"Client kết nối: {addr}")
    user_name = ""
    try: 
        while True:
            #menu hệ thống
            menu = "\n--- SYSTEM ---\n1. Đăng ký\n2. Đăng nhập\n3. Thoát\nChọn: "
            client_sock.sendall(menu.encode())
            choice = client_sock.recv(1024).decode().strip()
            
            if choice == '1':
                client_sock.sendall("Username mới: ".encode()); u = client_sock.recv(1024).decode().strip()
                client_sock.sendall("Password mới: ".encode()); p = client_sock.recv(1024).decode().strip()

                salt = secrets.token_hex(16)
                p_hash = hashlib.sha256((salt + p).encode()).hexdigest()
                otp_secret = pyotp.random_base32()

                try: 
                    conn = get_db()
                    conn.execute("insert into Client values(?, ?, ?, ?)", (u, p_hash, salt, otp_secret))
                    conn.commit()
                    conn.close()

                    uri = pyotp.TOTP(otp_secret).provisioning_uri(name=u, issuer_name="SecureApp")
                    link = f"https://api.qrserver.com/v1/create-qr-code/?data={uri}&size=200x200"
                    client_sock.sendall(f"[✔️] Đăng ký thành công\nSecret: {otp_secret}\nLink QR: {link}\n".encode())
                except: 
                    client_sock.sendall("[❌] Username đã tồn tại!\n".encode())
            elif choice == '2':
                client_sock.sendall("Username: ".encode()); u = client_sock.recv(1024).decode().strip()
                client_sock.sendall("Password: ".encode()); p = client_sock.recv(1024).decode().strip()

                conn = get_db()
                row = conn.execute("select Password, Salt, Otp_secret from Client where Username = ?", (u,)).fetchone()
                conn.close()

                if row:
                    stored_pass, salt, otp_sec = row
                    if hashlib.sha256((salt + p).encode()).hexdigest() == stored_pass: #phải encode vì thuật toán hash thì biết băm số nhị phân
                                                                                      #, không biết băm string
                        client_sock.sendall("Nhập OTP (6 số): ".encode())
                        otp_in = client_sock.recv(1024).decode().strip()
                        if pyotp.TOTP(otp_sec).verify(otp_in):
                            client_sock.sendall("[✔️] Login success\n".encode())
                            client_sock.sendall("""Hãy gửi tin nhắn theo cách của bạn:
(cú pháp gửi tin nhắn mã hóa: 'ENC: [nội dung tin nhắn]'\n""".encode())
                            username = u
                            clients.append(client_sock)
                            break
                        else: client_sock.sendall("[❌] Sai OTP!\n".encode())
                    else: client_sock.sendall("[❌] Sai password!\n".encode())
                else: client_sock.sendall("[❌] user không tồn tại!\n".encode())
            elif choice == '3':
                break

        #vòng lặp chat
        while True: 
            msg = client_sock.recv(5242880)
            if not msg: 
                break
            print(msg)
            for c in clients:
                if c != client_sock:
                    try: c.sendall(msg)
                    except: clients.remove(c)

    except: pass
    finally:
        if client_sock in clients:
            clients.remove(client_sock)
        client_sock.close()
        
def starts_server():
    # load chứng chỉ openssl đã tạo
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain("server.crt", "server.key")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port)) #() là cú pháp tuple-bộ dữ liệu
    s.listen() 
    print(f"Server OpenSSL đang chạy tại {host}:{port}")

    with context.wrap_socket(s, server_side=True) as ssl_sock:
        while True:
            try:
                client, addr = ssl_sock.accept()
                threading.Thread(target=handle_client, args=(client, addr)).start()
            except: pass

if __name__ == "__main__":
    starts_server()