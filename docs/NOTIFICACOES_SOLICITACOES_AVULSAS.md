# Integração das notificações — Solicitações Avulsas do MRP SETTA

## Situação e fluxo de produção

O MRP já possui a lógica de notificações, sem necessidade de alterar o fluxo de
estoque ou a situação dos pedidos:

1. **CONSULTA registra nova S.A.** — Edge Function `mrp-avulsas-api`, ação
   `create_batch`, publica um cartão no grupo de Teams do almoxarifado via
   `MRP_TEAMS_WORKFLOW_URL`. O status fica em `mrp_avulsas_pedidos.teams_status`.
2. **OPERADOR confirma SEPARAÇÃO** — RPC grava a separação e cria evento
   `mrp_avulsas_email_eventos` de tipo `SEPARADA`; a função solicita e-mail
   ao solicitante `@gruposetta.com`, com cópia para `junior.sousa@gruposetta.com`, e registra status.
3. **OPERADOR confirma ENTREGA** — RPC registra entrega e cria evento
   `ENTREGUE`; a função prepara e-mail para
   `almoxarifado.energy@gruposetta.com`, com cópia ao solicitante,
   `junior.sousa@gruposetta.com` e `jessica.samara@gruposetta.com`. Assunto:
   `ENTREGA DE PEÇAS AVULSAS - <FINALIDADE>`.
   A mensagem inclui materiais, quantidade, último preço do CADASTROS, totais
   e OP(s), CR/aprovador ou filial conforme a finalidade.
4. **Falha de envio não desfaz a operação**. O operador ou ADMIN pode executar
   `email_retry` por pedido/evento. Evitar disparos automáticos de eventos
   antigos na ativação do serviço.

## O que falta para a entrega de e-mails funcionar

Criar e autorizar um serviço de envio corporativo que aceite o payload da
Edge Function, por exemplo Power Automate com Outlook Microsoft 365, e cadastrar
o URL de entrada na secret de Supabase:

`MRP_EMAIL_WORKFLOW_URL`

**Nunca incluir o endereço completo do gatilho (com assinatura/segredo) no
GitHub, em screenshots ou em conversas.** Configurar somente no servidor:
Supabase -> projeto MRP -> Edge Functions -> Secrets.

> Observação: novos gatilhos "Quando uma solicitação HTTP for recebida" do
> Power Automate podem exigir autenticação Microsoft Entra ID por padrão.
> A integração atual envia JSON por HTTPS para a URL configurada e ainda não
> inclui um bearer token Entra. Não basta salvar a URL de um fluxo que exija
> OAuth: o emissor precisará de implementação de credenciais/aplicativo
> autorizados pela TI. Evitar usar o modo "Qualquer pessoa" sem aprovação
> corporativa de segurança, pois o URL assinado passa a ser credencial sensível.

### Payload HTTPS POST enviado pelo MRP

```json
{
  "notificacao_id": 1234,
  "pedido_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "tipo": "SEPARADA",
  "para": "nome.sobrenome@gruposetta.com",
  "copia": ["junior.sousa@gruposetta.com"],
  "assunto": "MRP SETTA - MATERIAIS SEPARADOS - SA-000004",
  "html": "<div>...mensagem em HTML...</div>",
  "texto": "Separação confirmada. ..."
}
```

Na entrega, `tipo` é `ENTREGUE`, `para` é
`almoxarifado.energy@gruposetta.com`, e `copia` contém o e-mail do
solicitante, `junior.sousa@gruposetta.com` e
`jessica.samara@gruposetta.com` (sem duplicatas). Na separação, `copia`
contém somente `junior.sousa@gruposetta.com`, exceto quando ele já for o destinatário principal. O MRP produz o HTML e a tabela, não é necessário construir
layout do e-mail no Power Automate.

### Schema do corpo no Power Automate

```json
{
  "type": "object",
  "properties": {
    "notificacao_id": {"type": "integer"},
    "pedido_id": {"type": "string"},
    "tipo": {"type": "string", "enum": ["SEPARADA", "ENTREGUE"]},
    "para": {"type": "string"},
    "copia": {"type": "array", "items": {"type": "string"}},
    "assunto": {"type": "string"},
    "html": {"type": "string"},
    "texto": {"type": "string"}
  },
  "required": [
    "notificacao_id","pedido_id","tipo","para","copia","assunto","html","texto"
  ]
}
```

### Ações sugeridas no Microsoft Power Automate

1. Criar fluxo em nuvem com gatilho **When an HTTP request is received**.
   Confirmar licenciamento e configuração de autenticação com a TI.
2. Informar o schema acima no gatilho.
3. Adicionar ação **Office 365 Outlook — Send an email (V2)** usando uma
   conexão corporativa autorizada:
   - **To**: `triggerBody()?['para']`
   - **Cc**: `join(triggerBody()?['copia'], ';')`
   - **Subject**: `triggerBody()?['assunto']`
   - **Body (HTML)**: `triggerBody()?['html']`
4. Opcional mas recomendado: **Response (200)** após o Outlook aceitar o
   envio; retornar falha HTTP se não aceitou. Sem essa resposta final, o fluxo
   pode retornar `202` ao MRP antes de saber se o Outlook conseguiu enviar.
5. Salvar a URL HTTPS no Supabase sem copiá-la para repositórios ou chats.

Para conferir a existência da configuração, usar no MRP o perfil **ADMIN**,
**Solicitações Avulsas -> Administração · Notificações por e-mail ->
Verificar configuração de e-mail**. A resposta **CONFIGURADO** quer dizer
apenas que há um endpoint HTTPS, e **não comprova entrega na caixa postal**.

## Validação operacional segura

1. Criar ou usar fluxo de teste devidamente autorizado pela TI e enviar
   mensagem explicitamente marcada `TESTE - MRP SETTA` para uma caixa
   corporativa de teste. Não usar nenhuma das S.A.s antigas apenas para
   testar transporte, para evitar aviso de entrega duplicado.
2. Verificar **Histórico de execução** no Power Automate e a caixa de entrada.
3. Após homologação, habilitar o fluxo de produção e executar uma S.A.
   controlada: Teams após solicitação; solicitante após separação; gestão
   + cópia ao solicitante após entrega.
4. Conferir no banco `mrp_avulsas_email_eventos` o status de cada etapa;
   `ACEITO` significa aceitação pelo endpoint, não necessariamente
   recebimento final na caixa postal. Monitorar exceções do fluxo.
5. Idealmente incluir deduplicação pelo `notificacao_id` no receptor para
   evitar e-mails repetidos caso o cliente tenha que reenviar após timeout.

Referências:
- https://learn.microsoft.com/pt-br/power-automate/oauth-authentication
- https://learn.microsoft.com/en-us/connectors/office365/
- https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/use-secure-inputs-outputs-triggers
