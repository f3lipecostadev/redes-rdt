from socket import *                 # Importa funções da biblioteca de sockets
import random                        # Importa biblioteca para gerar números aleatórios
import time                          # Importa biblioteca para controle de tempo (simulações)

SERVER_PORT = 12000                  # Porta em que o servidor ficará escutando
LOSS_PROBABILITY = 0.3               # Probabilidade de perda de pacote (30%)

def checksum(data):                  # Função que calcula o checksum dos dados
    return sum(bytearray(data.encode())) % 256  
    # Soma os bytes da mensagem e aplica módulo 256 para verificação de integridade

def is_corrupt(packet):              # Função que verifica se o pacote está corrompido
    try:
        seq, recv_checksum, data = packet.split("|", 2)  
        # Separa número de sequência, checksum recebido e dados
        return int(recv_checksum) != checksum(data)  
        # Compara checksum recebido com o checksum recalculado
    except:
        return True                  # Se ocorrer erro, considera o pacote corrompido

serverSocket = socket(AF_INET, SOCK_DGRAM)  
# Cria um socket UDP utilizando IPv4

serverSocket.bind(("", SERVER_PORT)) 
# Associa o socket a todas as interfaces de rede na porta definida

print("=== Servidor RDT 3.0 ativo ===")  
# Indica que o servidor está em execução

expected_seq = 0                     # Número de sequência esperado inicialmente

while True:                          # Loop principal do servidor
    packet, clientAddress = serverSocket.recvfrom(2048)  
    # Recebe pacote do cliente e o endereço de origem

    packet = packet.decode()         # Decodifica o pacote recebido


    print("\n[Servidor] Pacote recebido:", packet)

    if random.random() < LOSS_PROBABILITY:  
        # Simula a perda de pacotes no canal
        print("[Servidor] Pacote PERDIDO (simulação)")
        continue                     # Ignora o pacote

    if is_corrupt(packet):           # Verifica se o pacote está corrompido
        print("[Servidor] Pacote CORROMPIDO detectado → ignorado")
        continue                     # Descarta o pacote corrompido

    seq, recv_checksum, data = packet.split("|", 2)  
    # Extrai o número de sequência, checksum e dados

    seq = int(seq)                   # Converte o número de sequência para inteiro

    if seq == expected_seq:          # Verifica se o pacote é o esperado
        print(f"[Servidor] Pacote OK | Seq={seq} | Dados='{data}'")
        ack = f"ACK|{seq}"            # Cria o ACK com o número de sequência correto
        serverSocket.sendto(ack.encode(), clientAddress)  
        # Envia o ACK ao cliente
        print(f"[Servidor] ACK enviado: {ack}")
        expected_seq = 1 - expected_seq  
        # Alterna o número de sequência esperado
    else:
        print("[Servidor] Pacote duplicado → reenviando último ACK")
        ack = f"ACK|{1 - expected_seq}"  
        # Cria ACK duplicado para pacote já recebido
        serverSocket.sendto(ack.encode(), clientAddress)  
        # Reenvia o último ACK ao cliente