import socket
import json
import yaml
import toml
import csv
import io
import xml.etree.ElementTree as ET

HOST = "127.0.0.1"
PORT = 5000

dados = {
    "nome": "Márcio Cassiano de Mattos",
    "cpf": "(inserir CPF válido)",
    "idade": 27,
    "mensagem": "Segue comprovante de inscrição"
}

def to_csv(dados):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=dados.keys())
    writer.writeheader()
    writer.writerow(dados)
    return output.getvalue()

def to_xml(dados):
    root = ET.Element("dados")
    for k, v in dados.items():
        elem = ET.SubElement(root, k)
        elem.text = str(v)
    return ET.tostring(root, encoding="unicode")

def send_msg(sock, fmt, content):
    sock.sendall(f"{fmt}|{content}\nEND\n".encode("utf-8"))

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        send_msg(s, "JSON", json.dumps(dados))
        send_msg(s, "YAML", yaml.dump(dados))
        send_msg(s, "TOML", toml.dumps(dados))
        send_msg(s, "CSV", to_csv(dados))
        send_msg(s, "XML", to_xml(dados))

        print("Mensagens enviadas com sucesso!")

if __name__ == "__main__":
    main()
