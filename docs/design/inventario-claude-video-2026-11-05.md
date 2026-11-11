# Inventário local de claude-video — 05/11/2026

Este inventário identifica a cópia instalada no ambiente de desenvolvimento e
os arquivos que podem ser examinados para a v0. É uma fotografia, não uma cópia
de preservação, autorização para redistribuir, integração, pacote de dependências
ou backup. Nenhum arquivo externo foi incorporado ao produto nesta etapa.

## Procedência e integridade

- Fonte declarada: [Felpborges/claude-video](https://github.com/Felpborges/claude-video).
  A instalação observada está em `~/.codex/skills/claude-video` e não contém
  metadados Git. O [estudo anterior](estudo-claude-video-2026-11-05.md) registra
  o commit `ee3dc316759ae266effab49f55c1221c64028081`, 209 arquivos e conferência
  de blobs na instalação; esta rodada não repetiu a comparação com esse commit.
- A tabela abaixo calcula SHA-256 dos bytes encontrados agora, por caminho
  relativo à instalação. Os hashes identificam esta observação local, não provam
  por si só origem, direitos nem correspondência com o commit relatado.
- Há 21 diretórios de estilo e 21 vídeos de galeria. O estudo anterior registra
  que 20 prévias são 16:9 e uma 1:1; direção vertical precisa de adaptação e teste.

## Triagem para a v0

| Conjunto | Utilidade e tratamento antes de adoção |
| --- | --- |
| `SKILL.md`, `referencias/`, `exemplos/` | Orientação para brief, storyboard, perícia e inspeção. Adaptar ao produto e ao contexto da peça; não impor escolha manual de estilo nem tratar referências como fatos. |
| `estilos/*/ESTILO.md`, `LEIA-ME.md` | 21 fichas e instruções sobre mecanismo, ritmo, composição e limitações. Avaliar individualmente e adaptar ao negócio e ao formato. |
| `estilos/*/projeto/` e `modelos/motion/` | Composições e componentes candidatos. Verificar cada projeto, seus avisos e conteúdo, substituir marcas e mídia não autorizada e testar layout e execução antes de uso. |
| `scripts/pericia-movimento.py`, `ritmo.py`, `loop.py`, `_midia.py`, `storyboard.py` | Candidatos para apoio à medição e inspeção. Conferir dependências e limitações; não comprovam qualidade de áudio nem substituem revisão humana. |
| `scripts/render.sh`, `frames.sh`, `novo-projeto.sh` | Apoio à construção e render. O render usa `npx --yes hyperframes@0.8.181`; precisa de alternativa com versões e dependências empacotadas e sem download por pedido. Validar isolamento antes de runtime. |
| `galeria/videos/` | Prévias de referência, não componentes necessários para todas as gerações. Manter fora de uma distribuição até verificação individual dos direitos de conteúdo e ativos. |
| `scripts/higgsfield.py` | Integração de geração de mídia externa; fora do recorte de geração integral de vídeo por IA e não necessária para a primeira fatia. Seu inventário não autoriza chamadas pagas. |

## Direitos e dependências a resolver por item

- `LICENSE` declara MIT para o software e documentação associados e preserva
  avisos de Felipe Borges e dos contribuidores da estrutura anterior;
  `LICENSE-original.txt` contém a licença anterior. A reutilização sujeita-se
  às suas condições, inclusive preservação dos avisos aplicáveis. O README
  atribui vídeos, perícias e estilos a Felipe. A declaração geral não encerra
  a análise de direitos dos ativos e marcas embutidos.
- `estilos/barco-e-montanha/LEIA-ME.md` atribui funções portadas de `paper-world`
  a Jack Roberts e pede preservação do aviso MIT; verificar o código e aviso
  originais antes de redistribuir essa composição.
- `estilos/aviao-em-codigo/CREDITOS.md` atribui a foto Super Tucano a André Gustavo
  Stumpf, CC BY 2.0, e cita a fonte; verificar quais arquivos derivados a
  incorporam e cumprir atribuição e condições antes de incluir qualquer um.
- `estilos/festival-da-lua/LEIA-ME.md` informa que três imagens foram geradas
  com Higgsfield e pede conferir termos antes da redistribuição. A imagem de
  referência, saídas geradas e eventual conteúdo em prévias exigem análise
  própria; não foram liberadas por este inventário.
- `porto-de-nova-york` e `showreel` contêm arquivos WAV que os respectivos
  `LEIA-ME.md` descrevem como sintetizados por seus `trilha.py`. Confirmar
  proveniência e condições de distribuição de cada trilha e dependência.
  `showreel` cita referências de terceiros e menciona a marca Claude; não
  transportar nome, identidade ou materiais de terceiros para peças de cliente.
- Os projetos apontam para GSAP 3.14.2 por CDN e fontes externas, inclusive
  Google Fonts e Fontshare; `aviao-em-codigo` aponta também para Three.js
  0.181.2. `render.sh` fixa HyperFrames 0.8.181 via `npx`. Cada dependência,
  fonte e binário, inclusive transitivos e navegador/FFmpeg, precisa de versão,
  licença e artefato apropriados antes de empacotamento e uso sem rede.
  Não presumir que a gratuidade de uma fonte autorize qualquer redistribuição.
- Outras imagens, sons, marcas, instruções e conteúdo de exemplo ainda exigem
  revisão individual. Os hashes abaixo não são uma auditoria de direitos.

Para preservar fontes adotadas, ainda faltam cópia própria e backup independente,
manifesto de origem e licenças, avaliação de ativos, obtenção das dependências
permitidas e teste de integridade e restauração. Não depender do diretório local
nem presumir que um fork, sozinho, constitua backup.

## Arquivos observados e SHA-256

A lista cobre todos os arquivos regulares encontrados na instalação, inclusive
prévias e ativos ainda sem autorização de redistribuição; sua presença na lista
não é decisão de adotá-los. Os caminhos são relativos à raiz da cópia instalada.

Total observado: **209 arquivos**.

| Arquivo | SHA-256 |
| --- | --- |
| `.gitignore` | `60ab2fcc3d934efefe3bad715ee01852629bfb7cd72caaafbc6e9a45de9f3037` |
| `INSTALAR.md` | `c719180062dfecf99226d12af83aa307b6b7ecdb0892e4b3ff6b3dda687b5590` |
| `LICENSE` | `368252182b0afa27a322a938231b8eceea32d6661110c0f6b20fe607d67c517c` |
| `LICENSE-original.txt` | `b57a46bcddea1143c352d50cac7286cd7f7a0f1fefa58215c04d7450cc57d03f` |
| `NOTION.md` | `79ee3750366b831acd4a8bf6432140e680f08450f12ad6aeccbe446445f7eda1` |
| `README.md` | `9546adae0147bfd9f11b724ece2ea48b965cd83b3cee9396eacdbab1aef96a29` |
| `SKILL.md` | `8bb5dee10e7a2ddd9e5817d8bd97da5b84e8d28f58be070dc50d91add6cfec29` |
| `config.json` | `e683267e89ac8b377044ad17f738edd683ef4c180f4c025e4fcc1d2a00a9235d` |
| `estilos/app-de-design/ESTILO.md` | `2f88d5546f1ed983dad693c472e36a6fcbf7b809dfac69a9765ccaf117e23d64` |
| `estilos/app-de-design/LEIA-ME.md` | `a84ef0e8cb0c836426df892cc953f6cf66197a420cf0cf64f03c5d67d6f62054` |
| `estilos/app-de-design/projeto/app.css` | `5b08297108bb68558ea0f14d28fc356afe371a034dea946a278cc7a7424cb61a` |
| `estilos/app-de-design/projeto/app.js` | `45fddf2fa691ef7bc24f96499236d6d97ef179a1430cbf0863b23f681ca34e54` |
| `estilos/app-de-design/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/app-de-design/projeto/index.html` | `899533aca8bac9c4a2929a83354f8d7926bdbfa8d91f8cdb2fc88ca6e34d8046` |
| `estilos/app-de-design/projeto/motor.js` | `2ffc01b0dc101d92be7c75b17c0027d3b7051f2809e8b05e5b7202801b281d57` |
| `estilos/app-de-motion/ESTILO.md` | `969d45b496b14d5c4125755837e81e53ab1b1635463354d56c90b3c6a3101009` |
| `estilos/app-de-motion/LEIA-ME.md` | `cfe3f1ba021c6e0da8c8877da2fb4a7a2316c3633b841c475890961379f1fc92` |
| `estilos/app-de-motion/projeto/app.css` | `ba4e1e86378c77f4ecdebb936f6ae4d3d1a904be5ed39179fe941738e3ae4fdc` |
| `estilos/app-de-motion/projeto/app.js` | `dbe40c9e2ddd9374206dc854ed9dfa872ced7d195498705dedd7ba17567dacbd` |
| `estilos/app-de-motion/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/app-de-motion/projeto/index.html` | `7665ec05c6d725df005d79c8e5b6a2b3b706c33ca56cb1f472134432bbe2e47f` |
| `estilos/app-de-motion/projeto/motor.js` | `0501b947f0eb3a730bb83ac06a5bc36659477aba9897528f054fc39c007a7be2` |
| `estilos/aviao-em-codigo/CREDITOS.md` | `c3ca0b4c7466fb324aca54a70966762278df42467e2a18b1592884ddb2755327` |
| `estilos/aviao-em-codigo/ESTILO.md` | `a78e749b05216ccc960a6c324bd71bbab6e035086792fdf2bdd721eec6db42f2` |
| `estilos/aviao-em-codigo/LEIA-ME.md` | `3bd27088f6f8e41c99a9fe1f043d6bb50d986c2e08af8e58d838ac276edb36e2` |
| `estilos/aviao-em-codigo/projeto/app.css` | `7c7746af954ead5b942c096f71250cfe21aa8996acc3d0290bcb0e2062d81198` |
| `estilos/aviao-em-codigo/projeto/assets/reais/des-corpo.png` | `55ead2f800a8d9f1058f9b7b862fb9fa1cdfa91f6ad848447a669838d5998302` |
| `estilos/aviao-em-codigo/projeto/assets/reais/des-fundo.jpg` | `3ce17d37d43b1110ec619201c88fa9168e77b3dfefa81c97e3e5a2e0cb25ffe0` |
| `estilos/aviao-em-codigo/projeto/assets/reais/des-linha-corpo.png` | `3f896517d40e69e51e6271734bb3a66ed68a597de074ec05e868d05a9197d814` |
| `estilos/aviao-em-codigo/projeto/assets/reais/des-linha-perto.png` | `979bede91abd1a9874475a9441951eaf8c8289707c79bd3980b9cfcd48a1e894` |
| `estilos/aviao-em-codigo/projeto/assets/reais/des-pas.png` | `26903fc1e0656b727eb6fb303dc7889cd06e38c834ab73046eefb8a7e979a229` |
| `estilos/aviao-em-codigo/projeto/assets/reais/des-perto.png` | `5f1fb2b6cce5f0d5e695b2ad8de21ded68d8a889efd2783e6e8004ab3e529e6b` |
| `estilos/aviao-em-codigo/projeto/assets/reais/sombra.png` | `c55235652ddbd044bd4bda1c9e3ddcd626dd9f4c73bcd1531f9c973780bb4d54` |
| `estilos/aviao-em-codigo/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/aviao-em-codigo/projeto/index.html` | `c4defae13a3fd10128563f52acd58f7004f2e692fcfa43f1cb424b369ab18603` |
| `estilos/aviao-em-codigo/projeto/motor.js` | `508bece11fdcf5207f2cd4ce5fcc225b7636dfe3f0501442650926002258e20c` |
| `estilos/aviao-em-codigo/projeto/plane.js` | `5d0aa3cacde8e5f297da5f3449276ed64e0e0bd9694de2f4ad4ed79a487c48d5` |
| `estilos/aviao-em-codigo/projeto/real.js` | `b41eec96afcc20106ceb16db5f7148935c3c615e51802791055cf8952a79a4ee` |
| `estilos/barco-e-montanha/ESTILO.md` | `af9ccb81e169a2e188e02d329915f768b6d783932906e26d707b484cde7e6904` |
| `estilos/barco-e-montanha/LEIA-ME.md` | `defbecda350deda51a4cdc49c0c80b2605ab09113ecfbeeb412c12c978092dc7` |
| `estilos/barco-e-montanha/projeto/BRIEF.md` | `8e6c387386dccdf59627ebd920d79739e1c2209edc068b75e8343f245193887f` |
| `estilos/barco-e-montanha/projeto/STYLE.md` | `42d44106a9baf760e0ead28e382470f77c1e137748f2404ed89fdd237944c594` |
| `estilos/barco-e-montanha/projeto/hyperframes.json` | `9d8022339f0f5d9b325f5408a9d5ef5a63dfae4a3bf68abfaa243d718e54a4e9` |
| `estilos/barco-e-montanha/projeto/index.html` | `370f8ba1509b1ea0b60ccd0583f38c2457162c377d3ed6a6baca3abe44c1dd68` |
| `estilos/barco-e-montanha/projeto/meta.json` | `030e539a59e884fa12cf3aaa4910b38fc65e90036cccb088cb6154ccb8eabc33` |
| `estilos/barco-e-montanha/projeto/storyboard.json` | `fddcf3686bcd0afbf4e548f9e01e9cbc543e56c31f680115e8d1b764f8b39daf` |
| `estilos/barco-e-montanha/projeto/studio.js` | `b55c0f255aad0d9a93b6da40767ab726425531a9b5acd3c66a0bcf1233765d5a` |
| `estilos/cartaz-gritado/ESTILO.md` | `c495db2a4295c0fb7424fa3508f807f178ca4634b8ccbd99136fc950d4300632` |
| `estilos/cartaz-gritado/LEIA-ME.md` | `5c7cf633ba15c7e9abc372f98010dc6950f70f92db4efa83738f04099db49a2c` |
| `estilos/cartaz-gritado/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/cartaz-gritado/projeto/index.html` | `0eec9a19736651da8e5697b2ed2a9547308c24ab27919df79103710b70773f8a` |
| `estilos/cartaz-gritado/projeto/motor.js` | `3f92d031cdea39177f57315facac2c14c20f8368d515006dcc31d0d28a8836a7` |
| `estilos/cartaz-risografia/ESTILO.md` | `48adf1a128cfb45ac98fd497461d51c70ef40bac5bbed86d3430198a65536500` |
| `estilos/cartaz-risografia/LEIA-ME.md` | `6ad07ddbcc61c07f9e858fff97d3e806727932a4841f1928b79cbfffbf3aaf85` |
| `estilos/cartaz-risografia/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/cartaz-risografia/projeto/index.html` | `13dae15b7aa14f409e156b4daa1fdc091fd146f511db2fa94d92091b81c8a11b` |
| `estilos/cartaz-risografia/projeto/motor.js` | `0f60716326a0fd07995641e1fd09019c8939b79fcf57945682b157add279bc91` |
| `estilos/diagrama-azul-marinho/ESTILO.md` | `38f501a73114c503f2bfbf54c6a581524932542d14d2010817386afe62b3a72f` |
| `estilos/diagrama-azul-marinho/LEIA-ME.md` | `a5c588e97eb0e7edba766afc10298fe319e36bb4e11f6b032eed392cbb8270b4` |
| `estilos/diagrama-azul-marinho/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/diagrama-azul-marinho/projeto/index.html` | `16c1b7f1368f3fd93ec96f978c2a1e928bc762c7afe8bf4f42a49efc5823c257` |
| `estilos/diagrama-azul-marinho/projeto/motor.js` | `ed0d4a285de6e736f665ca51eb0a4c575267a3de5e845e7bfe321fbdaa7fb729` |
| `estilos/dirigivel-a-lapis/ESTILO.md` | `5629b073b354a89519f3c6f64ad9003ede845c0388327cb97343b15edc1eb409` |
| `estilos/dirigivel-a-lapis/LEIA-ME.md` | `c3b9ec783a6cd689a689e49e3256103de71614d9bb01b62d8f94dfd31faaf3f8` |
| `estilos/dirigivel-a-lapis/projeto/cena.js` | `4c8850889650b5762ca44f9132bb63254b16166aa0fdc9a670bf62f80648ad2b` |
| `estilos/dirigivel-a-lapis/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/dirigivel-a-lapis/projeto/index.html` | `fe03a502d56dc77e32fad9de46f94b31c3f4ec36175b875bc973fba8dacb12aa` |
| `estilos/dirigivel-a-lapis/projeto/motor.js` | `3491e8f8ecbe5130ab7eabee5cfaf2bbced32773e254b458929374490a229110` |
| `estilos/documento-vira-video/ESTILO.md` | `14fb035eb47d69915bdf58be51c5135f40c8c252eee04cdc07dc8f4c4def77bf` |
| `estilos/documento-vira-video/LEIA-ME.md` | `fb1f9a00e1243805e7f6702ccf6515211e029922428ed6a3cbfd57cef5faf72e` |
| `estilos/documento-vira-video/movimento-alvo.json` | `01aa02e5f168af1a9a717f5db4e2e1d838d4184086a091f8d5aa4c7555b62b19` |
| `estilos/documento-vira-video/projeto/estilo.js` | `bf76482e07024f11d1283e1d5f4e69d79fb5b18b8872ff0cb3deb1173f6e7983` |
| `estilos/documento-vira-video/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/documento-vira-video/projeto/index.html` | `3da122ba4b2a934cabc1b4dffba9675f7f752611ad6a75121ed63c6a00f728c9` |
| `estilos/editor-ia/ESTILO.md` | `01fdafef0df4c41a83661ed78a0f11be25ea69c650d208e8c55cd7f4459194c3` |
| `estilos/editor-ia/LEIA-ME.md` | `83b45ddd88d8176b18fe65180f7098f0589c47f040b51d981086ebc8beac8a81` |
| `estilos/editor-ia/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/editor-ia/projeto/index.html` | `0fdbb21bc7b56a9f03c542104c9d08dc963ee900f29b2319d80434c23bcf8cd5` |
| `estilos/editor-ia/projeto/motor.js` | `ae6183fe1fff016be62bf4ca0eefc9db126cd7cc2303967519b6ae5413ce4ac3` |
| `estilos/editor-ia/projeto/neve.js` | `bb0a17f57dc240fa48ccaad41962606c934fecfeb7759c84c1c0f925f25f0a1f` |
| `estilos/editor-ia/projeto/papel.js` | `3f2040d4da4b25a22c844742d2cb17ec8809d2aaaf45475af1271b70aeb1039a` |
| `estilos/festival-da-lua/ESTILO.md` | `0846c8ef61abaeeaa757ecedc42d96bea6be5b1393fb25a8d7a991ddf525b9b6` |
| `estilos/festival-da-lua/LEIA-ME.md` | `ddf7cf6b0d6ec7ba5b70b7d5150fecdc14d7aceaf35a1afa840c45766962e2f2` |
| `estilos/festival-da-lua/projeto/cena.js` | `8a7163d407222183ff516c96153382cd234d322ab46cb65411e7f6a490bbb714` |
| `estilos/festival-da-lua/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/festival-da-lua/projeto/index.html` | `53e466d096cebd2cbeb28283e677846d5cdf00b19865c8e4ba927c4cd41c709e` |
| `estilos/festival-da-lua/projeto/midia/gerados/crepusculo-1.png` | `fec1ede3227f9d36c54ecc94f2b7b0bbb284a74e1c1a1a8c283a858e031858ef` |
| `estilos/festival-da-lua/projeto/midia/gerados/dourado-1.png` | `361bb419dd3a21f175759149a22842df59c4e9541c06e8d97f201d598e27f3fa` |
| `estilos/festival-da-lua/projeto/midia/gerados/noite-1.png` | `35b684c7821f611f2b01160a335feda36cb6d5c8c73a8bcc452c86832b002260` |
| `estilos/festival-da-lua/projeto/midia/prompt-crepusculo.txt` | `1e92d548e90633fab3293bc6e6a63c6c3e611e826b0be5f4208c578ab213e9d1` |
| `estilos/festival-da-lua/projeto/midia/prompt-dourado.txt` | `5b222f46a60e96fc5735f0b99ccb30b1d600da92019e0b88d43ba7151a07fee7` |
| `estilos/festival-da-lua/projeto/midia/prompt-noite.txt` | `e4dd19ebe6973372a122ce7c3c08bf9963f5f563d237db8795f66aec95d35e25` |
| `estilos/festival-da-lua/projeto/midia/ref/tinta-17.5s.png` | `464a78040d01677aa49d24e1735704b151584ad45e7d478fdee747eec1e0e3bf` |
| `estilos/festival-da-lua/projeto/motor.js` | `02f590b9c2458aa8d8d0f72037815bc7228bbdda558d440d1edae1710d2bd81d` |
| `estilos/festival-da-lua/projeto/real.js` | `60c005c94f8af411624c0b5ef448b799b08266087722292ef41a5fd6ae24c3f3` |
| `estilos/festival-da-lua/projeto/tinta.js` | `46f24ed3888709b32684081dc48074079fb187dd8cd67e139dfcefd59947f353` |
| `estilos/folha-de-projeto/ESTILO.md` | `22b5a47f3a974fd6c779fdba2ffe5018ec0300704d86756cc7b6e5d3c11d68aa` |
| `estilos/folha-de-projeto/LEIA-ME.md` | `8c67e2c41a537d1f05703528299c5f5d9109d510cc84e0384a3d5209350f93ab` |
| `estilos/folha-de-projeto/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/folha-de-projeto/projeto/index.html` | `282d64cf776949358e35808023d994b471ed21f3458dd10272ab5d4afd293034` |
| `estilos/folha-de-projeto/projeto/motor.js` | `f1d05086463ad66bf302981534bbfd2e20031c8495a7e328490308a2571872e8` |
| `estilos/giz-de-cera/ESTILO.md` | `8c52f4162e82c7e845e03abfbe5941f9a64673164c8e048292b5378f495e4888` |
| `estilos/giz-de-cera/LEIA-ME.md` | `41c7f23ca15679ca552885beb20f7fca8b2bc5e201a22b5aa52c4aae0da581e4` |
| `estilos/giz-de-cera/movimento.json` | `41e0db223188be8164ffbf5c3a81f982f83ad6247dcff62942c66f583d016374` |
| `estilos/giz-de-cera/projeto/_pintura.js` | `d8eb0a3cd49ff11176c5806f9c71239d6401fd1769aede037adf038f5a5d6527` |
| `estilos/giz-de-cera/projeto/giz-de-cera.js` | `093182e11fbb2b59f95bae63c937a4910ff229caaebcc87221aa71a26bcc97ea` |
| `estilos/giz-de-cera/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/giz-de-cera/projeto/index.html` | `ecc9800ac214f7dd07f0c124ee2e54170431fb30ca5d0d485c89f208cdbc4bad` |
| `estilos/giz-de-cera/projeto/motor.js` | `e9745d2de988be4640d19e7294c074c15f2d4a2ef587458da3e1cabc97135175` |
| `estilos/grafico-de-jornal/ESTILO.md` | `0903fe10af8ffb822a6b7e9e0211ad7444846536ec8730dd8b57b39cb58ed3af` |
| `estilos/grafico-de-jornal/LEIA-ME.md` | `90c383c0cbd7b70ededadd640122236c4ea9fea7685aad895f41b5fd03741deb` |
| `estilos/grafico-de-jornal/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/grafico-de-jornal/projeto/index.html` | `f4da615375af4961194dd57e43b110f20538353de2c52f5a0065c79a2ea4756f` |
| `estilos/grafico-de-jornal/projeto/motor.js` | `ea6fcc5562b4226118be4c63d5f25f747a974060cbe6d31099f55b4560e22f68` |
| `estilos/interface-escura-3d/ESTILO.md` | `b5ad4bb82c43a5bf94c566a36942fd8d0dbb2137098e36b38333a77705331d8c` |
| `estilos/interface-escura-3d/LEIA-ME.md` | `cf411b42d7fdf4377b0cd8b857e2c0014bd5beab6e730a6cbdd82c6986ff67b1` |
| `estilos/interface-escura-3d/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/interface-escura-3d/projeto/index.html` | `f4fb40986116f9e8fbc3065768ead12f65742aeb35477eb9e66540c55989e642` |
| `estilos/interface-escura-3d/projeto/motor.js` | `f10072fe835909e86c938591721453fa0092525c91195a63698577d65ac567bc` |
| `estilos/livro-pop-up/ESTILO.md` | `fd44c11921d08a7f379f8e9d8434a1194c94dc1ac5407c27f724d97f3b089dbf` |
| `estilos/livro-pop-up/LEIA-ME.md` | `cf5b17870fab160129c1c3c6a05d51c9f666f2b5fbdee80b94fb094522c561fe` |
| `estilos/livro-pop-up/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/livro-pop-up/projeto/index.html` | `18b908970e399ab846879747a6b7b248861389f84e3ce894158f5e5dd383a626` |
| `estilos/livro-pop-up/projeto/motor.js` | `45039cef6cadb9a10715e29aae887c158a3286cc63ad187d7fe47122f8481124` |
| `estilos/porto-de-nova-york/ESTILO.md` | `1d12bd1f2de71bee3b59c5468d32bc79fcc1aefc07dcc44d95e3bd25ee00a663` |
| `estilos/porto-de-nova-york/LEIA-ME.md` | `9a3c52d844fb2df79c688fb5cc6fcba4f565fce179f60d35ea0c4083a0364c5e` |
| `estilos/porto-de-nova-york/projeto/assets/trilha.wav` | `3dc66fb84c6aafb8ec88ff9627f1f8c5610112f58039a1150f55b740c219a581` |
| `estilos/porto-de-nova-york/projeto/cena.js` | `167fe4768066d38cd2f51ba9c7743fa08f9df4da040825c8fd19adf389dab758` |
| `estilos/porto-de-nova-york/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/porto-de-nova-york/projeto/index.html` | `8526c5d02a10378e599d7e8743d6c6986e76c2993b7f8ee4d379a9d76629afdb` |
| `estilos/porto-de-nova-york/projeto/motor.js` | `f429c6b74d53b969978e45761cc8984edaa519aca2de35a78c4560624aed6c26` |
| `estilos/porto-de-nova-york/projeto/trilha.py` | `ba85cd37d8d80dffda06a9bd9d353aeb23dd35176f35002ec7db926c8dbc938c` |
| `estilos/poster-suico/ESTILO.md` | `1ba172162543244a32d9406e235947ccb23a72921c196aa19473aaa880343cb4` |
| `estilos/poster-suico/LEIA-ME.md` | `7dc30bc7ceae1d158efb2c452dbc36e2f28e3d9e7318443bd1e20717b921dc69` |
| `estilos/poster-suico/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/poster-suico/projeto/index.html` | `45b12d1fb4f58c2cd3628b1b2783805856ada0861127ec503fedbc73e045458b` |
| `estilos/poster-suico/projeto/motor.js` | `f6a41c14c2ab0ddd6f0657e2e6b7a0fac962768f4c6c7f1f4382999092def07d` |
| `estilos/rabisco-de-caneta/ESTILO.md` | `befc7318d40d47ed0eda4218d903e326863d7bc8fd73ecf7e644ab7c89c48963` |
| `estilos/rabisco-de-caneta/LEIA-ME.md` | `e0731c4610150f02c77455483c351da443e7d76e818bd58ad8108cb64629cabb` |
| `estilos/rabisco-de-caneta/movimento.json` | `2b27d8625a6ea247f5cb169748090a92f717ad82319fb360375f204a12a29018` |
| `estilos/rabisco-de-caneta/projeto/_pintura.js` | `d8eb0a3cd49ff11176c5806f9c71239d6401fd1769aede037adf038f5a5d6527` |
| `estilos/rabisco-de-caneta/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/rabisco-de-caneta/projeto/index.html` | `f7c4b305378bb5cce0db0fbc9484618cbd98f1f85339df1da7e4f54c4f0f21a6` |
| `estilos/rabisco-de-caneta/projeto/motor.js` | `e9745d2de988be4640d19e7294c074c15f2d4a2ef587458da3e1cabc97135175` |
| `estilos/rabisco-de-caneta/projeto/rabisco-de-caneta.js` | `07b6b569591b00d6e8202dec81c12321d049bbec25edd32cdac30ed5446d63a3` |
| `estilos/sessao-na-mesa/ESTILO.md` | `190d047ba915519d5b086a7ac00c3d6b94b87c8a03a0291dbd5d071de1d79490` |
| `estilos/sessao-na-mesa/LEIA-ME.md` | `a95df6eeb2e15175cfd7f6282f233d3bbee8dbca4b3628333020f12a0ca9b4e5` |
| `estilos/sessao-na-mesa/movimento-alvo.json` | `1951061783a8d53a4a0f67e62d1e94182b5a4cb77f94dbed9d2c4a411c3e4a63` |
| `estilos/sessao-na-mesa/projeto/estilo.js` | `351ffc6488098afb0d88c7334ace157853130ce16635b24623bf8e8c7599c417` |
| `estilos/sessao-na-mesa/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/sessao-na-mesa/projeto/index.html` | `670360b2733eed085102534ad67951feb7904d572b1851ecd2bd5d6ef14da3d1` |
| `estilos/showreel/ESTILO.md` | `aac56f67e3fe01ce64ac0acb232f64f42ed916cd4ab1f448e6691f160fb90261` |
| `estilos/showreel/LEIA-ME.md` | `cc6120879c504c325b62e328d157093a89397b067c99ac8acee5bf5ed2f04f6a` |
| `estilos/showreel/projeto/assets/trilha.wav` | `52abd5d451ebfcac4c036a293a8d746c16bacf7fdbc4ec8d0aa0fedd1c9fc9ca` |
| `estilos/showreel/projeto/hyperframes.json` | `57fda7e9bd8054756b082c9c2f3aa4c4e5f2c69c5199ad458d467401527ca4f7` |
| `estilos/showreel/projeto/index.html` | `4a1822cc3ded0a1b33b8c4942ed07fa979c8349d59ab65013a2052eed7d611d2` |
| `estilos/showreel/projeto/motor.js` | `202c3899d694ef0e7ef0e75671c950ed310c9937c836aa2c91a8d0d938d1c9c2` |
| `estilos/showreel/projeto/trilha.py` | `3d36d1c5deb20f9b483ae229ddb414ff7ac168d37f67ad75a85d1f31971dfd80` |
| `exemplos/brief-de-loop.md` | `8d7e5c295e51b3e202a6a2195ff8fc12ed5717659c2c5ed891bb621f7cd91e22` |
| `exemplos/storyboard.json` | `1f5b6b3e7d96791c4f5806ab699929f2fdce3dcd625ecb24d8a0bc757e780b9c` |
| `galeria/estilos.js` | `9cd76ceaa66f48958fdc65695637e8293ff0c00e387b55527a621a1507a66a5e` |
| `galeria/index.html` | `ce9d3adfb4fdcebd49f7bcb66d8a1454e50643e1dc04c243c6f9f7920f17e066` |
| `galeria/videos/app-de-design.mp4` | `1eb2b871bf66ef4f33f8c42aa3264cc278379e715fba38a9e01e11e52f1f0e9a` |
| `galeria/videos/app-de-motion.mp4` | `f6435b23e8a4240400f4d30e5649887f5b640e67b237698b0f30086350dd3270` |
| `galeria/videos/aviao-em-codigo.mp4` | `97e9cc91958d7e2c95ac440ee44aaf0266566f24e133c47058970400686549f0` |
| `galeria/videos/barco-e-montanha.mp4` | `39d5ca3f48a7bd9bf010dd0bac8b167ec31c11b60cdce382c3bcebcb1ada0b9e` |
| `galeria/videos/cartaz-gritado.mp4` | `e29f9d249f7f8853434aa17b3350310adcf6fb3e6e02b5728622ebbaddf43800` |
| `galeria/videos/cartaz-risografia.mp4` | `0cc6e4427814375e2d5a83b85b0838ff8aaba15194687f4154df3029c134528e` |
| `galeria/videos/diagrama-azul-marinho.mp4` | `23e0ef60d76f7581569e8dafcbc4173acf03bfce7404b32a37ac625df0a25242` |
| `galeria/videos/dirigivel-a-lapis.mp4` | `a8217d2d3e613283048e9ccab82ac5d19485c1262ba92569894744e54066e362` |
| `galeria/videos/documento-vira-video.mp4` | `8577864442d0990453c20fc93b10cd0fa1431fb5318593a6fcaf60653d7c67fd` |
| `galeria/videos/editor-ia.mp4` | `b8c4be30c6ce1fa45957f1234c56d32d142349d726b305f9cceb88142247132c` |
| `galeria/videos/festival-da-lua.mp4` | `b5acf592b33fea07ccaefaf6413a13af01f93db702e6d03caa7f98558097e677` |
| `galeria/videos/folha-de-projeto.mp4` | `07416cc1a8fc20bbdad0eefc15a815c100db405f384cbff908bc11e0586245c3` |
| `galeria/videos/giz-de-cera.mp4` | `695f2ce1e87e0715ea4449dc52ab2de9177114d47fced6f433c662f888eac2a2` |
| `galeria/videos/grafico-de-jornal.mp4` | `5832cd9883c4163fa60df9f60ec68a284c54cbbb35ca2272b82518237acd68b5` |
| `galeria/videos/interface-escura-3d.mp4` | `f85a40a40de663dd480bb9513514928174e8261afb765af8e416e8bfd3f7c9a5` |
| `galeria/videos/livro-pop-up.mp4` | `910a9391384d69f12afe47db0ad1cbb213e78dfdb627d75b05e2c9ee265932df` |
| `galeria/videos/porto-de-nova-york.mp4` | `c49c229928a2267e6825ba8f58e5d9f0b3444086c5032a22285d131bb835df89` |
| `galeria/videos/poster-suico.mp4` | `1757ac4d6fa9024b3b2883af651f2b2ee18a814b2d166bed0d848eb5ac5bb366` |
| `galeria/videos/rabisco-de-caneta.mp4` | `d603856b98b328d37c67c8ffa70ba708ab6c4b4cb9f225f8b5bc56dcb2209bba` |
| `galeria/videos/sessao-na-mesa.mp4` | `45aca35eb3661b477b84e9d1958ef3eef0ff95ee67f3bcf3865b049eb163f254` |
| `galeria/videos/showreel.mp4` | `81e4240a2279689f8e9bf784c17ca7c6cc58c5e45e813eab5a5a9f966012f94f` |
| `instalar.sh` | `9cf9bd014e5f7b70a4f43622abc8fe5108e9899d026ccd764e1032655ce8a685` |
| `modelos/motion/hyperframes.json` | `9d8022339f0f5d9b325f5408a9d5ef5a63dfae4a3bf68abfaa243d718e54a4e9` |
| `modelos/motion/index.html` | `4d1db03521bfe21371902a8543c017a97236b231ff3cf51aae5d094e2df46f40` |
| `modelos/motion/meta.json` | `030e539a59e884fa12cf3aaa4910b38fc65e90036cccb088cb6154ccb8eabc33` |
| `modelos/motion/studio.js` | `bb8be159438f361afc299c9023aabd59e61504060d82573559f2daa1f9b5b97f` |
| `perguntas.md` | `412017b271150d8ea9de66d064f7d243b9c580fab10512e945aa7b49990a7b08` |
| `referencias/esqueleto-de-frame.md` | `8cbdc307a8284d136574eb5e7acf5ee74983f758f31f3b713fa4d891078869d6` |
| `referencias/formato-de-estilo.md` | `07ff107349fc5e9361718b337e43fbdf5f5b5a2aa45f39b41fad8ac25eaacfb0` |
| `referencias/hyperframes.md` | `ec576f0ebc99b582a899688f138a127f02962b6f407dc788ea02f0ff667a92dc` |
| `referencias/loops.md` | `5bdaaa370cf9bf17ce0643022d30d3409b120d902119baf931d75ca6d5cb141e` |
| `referencias/midia.md` | `3000fe674fb7e07101197401ebb1d7614abc859c64b75dcd5e528b54c4b54b4a` |
| `referencias/movimento.md` | `a915b0451cf8d00426932a13451dd867b8140ebab25c9bc6b78a1e867e8952a1` |
| `referencias/os-5-habitos.md` | `d1cb4add6791a3e7bd5a8d89971b4b4bad050964fc358f731ba231ed7d2a1136` |
| `referencias/pericia-da-referencia.md` | `48b59fc91a2af20c53e9c638fb0153479becb5f4a8c5823711a9ec31605b7015` |
| `scripts/_midia.py` | `641fdfee07d0b1b5c70a8d759eeddb6e37e5f05bc429d318699ce995e4b22273` |
| `scripts/checar.sh` | `c0bc899c40e24242c14041ab959e3feccb0aea7a250ee22646a07e30f55b88bd` |
| `scripts/frames.sh` | `3bff985a76045a861978fb435261a6737234f4a0e4b139cb88f1f04175dd84f6` |
| `scripts/galeria.py` | `0aba6565f90fb9d4190dfe6c21fe137bd260d7eced441e621f5d2db0b581a012` |
| `scripts/higgsfield.py` | `ff253f78220dc7a37a001e7971ccc8bf0b77a22520b1377bca8211e6d0613b42` |
| `scripts/loop.py` | `8caa3035eb30d4359d77117bda42e90f9f980af9180d177d2877896559e7ba96` |
| `scripts/novo-projeto.sh` | `0f8854ddaef18d81c41da8fac478b3da2935acc6d1ee8b800ee2fd9b93777ca7` |
| `scripts/pericia-movimento.py` | `77326547a76e837c47a8d1aec97902dc12d9a22a9a7d95b80a75a7fed5fb6e98` |
| `scripts/portoes.py` | `487967532fe2e09f6405cc36f4255e153f13e4ef1d8ac52f15fd48213643f968` |
| `scripts/render.sh` | `b59d6a9fea7d4d59ad5cfb7460e0391e2408879b004732f3cab85f5a7200141b` |
| `scripts/ritmo.py` | `8995f7d0b3804b9edc62b38af682ec960fef4980c14b5ab8fc24d4064920c106` |
| `scripts/storyboard.py` | `b065b86a553437c3b6df5c3d2d7e2d503581ec36f13d4b7d1c7ff3c83583514a` |
