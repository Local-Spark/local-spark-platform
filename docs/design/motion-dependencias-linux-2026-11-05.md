# Motion — revisão curta de dependências e pacote Linux

05/11/2026. Revisão somente leitura; nenhum build, download de pacote, chamada
paga, acesso a credencial ou alteração em app/CI. As evidências abaixo identificam
o ambiente dos ensaios; não declaram licença única nem autorização de distribuição
de todas as bibliotecas transitivas.

## Achados concretos

- `Dockerfile` usa `python:3.13.7-slim` e `uv:0.10.6` por tag, sem digest. O alvo
  `media-worker` instala `ffmpeg` pelo APT sem versão; não inclui Node, Playwright
  ou navegador. O alvo padrão `app` nem inclui FFmpeg. Portanto nenhum dos dois
  é hoje o artefato de motion reprodutível.
- `.github/workflows/deploy.yml` constrói o alvo padrão em `ubuntu-latest`, envia
  a imagem por tag de commit ao ECR e reutiliza uma task definition ECS externa.
  Não fixa `--platform`; a arquitetura configurada da tarefa ECS não está no
  checkout. Linux/amd64 é uma hipótese coerente com o runner atual, não arquitetura
  confirmada do deploy. Antes de publicar imagem motion, conferir task definition.
- A direção/compilação próprias usam DOM/WAAPI. HyperFrames, GSAP e seus assets
  não são necessários no conjunto mínimo deste caminho. Isso não remove os
  avisos MIT das fichas/scripts adaptados ou preservados.

## Inventário local verificado

| Artefato | Evidência | SHA-256 dos bytes observados |
| --- | --- | --- |
| FFmpeg macOS arm64 9.0 | 52.070.376 bytes; `-L` declara GPL v2 ou posterior; `-version` inclui `--enable-gpl`, libx264, libx265 e muitas outras bibliotecas. BSD-2-Clause do wrapper não cobre esse binário. | `591260c945d0eef150e3bf82b0ef988bd36a9cecc18ff05d6679617159f0a95e` |
| FFprobe macOS arm64 4.4.8 | 18.411.112 bytes; `-L` e BUILD_INFO declaram LGPL 2.1 ou posterior. Build estático, autodetect desabilitado; hash coincide com BUILD_INFO. | `596d355d03b6e7530c4d19dd87fea056a31eb811443716a641b4c516562c0bc8` |
| Chrome Headless Shell macOS arm64 156.0.8078.4, revisão Playwright 1248 | Executável 176.747.664 bytes. Diretório tem `LICENSE.headless_shell` com 2.151.339 bytes de avisos e ABOUT identifica Chrome/Chromium. Preservar diretório completo, não apenas executável. | `77d8278b1ac9d0687fad4e817ea83023ede09b1deef36e1864b49ba194ac9634` |
| `playwright-core` 1.64.1 | package.json declara Apache-2.0; LICENSE e NOTICE presentes. Hash abaixo identifica package.json, não todo o pacote. | `8aa1c9863fa8dea324e674254158cdc79440f4124ef2d84d38053013541cb7d6` |
| Playwright LICENSE | 11.601 bytes; Apache 2.0. | `45873d00a0dd243596deb4aa23b2493b3d1f0671921bf2538ea431d7380220eb` |
| Playwright NOTICE | 254 bytes; Microsoft/Puppeteer. | `6d602191187b35b9b01d2cffa01c8469c2c8d9de8a96f1bf868e0f264f51c81d` |

Fontes do kit DejaVu já têm `catalog/kits/cafe-pausas/v1/fonts/LICENSE.txt`;
conservar esses avisos e hashes junto dos arquivos realmente usados. Nenhuma fonte
externa ou download por CDN é necessário no primeiro pacote.

O BUILD_INFO do FFprobe aponta `https://ffmpeg.org/releases/ffmpeg-4.4.8.tar.gz`,
SHA-256 declarado `6fdb32cc5cd8a3651c0b4ab9970e99402dbae9f18729014ab7901b84dee6a9de`.
O código-fonte correspondente não foi baixado nem conferido; URL/hash em um arquivo
não são preservação. O FFmpeg 9.0 local não possui neste diretório receita completa
e todas as fontes exatas das bibliotecas compiladas. Não promover esses binários
macOS como pacote de produção Linux.

## Fontes primárias consultadas

O FFmpeg documenta que componentes GPL opcionais alteram a licença do conjunto
compilado; os termos dependem da configuração e bibliotecas. Para redistribuição,
preservar a licença aplicável e o código-fonte correspondente/receita é parte do
trabalho pendente; não concluir que toda a aplicação Python assume GPL pelo uso
de um processo separado. [Licença FFmpeg](https://ffmpeg.org/legal.html),
[LICENSE.md oficial](https://github.com/FFmpeg/FFmpeg/blob/master/LICENSE.md?plain=1).

Playwright documenta que a imagem oficial inclui browsers/dependências de sistema,
mas não o pacote Playwright; versões devem coincidir. O usuário root desativa a
sandbox Chromium, e a documentação orienta usuário próprio/seccomp para conteúdo
não confiável. A imagem oficial é voltada a teste/desenvolvimento, portanto não
é prova de isolamento do produto. [Docker/Playwright](https://playwright.dev/docs/docker).

A licença principal Chromium prevê preservação de avisos em distribuição; o
arquivo local agrega muitas licenças de terceiros, que precisam acompanhar o
artefato exato. Não atribuir BSD a todo o pacote por inferência.
[Licença principal Chromium](https://chromium.googlesource.com/chromium/src/+/main/LICENSE).

## Artefato proposto

### Recuperação do laboratório macOS — 08/11/2026

Os binários que estavam em `/private/tmp` desapareceram entre sessões. Foram
recuperados de `imageio-ffmpeg` 0.8.1 (wheel macOS arm64) e
`@w6s/ffprobe-static` 3.1.1, com verificação da integridade dos arquivos de
distribuição e dos dois SHA-256 de binários da tabela acima. Os bytes recuperados
são os mesmos do ensaio; nenhuma composição ou entrada congelada foi alterada.

Arquivos de distribuição completos, incluindo avisos, binários e manifesto de
origem/hashes ficam em `.local/tools/motion-lab/`, fora de Git. Links nos caminhos
temporários antigos permitem executar os manifests históricos sem reescrevê-los.
Os testes novos usam variáveis `MOTION_TEST_FFMPEG`/`MOTION_TEST_FFPROBE`, PATH ou
`.local/tools/motion-lab/bin/`, nessa ordem. O CI Linux instala FFmpeg/FFprobe
explicitamente; ausência de ferramenta falha, sem pular testes.

Esta recuperação é do laboratório macOS. Não entrega a imagem Linux, backup
remoto, reconstrução a partir das fontes ou qualificação do isolamento descritos
abaixo. O cache privado persistente evita depender apenas de uma pasta temporária,
mas ainda não é backup independente.

Criar imagem própria de render com sistema glibc Linux, inicialmente uma única
arquitetura confirmada, contendo Node 24.18.0, `playwright-core` 1.64.1 e o browser
Linux compatível revisão 1248, FFmpeg/FFprobe provenientes da mesma distribuição
ou compilação própria, fontes do kit e compilador/runtime próprios. A versão de
FFmpeg Linux não deve ser inventada a partir do binário macOS: selecionar pacote
exato, provar filtros/codecs necessários e registrar fontes/patches/licenças.

No primeiro experimento Linux, usar base Debian/Ubuntu por digest com artefatos
pré-adquiridos e verificados; a imagem final não executa APT, npm ou downloads.
Não copiar `node_modules` do web: preservar tarball completo do pacote próprio
e seus avisos; browser exige arquivo completo por plataforma. Separar executor
sem credenciais/rede do worker Temporal que busca mídia, chama modelos autorizados
e persiste efeitos. É processo técnico chamado por atividade, não outro runner
de workflow. Validar sandbox do browser sem `--no-sandbox`, usuário sem privilégios,
filesystem somente leitura com área temporária limitada, PID/memória/CPU/tempo,
rede bloqueada no runtime e saída somente pelos arquivos esperados. Não habilitar
`SYS_ADMIN` ou `--privileged` como solução para falha de sandbox.

Cada release deve guardar sob controle próprio:

1. Imagem OCI final e base, por digest/plataforma; tarballs/debs usados no build,
   com manifesto de bytes/SHA-256/versão/origem/licença.
2. Receitas e toolchain; fontes correspondentes, patches e avisos das dependências
   redistribuídas, inclusive sistema/bibliotecas. Preservar manifestos e provas da
   correspondência source→binary; uma lista de URLs não basta.
3. Fontes próprias e externas adotadas em repositório privado, binários grandes
   em armazenamento/registry versionado próprio. Fazer backup independente e
   testar restauração; GitHub fork ou cache local isolados não satisfazem isso.
4. Prova sem rede: restaurar OCI e insumos do backup, gerar MP4 9:16 e páginas
   4:5 sintéticos, decodificar, comparar tempos/áudio/frames, confirmar não haver
   acesso a repositórios externos. Registrar fontes e limitações; isso não é
   homologação criativa nem reconstrução binária idêntica por si só.

## Menor próximo passo executável

Após a finalização do CI atual, preparar uma **fatia de aquisição e manifesto
Linux**, sem ativar produto: confirmar arquitetura ECS pela configuração existente,
fixar digest da base, obter apenas os pacotes necessários e respectivas fontes/
avisos, verificar hashes e gerar inventário SBOM/manifesto. Depois construir uma
imagem experimental e executar uma única cena sintética com rede bloqueada. Não
há chamada paga de modelo nessa fatia; downloads/armazenamento não foram feitos
nesta revisão. A autorização de criar repo privado já existe; falta acesso GitHub
no ambiente e destino independente de backup verificado, não nova decisão de estilo.

Não há repositório remoto criado nem pacote Linux pronto nesta revisão. A conclusão
de licença/distribuição e a validação do isolamento permanecem por artefato concreto.

## Conferência de configuração AWS — 05/11/2026

A CLI padrão disponível é AWS CLI 2.28.15 e `aws configure get region` retornou
`us-east-1`. Os documentos/scripts locais não informam família ECS concreta;
o workflow recebe o nome por variável GitHub, e a documentação antiga apresenta
ECS/Fargate como opção de arquitetura, não evidência de tarefa implantada.

Foi feita uma única consulta somente leitura, `ecs list-task-definition-families`,
filtrada pelo prefixo `meu-braco-direito`, na região padrão. A AWS respondeu
`UnrecognizedClientException`: token de segurança inválido. Não houve retorno
de famílias ou acesso a task definitions, envs ou segredos. Não foram tentados
outros perfis/contas/regiões, reautenticação ou alteração AWS.

Assim, a arquitetura de deploy permanece não confirmada por evidência remota.
É possível preparar manifesto/contrato e testes Linux locais; publicação e pacote
definitivo devem usar a arquitetura real quando o acesso já configurado estiver
funcional. A leitura falhou por autenticação, não por falta de escolha técnica do
titular.

## Conferência do acesso GitHub — 05/11/2026

A origem Git usa SSH na conta `israeljbsilva`; isso não demonstra acesso à API
para criar repositórios. O helper HTTPS configurado (`osxkeychain`) foi consultado
sem prompts, somente para GitHub e essa conta, e não disponibilizou credencial.
Nenhum segredo foi exibido/salvo, nenhum token foi procurado em outros locais e
nenhuma chamada à API foi feita. Não há ferramenta GitHub conectada nesta sessão.
A autorização do titular para criar a cópia privada continua vigente; falta
acesso configurado, não uma nova decisão sobre a preservação. Nenhum repositório
foi criado e a cópia remota independente continua pendente.
