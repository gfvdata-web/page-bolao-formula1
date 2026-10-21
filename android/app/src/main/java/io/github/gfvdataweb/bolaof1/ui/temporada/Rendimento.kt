package io.github.gfvdataweb.bolaof1.ui.temporada

import io.github.gfvdataweb.bolaof1.data.modelo.Palpites
import java.text.Collator
import java.util.Locale

// Aba Rendimento (porte de coletarRendimento & cia. em docs/app.js): quanto cada
// piloto rende para quem aposta nele, e quanto cada jogador rende por aposta.
// Só o top N conta; o piloto da rodada (bônus) fica de fora, como no site.
// Filtro `null` = "todos" (os JS usam a string "todos").

private val COLLATOR_PT_BR: Collator = Collator.getInstance(Locale.forLanguageTag("pt-BR"))

/** Soma das apostas de top N: 2 pts = posição exata, 1 = dentro do top N, 0 = fora. */
data class RegistroRendimento(
    val apostas: Int = 0,
    val pontos: Int = 0,
    val exatas: Int = 0,
    val dentro: Int = 0,
    val fora: Int = 0,
) {
    /** Pontos por aposta; 0 se ainda não há apostas. */
    val media: Double get() = if (apostas > 0) pontos.toDouble() / apostas else 0.0

    fun somando(pontosDoItem: Int) = RegistroRendimento(
        apostas = apostas + 1,
        pontos = pontos + pontosDoItem,
        exatas = exatas + if (pontosDoItem >= 2) 1 else 0,
        dentro = dentro + if (pontosDoItem == 1) 1 else 0,
        fora = fora + if (pontosDoItem < 1) 1 else 0,
    )
}

/** Uma linha do modo "por piloto". [mediaGeral] = média do piloto com todos os jogadores (null se ninguém apostou nele). */
data class LinhaPorPiloto(
    val codigo: String,
    val registro: RegistroRendimento,
    val apostasGeral: Int,
    val mediaGeral: Double?,
)

/** Uma linha do modo "por jogador". [mediaGeral] = média do jogador somando todos os pilotos. */
data class LinhaPorJogador(
    val id: String,
    val nome: String,
    val registro: RegistroRendimento,
    val mediaGeral: Double?,
)

/** Rendimento de cada piloto nas apostas dos jogadores em [ids] (null = todos). */
fun coletarRendimento(palpites: Palpites, ids: Set<String>?): Map<String, RegistroRendimento> {
    val porPiloto = mutableMapOf<String, RegistroRendimento>()
    for ((id, jogador) in palpites.jogadores) {
        if (ids != null && id !in ids) continue
        for (rodada in jogador.rodadas.values) {
            for (item in rodada.itens) {
                porPiloto[item.chute] = (porPiloto[item.chute] ?: RegistroRendimento()).somando(item.pontos)
            }
        }
    }
    return porPiloto
}

/** Rendimento de cada jogador (chave = id do mapa de palpites) só nas apostas nos pilotos em [codigos] (null = todos). */
fun coletarRendimentoPorJogador(palpites: Palpites, codigos: Set<String>?): Map<String, RegistroRendimento> {
    val porJogador = mutableMapOf<String, RegistroRendimento>()
    for ((id, jogador) in palpites.jogadores) {
        for (rodada in jogador.rodadas.values) {
            for (item in rodada.itens) {
                if (codigos != null && item.chute !in codigos) continue
                porJogador[id] = (porJogador[id] ?: RegistroRendimento()).somando(item.pontos)
            }
        }
    }
    return porJogador
}

/** Modo "por piloto": maior média primeiro; empate por mais apostas e depois pelo código. */
fun linhasPorPiloto(palpites: Palpites, ids: Set<String>?): List<LinhaPorPiloto> {
    val geral = coletarRendimento(palpites, null)
    return coletarRendimento(palpites, ids)
        .map { (codigo, registro) ->
            LinhaPorPiloto(codigo, registro, geral[codigo]?.apostas ?: 0, geral[codigo]?.media)
        }
        .sortedWith(
            compareByDescending<LinhaPorPiloto> { it.registro.media }
                .thenByDescending { it.registro.apostas }
                .thenBy { it.codigo },
        )
}

/** Modo "por jogador": todos aparecem; quem não tem apostas no filtro vai para o fim. */
fun linhasPorJogador(palpites: Palpites, codigos: Set<String>?): List<LinhaPorJogador> {
    val doFiltro = coletarRendimentoPorJogador(palpites, codigos)
    val geral = coletarRendimentoPorJogador(palpites, null)
    return palpites.jogadores.map { (id, jogador) ->
        val registro = doFiltro[id] ?: RegistroRendimento()
        LinhaPorJogador(id, jogador.nome, registro, geral[id]?.takeIf { it.apostas > 0 }?.media)
    }.sortedWith(
        compareBy<LinhaPorJogador> { it.registro.apostas == 0 }
            .thenByDescending { it.registro.media }
            .thenComparator { a, b -> COLLATOR_PT_BR.compare(a.nome, b.nome) },
    )
}

/** Jogadores que têm palpites, ordenados por nome (opções do filtro do modo "por piloto"). */
fun jogadoresDoRendimento(palpites: Palpites): List<Pair<String, String>> =
    palpites.jogadores.map { (id, jogador) -> id to jogador.nome }
        .sortedWith { a, b -> COLLATOR_PT_BR.compare(a.second, b.second) }

/** Pilotos que alguém já apostou, em ordem alfabética (opções do filtro do modo "por jogador"). */
fun pilotosApostados(palpites: Palpites): List<String> =
    coletarRendimento(palpites, null).keys.sorted()

/** Diferença entre a média e a média de comparação: ≥ 0 é "acima" (▲), negativa é "abaixo" (▼). */
fun diferencaParaGeral(media: Double, mediaGeral: Double): Double = media - mediaGeral
