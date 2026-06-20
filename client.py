from socket import *

# Configurações de conexão
serverName = 'localhost'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)

print("========================= CLIENTE RDT ============================")
print("1. Canal perfeito: sem perda, sem corrupcao, sem ACK/NAK.")
print("2. Canal com erro de bits. ACK/NAK, mas SEM numero de sequencia.")
print("3. Canal com corrupcao de ACK/NAK + numero de sequencia.")
print("4. Canal com erro de bits. So ACK (com numero de sequencia).")
print("5. Canal com erro de bits E perda de pacotes. ACK + temporizador.")
print("==================================================================")

opcao = int(input("Escolha a versão (1-5): "))
mensagem = input("Digite uma mensagem: ")

def calcular_checksum(mensagem_checksum):
    """Calcula a soma simples dos valores ASCII dos caracteres."""
    soma = 0
    for caractere in mensagem_checksum:
        soma += ord(caractere)
    return str(soma)

# RDT 1.0 - CANAL PERFEITO
if opcao == 1:
    pacote = f"{opcao}|{None}|{None}|{mensagem}"
    print(f"\n[CLIENTE] [ENVIANDO] Enviando pacote RDT 1.0...")
    clientSocket.sendto(pacote.encode(), (serverName, serverPort))
    
    resposta, serverAddress = clientSocket.recvfrom(2048)
    print(f"[CLIENTE] [SUCESSO] Servidor respondeu: {resposta.decode()}")

# RDT 2.0 - ERRO DE BITS (ACK/NAK SEM SEQUÊNCIA)
elif opcao == 2:
    checksum = calcular_checksum(mensagem)
    pacote = f"{opcao}|{None}|{checksum}|{mensagem}"
    print(f"\n[CLIENTE] [ENVIANDO] Enviando pacote RDT 2.0...")
    clientSocket.sendto(pacote.encode(), (serverName, serverPort))
    
    while True:
        resposta, serverAddress = clientSocket.recvfrom(2048)
        resposta = resposta.decode()
        print(f"[CLIENTE] [RECEBIDO] Resposta bruta: {resposta}")

        if resposta.startswith("ACK"):
            if "|" in resposta:
                _, msg_modificada = resposta.split("|", 1)
                print(f"[CLIENTE] [SUCESSO] Mensagem em maiúsculo: {msg_modificada}")
            break
        elif resposta == "NAK":
            print("[CLIENTE] [ERRO] NAK recebido (dados corrompidos). Retransmitindo...")
            clientSocket.sendto(pacote.encode(), (serverName, serverPort))

# RDT 2.1 - CORRUPÇÃO DE ACK/NAK + NÚMERO DE SEQUÊNCIA
elif opcao == 3:
    sequencia = 0
    checksum = calcular_checksum(mensagem)
    pacote = f"{opcao}|{sequencia}|{checksum}|{mensagem}"
    print(f"\n[CLIENTE] [ENVIANDO] Enviando pacote RDT 2.1 (seq={sequencia})...")
    clientSocket.sendto(pacote.encode(), (serverName, serverPort))

    while True:
        resposta, serverAddress = clientSocket.recvfrom(2048)
        resposta = resposta.decode()
        print(f"[CLIENTE] [RECEBIDO] Resposta bruta: {resposta}")

        if resposta.startswith(f"ACK{sequencia}"):
            if "|" in resposta:
                _, msg_modificada = resposta.split("|", 1)
                print(f"[CLIENTE] [SUCESSO] Mensagem recebida: {msg_modificada}")
            else:
                print("[CLIENTE] [AVISO] Recebido apenas ACK (pacote duplicado detectado pelo servidor).")
            break
        elif resposta.startswith(f"NAK{sequencia}"):
            print(f"[CLIENTE] [ERRO] NAK{sequencia} recebido. Retransmitindo...")
            clientSocket.sendto(pacote.encode(), (serverName, serverPort))
        else:
            print("[CLIENTE] [CORRUPÇÃO] ACK/NAK veio corrompido! Retransmitindo...")
            clientSocket.sendto(pacote.encode(), (serverName, serverPort))

# RDT 2.2 - PROTOCOLO SEM NAK (APENAS ACKS NUMERADOS)
elif opcao == 4:
    sequencia = 0
    checksum = calcular_checksum(mensagem)
    pacote = f"{opcao}|{sequencia}|{checksum}|{mensagem}"
    print(f"\n[CLIENTE] [ENVIANDO] Enviando pacote RDT 2.2 (seq={sequencia})...")
    clientSocket.sendto(pacote.encode(), (serverName, serverPort))

    while True:
        resposta, serverAddress = clientSocket.recvfrom(2048)
        resposta = resposta.decode()
        print(f"[CLIENTE] [RECEBIDO] Resposta bruta: {resposta}")

        if resposta.startswith(f"ACK{sequencia}"):
            if "|" in resposta:
                _, msg_modificada = resposta.split("|", 1)
                print(f"[CLIENTE] [SUCESSO] Mensagem recebida: {msg_modificada}")
            else:
                print("[CLIENTE] [AVISO] ACK correto recebido (Estado sincronizado).")
            break  
        else:
            print(f"[CLIENTE] [ERRO] ACK incorreto ou corrompido! Esperava ACK{sequencia}. Retransmitindo...")
            clientSocket.sendto(pacote.encode(), (serverName, serverPort))

# RDT 3.0 - ERRO DE BITS + PERDA DE PACOTES (TEMPORIZADOR)
elif opcao == 5:    
    sequencia = 0
    checksum = calcular_checksum(mensagem)
    pacote = f"{opcao}|{sequencia}|{checksum}|{mensagem}"
    
    # Configura o temporizador (timeout) para 2 segundos
    clientSocket.settimeout(2.0)
    print(f"\n[CLIENTE] [ENVIANDO] Enviando pacote RDT 3.0 (seq={sequencia}). Temporizador iniciado...")
    clientSocket.sendto(pacote.encode(), (serverName, serverPort))

    while True:
        try:
            resposta, serverAddress = clientSocket.recvfrom(2048)
            resposta = resposta.decode()
            print(f"[CLIENTE] [RECEBIDO] Resposta bruta: {resposta}")

            if resposta.startswith(f"ACK{sequencia}"):
                if "|" in resposta:
                    _, msg_modificada = resposta.split("|", 1)
                    print(f"[CLIENTE] [SUCESSO] Mensagem recebida: {msg_modificada}")
                else:
                    print("[CLIENTE] [AVISO] ACK de confirmação simples recebido.")
                
                # Desativa o temporizador para não afetar execuções futuras
                clientSocket.settimeout(None)
                break
            else:
                print(f"[CLIENTE] [ERRO] ACK incorreto/corrompido. Esperava ACK{sequencia}. Retransmitindo...")
                clientSocket.sendto(pacote.encode(), (serverName, serverPort))
                
        except timeout:
            print("\n[CLIENTE] [TIMEOUT] O tempo limite expirou! Nenhuma resposta chegou.")
            print("[CLIENTE] [RETRANSMISSÃO] Enviando o pacote novamente e reiniciando o timer...")
            clientSocket.sendto(pacote.encode(), (serverName, serverPort))

else:
    print("[CLIENTE] Opção inválida. Encerrando.")
    
clientSocket.close()