from socket import *
from random import randint
import time

# Configurações de conexão
serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

# Estado interno global do servidor
sequencia_esperada = 0
tentativas_cenario = 0  # Controla se é a 1ª vez (obrigatória) ou retransmissões (random)

print("========================= SERVIDOR RDT 3.0 ========================")
print(f"Servidor rodando na porta {serverPort} e aguardando mensagens...")
print("===================================================================")

def calcular_checksum(mensagem_checksum):
    """Calcula a soma simples dos valores ASCII dos caracteres."""
    soma = 0
    for caractere in mensagem_checksum:
        soma += ord(caractere)
    return str(soma)

while True:
    # Recebe os dados brutos da rede
    message, clientAddress = serverSocket.recvfrom(2048)
    dados = message.decode()
    versao, sequencia_str, checksum_cliente, mensagem = dados.split("|", 3)
    
    versao = int(versao)
    sequencia_recebida = int(sequencia_str)
    
    print(f"\n{'-'*75}")
    print(f"[SERVIDOR] [PACOTE RECEBIDO] Cenário: {versao} | Seq Recebida: {sequencia_recebida} | Seq Esperada: {sequencia_esperada}")

    # Prepara a mensagem modificada em maiúsculas que o cliente espera receber
    modifiedMessage = mensagem.upper()

    # =====================================================================
    # 1. Tratamento de Dados Duplicados (Retransmissões do Cliente)
    # =====================================================================
    # Se a sequência recebida é diferente da esperada, é uma RETRANSMISSÃO.
    if sequencia_recebida != sequencia_esperada:
        print(f"[SERVIDOR] [AVISO] Pacote DUPLICADO detectado. O cliente retransmitiu a Seq={sequencia_recebida}.")
        
        if versao == 4:
            if randint(0, 1) == 1:
                print("[SERVIDOR] [CENÁRIO 4] Retransmissão: AZAR! O ACK foi perdido NOVAMENTE na rede!")
            else:
                print("[SERVIDOR] [CENÁRIO 4] Retransmissão: SORTE! O ACK não foi perdido desta vez.")
                pacote_resposta = f"ACK{sequencia_recebida}|{modifiedMessage}"
                serverSocket.sendto(pacote_resposta.encode(), clientAddress)
                print(f"[SERVIDOR] -> Reenviando confirmação atrasada: ACK{sequencia_recebida} com mensagem.")
                tentativas_cenario = 0 # Reseta para a próxima operação
                
        elif versao == 5:
            if randint(0, 1) == 1:
                print(f"[SERVIDOR] [CENÁRIO 5] Retransmissão: AZAR! Enviando ACK{sequencia_recebida} corrompido NOVAMENTE.")
                pacote_resposta = f"ACX{sequencia_recebida}|{modifiedMessage}"
                serverSocket.sendto(pacote_resposta.encode(), clientAddress)
            else:
                print(f"[SERVIDOR] [CENÁRIO 5] Retransmissão: SORTE! Enviando ACK{sequencia_recebida} íntegro.")
                pacote_resposta = f"ACK{sequencia_recebida}|{modifiedMessage}"
                serverSocket.sendto(pacote_resposta.encode(), clientAddress)
                tentativas_cenario = 0
                
        else:
            # Comportamento padrão: devolve o ACK imediatamente com a mensagem
            print(f"[SERVIDOR] -> Reenviando confirmação padrão de segurança: ACK{sequencia_recebida}")
            pacote_resposta = f"ACK{sequencia_recebida}|{modifiedMessage}"
            serverSocket.sendto(pacote_resposta.encode(), clientAddress)
            
        continue # Ignora o processamento do dado, pois já foi processado antes!

    # =====================================================================
    # 2. Processamento dos Cenários (Pacote INÉDITO)
    # =====================================================================
    
    if versao == 1:
        print("[SERVIDOR] [CENÁRIO 1] Transmissão Perfeita! Processando dados...")
        checksum_servidor = calcular_checksum(mensagem)
        print(f"[SERVIDOR] [VERIFICAÇÃO] Check Client: {checksum_cliente} | Check Server: {checksum_servidor}")
        
        pacote_resposta = f"ACK{sequencia_recebida}|{modifiedMessage}"
        serverSocket.sendto(pacote_resposta.encode(), clientAddress)
        
        print(f"[SERVIDOR] -> SUCESSO. ACK{sequencia_recebida} enviado. Atualizando expectativa para o próximo pacote.")
        sequencia_esperada = 1 - sequencia_esperada
        tentativas_cenario = 0
            
    elif versao == 2:
        if tentativas_cenario == 0 or randint(0, 1) == 1:
            print("[SERVIDOR] [CENÁRIO 2] AZAR! Simulação de perda ativada: Pacote de DADOS sumiu na rede!")
            print("[SERVIDOR] -> Nenhuma ação será tomada. Aguardando o cliente dar timeout...")
            tentativas_cenario += 1
        else:
            print("[SERVIDOR] [CENÁRIO 2] SORTE! O pacote de dados conseguiu chegar intacto desta vez!")
            checksum_servidor = calcular_checksum(mensagem)
            print(f"[SERVIDOR] [VERIFICAÇÃO] Check Client: {checksum_cliente} | Check Server: {checksum_servidor}")
            
            pacote_resposta = f"ACK{sequencia_recebida}|{modifiedMessage}"
            serverSocket.sendto(pacote_resposta.encode(), clientAddress)
            
            sequencia_esperada = 1 - sequencia_esperada
            tentativas_cenario = 0
            print(f"[SERVIDOR] -> Dados aceitos. Enviando ACK{sequencia_recebida} e avançando o estado.")
            
    elif versao == 3:
        if tentativas_cenario == 0 or randint(0, 1) == 1:
            mensagem += "x"  # Corrompe a string de dados propositalmente
            print("[SERVIDOR] [CENÁRIO 3] AZAR! Simulando ruído: Mensagem foi corrompida artificialmente (+ 'x').")
            tentativas_cenario += 1
        else:
            print("[SERVIDOR] [CENÁRIO 3] SORTE! Nenhum ruído inserido nesta tentativa.")

        checksum_servidor = calcular_checksum(mensagem)
        print(f"[SERVIDOR] [VERIFICAÇÃO] Check Client: {checksum_cliente} | Check Server: {checksum_servidor}")

        if checksum_cliente == checksum_servidor:
            print("[SERVIDOR] [SUCESSO] Dados íntegros. Enviando ACK.")
            pacote_resposta = f"ACK{sequencia_recebida}|{mensagem.upper()}"
            serverSocket.sendto(pacote_resposta.encode(), clientAddress)
            sequencia_esperada = 1 - sequencia_esperada
            tentativas_cenario = 0
        else:
            print("[SERVIDOR] [ERRO] Dados corrompidos detectados! Checksums não batem.")
            print("[SERVIDOR] -> Descartando pacote silenciosamente e aguardando retransmissão...")
            
    elif versao == 4:
        print("[SERVIDOR] [CENÁRIO 4] Pacote aceito. Verificando Checksum e processando...")
        checksum_servidor = calcular_checksum(mensagem)
        print(f"[SERVIDOR] [VERIFICAÇÃO] Check Client: {checksum_cliente} | Check Server: {checksum_servidor}")
        print("[SERVIDOR] [CENÁRIO 4] AZAR OBRIGATÓRIO (1ª vez)! O ACK foi PERDIDO no caminho de volta!")
        print("[SERVIDOR] -> Atualizando estado local. O cliente não saberá e enviará uma duplicata.")
        
        # Como o dado inédito chegou bem, avançamos o estado interno
        sequencia_esperada = 1 - sequencia_esperada
        tentativas_cenario += 1
        
    elif versao == 5:
        print("[SERVIDOR] [CENÁRIO 5] Pacote aceito. Verificando Checksum e processando...")
        checksum_servidor = calcular_checksum(mensagem)
        print(f"[SERVIDOR] [VERIFICAÇÃO] Check Client: {checksum_cliente} | Check Server: {checksum_servidor}")
        print(f"[SERVIDOR] [CENÁRIO 5] CORRUPÇÃO OBRIGATÓRIA (1ª vez)! Enviando ACK corrompido (ACX).")
        
        # Envia ACX com a mensagem para manter o mesmo padrão visual de pacotes na rede
        pacote_resposta = f"ACX{sequencia_recebida}|{modifiedMessage}"
        serverSocket.sendto(pacote_resposta.encode(), clientAddress)
        
        sequencia_esperada = 1 - sequencia_esperada
        tentativas_cenario += 1
            
    elif versao == 6:
        print("[SERVIDOR] [CENÁRIO 6] Timeout Prematuro! Retendo o pacote por 4 segundos...")
        time.sleep(4.0)  
        print("[SERVIDOR] [CENÁRIO 6] Liberação do atraso! Processando e respondendo...")
        
        checksum_servidor = calcular_checksum(mensagem)
        print(f"[SERVIDOR] [VERIFICAÇÃO] Check Client: {checksum_cliente} | Check Server: {checksum_servidor}")
        
        pacote_resposta = f"ACK{sequencia_recebida}|{modifiedMessage}"
        serverSocket.sendto(pacote_resposta.encode(), clientAddress)
        
        sequencia_esperada = 1 - sequencia_esperada
        tentativas_cenario = 0
        print(f"[SERVIDOR] -> ACK{sequencia_recebida} finalmente enviado para a rede.")