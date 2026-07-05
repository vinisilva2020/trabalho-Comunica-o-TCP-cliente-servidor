import hashlib
import hmac
import os
from pathlib import Path
import socket
import struct
import threading

HOST = "0.0.0.0"
PORT = 5000
BUFFER_SIZE = 64 * 1024
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
OUTPUT_DIR = Path("arquivos_recebidos")

HEADER_FORMAT = "!4sBHQ32s"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


def recv_exact(sock, total_bytes):
    """Recebe exatamente a quantidade de bytes esperada."""
    data = bytearray()

    while len(data) < total_bytes:
        chunk = sock.recv(min(BUFFER_SIZE, total_bytes - len(data)))

        if not chunk:
            raise ConnectionError("Conexão encerrada antes do fim da transferência.")

        data.extend(chunk)

    return bytes(data)


def send_response(sock, status, message):
    encoded_message = message.encode("utf-8")

    if len(encoded_message) > 65535:
        encoded_message = encoded_message[:65535]

    response_header = struct.pack("!BH", status, len(encoded_message))
    sock.sendall(response_header + encoded_message)


def handle_client(conn, address):
    print(f"[NOVA CONEXÃO] Cliente conectado: {address}")

    with conn:
        temp_path = None

        try:
            header = recv_exact(conn, HEADER_SIZE)

            magic, version, filename_length, file_size, expected_hash = struct.unpack(
                HEADER_FORMAT,
                header,
            )

            if magic != b"TRED":
                raise ValueError("Protocolo inválido.")

            if version != 1:
                raise ValueError("Versão de protocolo não suportada.")

            if filename_length == 0 or filename_length > 255:
                raise ValueError("Tamanho de nome de arquivo inválido.")

            if file_size > MAX_FILE_SIZE:
                raise ValueError("Arquivo excede o limite de 100 MB.")

            raw_filename = recv_exact(conn, filename_length)
            filename = Path(raw_filename.decode("utf-8")).name

            if filename in ("", ".", ".."):
                raise ValueError("Nome de arquivo inválido.")

            OUTPUT_DIR.mkdir(exist_ok=True)

            final_path = OUTPUT_DIR / filename
            temp_path = OUTPUT_DIR / f"{filename}.part"

            received_bytes = 0
            hasher = hashlib.sha256()

            with open(temp_path, "wb") as output_file:
                while received_bytes < file_size:
                    bytes_to_read = min(BUFFER_SIZE, file_size - received_bytes)
                    chunk = conn.recv(bytes_to_read)

                    if not chunk:
                        raise ConnectionError(
                            "Conexão encerrada durante o recebimento do arquivo."
                        )

                    output_file.write(chunk)
                    hasher.update(chunk)
                    received_bytes += len(chunk)

            received_hash = hasher.digest()

            if not hmac.compare_digest(received_hash, expected_hash):
                temp_path.unlink(missing_ok=True)
                raise ValueError("Falha na verificação de integridade SHA-256.")

            os.replace(temp_path, final_path)

            message = f"Arquivo recebido com sucesso: {filename} ({file_size} bytes)"
            print(f"[SUCESSO] {message}")
            send_response(conn, 0, message)

        except Exception as error:
            print(f"[ERRO] Cliente {address}: {error}")

            if temp_path:
                temp_path.unlink(missing_ok=True)

            try:
                send_response(conn, 1, str(error))
            except OSError:
                pass


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()

        print(f"Servidor TCP escutando em {HOST}:{PORT}")
        print("Aguardando conexões...")

        while True:
            conn, address = server.accept()

            thread = threading.Thread(
                target=handle_client,
                args=(conn, address),
                daemon=True,
            )
            thread.start()


if __name__ == "__main__":
    main()
