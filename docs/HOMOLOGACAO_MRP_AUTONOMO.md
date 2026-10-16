# SETTA — Homologação do MRP autônomo

## Situação
O Conversor MRP já publica as quatro bases tratadas. O MRP final é publicado
pelo aplicativo Streamlit quando um administrador o executa. A automação
de publicação do MRP final **não foi habilitada**.

O monitor read-only já instalado em main identifica se o relatório MRP está
desatualizado em relação às cinco dependências. O código de cálculo sem
Streamlit e o comparador de snapshots desta branch são ferramentas de
homologação, não um worker de produção.

## Critérios para publicação futura

1. Capturar um conjunto **consistente** de entrada: versão de CADASTROS,
   versões de quatro bases tratadas, tratativas de projeto e de produto.
2. Consultar ambas as tabelas de tratativas
   (`mrp_project_treatments` e `mrp_project_product_treatments`) com
   credencial de serviço de leitura autorizada, **sem abrir o acesso público**
   a essas tabelas. Não incluir credenciais em repositório ou logs.
3. Rodar `calcular_mrp(...)` sem Streamlit e sem gravação, com todos os
   parâmetros obtidos do mesmo instantâneo lógico.
4. Confrontar as seis saídas (macro, projeção, demanda por projeto, lista de
   S.C., compras e fabricação) com um snapshot oficial salvo quando as
   **mesmas fontes e tratativas** estavam vigentes. Apenas comparar com o
   snapshot mais recente não garante equivalência se as fontes mudaram.
5. Executar os cenários de regressão: NORMAL, CANCELADO, SUSPENSO, RESIDUO,
   RESIDUO por produto, código do tipo II, OP duplicada e semanas.
6. Adicionar registro de execução, hash das fontes e tratativas, idempotência
   por versão, timeout, revalidação de versão antes da publicação e travamento
   contra jobs simultâneos. Falha ou divergência deve **interromper** a
   publicação mantendo o último MRP oficial válido.
7. Validar em homologação um caso de atualização do PMP e outro de atualização
   das planilhas brutas; verificar que o Conversor termina antes do MRP.
8. Somente então habilitar a gravação programática e o agendamento autônomo.

## Scripts de homologação

- `mrp_engine_extract.py`: montagem auditada do runtime produtivo.
- `mrp_engine_headless.py`: motor puro com tratativas injetadas, sem leitura de
  rede e sem gravar.
- `mrp_shadow_compare.py`: compara registros DataFrame com as seis seções de
  `mrp_snapshots`, inclusive os históricos compactados.
- `mrp_worker_estado.py`: diagnóstico read-only já utilizado pelo monitor.

## O que o usuário precisa fazer

Neste estágio, nada. Um Excel exportado da plataforma poderá ajudar na
homologação visual, mas **não é obrigatório como fonte primária**: o histórico
MRP já existe no Supabase. A comparação real ainda depende do acesso
controlado às tratativas e da coleta consistente das versões das fontes.
