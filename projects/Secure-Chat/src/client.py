import socket, ssl, threading, base64, os
from cryptography.fernet import Fernet

host = '127.0.0.1'
post = 8080

try: 
    with open("secret.key", "rb") as f:
        cipher = Fernet(f.read())
except: 
    print("Thiếu file secret.key!")
    exit()

def receive(sock):
    while True:
        try:
            data = sock.recv(5242880)
            if not data: break
            try: 
                decrypted_text = cipher.decrypt(data).decode()

                if decrypted_text.startswith("File:"): #nếu là gửi file
                    parts = decrypted_text.split("|", 1) # 1 nghĩa là chỉ cắt ở dấu | đầu tiên tìm thấy
                    filename = parts[0].replace("File:","") #xóa chữ File: đi, chỉ để lại tên file
                    file_b64 = parts[1]

                    file_bytes = base64.b64decode(file_b64)

                    #lưu file vào máy 
                    save_path = "downloaded_" + filename
                    with open(save_path, "wb") as f: 
                        f.write(file_bytes)
                    print(f"\n[📂] Đã nhận file '{save_path}'")
                else: #nếu là tin nhắn text mã hóa bình thường
                    print(f"\n[🔑] {decrypted_text}")
            except: 
                #Nếu tin nhắn không mã hóa (menu hệ thống)
                print(data.decode(), end ="", flush=True) #end="" để không tự động xuống dòng
                                                        #flush=true để hiển thị luôn ra màn hình, tránh giữ lại trong buffer
        except Exception as e:
            break


def start_client():
    #bỏ qua check chứng chỉ uy tín không
    context = ssl._create_unverified_context()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s = context.wrap_socket(s, server_hostname=host)

    try:
        s.connect((host, post))
    except:
        print("Không kết nối được với Server!")
        return

    threading.Thread(target=receive, args=(s,), daemon=True).start()

    while True:
        msg = input()
        if msg == 'exit': break

        #nếu gõ "File: đường dẫn file" thì sẽ gửi file mã hóa
        if msg.startswith("File:"):
            file_path = msg[5:].strip()
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)

                #1. đọc file dưới dạng nhị phân
                with open(file_path, "rb") as f:
                    file_data = f.read()
                
                #2. encode base64 file
                file_b64 = base64.b64encode(file_data).decode('utf-8')

                #3. ghép thành chuỗi dài
                payload = f"File:{filename}|{file_b64}"

                #4. mã hóa E2EE
                enc_payload = cipher.encrypt(payload.encode())
                s.sendall(enc_payload)
                print(f"[✔️] Đã mã hóa và gửi file {filename}")
            else: 
                print(f"[❌] không tìm thấy tệp: {filename}")

        #nếu gõ "ENC: nội dung" thì sẽ mã hóa
        elif msg.startswith("ENC:"):
            real_msg = msg[4:]
            enc = cipher.encrypt(real_msg.encode())
            s.sendall(enc)
        else:
            s.sendall(msg.encode())
    s.close()

if __name__ == "__main__":
    start_client()