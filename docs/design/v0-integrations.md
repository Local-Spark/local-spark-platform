# v0 — Catálogo de integrações e APIs

Data de consulta: 20/10/2026. Decisões concretas de implementação, ainda sujeitas a
teste de acesso/contrato, orçamento e benchmark. “Selecionado” não significa serviço
contratado, modelo habilitado na nossa conta ou integração já testada.

Atualização de 21/10: [decisão de contexto/geração](business-context-and-generation.md)
prevalece sobre a escolha antecipada de HeyGen/Runway e sobre versões de modelo
desta tabela. São candidatos para spike; manter aqui os contratos pesquisados como
referência, sem tratá-los como fornecedor aprovado. Portas são por capacidade.

## 1. Mapa de responsabilidades

Complemento vigente: [pesquisa local e Jev](v0-intelligence.md), com APIs, política
de fontes, frequência, orçamento e critérios de ativação.

| Função | Seleção para a v0 | Execução |
| --- | --- | --- |
| Entrada e saída WhatsApp | Meta WhatsApp Cloud API direta | API externa oficial |
| Download de mídia WhatsApp | Meta Media API | Worker Python baixa para S3 |
| Vídeo para áudio | FFmpeg | Worker próprio, sem API paga |
| Metadados e duração | ffprobe | Worker próprio |
| Transcrição do pedido | OpenAI Audio Transcriptions | API externa |
| Texto, ideias, roteiro e interpretação visual | OpenAI Responses com JSON Schema | API externa |
| Geração/edição de imagem | OpenAI Images | API externa |
| Arte, tipografia e carrossel | Pillow + compositor com templates | Worker próprio |
| Voz e avatar do cliente | HeyGen Digital Twin, speech e vídeo | API externa |
| Cena sintética a partir de imagem/texto | Runway, modelo inicial `gen4.5` | API externa |
| Legendas com tempo | ASR com timestamps + revisão/sincronização | API + processamento próprio |
| Montagem final, música, cortes e exportação | FFmpeg com manifesto validado | Worker próprio |
| Publicação e insights | Instagram Platform, Instagram Login preferencial | API externa oficial |
| Armazenamento | AWS S3 privado | Serviço gerenciado |
| Assinatura | Stripe Billing/Checkout como proposta inicial | API externa; método BR a validar |

Reduzir fornecedores: usar voz HeyGen inicialmente junto do avatar, inclusive em
narrativas sem rosto quando a API/contrato habilitar. ElevenLabs é alternativa a
avaliar se qualidade/controle da voz não atenderem; não integrar dois provedores de
voz na v0 sem evidência. Voz original enviada pelo cliente é outro caminho de áudio.

## 2. Meta — WhatsApp

Base Graph: `https://graph.facebook.com/{META_GRAPH_VERSION}`.
Pin da versão é obrigatório antes do primeiro deploy; configurável e testado, nunca
usar implicitamente `latest`. Escolher a versão disponível no app de produção no
bootstrap e registrar scopes, data de expiração/depreciação e fixtures correspondentes.

Operações a implementar:

- Webhook público `GET /webhooks/meta/whatsapp` para challenge.
- `POST /webhooks/meta/whatsapp` para mensagens e recibos; verificar corpo bruto e
  assinatura Meta antes de gravar. Normalizar eventos separados e deduplicar.
- `GET /{media_id}` para URL/metadados e download autenticado da mídia; URL transitória
  não vira identidade persistente do arquivo.
- `POST /{phone_number_id}/media` para upload quando aplicável.
- `POST /{phone_number_id}/messages` para texto, mídia, ações e templates suportados.
- Configurar inscrição na WABA, número do produto e templates necessários no app Meta.

Autenticação: token de sistema/credenciais do app em Secret Manager. Não publicar
verify token, App Secret ou token Graph em frontend/logs. Verificar telefone do
cliente e vínculo de ator/negócio. Nosso número central recebe material; não confundir
isso com integrar o WhatsApp de vendas de cada estabelecimento.

Proatividade: seleção de template, janela, opt-in e limites de frequência em adapter
de notificações. Custos e categorias vigentes entram em configuração financeira;
não presumir que qualquer mensagem é gratuita por o cliente ter falado antes.
Resposta ambígua após envio de mensagem pode duplicar notificação; tratar por operação,
recibos quando disponíveis e política explícita de revisão, sem exactly-once inventado.

Fontes: [webhooks na coleção oficial Meta](https://www.postman.com/meta/whatsapp-business-platform/folder/tduohwq/webhook-payload-reference),
[preços/categorias oficiais](https://business.whatsapp.com/products/platform-pricing).

## 3. OpenAI — texto, imagem e áudio

Base `https://api.openai.com/v1`. SDK oficial Python ou HTTPX em adapter único.
Não usar credenciais pessoais do ChatGPT como substituto da API.

| Operação | Endpoint | Modelo inicial proposto |
| --- | --- | --- |
| Briefing, ideias, análise de imagens e roteiros | `POST /responses` | `gpt-5.6-terra` |
| Transcrição de áudio recebido | `POST /audio/transcriptions` | `gpt-transcribe` |
| Alinhamento de legendas com tempo | `POST /audio/transcriptions` | `whisper-1` com formato compatível e timestamps |
| Imagem ilustrativa | `POST /images/generations` | `gpt-image-2.5-flare` |
| Edição visual controlada | `POST /images/edits` | `gpt-image-2.5-sunburst` |

Modelos são escolhas iniciais documentadas, não promessas de melhor custo. Antes de
habilitar: confirmar acesso, schema de request, limites, preço e eventual snapshot
disponível; fixar perfil de execução. Atualização de modelo passa por evals. Se conta
não tiver acesso, registrar nova decisão e benchmark, sem fallback oculto.

Schema estruturado inclui fatos usados, dúvidas, CTA, formato, cenas e custo previsto.
JSON válido não garante fato verdadeiro: validação de preço, oferta, proveniência e
permissões continua no domínio. Recusa, resultado incompleto e saída semanticamente
inválida são estados distintos. No máximo uma tentativa de reparo semanticamente
limitada por orçamento; não repetir geração indefinidamente até sair algo aceitável.

Transcrição do áudio de briefing não é o mesmo que legenda sincronizada do vídeo
final. Para texto falado gerado: produzir voz primeiro, obter timings dessa fala e
aplicar offsets das cenas. Se a fala mudar, refazer alinhamento. Sem suporte nativo
a timestamps no modelo escolhido, usar o caminho de alinhamento separado; não
distribuir palavras por duração uniforme e chamar de sincronização precisa.

Fontes: [Responses](https://developers.openai.com/api/reference/responses/overview),
[saída estruturada](https://developers.openai.com/api/docs/guides/structured-outputs),
[modelo de texto selecionado](https://developers.openai.com/api/docs/models/gpt-5.6-terra),
[transcrição e timestamps](https://developers.openai.com/api/docs/guides/speech-to-text),
[imagens](https://developers.openai.com/api/docs/guides/image-generation).

## 4. HeyGen — identidade, voz e vídeo do dono

Base `https://api.heygen.com`, header `X-Api-Key`.

| Operação | Contrato externo selecionado |
| --- | --- |
| Cadastrar arquivos | Assets/direct upload conforme tamanho permitido |
| Criar clone de vídeo | `POST /v3/avatars`, tipo `digital_twin` |
| Registrar consentimento do clone | `POST /v3/avatars/{group_id}/consent` |
| Consultar prontidão do look | `GET /v3/avatars/looks/{look_id}` |
| Gerar fala reutilizável | `POST /v3/voices/speech` |
| Gerar avatar falando | `POST /v3/videos`, com script/voz ou áudio já produzido |
| Consultar vídeo | `GET /v3/videos/{video_id}` |
| Registrar callback | `POST /v3/webhooks/endpoints` |

Persistir IDs de grupo, look, voice e consentimento separadamente. Arquivo de captura
e consentimento passam por UX guiada, validação de qualidade e limites da API. Testar
extração/reuso da voz treinada em narrativas sem rosto antes de liberar essa receita.
Autorização do cliente deve existir mesmo se algum modo técnico aceitar imagem sem
verificação adicional. Não utilizar opções de dispensa de consentimento como padrão.

Callback usa segredo do endpoint e HMAC-SHA256 do corpo bruto conforme contrato v3.
Guardar evento e operação antes de sinalizar Temporal. Polling autenticado cobre
callback perdido; saída copiada ao S3 antes de URL do fornecedor expirar.

Inscrição avulsa no aplicativo não garante cota/API, treinamento de centenas de
milhares de identidades ou revenda. Verificar slots, concorrência, direitos, exclusão
de identidades e custos de retenção/treinamento para cada cliente no contrato.

Fontes: [clone em vídeo](https://developers.heygen.com/docs/avatar-from-video),
[áudio para avatar e speech](https://developers.heygen.com/audio-to-video),
[callbacks e assinatura](https://developers.heygen.com/docs/webhooks).

## 5. Runway — cenas geradas

SDK oficial Python `runwayml`, criação `client.image_to_video.create(...)` com modelo
inicial `gen4.5`, conforme guia oficial consultado. Perfil da receita fixa tamanho,
proporção e duração suportados; sem prometer qualquer resolução arbitrária.

O adapter faz submit, salva task ID, consulta status e copia o resultado para S3.
Não usar helper bloqueante que espera o job inteiro dentro do workflow. Polling roda
como activities curtas separadas por timers duráveis. ID de tarefa é persistido antes
da próxima consulta. Se o submit teve efeito desconhecido, não criar outro job às cegas.

Cenas sintéticas são limitadas por orçamento e contexto; não modificar comida real
ou resultado de um serviço e apresentar como evidência autêntica. Material gerado
integra a prévia e aprovações. Fallback para movimento de foto altera a receita e
deve ser informado; não substituir silenciosamente a entrega contratada.

Fonte: [guia oficial Runway e SDK Python](https://docs.dev.runwayml.com/guides/using-the-api/).

## 6. Mídia local — nenhuma API de conversão obrigatória

FFmpeg extrai áudio, normaliza, corta, concatena e aplica trilha/legendas. ffprobe
inspeciona streams. Pillow compõe cards com fontes e assets licenciados. Os serviços
Python chamam executáveis com lista de argumentos, sem shell e sem comandos do LLM.

Cada receita gera manifesto com duração, trilhas, fontes, tempos, safe areas e IDs
de arquivo autorizados. Render opera em container isolado com CPU/RAM/disco/tempo
limitados; protocolos e acesso de rede restritos. Uploads não confiáveis não são
processados dentro do processo da API.

Saídas têm checksum e render_key determinístico; escrita em objeto temporário,
validação de integridade e registro atômico do artefato pronto. Retry reaproveita
resultado concluído. Não armazenar vídeo base64 no broker/histórico Temporal.

Fontes: [FFmpeg](https://www.ffmpeg.org/ffmpeg.html).

## 7. Instagram — publicação e métricas

Escolha: Instagram Platform com Instagram Login para contas profissionais elegíveis.
Adapter expõe autorização, capability discovery, criação de container, consulta de
processamento, publicação e insights. Base/versionamento/scopes devem corresponder
ao caminho de login aprovado; não misturar tokens Facebook Login e Instagram Login.

Família de operações: `/{ig_user_id}/media`, `/{container_id}`,
`/{ig_user_id}/media_publish`, insights da conta e da mídia. Fazer spike na versão
Graph pinada para imagem, carrossel, Reel e Story por tipo de conta. Conta sem Stories
elegíveis não recebe essa opção. App review e acesso às contas de clientes são gate
de produção; sucesso em conta da equipe não encerra esse gate.

Arquivo é servido em URL temporária alcançável pela Meta pelo tempo necessário.
Token OAuth é criptografado e associado ao tenant/conta. Consentimento identifica
conta e destinos. Legenda/arquivo/horário são imutáveis após aprovação; alteração
gera nova aprovação. Estado externo confirmado é persistido antes de notificar sucesso.

Sem assumir suporte a exclusão programática ou cancelamento de container. Se algo
já foi publicado, recuperação exige decisão do cliente e capability comprovada;
não apagar automaticamente como compensação de falha no relatório.

Fonte acessível: [coleção oficial Meta](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api?entity=request-23987686-ab559ffb-8e2c-4b0a-b43a-5737b6d2f672).
O guia direto de Instagram Login não pôde ser lido nesta pesquisa; endpoints,
scopes e matriz de formatos desse caminho são verificados no spike antes de codificar
o adapter contra uma versão específica. Isso é pendência real, não confirmação implícita.

## 8. Registro de integração e liberação

Cada adapter possui ficha versionada: proprietário, base/version, modelo, scopes,
auth, secret_ref, custo por unidade, timeouts, erro recuperável, idempotência,
callback, limites, retenção, exclusão e data de smoke test.

Check obrigatório antes de ativar: request válido real, erro real ou simulado,
limite/timeout, recuperação de callback, autorização, cobrança e custo por entrega.
Mocks permitem implementar o domínio; não satisfazem o gate comercial da integração.
