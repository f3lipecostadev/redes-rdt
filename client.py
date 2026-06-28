from socket import *

# Configurações de conexão (Recomenda-se 127.0.0.1 em vez de localhost)
serverName = '127.0.0.1'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)

def calcular_checksum(mensagem_checksum):
    """Calcula a soma simples dos valores ASCII dos caracteres."""
    soma = 0
    for caractere in mensagem_checksum:
        soma += ord(caractere)
    return str(soma)

# A sequência global do cliente (RDT 3.0 alterna entre 0 e 1)
sequencia = 0

while True:
    print("\n" + "="*66)
    print("========================= CLIENTE RDT 3.0 ========================")
    print("0. Encerrar Transmissão")
    print("1. Transmissão Perfeita")
    print("2. Perda de Pacote (Dado)")
    print("3. Corrupção de Pacote (Dado)")
    print("4. Perda de ACK (Confirmação)")
    print("5. Corrupção de ACK (Confirmação)")
    print("6. Lentidão / Atraso na Rede")
    print("==================================================================")

    opcao = int(input("Escolha o cenário que deseja testar (0-6): "))
    
    if opcao == 0:
        print("[CLIENTE] Operação 0 selecionada. Encerrando o cliente...")
        break

    mensagem = input("Digite a mensagem a ser enviada: ")
    checksum = calcular_checksum(mensagem)

    # Variável de controle do loop de retransmissão
    sucesso = False

    while not sucesso:
        # Construção do pacote
        pacote = f"{opcao}|{sequencia}|{checksum}|{mensagem}"
            
        # Configura o temporizador (timeout) para estourar em 2 segundos
        clientSocket.settimeout(2.0)
        print(f"\n[CLIENTE] [ENVIANDO] Pacote (Cenário={opcao}, Seq={sequencia}, Check={checksum}, Msg='{mensagem}')")
        print(f"[CLIENTE] Timer de 2s iniciado...")
        clientSocket.sendto(pacote.encode(), (serverName, serverPort))

        try:
            # Fica travado aguardando a resposta
            resposta, serverAddress = clientSocket.recvfrom(2048)
            resposta = resposta.decode()
            print(f"[CLIENTE] [RECEBIDO] Resposta capturada da rede: {resposta}")

            # Valida se o ACK recebido é correto e íntegro
            if resposta.startswith(f"ACK{sequencia}"):
                if "|" in resposta:
                    _, msg_modificada = resposta.split("|", 1)
                    print(f"[CLIENTE] [SUCESSO TOTAL] O pacote foi entregue e confirmado! Msg: {msg_modificada}")
                else:
                    print("[CLIENTE] [SUCESSO/AVISO] ACK de confirmação simples recebido.")
                    
                # Desativa o temporizador, inverte a sequência para o próximo pacote e sai do loop
                clientSocket.settimeout(None)
                sequencia = 1 - sequencia
                sucesso = True 
                
            elif resposta.startswith("ACX"):
                # Captura do cenário 5 (ACK Corrompido)
                print(f"[CLIENTE] [ERRO] Confirmação corrompida (ACX) recebida! Descartando em silêncio...")
                print("[CLIENTE] [AGUARDANDO] O timer continua correndo até o timeout...")
                
            else:
                # Caso chegue um ACK atrasado ou de outra sequência
                print(f"[CLIENTE] [ERRO] ACK incorreto. Esperava ACK{sequencia}. Descartando e aguardando timeout...")
                        
        except timeout:
            # Se a rede perder o dado ou o ACK, ou se foi ignorado por corrupção, cai aqui
            print(f"[CLIENTE] [TIMEOUT] Alerta! Já se passaram 2 segundos e nenhuma confirmação válida chegou.")
            print(f"[CLIENTE] [RETRANSMISSÃO] Assumindo falha na rede. Preparando reenvio...")
            # Como sucesso continua False, o while repete o envio na mesma sequência!
        
clientSocket.close()