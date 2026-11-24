# Video-reel v1 — texto sem elementos filhos e erros específicos

Continuação em código e aplicação local: [runtime de visibilidade por cena](motion-video-reel-v1-scene-visibility-2026-11-24.md).

## 24/11/2026 — video-reel v19: texto puro e diagnóstico seguro do renderer

Run `360588a6…` com v18/v2 passou por plano/implementação e falhou no render.
Simulação local com mídia sintética isolou `<br>` em cena2-convite/cena2-cta:
a guarda exige children.length=0 e recusa os textos no primeiro frame visível.
Substituir apenas os BR em memória eliminou a rejeição nos instantes examinados;
nenhuma alteração foi feita no run. Fundo de leitura e ausência de hastes já
estavam corretos nesta candidata.

Nova skill pinada `instagram-reel-video-v19` exige textContent sem elementos
filhos (incluindo BR/SPAN), com quebra natural ou nova linha real + pre-line
quando houver múltiplas linhas. Mantém medições de texto/scrim, VR1–VR3 e CTA.
Replay v16/v17/v18 permanece com seus pins. Repertório v2 e guarda DOM intactos.
O runner agora traduz somente seis códigos exatos da guarda vídeo recebidos do
Playwright para o protocolo de erro, e o adapter aceita os mesmos códigos.
Prefixo conhecido de page.evaluate é tratado; stacks/conteúdo não são emitidos.
Erros desconhecidos continuam MOTION_RENDER_EXECUTION_FAILED; photo não ganha
novos códigos ou regras. Isso diagnostica a recusa, não aprova a composição.

Validação: 405 unitários Python, 286 Node e oito integrações locais em PostgreSQL
`_test` com roles restritas/fornecedores simulados. 100% linhas/branches nos cinco
módulos Python medidos (adapter HTML, skills, repertoire, video_reel e
video_requests: 522 statements/228 branches); 100% linhas/branches/funções nos
quatro módulos Node medidos, incluindo runner. Sem exclusões novas. Chromium
executa exemplo v19 com texto puro multilinha, todos os frames/seeks reversos,
e recusa BR/SPAN; o erro real atravessa o mapeamento seguro. Duas falhas de áudio
na seleção ampliada foram reproduzidas no índice anterior isolado; não mascaradas.
Ruff/formato e mypy do recorte passaram; make ci segue bloqueado nos 66 lints
preexistentes. CI integral/cobertura global continuam pendentes.

Dos 184 arquivos históricos comparados, só runner.cjs mudou, para diagnóstico;
183 assets/validador permanecem intactos, inclusive skills antigas, repertório,
guarda e polish photo. Sem chamada paga, MP4, reload ou alteração de snapshots.
Aplicação operacional requer worker com v19 e imagem do renderer reconstruída
com o novo runner, usando seu digest explícito; não foi feito deploy. Imagem
antiga mantém o diagnóstico genérico. Sem Fatia B/VR4–VR6 ou aceite E2E.

## Evidência e limites

Run `360588a6-a842-59f5-8a6a-1dfb284f0e38`: 24/11/2026, 10:33:32–10:38:49
(São Paulo), custo já registrado 1.702.688 micros de USD, zero versões MP4.
Snapshot: v18/v2, proposed-video-output-v1, quality-v2, staging-v1 e contrato
motion-video-reel-v1. Existe pedido de render sem resposta de render.

Em Chrome com mídia sintética, 0/33/650/1650/6780ms passam. Aos 6813,333ms,
texto opacity≈0,052 e scrim alpha=0,76, mas cada texto da cena2 possui um BR;
falha MOTION_VIDEO_READABLE_ACTION_OVERLAY_REQUIRED. A variante exclusivamente
em memória, com BR substituído por espaço, passou nos instantes 6813,333/7300/
7900/8020/10600/11166,667ms e retorno a 0. Não é prova do ambiente original ou
aceite audiovisual; o stderr histórico não foi recuperado.

## Contrato de diagnóstico

O runner reconhece somente DOM_ID_INVALID, FULL_BLEED_REQUIRED,
KIT_OVERLAY_REQUIRED, TEXT_NOT_EXECUTED, READABLE_ACTION_OVERLAY_REQUIRED e
UNPLANNED_OVERLAY, todos com prefixo MOTION_VIDEO_. A comparação usa a primeira
linha exata após o prefixo conhecido de Playwright, com ou sem Error:. Mensagem
com sufixo arbitrário, prefixo estranho, código desconhecido ou objeto sem
message string cai no código genérico. Nenhum HTML, stack, caminho, texto ou
log do navegador atravessa o protocolo. Erros são indicações de execução,
não evidência confiável de qualidade nem mecanismo de autorização.

A whitelist Python mantém o mesmo conjunto. Testes exercitam stderr JSON do
entrypoint, o subprocesso do adapter e erros reais do navegador. Não há nova
operação, chamada externa, retry ou alteração de durabilidade.
