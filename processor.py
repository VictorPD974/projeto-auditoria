import os
import zipfile
import chardet
import requests
import json
import time
import re
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Carrega as chaves de API do ficheiro .env
load_dotenv()


class AuditorIA:
    """
    Sistema de Auditoria Inteligente - NLConsulting
    Versão Estável com Retry, Backoff e Slicing de Amostra.
    """

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Regra de Negócio: Aprovadores autorizados conforme briefing
        self.aprovadores_oficiais = ["Maria Silva", "João Souza", "Ana Costa"]
        self.prompt_version = "v2.1-clean-output"

    def tratar_encoding(self, binario):
        """Garante a leitura correta de ficheiros com diferentes encodings (ANSI, UTF-8, etc)"""
        deteccao = chardet.detect(binario)
        encoding = deteccao['encoding'] or 'utf-8'
        return binario.decode(encoding, errors='ignore')

    def validar_e_limpar_dados(self, dados):
        """Auditoria Sintética: Normaliza campos para processamento matemático e BI"""
        if not dados: return {}

        # Limpa CNPJ: apenas números
        cnpj_raw = str(dados.get('CNPJ_FORNECEDOR', ''))
        dados['CNPJ_FORNECEDOR'] = re.sub(r'\D', '', cnpj_raw)

        # Limpa Valor: Converte para float (ex: R$ 1.250,00 -> 1250.0)
        valor_raw = str(dados.get('VALOR_BRUTO', '0'))
        try:
            valor_limpo = valor_raw.replace('R$', '').replace('.', '').replace(',', '.').strip()
            dados['VALOR_BRUTO'] = float(re.sub(r'[^\d.]', '', valor_limpo))
        except:
            dados['VALOR_BRUTO'] = 0.0
        return dados

    def extrair_com_ia(self, texto, max_tentativas=3):
        """Interface com a API Groq com lógica de 3 tentativas e limpeza de Markdown"""
        tentativa = 0
        while tentativa < max_tentativas:
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": "Aja como auditor. Extraia os dados e responda APENAS o JSON puro, sem markdown ou explicações."
                    },
                    {
                        "role": "user",
                        "content": f"Extraia: TIPO_DOCUMENTO, NUMERO_DOCUMENTO, DATA_EMISSAO_NF, FORNECEDOR, CNPJ_FORNECEDOR, VALOR_BRUTO, DATA_PAGAMENTO, APROVADO_POR, STATUS. Texto: {texto}"
                    }
                ],
                "response_format": {"type": "json_object"}
            }

            try:
                response = requests.post(self.url, headers=self.headers, json=payload, timeout=30)

                # Debug em caso de erro de API (útil para o avaliador ver no terminal)
                if response.status_code != 200 and response.status_code != 429:
                    print(f"--- ERRO API (Status {response.status_code}) ---")
                    print(response.text)

                if response.status_code == 200:
                    raw_content = response.json()['choices'][0]['message']['content']
                    # Remove possíveis blocos de código markdown que a IA possa enviar
                    json_clean = raw_content.replace("```json", "").replace("```", "").strip()
                    return self.validar_e_limpar_dados(json.loads(json_clean))

                if response.status_code == 429:
                    print(f"[RETRY] Rate Limit atingido. Tentativa {tentativa + 1}/3. Aguardando 10s...")
                    time.sleep(5)

                tentativa += 1
            except Exception as e:
                print(f"[RETRY] Erro na tentativa {tentativa + 1}: {str(e)}")
                tentativa += 1
                time.sleep(2)

        return {"erro_critico": "Falha total após 3 tentativas", "STATUS": "ERRO_PROCESSAMENTO"}

    def detectar_anomalias(self, nota, todos_resultados):
        """Motor de Regras: Identifica fraudes e erros nos documentos"""
        # Se for um erro de processamento, não executa a detecção para evitar falsos positivos
        if "erro_critico" in nota or nota.get("NUMERO_DOCUMENTO") == "FALHA":
            return []

        anomalias = []

        # 1. Verificação de Duplicidade
        for outra in todos_resultados:
            if "erro_critico" not in outra and \
                    nota.get('NUMERO_DOCUMENTO') == outra.get('NUMERO_DOCUMENTO') and \
                    nota.get('FORNECEDOR') == outra.get('FORNECEDOR'):
                anomalias.append(
                    {"regra": "NF duplicada", "evidencia": str(nota.get('NUMERO_DOCUMENTO')), "confianca": "Alto"})
                break

        # 2. Inconsistência Temporal (Emissão > Pagamento)
        try:
            dt_em = datetime.strptime(nota.get('DATA_EMISSAO_NF', ''), '%d/%m/%Y')
            dt_pg = datetime.strptime(nota.get('DATA_PAGAMENTO', ''), '%d/%m/%Y')
            if dt_em > dt_pg:
                anomalias.append({"regra": "NF emitida após pagamento",
                                  "evidencia": f"E:{nota['DATA_EMISSAO_NF']} P:{nota['DATA_PAGAMENTO']}",
                                  "confianca": "Alto"})
        except:
            pass

        # 3. Compliance de Aprovação
        if nota.get('APROVADO_POR') not in self.aprovadores_oficiais:
            anomalias.append({"regra": "Aprovador não reconhecido", "evidencia": str(nota.get('APROVADO_POR')),
                              "confianca": "Médio"})

        # 4. Conflito de Status
        if str(nota.get('STATUS')).upper() == 'CANCELADO' and nota.get('DATA_PAGAMENTO'):
            anomalias.append(
                {"regra": "STATUS inconsistente", "evidencia": "Cancelado com data de pagamento", "confianca": "Médio"})

        return anomalias

    def processar_zip(self, zip_path):
        """Processamento Linear Sequencial para escala de 1.000 ficheiros"""
        if not os.path.exists(zip_path):
            return [{"erro": "ZIP não encontrado"}]

        resultados_finais = []
        log_auditoria = []

        with zipfile.ZipFile(zip_path, 'r') as z:
            # Lista apenas ficheiros txt ignorando pastas ocultas de sistema
            arquivos = [f for f in z.namelist() if f.endswith('.txt') and not f.startswith('__MACOSX')]

            # --- AMOSTRA DE TESTE: Processa apenas os primeiros 5 ---
            # Para o processamento total (1.000), basta comentar a linha abaixo
            # arquivos = arquivos[:15]

            total = len(arquivos)
            print(f"--- Iniciando Auditoria Linear: {total} ficheiros ---")

            for i, nome in enumerate(arquivos):
                with z.open(nome) as f:
                    texto = self.tratar_encoding(f.read())

                dados = self.extrair_com_ia(texto)

                # Tratamento de segurança se a IA falhar
                if "erro_critico" in dados:
                    dados = {
                        "arquivo_origem": nome,
                        "data_processamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "STATUS": "ERRO_IA",
                        "FORNECEDOR": "FALHA_NA_EXTRACAO",
                        "NUMERO_DOCUMENTO": "FALHA",
                        "VALOR_BRUTO": 0.0,
                        "erro": dados["erro_critico"]
                    }
                else:
                    dados['arquivo_origem'] = nome
                    dados['data_processamento'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Detecta anomalias comparando com o que já foi processado
                anomalias_encontradas = self.detectar_anomalias(dados, resultados_finais)
                dados['tem_anomalia'] = len(anomalias_encontradas) > 0

                # Preenche o Log de Auditoria Rastreável
                for anom in anomalias_encontradas:
                    log_auditoria.append({
                        "arquivo": nome,
                        "timestamp": dados['data_processamento'],
                        "regra": anom['regra'],
                        "evidencia": anom['evidencia'],
                        "confianca": anom['confianca']
                    })

                resultados_finais.append(dados)
                print(f"[PROGRESSO] {i + 1} de {total} | Concluído: {nome}")

                # Intervalo de segurança para respeitar a cota RPM
                time.sleep(2)

        # Geração dos CSVs Finais para Power BI
        pd.DataFrame(resultados_finais).drop(columns=['anomalias'], errors='ignore').to_csv('resultados_bi.csv',
                                                                                            index=False, sep=';',
                                                                                            encoding='utf-8-sig')
        pd.DataFrame(log_auditoria).to_csv('log_auditoria.csv', index=False, sep=';', encoding='utf-8-sig')

        print("--- Processo Finalizado: 'resultados_bi.csv' e 'log_auditoria.csv' gerados ---")
        return resultados_finais