"""Versioned creative expectations captured with each new private Reel request."""

from typing import Any

from app.services.motion_elements import elements_contract
from app.services.motion_movement import movement_contract
from app.services.motion_temporal import POLICY

CREATIVE_CONTRACT_VERSION = "reel-creative-v4"
PROVIDED_DIRECTION_CONTRACT_VERSION = "reel-creative-v5"
SUPPORTED_CREATIVE_CONTRACTS = frozenset(
    {
        "reel-creative-v1",
        "reel-creative-v2",
        "reel-creative-v3",
        CREATIVE_CONTRACT_VERSION,
        PROVIDED_DIRECTION_CONTRACT_VERSION,
        "reel-creative-v6",
        "reel-creative-v7",
    }
)
CREATIVE_CRITERIA = {
    "brief_alignment": "composition",
    "narrative_progression": "motion",
    "motion_role": "motion",
    "visual_development": "composition",
}


def motion_creative_contract() -> dict[str, Any]:
    return {
        "version": CREATIVE_CONTRACT_VERSION,
        "motion_plan_version": "motion-plan-v1",
        "scene_direction_version": "scene-direction-v1",
        "element_library": elements_contract(),
        "scene_direction_rules": (
            "Antes de escrever a animação, desenvolva a direção visual de cada cena a partir da mensagem. "
            "Entregue scene_direction na mesma resposta que motion_plan e HTML/scene_init, sem chamada extra. "
            "Cada cena aponta scene_id do motion_plan, brief_basis nos fatos/pedido confirmados, "
            "visual_representation (como tornar a mensagem visível), composition (quadro principal com hierarquia, "
            "escala relativa, posição, profundidade e espaço para leitura) e narrative_action "
            "(qual interação ou transformação explica a mensagem, e como a atenção passa à próxima cena). "
            "attention_order lista IDs distintos dos focos da própria cena na ordem narrativa. "
            "Descreva cada elemento do plano uma vez: element_id, depicts (objeto/conceito/texto concreto), "
            "appearance (desenho, partes, silhueta ou tratamento usando o kit) e construction. "
            "construction=code para texto/grafismo original; component para componente fornecido com component_id; "
            "generated_asset para ilustração declarada em illustrations com illustration_generation habilitada; "
            "authorized_asset para imagem/vídeo já fornecido "
            "e vinculado pelo asset_id do motion_plan. Não invente caminhos, bibliotecas, arquivos nem geração "
            "de imagens fora dessa capacidade. Código pode desenhar objetos figurativos, ícones, diagramas e cenários "
            "originais; não depende de uma biblioteca pronta. Não simule foto real de produto por ilustração. "
            "Os segundos, estados, trajetórias e relações vivem nos beats/coordination/transition_to_next do "
            "motion_plan: vincule-os à direção, sem criar outro relógio. Preserve a fala; sem transcrição "
            "alinhada, não invente palavras nem sincronismo. Uma cena por cena do plano, mesmos IDs. "
            "Variedade deve servir à mensagem: não preencher a tela com ícones aleatórios ou impor quantidade "
            "de elementos. Se o pedido exige elaboração, vídeo reposicionado com títulos e barras não basta. "
            "Planeje também a evolução da composição entre cenas: foco dominante, escala e relação espacial "
            "entre gravação, objetos e texto. Acrescentar um desenho ao lado do mesmo retângulo de vídeo "
            "em todas as cenas não resolve, por si só, um pedido de elaboração. Repita uma organização visual "
            "quando houver função narrativa; varie-a quando a mensagem mudar, preservando continuidade e kit. "
            "Na correção preserve direção e IDs não afetados; atualize direção, plano e código em conjunto. "
            "Este documento é intenção; não afirma que os quadros foram renderizados ou aprovados."
        ),
        "movement_runtime": movement_contract(legacy=True),
        "temporal_review": dict(POLICY),
        "identity_policy": (
            "Kit confirmado define cores, fontes, logo e identidade. Acervo fornece apenas materiais autorizados. "
            "Skill e biblioteca styles orientam criação; referências orientam acabamento do MOVIMENTO, "
            "nunca substituem kit, fatos ou materiais. Não copiar paleta, fontes, marca ou assets das referências."
        ),
        "motion_plan_rules": (
            "Entregue motion_plan junto com HTML/scene_init na mesma geração. Tempos absolutos em milissegundos, "
            "duração igual a output.duration_ms. Cenas ordenadas cobrem toda a peça; podem se sobrepor em transições. "
            "Cada elemento tem identidade estável, propósito, relações e beats de entrada/leitura/transformação/saída. "
            "Descreva estados concretos, trajetória e curva; execute isso no código com seek(ms). "
            "Use as relações para coordenar atenção, antecipação e continuidade; não force todos os efeitos. "
            "Curvas linear/ease_in/ease_out/ease_in_out usam parameters vazio; cubic_bezier usa x1,y1,x2,y2; "
            "spring usa rigidez, amortecimento, massa positivos. Preserve estados durante intervalos sem movimento. "
            "identity_source é business_kit; style_id pode identificar uma opção de styles, sem impor seu kit. "
            "Imagem/vídeo indicam asset_id da lista autorizada; texto/grafismo usam null. "
            "O plano é intenção verificável, não evidência de qualidade nem novo renderer. "
            "Não invente sincronismo com fala/áudio sem alinhamento fornecido."
        ),
        "requirements": {
            "brief_alignment": "Demonstrar como a peça atende objetivo, pedido, marca e material autorizado.",
            "narrative_progression": "Evoluir a mensagem entre momentos, sem apenas trocar frases equivalentes.",
            "motion_role": "Relacionar transformações visuais à atenção, revelação, conexão ou conclusão da mensagem.",
            "visual_development": (
                "Desenvolver representações visuais pertinentes à mensagem, composição e interação entre elementos; "
                "não confundir variedade com decoração nem restringir a peça a tipografia sobre gravação. "
                "Avaliar se foco, escala e organização dos quadros desenvolvem a narrativa: trocar desenhos "
                "ou frases numa composição repetida não demonstra elaboração por si só. Repetição com propósito "
                "narrativo é válida; justificar a avaliação pelos quadros observados."
            ),
        },
        "direction": (
            "Resuma a ideia central no concept; planeje a arte e representação em scene_direction, "
            "e detalhe tempos, estados, transformação e função no motion_plan. "
            "Implemente esse plano no HTML/scene_init. Abertura, desenvolvimento e conclusão são funções narrativas, "
            "não três cartelas obrigatórias. Preserve a gravação inteira e seu áudio nesta integração. "
            "Use intensidade apropriada ao pedido; não transforme toda marca em um cartaz agitado. "
            "Quando o pedido exige motion elaborado, título sobre vídeo, fades e zoom/reposição da janela, "
            "isoladamente, não bastam: componha transformações que desenvolvam a ideia. "
            "Escolha soluções, sem checklist obrigatório de máscaras, cores, cortes ou quantidade de efeitos."
        ),
        "calibration": [
            {
                "case": "Intensa",
                "qualities": "Tipografia, revelações e transformações de janela/fundo organizam momentos da mensagem.",
                "limit": "Preferência histórica de intensidade não torna esse estilo obrigatório.",
            },
            {
                "case": "Dog",
                "qualities": "Linguagem de cartaz, contraste e janela variável adaptados ao negócio de alimentação.",
                "limit": "Inspiração de funções; não copiar paleta, textos ou ativos para outros negócios.",
            },
            {
                "case": "Luma",
                "qualities": "Composição editorial de beleza com variação de janela e hierarquia adequada à marca.",
                "limit": "Delicadeza pode coexistir com desenvolvimento visual; agitação não mede qualidade.",
            },
            {
                "case": "Giz B",
                "qualities": "Transformação de janela e tema acompanha pergunta, momento sensorial e convite.",
                "limit": "Preferência específica com feedback adicional, sem provar ganho universal de autocrítica.",
            },
        ],
        "reference_scope": (
            "São descrições textuais de qualidades dos ensaios, não quadros de referência enviados nesta chamada. "
            "Não alegar comparação visual com esses vídeos nem copiar suas mídias."
        ),
        "counterexample": (
            "Café Pausa: consertar acentos e manter a animação não demonstra ganho de motion. "
            "Não confundir integridade/legibilidade com atendimento criativo."
        ),
        "evaluation_limit": (
            "Avaliar estados e relações observáveis nas amostras. Código e concept expressam intenção, não prova. "
            "Quadros não certificam fluidez, ritmo integral, sincronismo ou áudio. Aceite final é humano."
        ),
    }


def provided_direction_contract() -> dict[str, Any]:
    """Versioned construction policy; historical v4 bytes/semantics remain intact."""
    return {
        **motion_creative_contract(),
        "version": PROVIDED_DIRECTION_CONTRACT_VERSION,
        "scene_direction_rules": (
            "A direção visual foi fornecida em request.scene_direction antes desta construção. "
            "Implemente essa direção, sem escolher outra representação ou quantidade de cenas. "
            "Devolva scene_direction com os mesmos campos, valores e IDs fornecidos. Isso registra fidelidade "
            "à entrada, não aprovação humana. A direção informa ideia, composição, camadas, ação e atenção; "
            "motion_plan detalha os tempos, estados, relações e curvas, e HTML/scene_init os implementam. "
            "Use os mesmos scene_id e element_id; uma cena por cena do plano. Nenhum segundo relógio. "
            "A implementação tem liberdade de layout fino, dimensões, tempos e curvas coerentes com a direção "
            "e o kit; não adicione fatos ou mídias. construction e component_id devem corresponder aos materiais "
            "e capacidades autorizados. Preserve gravação, ação e voz; sem inventar transcrição ou sincronismo. "
            "Na correção altere a implementação dentro da direção fornecida. Se a solução exigir outra direção, "
            "não declare aprovação ou substituição autorizada: a mudança exige uma nova entrada explícita. "
            "Os quadros e o vídeo ainda precisam da revisão própria; nenhuma aprovação é inferida desta entrada."
        ),
        "direction": (
            "Construa a partir de request.scene_direction. Não volte a resolver a direção junto do código. "
            "Resuma a ideia no concept; complete motion_plan e implemente HTML/scene_init mantendo a direção. "
            "Preserve a gravação inteira e seu áudio, os fatos e o kit. Não acrescente ícones, efeitos, desenhos "
            "ou cenas apenas para aumentar intensidade. Repertório oferece mecanismos, não substitui a direção."
        ),
    }


MEDIA_VISIBILITY_POLICY = (
    "Preservar a duração, ordem temporal e áudio integral da fonte não exige vídeo sempre visível. "
    "Decida por unidade de sentido entre gravação dominante, gravação integrada aos grafismos e motion "
    "em tela inteira, conforme pedido/material; não imponha percentuais nem alternância por cronômetro. "
    "Explique em scene_direction por que o vídeo sai e retorna; tempos/estados ficam no motion_plan. "
    "Durante cobertura gráfica, mantenha o mesmo vídeo e seek no tempo absoluto; sem reiniciar, congelar, "
    "encurtar, reordenar ou duplicar áudio. Quando retornar, mostre o instante corrente da fonte. "
    "Nos momentos visíveis preserve proporção/contain e ação relevante; não use recorte acidental "
    "ou uma faixa minúscula como transição. Motion conceitual não é prova real de produto/pessoa. "
    "Uma ação que precise demonstrar um fato deve permanecer observável no trecho pertinente. "
    "Sem alinhamento real de fala, coreografe texto editorial autorizado sem alegar sincronismo vocal."
)


def alternating_creative_contract(*, provided: bool = False) -> dict[str, Any]:
    """New captures only; legacy v4/v5 contracts remain reproducible."""
    contract = provided_direction_contract() if provided else motion_creative_contract()
    contract["version"] = "reel-creative-v7" if provided else "reel-creative-v6"
    contract["movement_runtime"] = movement_contract()
    contract["media_visibility_policy"] = MEDIA_VISIBILITY_POLICY
    contract["direction"] = contract["direction"].replace(
        "Preserve a gravação inteira e seu áudio", "Preserve duração/ordem da fonte e seu áudio integral"
    ) + " " + MEDIA_VISIBILITY_POLICY
    return contract
