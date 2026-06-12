from socket import *              # Importa todas as funções da biblioteca de sockets
import time                       # Importa biblioteca para controle de tempo (delay)

SERVER_NAME = "localhost"         # Endereço do servidor (mesma máquina)
SERVER_PORT = 12000               # Porta utilizada pelo servidor
TIMEOUT = 2                       # Tempo máximo de espera por ACK (em segundos)

def checksum(data):               # Função que calcula o checksum dos dados
    return sum(bytearray(data.encode())) % 256  # Soma os bytes da mensagem e aplica módulo 256

clientSocket = socket(AF_INET, SOCK_DGRAM)  # Cria socket UDP (IPv4)
clientSocket.settimeout(TIMEOUT)            # Define tempo limite para espera de resposta

seq = 0                           # Número de sequência inicial (0 ou 1)

print("=== Cliente RDT 3.0 ===")  # Mensagem de inicialização do cliente

print("\nMENU DO CANAL:")
print("1 - Entrega normal")       # Opção de envio sem erros
print("2 - Corromper dados")      # Opção de envio com corrupção simulada
print("3 - Inserir atraso artificial")  # Opção de atraso na transmissão

choice = input("Escolha a opção: ")  # Lê a escolha do usuário

message = input("\nDigite a mensagem a ser enviada: ")  # Lê a mensagem a ser enviada

send_data = message               # Inicialmente, dados enviados são iguais à mensagem

if choice == "2":                 # Verifica se o usuário escolheu corromper os dados
    send_data = message + "XXX"   # Altera a mensagem para causar erro de checksum
    print("[Canal] Dados CORROMPIDOS intencionalmente")

if choice == "3":                 # Verifica se o usuário escolheu atraso artificial
    print("[Canal] Atraso artificial inserido")
    time.sleep(3)                 # Pausa a execução por 3 segundos

pkt_checksum = checksum(send_data)  # Calcula o checksum dos dados enviados
packet = f"{seq}|{pkt_checksum}|{send_data}"  # Monta o pacote no formato RDT

while True:                       # Loop para retransmissão em caso de erro
    print("\n[Cliente] Enviando pacote:")
    print(f"Seq={seq}, Checksum={pkt_checksum}, Dados='{send_data}'")

    clientSocket.sendto(packet.encode(), (SERVER_NAME, SERVER_PORT))  
    # Envia o pacote ao servidor via UDP

    print("[Cliente] Aguardando ACK...")

    try:
        ack, _ = clientSocket.recvfrom(2048)  # Aguarda ACK do servidor
        ack = ack.decode()                    # Decodifica a mensagem recebida
        print("[Cliente] ACK recebido:", ack)

        _, ack_seq = ack.split("|")           # Extrai o número de sequência do ACK
        ack_seq = int(ack_seq)                # Converte para inteiro

        if ack_seq == seq:                    # Verifica se o ACK corresponde ao pacote enviado
            print("[Cliente] ACK correto → envio concluído")
            seq = 1 - seq                     # Alterna o número de sequência
            break                             # Encerra o loop
        else:
            print("[Cliente] ACK duplicado → retransmitindo")

    except timeout:                           # Tratamento de estouro de tempo
        print("[Cliente] TIMEOUT! Retransmitindo pacote...")

clientSocket.close()                          # Fecha o socket do cliente