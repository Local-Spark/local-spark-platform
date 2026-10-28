# Meu Braço Direito — contexto vigente

Atualizado em **28/10/2026**. Estado do código local conferido nesta revisão;
nenhum serviço ou banco foi alterado. Decisões de produto e pendências ficam em
[DECISIONS](DECISIONS.md); contratos no [SDD](SDD.md); sequência no
[índice de fases](phases/README.md) e na [trilha BL](phases/BL-brand-library.md).
As versões anteriores foram [preservadas integralmente](history/2026-10-28-pre-documentation-reconciliation/index.md).
Uma entrega local não equivale a uma capacidade comercial homologada.

## Produto

Pequenos negócios enviam texto, foto, áudio ou vídeo pelo WhatsApp. A plataforma
usa os fatos confirmados, o kit e os materiais do próprio negócio para preparar
conteúdo, pedir aprovação específica, publicar nos canais habilitados e mostrar
resultados observáveis. Também deverá propor conteúdo sem envio novo, dentro de
uma cadência aceita e da franquia; essa proatividade ainda não está implementada.
O cliente não precisa escrever prompt ou operar um editor.

A web complementa identidade, contratação, canal, fatos, acervo, kits e revisão.
A vitrine pública usa exemplos fictícios já produzidos; uma visita não chama IA
nem conecta contas sociais. A escolha do kit não aprova publicação.

Uma conta de cliente e uma organização por negócio, com cobrança e aceite
próprios. O runtime garante no máximo um negócio por organização; memberships e
seleção legadas são preservadas. Staff é independente de cadastro de negócio.
Um número WhatsApp de cliente ativo por negócio na primeira versão.

## Decisões atuais sobre IA, materiais e prévias

- **Aceite único entregue localmente (C01):** em Plano e acesso, antes do
  checkout, o cliente concorda uma vez com IA para interpretação, texto, imagem
  e transcrição. Contas existentes recebem o mesmo passo. Não há permissões por
  fornecedor em WhatsApp ou Informações e preferências. Credenciais, plano,
  orçamento e versões são controles internos. Aceitar não confirma pagamento.
- **Envios WhatsApp preservados (C04/C05):** materiais associados ficam sem
  expiração automática; histórico e API não oferecem sua exclusão. A troca de
  número não interrompe material já associado; a entrega simulada usa o novo
  vínculo. Envio real de candidata ainda falta. Eventos técnicos não atribuídos
  e uploads órfãos têm limpeza separada.
- **Acervo:** fotos desatualizadas de item/espaço podem ser removidas. A cópia
  explícita de uma foto do WhatsApp cria outro objeto; preservar o envio não
  cria uma ficha de produto, fato confirmado, memória pesquisável ou skill.
- **Mudanças durante criação (C06/C07):** aguardar processos iniciados, cancelar
  a fila que não começou e impedir novos inícios até aplicar a mudança de kit,
  foto ou contexto. A prévia anterior continua para revisão, identificada como
  anterior à alteração. Implementação parcial no modo simulado.
- **Novas decisões aprovadas, ainda não implementadas (C08/C09/C10):** concluir
  criação já iniciada se o plano vencer e permitir revisar sua prévia; bloquear
  novas criações e publicação até renovar. Preservar prévias sem expiração
  automática enquanto a conta estiver ativa. Só a equipe da plataforma pode
  resolver uma pendência cujo autor perdeu acesso, com ação registrada.

O código ainda usa prazos de propostas/prévias e verifica plano na conclusão e
na leitura. C08/C09 exigem adaptar esses caminhos e a limpeza, preservando a
proveniência. A migration 0058 cobre materiais WhatsApp, não prévias. URL
assinada de arquivo, validade de fato e prazo de aprovação são conceitos
separados da preservação do arquivo.

O prazo de exclusão após encerramento da conta foi explicitamente adiado para
essa fase; não implementar exclusão automática nesta etapa (P03). Vencimento do
plano não equivale a encerrar conta nem a perder membership.

## Estado implementado e limites

| Área | Existe localmente | Falta demonstrar ou entregar |
| --- | --- | --- |
| Fundação e identidade | FastAPI, PostgreSQL/RLS, auth própria, sessões, recuperação, e-mail HTML, onboarding, MFA/convites de staff | Homologação de operação e segurança em staging/produção. |
| Contratação | Stripe sandbox, webhook/jobs/reconciliação, patrocínio e aceite único versionado por negócio | Contratos comerciais definitivos, franquias e cenários externos restantes. Cadastro e retorno de checkout não ativam plano. |
| WhatsApp | Inbox assinada/cifrada, vínculo, correlação, processamento, transcrição configurável e preservação de materiais | Meta oficial, envio real de candidata e conversa completa ainda não homologados. |
| Contexto e texto | Fatos/preferências versionados, propostas/roteiros, adapter editorial, reservas/tokens e projeção administrativa restrita | Qualidade comercial, conversa com memória, pesquisa ampla e skills executáveis. |
| BL01/BL02 | Vitrine fictícia de cafeteria, escolha e edição guiada de kit, logo privado, rascunho, confirmação e histórico | Kit `public_demo` não tem liberação comercial; produção real ainda não aplica o kit. |
| BL03.1/BL03.2 | Cadastro manual de produtos/serviços/promoções e fotos privadas de item/espaço | Importação de cardápio é BL03.3 futura; contexto visual real integrado ainda falta. |
| BL04 | Retrieval do acervo e Jev opcionais no worker de desenvolvimento/teste; briefing, fontes, adapter de imagem, ledger, acabamento e prévia simulada | Coordenação completa, C08/C09/C10 e conexão do provedor real; qualidade/custo por peça aceita. |
| F04/F06 | Prévias técnicas estáticas/vídeo, candidata, revisão e publicação simulada com versão/hash | Ajuste não regenera automaticamente; candidata WhatsApp e Instagram reais pendentes. |
| F08 | Compose, CI e workflow manual de deploy preparados | AWS/staging, recuperação coordenada, observabilidade operacional e capacidade não homologadas. |

Os ensaios em [evals](evals/) são evidências datadas, não features ou aceites
comerciais. As imagens reais de IA de 27/10 e 28/10 foram geradas em ensaios
isolados, fora do worker do cliente. Não comprovam fidelidade, margem ou custo
mensal. Consultar perfil público não concede direitos sobre o material observado.

## Jornada web vigente

| Área | Finalidade |
| --- | --- |
| Início | Resumo e orientações com estados reais do negócio. |
| Plano e acesso | Aceite único do serviço, assinatura, patrocínio e situação financeira. |
| WhatsApp | Telefone/SMS, vínculo e histórico preservado de envios como consulta secundária. |
| Sobre meu negócio | Informações e preferências, Produtos e serviços e Meu espaço. |
| Conteúdos | Acompanhar propostas/prévias e decisões disponíveis; simulações identificadas. |
| Kits visuais | Explorar, escolher e editar a direção visual. |

Organização/negócio ativos são compartilhados em memória; a autorização é
verificada na API/RLS. `/app/content` é a rota vigente; `/app/ideas` redireciona
para ela e `/app/guide` para Início. `/app/phone` é utilitária do WhatsApp.
`/app/editorial-lab` mantém os controles técnicos só no build DEV. O valor
histórico `posts_per_week` é preservado, sem campo manual de frequência.

## Próxima entrega e sequência

1. **BL04.2:** adaptar a execução e a preservação às decisões C08/C09/C10;
   completar a coordenação de fontes, plano/acesso, orçamento e recuperação com
   as roles existentes. Demonstrar o percurso com provedor simulado antes de
   ligar dispatcher, workflow e provedor real.
2. **BL04.3:** produzir post/story pelo produto, revisar com titular e fontes
   consentidas, medir fidelidade, texto, legibilidade, rejeições e custo por
   peça aceita, incluindo refações.
3. **BL05:** fechar jornada local de mensagem → prévia → ajuste → aprovação →
   publicação simulada, incluindo iniciativa em dia sem mensagem e pausa.
4. **Piloto:** homologar Meta/Instagram, aplicar franquias F07 e operar staging,
   observabilidade e recuperação F08. A Meta pendente não impede testes locais.
5. **Expansão:** BL03.3 importa cardápio como rascunho; BL06 amplia kits/nichos e
   catálogo/CDN. Pesquisa ampla, avatar/voz e multicanal seguem fases próprias.

Foto e story são os formatos iniciais; vídeo e suas franquias/preço permanecem
para definição posterior. R$ 99/mês e teto total de R$ 50/cliente/mês orientam
medição, sem margem comprovada. Avatar/voz sintética ficam após o primeiro
piloto. HyperFrames/Remotion e outros estudos são candidatos, não integrações.
A aquisição por vídeos longos dos três sócios segue estratégia comercial; a
meta de 200 mil clientes orienta capacidade gradual, sem comprovação atual.

## Arquitetura, validação e continuidade

Backend Python modular, FastAPI, PostgreSQL compartilhado/RLS, Temporal e S3;
React em `local-spark-web`. API, dispatchers e workers escalam separadamente.
Redis não é dependência ativa; não adicionar outro runner para os processos de
Temporal. Sem rede sob row lock e sem IO em workflows determinísticos.

Negócios/kits usam auditoria transacional; relay, tabelas e handlers antigos
ficam só para compatibilidade, sem novos recibos de CRUD. Auth é própria;
access token em memória e refresh HttpOnly. Staff/MFA não equivale a owner.
Os modelos atuais são configuração, não escolha comercial definitiva. Contexto
versionado não treina automaticamente modelos e tokens não são COGS monetário.

Última validação de aplicação: 1.583 testes backend e complemento de 24 testes
com sete casos novos; cobertura final de 100% de linhas/branches. Web: 360 testes,
100% nos quatro critérios, build e três jornadas Chromium. Evidências datadas
no [CHANGELOG](CHANGELOG.md). Esta revisão documental valida links, referências,
integridade dos snapshots e coerência com o código; não reexecuta chamadas pagas
ou suítes de aplicação sem mudança de comportamento.

Diretórios/remotos continuam `local-spark-platform` e `local-spark-web`, com marca
Meu Braço Direito, prefixo `MEU_BRACO_DIREITO_` e bancos renomeados conforme
[registro](product-rename.md). Operação em [operations](operations.md).
Atualizar PROJECT, SDD, fase e CHANGELOG em cada entrega; decisões novas entram
em [DECISIONS](DECISIONS.md), sem recolocar perguntas já respondidas na fila.
