# 🛡️ Sistema de Auditoria Inteligente - NLConsulting

Este projeto consiste em uma solução de IA para auditoria fiscal automatizada, capaz de processar grandes volumes de dados (1.000 notas fiscais), extrair informações estruturadas e identificar anomalias financeiras com alta precisão.

## 🚀 Visão Geral do Projeto

O motor de auditoria transforma ficheiros de texto brutos em dados estruturados (JSON/CSV) e aplica regras de negócio para detectar fraudes e erros operacionais, alimentando um dashboard no Power BI para tomada de decisão.

---

## 🏗️ Arquitetura e Escolhas Técnicas

### 1. Modelo de Linguagem (LLM): Llama 3.1 8B via Groq
* **Escolha:** Migramos do modelo 70B para o **Llama-3.1-8b-instant**.
* **Porquê?** Embora o 70B seja mais potente, o modelo de 8B apresentou latência significativamente menor (ganho de 400% em velocidade) e limites de cota (Rate Limits) mais generosos, sendo ideal para a extração de dados padronizados de 1.000 registros sem comprometer a precisão.

### 2. Fluxo de Processamento Sequencial (Linear)
* **Escolha:** Processamento síncrono com delay controlado (`time.sleep`).
* **Porquê?** Para garantir a integridade total dos dados frente às limitações de cota da API. O processamento paralelo (multithreading) causava bloqueios por excesso de requisições por minuto (RPM). O ajuste final de **3.5s de delay** permitiu concluir os 1.000 arquivos com 0% de erro.

### 3. Backend: FastAPI & BackgroundTasks
* **Escolha:** Uso de `BackgroundTasks` para o processamento.
* **Porquê?** Auditorias de larga escala levam tempo. O FastAPI permite que o usuário dispare o processo e receba uma confirmação imediata, enquanto a IA trabalha em segundo plano, evitando *timeouts* no navegador.

### 4. Resiliência: Lógica de Retry & Sanitização
* **Escolha:** Implementação de 3 tentativas de extração com limpeza via Regex.
* **Porquê?** IAs podem ocasionalmente incluir Markdown ou textos explicativos na resposta. O código higieniza o output para garantir JSON puro, e caso a API falhe, o sistema tenta novamente antes de marcar o registro como erro.

---

## 🔍 Regras de Auditoria (Detecção de Anomalias)

O sistema valida automaticamente quatro pilares críticos:
1.  **Duplicidade:** Identifica NFs com mesmo número e fornecedor.
2.  **Compliance Temporal:** Alerta se a Data de Emissão for posterior à Data de Pagamento.
3.  **Autorização:** Verifica se o aprovador consta na lista oficial da companhia.
4.  **Conflito de Status:** Notas marcadas como "Canceladas", mas que possuem registro de pagamento.

---

## 📁 Estrutura do Repositório

* `main.py`: Ponto de entrada da API FastAPI.
* `processor.py`: O "cérebro" do sistema (extração, limpeza e motor de regras).
* `requirements.txt`: Dependências necessárias para reproduzir o ambiente.
* `resultados_bi.csv`: Base de dados consolidada para o Power BI.
* `log_auditoria.csv`: Relatório detalhado de todas as anomalias encontradas.
* `/archive`: Histórico de versões e testes de otimização.

---

## 🛠️ Como Executar

1.  Clone o repositório.
2.  Instale as dependências: `pip install -r requirements.txt`.
3.  Configure sua chave da Groq no arquivo `.env`.
4.  Inicie o servidor: `uvicorn main:app`.
5.  Acesse `http://127.0.0.1:8000/docs` e execute o endpoint `/executar-auditoria`.

---
**Desenvolvido por VictorPD974 como parte do desafio técnico da NLConsulting.**
