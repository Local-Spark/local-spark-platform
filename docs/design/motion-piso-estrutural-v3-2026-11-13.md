# Piso estrutural v3 — proposto na geração, implementado como avaliador

**Estado: implementado só como função pura. Não selecionado pela geração.**

O perfil ativo continua `motion-production-quality-v2`. O v2 pede `visual_development` em texto e não impõe quantidade de cenas nem proíbe barra editorial. A peça de 13/11 coube nesse contrato e recebeu `adequate`. O v3 não substitui o v2 e não está em `validate_quality_context`.

## O que entrou

`app/services/motion_structural_floor.py`

- `FLOOR_VERSION = motion-production-quality-v3`
- `ENABLED_BY_DEFAULT = False`
- `structural_floor_enabled` só devolve verdadeiro quando o chamador passa exatamente essa versão.
- `evaluate_structural_floor` lê um dict de plano e devolve ids de gate. Não renderiza, não gasta e não marca aceite humano.

Gates desta fatia, iguais para qualquer negócio:

| id | falha quando |
| --- | --- |
| `margin_ban` | `letterbox` não é `kit_color`, ou algum beat tem `text_outside_media` |
| `third_party_mark` | marca de terceiro ainda legível |
| `scale_count` | peça ≥ 8 s com menos de 3 beats ou menos de 3 escalas; peça curta com menos de 2 escalas |
| `role_sequence` | peça ≥ 8 s sem `establish`, `extract` e `invite` |
| `no_dead_hold` | um beat passa de 2500 ms sem mudança de crop |
| `copy_coverage` | frase falada sem `copy`/`support_copy` e sem `audio_trimmed` |
| `anchor_required` | protagonista `type` ou `cta` com âncora `none` |
| `hold_legibility` | hero com hold < 700 ms, altura < 18% ou movimento durante o hold |
| `contrast` | razão declarada < 4.5 no beat de tipo |
| `mechanism_known` | tipo sem ficha, ou ficha fora de `ellipse_to_glyph`, `axis_type_in`, `mask_open_from_point`, `plate_cta` |
| `cta_block` | CTA sem placa, hold < 1000 ms, ou bloco fora da mídia |

## O que esta fatia não prova

Não mede pixel. `anchor_hit` real e `mechanism_executed` no quadro continuam fora. Vazio no retorno do avaliador não é aprovação artística. `human_approval` não muda.

A geração não chama esta função. Ligá-la no builder é outra fatia, com autorização explícita, porque muda o que todo cliente pode admitir.

## Prova automatizada

`app/tests/unit/test_motion_structural_floor.py`

- A forma da peça rejeitada em 13/11 (uma escala, texto na margem, CTA sem placa, marca de terceiro, frases sem beat) falha.
- Um plano de outro ramo, com objeto `serra` e as mesmas regras, passa.
- V2 e omissão não ligam o piso.

Café Pausa é fixture negativa, não regra de produto.
