🛡️ Sistema de Auditoria Inteligente - NLConsulting
Este projeto consiste em uma solução de IA para auditoria fiscal automatizada, capaz de processar grandes volumes de dados (1.000 notas fiscais), extrair informações estruturadas e identificar anomalias financeiras com alta precisão utilizando LLMs de última geração.

🚀 Visão Geral do Projeto
O motor de auditoria transforma ficheiros de texto brutos em dados estruturados (JSON/CSV) e aplica regras de negócio para detectar fraudes e erros operacionais, alimentando um dashboard no Power BI para tomada de decisão estratégica.

📊 Dashboard de Auditoria (BI)
O resultado do processamento é visualizado em um dashboard de alta fidelidade com interface Dark Mode, focado em clareza e urgência.

Página 1: Resumo Executivo & Compliance
Focada em KPIs globais e detecção de riscos por fornecedor.

Página 2: Log de Auditoria Detalhado
Focada na rastreabilidade total de cada anomalia encontrada.


🏗️ Arquitetura e Escolhas Técnicas
1. Modelo de Linguagem (LLM): Llama 3.1 8B via Groq
Escolha: Migração do modelo 70B para o Llama-3.1-8b-instant.

Porquê? Apresentou latência 400% menor e limites de cota (Rate Limits) mais generosos, garantindo o processamento dos 1.000 registros com agilidade sem perda de precisão na extração de campos fixos.

2. Backend & Resiliência (FastAPI)
BackgroundTasks: Auditorias de larga escala levam tempo. O FastAPI permite que o processo rode em segundo plano, evitando timeouts de rede.

Processamento Sequencial: Ajuste de 3.5s de delay para respeitar as limitações de RPM da API, garantindo 0% de perda de dados.

Sanitização via Regex: Implementação de lógica para limpar o output da IA, garantindo que apenas JSON puro seja convertido em colunas de dados.

3. Regras de Auditoria (Motor de Anomalias)
O sistema valida automaticamente quatro pilares críticos:

Duplicidade: Identifica NFs com mesmo número e fornecedor.

Compliance Temporal: Alerta se a Data de Emissão for posterior à Data de Pagamento.

Autorização: Verifica se o aprovador consta na lista oficial da companhia.

Conflito de Status: Notas "Canceladas" com registro de pagamento ativo.

📁 Estrutura do Repositório
main.py: Ponto de entrada da API FastAPI.

processor.py: O "cérebro" do sistema (extração, limpeza e motor de regras).

resultados_bi.csv: Base de dados consolidada para o Power BI (Exigência do Briefing).

Dashboard_Auditoria_V1.pbix: Arquivo fonte do Power BI.

requirements.txt: Dependências para reprodução do ambiente.

🛠️ Como Executar
Clone o repositório.

Instale as dependências: pip install -r requirements.txt.

Configure sua chave da Groq no arquivo .env.

Inicie o servidor: uvicorn main:app.

Acesse http://127.0.0.1:8000/docs e execute o endpoint /executar-auditoria.

Desenvolvido por VictorPD974 como parte do desafio técnico da NLConsulting.
