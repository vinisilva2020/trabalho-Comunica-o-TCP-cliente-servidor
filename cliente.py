import hashlib
from pathlib import Path
import socket
import struct
import sys

# Tamanho usado para ler e enviar o arquivo em blocos, evitando carregar tudo
# em memória de uma vez.
BUFFER_SIZE = 64 * 1024

# Formato do cabeçalho binário enviado antes do arquivo:
# magic(4), versão(1), tamanho do nome(2), tamanho do arquivo(8), SHA-256(32).
HEADER_FORMAT = "!4sBHQ32s"


def recv_exact(sock, total_bytes):
    """Lê exatamente total_bytes do socket.

    TCP entrega um fluxo contínuo de bytes. Uma chamada a recv pode retornar
    menos dados do que o solicitado, então esta função repete a leitura até
    montar a quantidade exata esperada pelo protocolo.
    """
    data = bytearray()

    while len(data) < total_bytes:
        chunk = sock.recv(total_bytes - len(data))

        if not chunk:
            raise ConnectionError("Servidor encerrou a conexão inesperadamente.")

        data.extend(chunk)

    return bytes(data)


def calculate_sha256(file_path):
    """Calcula o SHA-256 do arquivo em blocos."""
    hasher = hashlib.sha256()

    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(BUFFER_SIZE)

            if not chunk:
                break

            hasher.update(chunk)

    return hasher.digest()


def send_file(host, port, file_path):
    """Conecta ao servidor e envia um arquivo usando o protocolo da aplicação."""
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    filename = path.name.encode("utf-8")
    file_size = path.stat().st_size
    file_hash = calculate_sha256(path)

    # O servidor aceita nomes curtos e previsíveis para evitar entradas
    # grandes demais ou nomes vazios no protocolo didático.
    if len(filename) == 0 or len(filename) > 255:
        raise ValueError("Nome de arquivo inválido ou muito longo.")

    # O cabeçalho permite que o servidor saiba quanto deve ler e qual hash
    # deve validar antes de confirmar o recebimento.
    header = struct.pack(
        HEADER_FORMAT,
        b"TRED",
        1,
        len(filename),
        file_size,
        file_hash,
    )

    with socket.create_connection((host, port), timeout=15) as client:
        # sendall garante que todos os bytes sejam entregues ao buffer do SO.
        client.sendall(header)
        client.sendall(filename)

        # O conteúdo do arquivo é enviado em blocos para economizar memória.
        with open(path, "rb") as file:
            while True:
                chunk = file.read(BUFFER_SIZE)

                if not chunk:
                    break

                client.sendall(chunk)

        response_header = recv_exact(client, 3)
        status, message_length = struct.unpack("!BH", response_header)

        # A resposta também é delimitada: primeiro vem o tamanho da mensagem,
        # depois a mensagem em UTF-8.
        message = recv_exact(client, message_length).decode("utf-8")

        if status == 0:
            print(f"[SUCESSO] {message}")
        else:
            print(f"[ERRO DO SERVIDOR] {message}")


def main():
    if len(sys.argv) != 4:
        print("Uso: python cliente.py <IP_SERVIDOR> <PORTA> <ARQUIVO>")
        print("Exemplo: python cliente.py 127.0.0.1 5000 documento.pdf")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    file_path = sys.argv[3]

    try:
        send_file(host, port, file_path)
    except Exception as error:
        print(f"[ERRO] {error}")


if __name__ == "__main__":
    main()
