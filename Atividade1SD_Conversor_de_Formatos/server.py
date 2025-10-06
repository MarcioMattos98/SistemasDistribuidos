import socket
import json
import yaml
import toml
import csv
import io
import xml.etree.ElementTree as ET

HOST = "127.0.0.1"
PORT = 5000

def parse_message(fmt, data):
    if fmt == "JSON":
        return json.loads(data)

    elif fmt == "YAML":
        return yaml.safe_load(data)

    elif fmt == "TOML":
        return toml.loads(data)

    elif fmt == "CSV":
        reader = csv.DictReader(io.StringIO(data))
        return list(reader)[0]

    elif fmt == "XML":
        root = ET.fromstring(data)
        return {child.tag: child.text for child in root}

    else:
        return {"erro": "Formato desconhecido"}

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Servidor rodando em {HOST}:{PORT}...")

        conn, addr = s.accept()
        with conn:
            print(f"Conectado a {addr}")

            buffer = ""
            while True:
                data = conn.recv(4096).decode("utf-8")
                if not data:
                    break

                buffer += data

                while "\nEND\n" in buffer:
                    mensagem, buffer = buffer.split("\nEND\n", 1)

                    try:
                        fmt, content = mensagem.split("|", 1)
                        recebido = parse_message(fmt, content)

                        print(f"\n--- Mensagem recebida ({fmt}) ---")
                        for k, v in recebido.items():
                            print(f"{k}: {v}")
                        print("----------------------------")

                    except Exception as e:
                        print("Erro ao processar:", e)


if __name__ == "__main__":
    main()
