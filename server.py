from socket import *
from random import randint
import time

# Configurações de conexão
serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

# Estado interno global do servidor para controle de fluxo alternado (RDT 2.1 a 3.0)
sequencia_esperada = 0

print("========================= SERVIDOR RDT ==========================")
print(f"Servidor rodando na porta {serverPort} e aguardando mensagens...")
print("=================================================================")

def calcular_checksum(mensagem_checksum):
    """Calcula a soma simples dos valores ASCII dos caracteres."""
    soma = 0
    for caractere in mensagem_checksum:
        soma += ord(caractere)
    return str(soma)

while True:
    # Recebe e desempacota os dados vindos do cliente
    message, clientAddress = serverSocket.recvfrom(2048)
    dados = message.decode()
    versao, sequencia, checksum, mensagem = dados.split("|", 3)
    
    print(f"\n[SERVIDOR] [RECEBIDO] Opção: {versao} | Seq: {sequencia} | Msg: {mensagem}")

    # RDT 1.0 - CANAL PERFEITO
    if versao == "1":
        modifiedMessage = mensagem.upper()
        serverSocket.sendto(modifiedMessage.encode(), clientAddress)
        print("[SERVIDOR] [SUCESSO] Resposta enviada sem falhas.")

    # RDT 2.0 - ERRO DE BITS (ACK/NAK SEM SEQUÊNCIA)
    elif versao == "2":
        checksum_cliente = checksum
        checksum_servidor = calcular_checksum(mensagem)
        
        # Simula erro de bits nos dados (50% de chance)
        if randint(0, 1) == 1:
            mensagem += "x"  # Corrompe a string de dados propositalmente
            checksum_servidor = calcular_checksum(mensagem)
            
        if checksum_cliente == checksum_servidor:
            print("[SERVIDOR] [SUCESSO] Dados íntegros. Enviando ACK.")
            pacote_resposta = f"ACK|{mensagem.upper()}"
            serverSocket.sendto(pacote_resposta.encode(), clientAddress)
        else:
            print("[SERVIDOR] [ERRO] Dados corrompidos detectados! Enviando NAK.")
            serverSocket.sendto("NAK".encode(), clientAddress)

    # RDT 2.1 - CORRUPÇÃO DE ACK/NAK + NÚMERO DE SEQUÊNCIA
    elif versao == "3":
        checksum_cliente = checksum
        checksum_servidor = calcular_checksum(mensagem)
        
        if checksum_cliente == checksum_servidor:
            if int(sequencia) == sequencia_esperada:
                modifiedMessage = mensagem.upper()
                
                # Simula corrupção do ACK de retorno (50% de chance)
                if randint(0, 1) == 1:
                    print(f"[SERVIDOR] [CORRUPÇÃO] Dados corretos, mas simulando envio de ACK{sequencia} corrompido.")
                    serverSocket.sendto(f"ACX{sequencia}".encode(), clientAddress)
                else:
                    print(f"[SERVIDOR] [SUCESSO] Dados corretos (seq={sequencia}). Enviando ACK{sequencia}.")
                    pacote_resposta = f"ACK{sequencia}|{modifiedMessage}"
                    serverSocket.sendto(pacote_resposta.encode(), clientAddress)
                    sequencia_esperada = 1 - sequencia_esperada  # Alterna o estado esperado
            else:
                print(f"[SERVIDOR] [AVISO] Pacote duplicado detectado (seq={sequencia}). Reenviando apenas ACK.")
                serverSocket.sendto(f"ACK{sequencia}".encode(), clientAddress)
        else:
            print(f"[SERVIDOR] [ERRO] Dados corrompidos. Enviando NAK{sequencia}.")
            serverSocket.sendto(f"NAK{sequencia}".encode(), clientAddress)

    # RDT 2.2 - PROTOCOLO SEM NAK (APENAS ACKS NUMERADOS)
    elif versao == "4":
        checksum_cliente = checksum
        checksum_servidor = calcular_checksum(mensagem)
        
        # Simula erro de bits nos dados (50% de chance)
        if randint(0, 1) == 1:
            mensagem += "x"
            checksum_servidor = calcular_checksum(mensagem)

        if checksum_cliente == checksum_servidor and int(sequencia) == sequencia_esperada:
            modifiedMessage = mensagem.upper()
            
            # Simula corrupção do ACK de retorno (50% de chance)
            if randint(0, 1) == 1:
                print(f"[SERVIDOR] [CORRUPÇÃO] Dados corretos, mas simulando envio de ACK{sequencia} corrompido.")
                serverSocket.sendto(f"ACX{sequencia}".encode(), clientAddress)
            else:
                print(f"[SERVIDOR] [SUCESSO] Dados corretos (seq={sequencia}). Enviando ACK{sequencia}.")
                pacote_resposta = f"ACK{sequencia}|{modifiedMessage}"
                serverSocket.sendto(pacote_resposta.encode(), clientAddress)
                sequencia_esperada = 1 - sequencia_esperada
        else:
            # Lógica Kurose RDT 2.2: Envia o ACK do ÚLTIMO pacote que deu certo
            ultimo_correto = 1 - sequencia_esperada
            print(f"[SERVIDOR] [ERRO/DUPLICADO] Esperava seq={sequencia_esperada}, veio seq={sequencia} (ou corrompido).")
            print(f"[SERVIDOR] -> Reenviando ACK anterior: ACK{ultimo_correto}")
            serverSocket.sendto(f"ACK{ultimo_correto}".encode(), clientAddress)

    # RDT 3.0 - ERRO DE BITS E PERDA DE PACOTES (TEMPORIZADOR)
    elif versao == "5":
        checksum_cliente = checksum
        checksum_servidor = calcular_checksum(mensagem)
        
        # 1. Tratamento de Corrupção de Bits nos Dados
        if checksum_cliente != checksum_servidor:
            print("[SERVIDOR] [ERRO] Pacote corrompido recebido. Descartando em silêncio (força timeout no cliente).")
            continue  
            
        # 2. Tratamento de Dados Duplicados (Cenários 3 e 4 do Kurose)
        if int(sequencia) != sequencia_esperada:
            print(f"[SERVIDOR] [AVISO] Pacote duplicado detectado (esperado={sequencia_esperada}, recebido={sequencia}).")
            print(f"[SERVIDOR] -> Reenviando apenas confirmação: ACK{sequencia}")
            serverSocket.sendto(f"ACK{sequencia}".encode(), clientAddress)
            continue  

        # 3. Simulação aleatória dos 4 cenários clássicos do livro do Kurose
        cenario = randint(1, 4)
        
        if cenario == 1:
            print("[SERVIDOR] [CENÁRIO 1] Transmissão Perfeita!")
            modifiedMessage = mensagem.upper()
            pacote_resposta = f"ACK{sequencia}|{modifiedMessage}"
            serverSocket.sendto(pacote_resposta.encode(), clientAddress)
            sequencia_esperada = 1 - sequencia_esperada
            
        elif cenario == 2:
            print("[SERVIDOR] [CENÁRIO 2] Pacote foi Perdido na rede! Ignorando propositalmente...")
            # Não faz nada. O cliente dará timeout e retransmitirá.
            
        elif cenario == 3:
            print("[SERVIDOR] [CENÁRIO 3] ACK foi Perdido na rede! Aceitando dado internamente, mas retendo ACK...")
            sequencia_esperada = 1 - sequencia_esperada
            # Não responde. O cliente dará timeout, enviará duplicata e o servidor responderá no bloco acima.
            
        elif cenario == 4:
            print("[SERVIDOR] [CENÁRIO 4] Timeout Prematuro! Forçando atraso na rede (lag de 4 segundos)...")
            time.sleep(4.0)  
            modifiedMessage = mensagem.upper()
            pacote_resposta = f"ACK{sequencia}|{modifiedMessage}"
            serverSocket.sendto(pacote_resposta.encode(), clientAddress)
            sequencia_esperada = 1 - sequencia_esperada