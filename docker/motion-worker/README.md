# Executor do Reel no worker do produto

O overlay `docker-compose.motion.yml` conecta os serviços existentes API,
relay do outbox e worker Temporal. O target `motion-worker` acrescenta somente
o cliente Docker 28.0.4 ao `media-worker`, que já contém FFmpeg/FFprobe.
Não instala outro daemon nem outro executor de workflows.

O worker confiável recebe o socket Unix e uma pasta de trabalho dedicada.
O renderizador recebe **somente a subpasta de entrada daquela tentativa, somente
leitura**; mantém rede desativada, filesystem somente leitura, UID 65532,
seccomp, limites e remoção exclusivamente por ID criado pela tentativa.
O socket não entra no renderizador. O acesso do worker ao socket permite
controlar o daemon; montar o socket como `read_only` não restringe sua API.

## Preparar a configuração

Copie `environment.example` para `.local/motion-worker.env` e mantenha esse
arquivo fora do git, com modo 0600. Preencha:

- `MOTION_SCRATCH_DIRECTORY`: diretório absoluto dedicado e existente no host,
  sem vírgulas/aspas. Resolva links simbólicos antes de configurar. O overlay
  monta exatamente o mesmo caminho no worker, necessário para o bind criado
  pelo daemon. Não use a raiz do projeto nem uma pasta com outros dados.
- `MOTION_WORKER_UID/GID`: usuário sem root com permissão para escrever nessa
  pasta. No Mac, use os números de `id -u` e `id -g` do dono da pasta; em Linux,
  prepare a pasta para o UID/GID escolhido (padrão 10001). Mantenha modo 0700.
- `MOTION_DOCKER_SOCKET`: socket local existente, por exemplo `/var/run/docker.sock`
  ou o socket do Docker Desktop. `MOTION_DOCKER_GID` deve permitir ao worker
  acessá-lo; configure o grupo observado na montagem, sem `chmod 666`.
- `MEU_BRACO_DIREITO_MOTION_RENDERER_IMAGE`: ID `sha256:...` ou referência por
  digest da imagem já carregada nesse daemon. O adapter usa `--pull=never`.
  A imagem qualificada anteriormente é Linux/ARM64; esta entrega não qualifica AMD64.

O diretório e o socket não são criados implicitamente pelo Compose. O overlay
mantém execução e provedor desativados por padrão, sem orçamento presumido.
Flags, materiais sintéticos permitidos, tarifas, reservas e chave de criptografia
são iguais entre API, relay e worker. A chave de criptografia deve ser a existente.
O relay precisa executar: é ele que entrega `motion.requested` ao Temporal.
Atualize todos os workers que consomem a mesma fila com a mesma configuração;
um worker antigo não conhece as atividades de motion.

## Comandos para a próxima execução

Da raiz do repositório, depois de preencher o arquivo local:

```sh
docker compose --env-file .env --env-file .local/motion-worker.env -f docker-compose.yml -f docker-compose.motion.yml --profile workers config --quiet
docker compose --env-file .env --env-file .local/motion-worker.env -f docker-compose.yml -f docker-compose.motion.yml --profile workers build worker
docker compose --env-file .env --env-file .local/motion-worker.env -f docker-compose.yml -f docker-compose.motion.yml --profile workers run --rm --no-deps worker python -m app.entrypoints.motion_executor_check
```

A verificação faz uma única peça sintética de 64×64, dois quadros, sem assets,
áudio, IA, banco ou Temporal. Confere o compartilhamento real, a execução Linux,
a sandbox e a saída pelo mesmo adapter; timeout de render de 60 s. Ela não
habilita pedidos, não comprova qualidade criativa e não chama uma API paga.
Somente a criação/start/remoção do contêiner próprio e a pasta temporária são usados.

Com essa verificação aprovada e o plano do ponto 3 autorizado, a configuração
normal é aplicada aos serviços `api worker relay` com o mesmo overlay. Não
execute `down -v`, migrações ou limpeza do banco como parte dessa configuração.
A entrega inicial do ponto 2 forneceu código/configuração e testes direcionados.
No ponto 3, a imagem foi construída e a checagem real dentro do worker passou.
A prova paga produziu duas versões, mas parou na persistência da crítica final.
[Resultado e limites](../../docs/evals/plano-prova-reel-integrada-2026-11-09.md).
A imagem do renderer com a correção de UTF-8 é
`sha256:fa18127583b7d2e66cee3c49900179b52a81e9298913293a164cd9ef3aef8c25`;
sua checagem mínima passou, enquanto a primeira prova paga preservou o digest anterior.
A [nova rodada](../../docs/evals/plano-comparacao-criativa-integrada-2026-11-09.md#resultado-da-execução-autorizada)
usou esse renderer e worker reconstruído, concluindo geração, render, crítica e
download autenticado. Worker próprio encerrado ao terminar; o titular reconheceu
pequena melhora, ainda abaixo do nível criativo esperado, sem ativação comercial.

O caminho compartilhado segue a [regra de bind mounts do Docker](https://docs.docker.com/engine/storage/bind-mounts/):
a origem é interpretada pelo daemon, não pelo cliente dentro do worker.

## Ilustrações opcionais do Reel

Configurar na API e worker os mesmos `MEU_BRACO_DIREITO_MOTION_ILLUSTRATIONS_ENABLED`,
`MEU_BRACO_DIREITO_MOTION_ILLUSTRATION_RESERVATION_USD_MICROS` e
`MEU_BRACO_DIREITO_MOTION_ILLUSTRATION_BUDGET_USD_MICROS`. Defaults false/0/0;
nenhuma ativação é autorizada pelo exemplo. Apenas no modo OpenAI explicitamente
configurado, no escopo de qualificação existente. Máximo de duas imagens;
suborçamento deve caber no orçamento total do Reel junto da geração e crítica.

A reserva controla admissão local, não limita a fatura no provedor. Usage desconhecido,
estimativa excedida ou falha interrompem sem nova chamada automática. Reconciliação
usa IDs/uso no efeito cifrado e a reserva compartilhada. Não reutilizar orçamentos
de ensaios anteriores. Arquivos ficam privados sob o pedido; correções usam os
mesmos pixels. Ver [contrato e limites](../../docs/design/evolucao-qualidade-motion-referencias-2026-11-09.md).

## Quadros antes do vídeo

Para novos pedidos com `storyboard=true`, aplicar a migração `0114_motion_storyboards`,
reconstruir a imagem do renderer a partir deste código (protocolo 2), configurar o
novo digest na API/worker e habilitar `MEU_BRACO_DIREITO_MOTION_STORYBOARD_ENABLED=true`.
O exemplo permanece false; imagem antiga rejeita o protocolo, sem fallback ao vídeo.
Não basta ligar a flag. A qualificação real do container atualizado é parte da
próxima prova, não foi executada nesta implementação.

A galeria e o aceite usam endpoints autenticados de `/motion-requests/{id}/storyboard`.
Enquanto aguarda aceite, a atividade inicial termina, e o pedido continua protegido
como ativo no banco. A decisão emite outbox para a continuação Temporal, revalidando
acesso/fontes e reutilizando os arquivos. Reprovar encerra o pedido e registra feedback.
Nenhuma geração paga adicional ocorre apenas por aprovar ou reentregar o evento.

Com `motion_storyboard_enabled=true`, `motion_executor_check` também captura
um PNG pelo protocolo 2 e exige ausência de MP4 nesse resultado. A verificação
continua sintética, curta e sem conexão ao banco ou chamada de IA.
