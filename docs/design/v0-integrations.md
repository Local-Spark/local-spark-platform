# Integrações — estado local, homologação e candidatos

Reconciliado em **28/10/2026**. O [SDD](../SDD.md), a [fase ativa](../phases/BL04-context-and-ai-production.md)
e as [decisões](../DECISIONS.md) prevalecem. Fornecedores/endpoints/preços do
estudo original são referências datadas, precisam de verificação no spike;
não representam configuração contratada ou autorização contínua de gasto.

## Estado por capacidade

| Integração | Estado local | Gate restante |
| --- | --- | --- |
| Stripe | Checkout, webhook assinado, jobs Temporal e reconciliação; sandbox exercitada. | Cenários completos de sandbox, termos/franquia e staging/produção. |
| SMTP/Mailpit | E-mail HTML/texto e captura local. | Configuração e operação real. |
| Twilio Verify | Adapter de verificação e SMS padrão. | Credenciais/homologação por ambiente. |
| Meta WhatsApp | Inbox, assinatura/cifra, vínculo/correlação, processamento, entrega falsa e adapters de resposta delimitados. | Conta/permissões oficiais, prévia/aprovação reais e recuperação ponta a ponta. |
| OpenAI texto | Responses com saída estruturada, reservas/tokens e controles de domínio. | Receita/qualidade e custo comerciais; não é agente geral. |
| OpenAI áudio | Adapter de transcrição sob aceite único, limites e configuração. | Homologação operacional/financeira completa. |
| TypeSafe/Jev | Interpretação delimitada/retrieval opcionais no worker dev/test, desligados por padrão, orçamento por tenant. | Corpus PT-BR mais amplo e liberação comercial; sem autorização por fornecedor na web. |
| OpenAI imagem | Adapter/orquestrador e ensaios sintéticos isolados; HTTP falso nos testes. | Guarda real, schema/modo, dispatcher/worker/Temporal e recuperação integrados; depois BL04.3. |
| Instagram | Aprovação/publicação falsas com versão/hash. | OAuth/publicação/reauth/reconciliação/métricas oficiais. |
| Avatar/voz/cena generativa | Candidatos e plano posterior ao piloto. | Direitos/consentimento específicos, contrato/licenças, qualidade e custo próprios. |
| Pesquisa/Places/busca | Desenhos e fontes candidatas, sem integração de pesquisa ampla. | Termos de cada fonte, escopo permitido, proveniência, gasto e ganho sobre baseline. |
| AWS/Redis/CDN | Infraestrutura planejada/artefatos de deploy; Redis sem runtime ativo. | Provisionamento, backup de DB/objetos/Temporal e operação F08. |

## Contratos comuns

Cada adapter representa uma capacidade e não escolhe política de produto.
Serviços decidem elegibilidade, receita, direito sobre fontes, orçamento e estado.
O aceite único cobre interpretação, texto, imagem e transcrição. Configuração,
plano, quota/custo, aprovação de publicação e identidade audiovisual futura são
controles distintos. Não criar toggles por marca/modelo para expor esses gates.

Persistir operação e intenção antes de efeito externo. SDK/HTTP/Temporal precisam
compartilhar política explícita de retry, sem multiplicar POSTs pagos. Timeout
após possível envio permanece incerto até conciliação; não trocar fornecedor
para contornar resposta perdida, política de conteúdo ou orçamento.

Callbacks verificam assinatura, conta provedora, operação e escopo do recurso;
ID externo ou parâmetro de tenant não autoriza acesso. Copiar saídas de URL
expirável para storage privado sob limites; nunca pôr token, mídia ou prompt
bruto no histórico/log de workflow. Cliente aprova versão/hash/legenda/destino/
horário; integrar canal não autoriza postar sem essa decisão.

## Material e qualidade

Só enviar fontes pertinentes do negócio, minimizadas e com hash/versão/direitos.
Foto conceitual não é prova de produto/local real. A preservação WhatsApp e a
remoção de foto do acervo têm contratos diferentes. Prévias devem ser preservadas
enquanto conta ativa; o runtime ainda precisa da alteração coordenada de TTL/acesso.

Um fornecedor de voz/avatar requer consentimento específico da própria pessoa
quando essa etapa for implementada, depois do piloto. HeyGen, Runway, Kling,
Veo e modelos abertos são candidatos por capacidade, sem fornecedor primário
homologado. Ferramenta com interface exportando vídeo não comprova API comercial.
Ver [vídeo e voz](video-real-and-voice.md) e [pesquisa datada](video-tool-candidates-2026-10-27.md).

Cada ficha de ativação deve registrar versão de API/modelo, configuração, limite,
credencial por ambiente, regiões/retentiva da fonte, direitos, operação incerta,
callback, custo e evidência datada. Ensaios fora do worker são evidência do ensaio;
capacidade comercial exige BL04.3 e jornada homologada, não apenas HTTP 200.

Versão anterior integral: [snapshot de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/v0-integrations.md).
