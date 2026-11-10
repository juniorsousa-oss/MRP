# SETTA — Envio diário de excedentes de S.C. e P.C.

## Objetivo

Enviar para Suprimentos, diariamente às **08h30 (America/Sao_Paulo)**,
uma planilha Excel de **sugestões de cancelamento**, gerada pelo
`mrp_excedentes.py`. A recomendação não altera pedidos no ERP.

O Excel terá duas abas independentes:

- `Solicitações SC` — um produto + número de S.C. por linha.
- `Pedidos PC` — um produto + número de P.C. por linha.

As colunas são: Código, Descrição, Nº S.C./Nº P.C., **Qtd. Cancelar**,
Semana prevista, Prioridade e Cancelamento (TOTAL/PARCIAL).
Não são mostradas quantidades a manter, nem números agregados de
documentos. A prioridade usa o **início da semana prevista**, não o
dia exato de entrega, pois a base disponível não possui tal precisão.
O motor já preserva quantidades necessárias e descarta o tipo II.

## Segurança dos dados e pré-condições

O script `mrp_email_excedentes.py` lê o **último snapshot oficial**
do MRP no Supabase (colunas compactadas) e metadados das bases tratadas.
Ele só pode gerar recomendações se:

1. O snapshot MRP tiver sido gerado **no mesmo dia local**.
2. Nenhuma base tratada tiver sido atualizada após a criação do snapshot.
3. As quatro versões de entradas registradas no MRP consolidado
   coincidirem com as versões atuais da Central.
4. Houver MRP, compras e projeção com campos essenciais.
5. Houver quantidade cancelável realmente segura segundo o motor atual.
6. A planilha gerada tiver tamanho máximo de 6 MB.

Sem itens canceláveis, não envia e-mail vazio. Se o snapshot estiver
desatualizado, **não envia** e a execução acusa o motivo no GitHub.
Isso evita recomendar cancelamentos baseados em dados anteriores.

**Dependência operacional importante:** a publicação do MRP final no
histórico de snapshots ainda depende da execução do MRP. O monitor de
dependências não faz esse processamento. A rotina diária de e-mails
não corrige esse problema e não dispara com um snapshot antigo.
Para garantir envios em todos os dias, é necessário que um snapshot
válido seja publicado antes das 08h30, inclusive após a coleta MES
e o processamento do Conversor.

## Controle de duplicidade

Tabela protegida: `public.mrp_excedentes_envios` (RLS habilitado,
sem SELECT/INSERT/UPDATE para `anon` ou `authenticated`).
Chave primária `data_referencia`: impede dois e-mails no mesmo dia.

Antes de chamar o serviço, cria reserva `RESERVADO`. Se o transporte
confirmar (SMTP ou HTTP 200 do fluxo), marca `ACEITO_PELO_TRANSPORTE`.
Caso o retorno seja incerto, marca `VERIFICAR_FALHA`; **não reenvia
automaticamente** para evitar duplicidades. Administrador deve verificar
o histórico da caixa/fluxo antes de qualquer reprocessamento de envio.
O sistema registra hash do arquivo e dos destinatários, não guarda
códigos, descrições ou endereços de e-mail nessa tabela.

Confirmação do transporte não prova leitura pelo destinatário.

## Agendamento

Arquivo `.github/workflows/mrp-email-excedentes-diario.yml`:

- Agendamento GitHub Actions: `30 11 * * *` (11h30 UTC = 8h30 BRT).
- Pode iniciar com atraso conforme a fila de execução do GitHub.
- `workflow_dispatch`: oferece simulação (dry run) como padrão.
- O envio agendado **só é executado** quando a variável de repositório
  `MRP_CANCEL_SEND_ENABLED` está exatamente `true`.

## Configuração do GitHub Actions

No repositório `juniorsousa-oss/MRP`, Settings → Secrets and variables
→ Actions:

**Secrets obrigatórios:**

- `MRP_EMAIL_SUPABASE_KEY`: credencial *somente servidor*, autorizada a
  consultar snapshots e bases e registrar envios. Não colocar no
  Streamlit ou em código público. Serviço de menor privilégio possível;
  caso use `service_role`, restringir seu acesso ao GitHub Actions.
- `MRP_CANCEL_EMAIL_TO`: e-mail corporativo confirmado de Suprimentos.
- `MRP_CANCEL_EMAIL_CC`: opcional, endereços corporativos separados
  por vírgulas ou ponto e vírgula.

**Variables obrigatórias:**

- `MRP_CANCEL_DELIVERY_MODE`: `power_automate` (preferencial, usando
  Outlook corporativo aprovado pela TI) ou `smtp`.
- `MRP_CANCEL_SEND_ENABLED`: manter `false` até validar o destinatário,
  o fluxo, o anexo e um teste controlado. Só então usar `true`.

**Envio Power Automate:**

Secret `MRP_CANCEL_EMAIL_WORKFLOW_URL`: URL HTTPS de um **novo fluxo
corporativo exclusivo para compras** com gatilho
`When a Teams webhook request is received (V2)`, no padrão já
validado nos fluxos SETTA de NFs vencidas e de separação/entrega.
Não reutilizar a URL de Solicitações Avulsas.

Os fluxos existentes respondem **HTTP 202** ao aceitar o POST.
O emissor aceita HTTP 200 ou 202, mas **isso não comprova que o Outlook
enviou**; confirmar o histórico de execução e a caixa destinatária.
Se o gatilho estiver limitado a usuários do locatário, as chamadas
sem token Microsoft poderão receber HTTP 401/403. Replicar a política
**aprovada** do fluxo funcional; não remover autenticação só para contornar
falhas de chamada.

Payload:

```json
{
  "type": "message",
  "attachments": [],
  "tipo": "CANCELAMENTO_COMPRAS",
  "para": "compras@gruposetta.com",
  "copia": [],
  "assunto": "SETTA | Análise de cancelamentos S.C. e P.C. | 10/11/2026",
  "texto": "Mensagem com resumo dos documentos, sem comando de cancelamento.",
  "html": "<html><body>Resumo estruturado</body></html>",
  "nome_anexo": "SETTA_Cancelamentos_SC_PC_20261110.xlsx",
  "anexo_base64": "CONTEUDO_BASE64_AQUI"
}
```

No **Enviar um email (V2)**, reutilizar o padrão validado:
- **Para:** `triggerBody()?['para']`
- **Cc:** `join(coalesce(triggerBody()?['copia'],json('[]')),';')`
- **Assunto:** `triggerBody()?['assunto']`
- **Corpo:** `triggerBody()?['html']`
- **Nome do anexo:** `triggerBody()?['nome_anexo']`
- **Conteúdo do anexo:** `base64ToBinary(triggerBody()?['anexo_base64'])`

O **anexo** diferencia esse fluxo dos alertas de NFs e entregas.
Webhooks destinados a mensagens do Teams possuem limitações de formato
e tamanho (a documentação menciona limite de **28 KB por mensagem**).
**Antes de produção**, testar planilhas reais de diferentes tamanhos;
um teste curto com arquivo pequeno não valida anexos maiores. Se exceder
o limite da plataforma, usar armazenamento corporativo protegido para
entregar o arquivo ao Outlook, mantendo o webhook apenas como gatilho.

Configurar controle de acesso e **Secure Inputs/Outputs** para não
expor documentos nem URL assinada nos logs. Rejeitar chamadas fora
da autenticação aprovada pela TI.

**Envio SMTP corporativo (alternativa):**

Secrets `MRP_CANCEL_SMTP_HOST`, `MRP_CANCEL_SMTP_USER`,
`MRP_CANCEL_SMTP_PASSWORD`, `MRP_CANCEL_EMAIL_FROM`;
variable `MRP_CANCEL_SMTP_PORT` = `587` (STARTTLS) ou `465` (SSL).
Usar somente credencial autorizada pelo administrador de e-mail.

Por padrão, apenas e-mails `@gruposetta.com` são aceitos como
destinatários. Alteração de domínios somente com aprovação explícita.

## Homologação controlada

1. Confirmar com Suprimentos o endereço que receberá a planilha.
2. Confirmar com a TI o envio corporativo (SMTP ou Power Automate).
3. Configurar as credenciais **somente no GitHub**.
4. Manter `MRP_CANCEL_SEND_ENABLED=false`.
5. Publicar um MRP oficial atualizado depois da última fonte tratada.
6. No Actions, abrir `SETTA MRP | E-mail de cancelamentos S.C. e P.C.`
   e executar manualmente com `dry_run=true`: valida dados e contagens
   sem enviar ou registrar reserva.
7. Liberar um destinatário piloto autorizado. Alterar
   `MRP_CANCEL_SEND_ENABLED=true` apenas depois de verificar o anexo
   e o recebimento no Outlook.
8. Conferir o primeiro envio em `mrp_excedentes_envios`
   e o histórico de execução no serviço de e-mail.

## Observação

O número total de peças de produtos diferentes **não** é agregado:
somente são informadas as quantidades por material e documento, evitando
somar unidades de natureza diferente. A comunicação é uma solicitação
de *avaliação de cancelamento*, não ordem de cancelamento automático.
