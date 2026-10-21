# Decisão — contexto do negócio, geração e custo por peça

Data: 21/10/2026. Status: especificação aceita para F02–F07; nada deste documento
está implementado por sua publicação. Origem: avaliação crítica de
`../Local-Spark-Analise-Melhorias-IA-Skills-2026-10-21.md`.

## Avaliação das recomendações recebidas

| Proposta | Decisão | Motivo |
| --- | --- | --- |
| Contexto compacto por negócio e enriquecimento progressivo | Acatar com ajustes | Melhor primeira proposta sem cadastro extenso; medir economia, separar fatos de preferências e hipóteses. |
| Atualizar automaticamente a partir de toda aprovação | Não acatar assim | Aprovação de peça é sinal de preferência, não autenticação de preço, horário ou promessa. |
| Edição/reset pelo cliente só após o MVP | Antecipar para F03 | O dono precisa corrigir o que a IA usa desde o início; rollback auditado é parte da confiança. |
| Adapter único com uma classe por marca | Acatar por capacidade | Texto, cena, avatar e render têm contratos, riscos e custos diferentes. |
| HeyGen primário; Kling/Veo/Runway superiores | Manter como candidatos | Afirmações de liderança/qualidade e acesso comercial exigem corpus, contrato, custo e smoke próprios. |
| FFmpeg como base de custo baixo | Acatar nas receitas compatíveis | Reuso de fotos/vídeos reais e templates previsíveis pode reduzir gasto sem prometer que toda peça dispensa IA. |
| Ledger mínimo junto à primeira geração paga | Acatar e antecipar se necessário | Pesquisa/modelos pagos de F03 também precisam de reserva antes da chamada. |
| Shadow eval contínuo | Limitar | Amostra consentida, teto financeiro e direitos de uso; não duplicar custo da base inteira. |
| Limite fixo de 2–4k tokens e economia garantida | Tratar como hipótese | Medir por modelo, tarefa e qualidade antes de fixar política. |
| “200 mil clientes factível” por arquitetura | Não assumir | Capacidade depende de custos, quota externa, carga, operação e retenção demonstrados em F08. |

## Decisões de produto

O cadastro F01 continua curto. F02 recolhe preferências opcionais ao longo da
conversa (tom, produtos, oferta, frequência) sem bloquear a entrada; medir abandono
antes de acrescentar campos à tela inicial. Chamar o conjunto persistido de
**contexto do negócio** (`BusinessContext`), não de skill executável: contém dados
e preferências do cliente, nunca código, ferramentas ou instruções de sistema.

F03 entrega a primeira versão compacta e inspecionável desse contexto. Separar:

- Fatos autorizados: valor, fonte/ator, data de confirmação, validade, escopo e
  estado (`proposed`, `confirmed`, `expired`, `revoked`). Preço, horário, endereço e
  promoção precisam de confirmação explícita do proprietário ou fonte confiável
  compatível; aprovação de uma peça não valida automaticamente cada fato dela.
- Preferências explícitas: tom, formato, expressões a evitar, frequência e orçamento,
  com autor e versão. Correção clara do cliente pode atualizar esse grupo após
  interpretação confirmada; mensagem ambígua produz proposta de alteração.
- Padrões observados: hipóteses provenientes de aprovações/rejeições e, mais tarde,
  métricas próprias. Não são fatos comerciais nem promessa de aumento de vendas.

Cada versão é imutável, isolada por `tenant_id` **e** `business_id` com RLS, tem
`version`, `schema_version`, fonte de alteração, hash e referência à versão anterior.
Atualização usa identidade de evento, compare-and-swap e auditoria/outbox na mesma
transação; replay e duas aprovações concorrentes não perdem alterações. O snapshot
usado na geração fica fixado na `content_version` para permitir reprodução. O
proprietário pode ver, corrigir, rejeitar e restaurar uma versão anterior; restauração
cria nova versão auditada. Exclusão/revogação deve alcançar snapshots e derivados
conforme política de retenção. Mídia, transcrições e fontes longas ficam no storage
privado e são carregadas sob demanda, com permissão e prazo válidos.

O orçamento de contexto é configurável e medido em tokens reais do modelo escolhido;
2–4 mil tokens da análise são hipótese de benchmark, não limite universal. Resumo
não pode converter hipótese em fato nem remover restrição. Comparar tokens, custo,
qualidade e taxa de correção contra baseline sem contexto compacto antes de afirmar
economia. Conteúdo de WhatsApp, web e concorrentes é entrada não confiável: não
obedece instruções embutidas, não atravessa tenant e não vira contexto confirmado
sem autorização. Edição web do contexto entra com o MVP de F03; comandos WhatsApp
equivalentes podem ser liberados em fatia posterior com confirmação de identidade.

## Geração e seleção de fornecedor

F04 define portas por **capacidade** (`TextGeneration`, `ImageGeneration`,
`Speech`, `SceneVideo`, `AvatarVideo`, `MediaRender`), contrato de entrada/saída,
idempotência, operação externa, custo e status `UNKNOWN`. FFmpeg é renderizador
determinístico para receitas que o permitam, não fallback universal nem substituto
de avatar contratado. F05 implementa as capacidades de avatar/cena autorizadas.
Temporal coordena activities, mas seleção de receita/provedor e direitos de gasto
ficam em serviço de domínio; a decisão, a versão de configuração e o custo máximo
são persistidos antes do submit. Replanejar após erro requer nova autorização quando
muda formato, identidade, preço ou franquia. Timeout após possível submit não
dispara outro fornecedor até reconciliação. Filas de tasks/pools separam IO e mídia;
GPU só se uma receita realmente exigir e houver medição de capacidade/custo.

HeyGen, Runway, Kling e Veo são **candidatos por capacidade**, não primários
aprovados nem compromisso de preço/qualidade. Verificar versão vigente, API para
conta comercial, consentimento, direitos de uso/revenda, retenção, exclusão,
limites, PT-BR, custo por peça, latência e callbacks em spike com dados consentidos.
Em especial, não presumir que ferramenta de edição de consumidor ofereça API
adequada para uma plataforma multi-tenant. Versões de modelos e preços podem mudar;
ficha de integração e benchmark datados são gate de ativação. Documentação oficial
consultada: [HeyGen Developers](https://developers.heygen.com/),
[Kling API](https://kling.ai/dev/api),
[Veo na Gemini API](https://ai.google.dev/gemini-api/docs/veo).

Avaliação paralela de modelo é **amostra controlada**, desativada por padrão, com
direitos de uso dos materiais, teto de custo, retenção e descarte. Não gerar duas
peças pagas para todo cliente. Medir qualidade com rubrica humana (produto real,
nome/preço, legibilidade, voz/sotaque, identidade, artefatos), latência, rejeição,
retrabalho e custo; métricas sociais só quando comparáveis. Mudança de fornecedor
passa por decisão versionada e rollout por coorte, sem fallback silencioso.

## Franquia, COGS e observabilidade

O ledger mínimo nasce **antes da primeira chamada paga**: em F03 se pesquisa/modelo
pago estiver habilitado; obrigatoriamente antes de produção F04/F05. Separar direito
comercial (franquia do plano) de custo real/estimado do fornecedor. Reservar de forma
atômica por `operation_id` e tenant, com teto por peça/dia/período; liquidar pelo
resultado conhecido, liberar só o não consumido e reconciliar `UNKNOWN`. Retry,
callback duplicado e troca de worker não criam nova reserva ou custo lógico.
F07 acrescenta planos, recargas, relatórios financeiros e reconciliação completa;
não é a primeira implementação do controle de gasto.

Métricas por operação incluem tokens de entrada/saída, unidades cobradas, estimativa
e custo faturado, duração, fornecedor/modelo/configuração, rejeição, retrabalho e
falha, sem prompt bruto/PII nos logs. Agregados por tenant para quota e suporte;
telemetria global usa acesso restrito e não expõe conteúdo. Relatório semanal usa
origem, período, última coleta e lacunas; alcance não prova faturamento.

## Sequência de entrega

| Fase | Entrega verificável |
| --- | --- |
| F01 | Manter onboarding leve; nenhum novo campo obrigatório retroativo. |
| F02 | Capturar material/preferências opcionais, consentimento, autoria e proveniência. |
| F03 | `BusinessContext` versionado, edição/revisão pelo dono, montagem de contexto mínimo, limite e ledger antes de pesquisa paga; eval de texto/decisão. |
| F04 | Portas por capacidade, FFmpeg, reserva/custo por peça, prévias e avaliação controlada de imagem/edição. |
| F05 | Spikes e adapters de avatar/cena/voz selecionados por evidência, consentimento e custo. |
| F06 | Aprovação versionada e correção explícita alimentam propostas de atualização do contexto; observar publicação/insights. |
| F07 | Evoluir franquias, COGS, relatórios, aprendizado por métricas próprias e controles comerciais. |
| F08 | Testar carga/coortes, limites externos, isolamento e recuperação em escala. |

Não adotamos a tabela SQL da análise como migration pronta: falta separar fatos,
preferências e hipóteses, proveniência, concorrência e ciclo de exclusão. Não
prometemos redução de tokens, liderança de fornecedor ou capacidade para 200 mil
clientes sem benchmark e teste de carga.
