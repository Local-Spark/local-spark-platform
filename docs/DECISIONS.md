# Decisões vigentes e pendências

Atualizado em **28/10/2026** após confirmação do proprietário nesta conversa.
Este registro reúne decisões de produto; implementação e contratos técnicos
ficam no [PROJECT](PROJECT.md), no [SDD](SDD.md) e nos [SDDs de fase](phases/README.md).
Uma decisão aprovada ainda não implementada deve aparecer com esse estado em
todos os consumidores. O texto antigo preservado em histórico não é requisito atual.

## Ordem de leitura e resolução de divergências

1. A decisão explícita mais recente do proprietário prevalece.
2. Este registro define o produto aceito; PROJECT resume o que existe e o que falta.
3. SDD geral e fase ativa definem contratos e critérios da próxima entrega.
4. Designs detalham alternativas e execução, respeitando os documentos acima.
5. Changelogs, evals, auditorias e snapshots são evidências datadas. Um estado
   antigo nesses registros não deve ser copiado como pendência ou regra vigente.

O código comprova o comportamento implementado, mas uma limitação atual não
substitui uma decisão de produto. Quando houver diferença, registrar a lacuna;
não afirmar que documentação, flag ou migration isoladas já a resolveram.

## Conceitos que não devem ser confundidos

- **Conta ativa:** conta não encerrada ou desativada. Pode existir com plano
  vencido; isso não dispensa identidade e membership válidas para consultar dados.
- **Plano ativo:** acesso financeiro vigente por assinatura ou patrocínio. C08
  separa revisão de uma criação admitida das novas criações e da publicação.
- **Arquivo preservado:** bytes e proveniência necessários à revisão. Não
  equivale a uma URL pública permanente, fato atualizado ou publicação aprovada.
- **Aceite de IA:** decisão contratual única. Direitos sobre cada material,
  comprovação de canal e aprovação de uma peça têm finalidades diferentes.

## Decisões confirmadas

| ID | Decisão de produto | Implementação local e limite |
| --- | --- | --- |
| C01 | IA para interpretação, texto, imagem e transcrição integra o serviço. Um único aceite explícito por negócio em Plano e acesso, antes do checkout; contas existentes aceitam a versão uma vez. | GET/POST versionado com hash, ator, data e auditoria; web sem permissões por fornecedor. Credenciais, orçamento e plano continuam internos. Registros antigos não são reescritos; geração visual real segue pendente. |
| C02 | Cada negócio tem conta de cliente e organização próprias, com cobrança e aceite próprios. | Onboarding cria organização/negócio; API e migration 0057 garantem no máximo um negócio por organização. Cobrança continua por organização. Memberships/seleção legadas e staff são preservados. |
| C03 | Um número de cliente WhatsApp ativo por negócio na primeira versão. | Vínculo único local. Múltiplos números e sua experiência ficam para evolução posterior. |
| C04 | Envios WhatsApp associados ao negócio são preservados sem expiração automática e não oferecem exclusão pelo histórico, para texto, imagem, áudio e vídeo. | Migration 0058 e leitores adaptados; API recusa exclusão. Eventos técnicos não atribuídos e uploads órfãos têm limpeza própria. Preservação não cria automaticamente memória pesquisável ou produto confirmado. |
| C05 | Trocar de número não interrompe o processamento de materiais já associados. A futura prévia e aprovação seguem para o número ativo novo. | Processamento e entrega simulada adaptados. Envio real de candidata WhatsApp pendente. Mensagens ainda não associadas não ganham origem retroativa por suposição. |
| C06 | Alterar kit, foto do acervo ou contexto durante uma criação aguarda os processos iniciados; cancela a fila ainda não iniciada e bloqueia novas admissões até aplicar a mudança. | Parcial no modo simulado: contexto, catálogo, confirmação de kit e fotos. Cobertura de todos os escritores, recuperação e integração real ainda faltam. |
| C07 | A prévia anterior à alteração continua disponível para revisão e deve ser identificada como anterior à mudança. | Há provas e campos no fluxo simulado. Preservar para revisão não confirma fatos vencidos, direitos ou aprovação de publicação. |
| C08 | Se o plano vencer durante uma criação já iniciada, concluir e permitir revisar a prévia privada; bloquear novas criações e publicação até renovar. | **Aprovado em 28/10, ainda não implementado de ponta a ponta.** O código atual revalida acesso durante geração, conclusão e leitura. Alterar esses caminhos junto com testes e tratamento de incerteza. Perda de membership não é vencimento do plano. |
| C09 | Preservar as prévias geradas sem expiração automática enquanto a conta estiver ativa. | **Aprovado em 28/10, ainda não implementado.** Propostas/prévias e limpeza ainda usam `expires_at`; preservar também a proveniência necessária à revisão. A migration 0058 não cobre prévias. URL assinada, validade factual e janela de aprovação continuam prazos diferentes. |
| C10 | Se quem iniciou uma alteração perder acesso, somente a equipe da plataforma pode resolver a pendência, com ação registrada. | **Aprovado em 28/10, ainda não implementado.** Não transferir a autoria para outro proprietário nem simular sua identidade. Criar recuperação de suporte restrita e auditada; staff não recebe acesso geral a mídia privada. |
| C11 | Publicação exige aprovação explícita da versão, arquivo/hash, legenda, destino e horário aplicáveis. | Revisão/publicação simuladas locais. Escolher kit, confirmar fato, aceitar o serviço ou permanecer em silêncio não aprova publicação. Meta/Instagram reais pendentes. |
| C12 | Foto e story são os formatos da oferta inicial. Vídeo e suas franquias/preço serão definidos depois; avatar/voz sintética ficam após o primeiro piloto comercial. | Regra inicial de formatos no código; não há franquia comercial final nem qualidade homologada. R$ 99/mês e teto total de R$ 50/cliente/mês orientam medição. |
| C13 | Provar a primeira peça personalizada antes de ampliar nichos; fechar BL04, depois a jornada/ajuste/proatividade BL05. | BL01/BL02 e BL03.1/BL03.2 locais; BL04 em implementação. BL03.3, BL06, pesquisa ampla, avatar e expansão multicanal têm etapas próprias. |

## Perguntas resolvidas nesta revisão

| Referência da pergunta | Resolução |
| --- | --- |
| P01 — plano vencido durante criação | Respondida pelo proprietário; aplicar C08 na implementação futura. |
| P02 — prazo das prévias | Respondida pelo proprietário; aplicar C09. |
| P04 — autor sem acesso com alteração pendente | Respondida pelo proprietário; aplicar C10. |

Não reapresentar essas perguntas como dúvida de produto. Falta implementar e
validar o comportamento aceito; isso não autoriza remover verificações de
identidade, direitos, assinatura, orçamento ou versão sem uma solução equivalente.

## Pendências delimitadas

| ID | Tema | Tratamento e momento |
| --- | --- | --- |
| P03 | Prazo de exclusão dos envios e prévias após encerramento da conta. | O proprietário decidiu **deixar pendente da fase de encerramento** e não implementar exclusão automática nesta etapa. Não escolher prazo ou prometer retenção pós-encerramento. Não bloqueia a BL04 para conta ativa. |
| P05 | Franquias, revisões, preço/volume de vídeo, cadência e custo comercial. | Definir com qualidade e custo por peça aceita medidos em BL04.3/F07; não fixar números por inferência ou com base em uma chamada isolada. |
| P06 | Recuperação da organização legada sem negócio. | Lacuna de implementação/UX: definir percurso que preserve organização, auditoria e histórico financeiro, sem loop entre onboarding e seleção. Não autoriza excluir ou atribuir dados automaticamente. |

Contratos comerciais definitivos, homologação Meta, staging e recuperação
operacional são entregas de prontidão, não prova já obtida nem motivo para
pedir outra autorização individual de IA ao cliente.

## Próxima entrega após a revisão documental

Detalhar e implementar, em fatias revisáveis, C08/C09/C10 e a coordenação de
fontes/orçamento BL04.2 usando o aceite único C01. Começar com provedor simulado,
PostgreSQL/RLS e Temporal reais. Só conectar o provedor visual após demonstrar
concorrência, recuperação, orçamento e ausência de submissão duplicada.

Esta revisão **altera somente documentação**. Nenhum prazo, job de limpeza,
política de acesso, role, fornecedor ou banco é alterado por este arquivo.
