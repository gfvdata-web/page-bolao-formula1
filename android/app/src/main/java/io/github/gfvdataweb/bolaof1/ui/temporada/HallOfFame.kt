package io.github.gfvdataweb.bolaof1.ui.temporada

import io.github.gfvdataweb.bolaof1.data.Historico
import io.github.gfvdataweb.bolaof1.data.modelo.Classificacao
import io.github.gfvdataweb.bolaof1.data.modelo.HallOfFame
import java.text.Collator
import java.util.Locale

// Aba Hall of Fame (porte de construirRankingHall, construirTabelaVitorias e
// universoJogadores em docs/app.js). Nomes: `hall_of_fame.json` ("nomes") e,
// na falta, o nome do ranking final; por último o próprio id.

private val COLLATOR_PT_BR: Collator = Collator.getInstance(Locale.forLanguageTag("pt-BR"))

/** Tudo o que um jogador já fez no bolão, somando as temporadas em que apareceu num ranking. */
data class UniversoDoJogador(
    /** Nome no ranking da primeira temporada em que aparece. */
    val nome: String,
    val anos: List<Int>,
    /** Soma do `total` oficial de cada temporada. */
    val pontos: Int,
    /** Pontos feitos × pontos possíveis nas corridas em que palpitou (base do % de acerto). */
    val acertoNum: Int,
    val acertoDen: Int,
)

/** Uma linha do ranking de vitórias. [acerto] em % (0–100), ou null sem corridas palpitadas. */
data class LinhaDoHall(
    val id: String,
    val nome: String,
    val ouro: Int,
    val prata: Int,
    val bronze: Int,
    val participacoes: Int,
    val pontos: Int,
    val acerto: Double?,
) {
    val medalhas: Int get() = ouro + prata + bronze
}

/** Um cartão da lista de temporadas: pódio (nomes), tamanho do grupo e se ainda está em jogo. */
data class CartaoDoAno(
    val ano: Int,
    val ouro: String?,
    val prata: String?,
    val bronze: String?,
    val jogadores: Int,
    val emAndamento: Boolean,
)

private data class Medalhas(var ouro: Int = 0, var prata: Int = 0, var bronze: Int = 0)

/**
 * Acerto de cada jogador: pontos feitos contra o máximo possível (`max_points`
 * da temporada), contando só as corridas em que palpitou (`per_round` + o saldo
 * `carry_*` de 2021). Compensação e pontos avulsos não entram.
 */
fun universoDeJogadores(classificacoes: Map<Int, Classificacao>): Map<String, UniversoDoJogador> {
    val universo = linkedMapOf<String, UniversoDoJogador>()
    for (ano in classificacoes.keys.sorted()) {
        val classificacao = classificacoes.getValue(ano)
        val maximo = classificacao.formato.pontosMaximos
        for (jogador in classificacao.jogadores) {
            val feitos = jogador.pontosAcumulados + jogador.pontosPorRodada.values.sum()
            val corridas = jogador.rodadasAcumuladas + jogador.pontosPorRodada.size
            val temAcerto = corridas > 0 && maximo > 0
            val anterior = universo[jogador.id]
            universo[jogador.id] = UniversoDoJogador(
                nome = anterior?.nome ?: jogador.nome,
                anos = (anterior?.anos ?: emptyList()) + ano,
                pontos = (anterior?.pontos ?: 0) + jogador.total,
                acertoNum = (anterior?.acertoNum ?: 0) + if (temAcerto) feitos else 0,
                acertoDen = (anterior?.acertoDen ?: 0) + if (temAcerto) corridas * maximo else 0,
            )
        }
    }
    return universo
}

/** Nome de exibição: `nomes` do Hall of Fame, depois o nome do ranking, depois o id. */
private fun nomeDe(hall: HallOfFame, universo: Map<String, UniversoDoJogador>, id: String): String =
    hall.nomes[id] ?: universo[id]?.nome ?: id

/**
 * Ranking de vitórias: medalhistas primeiro (ouro, prata, bronze, nome), depois
 * quem já disputou mas nunca subiu ao pódio, por pontos somados (desc).
 */
fun rankingDoHall(hall: HallOfFame, classificacoes: Map<Int, Classificacao>): List<LinhaDoHall> {
    val universo = universoDeJogadores(classificacoes)
    val medalhas = linkedMapOf<String, Medalhas>()
    for (podio in hall.anos) {
        podio.ouro?.let { medalhas.getOrPut(it) { Medalhas() }.ouro++ }
        podio.prata?.let { medalhas.getOrPut(it) { Medalhas() }.prata++ }
        podio.bronze?.let { medalhas.getOrPut(it) { Medalhas() }.bronze++ }
    }
    fun linha(id: String, m: Medalhas?): LinhaDoHall {
        val u = universo[id]
        return LinhaDoHall(
            id = id,
            nome = nomeDe(hall, universo, id),
            ouro = m?.ouro ?: 0,
            prata = m?.prata ?: 0,
            bronze = m?.bronze ?: 0,
            participacoes = u?.anos?.size ?: 0,
            pontos = u?.pontos ?: 0,
            acerto = u?.takeIf { it.acertoDen > 0 }?.let { it.acertoNum.toDouble() / it.acertoDen * 100 },
        )
    }
    val medalhistas = medalhas.map { (id, m) -> linha(id, m) }
        .sortedWith(
            compareByDescending<LinhaDoHall> { it.ouro }
                .thenByDescending { it.prata }
                .thenByDescending { it.bronze }
                .thenComparator { a, b -> COLLATOR_PT_BR.compare(a.nome, b.nome) },
        )
    val demais = universo.keys.filter { it !in medalhas }.map { linha(it, null) }
        .sortedWith(
            compareByDescending<LinhaDoHall> { it.pontos }
                .thenComparator { a, b -> COLLATOR_PT_BR.compare(a.nome, b.nome) },
        )
    return medalhistas + demais
}

/** Um cartão por temporada publicada, da mais nova para a mais antiga. */
fun cartoesDosAnos(historico: Historico): List<CartaoDoAno> {
    val universo = universoDeJogadores(historico.classificacoes)
    return historico.classificacoes.keys.sortedDescending().map { ano ->
        val podio = historico.hall.anos.firstOrNull { it.ano == ano }
        fun nome(id: String?) = id?.let { nomeDe(historico.hall, universo, it) }
        CartaoDoAno(
            ano = ano,
            ouro = nome(podio?.ouro),
            prata = nome(podio?.prata),
            bronze = nome(podio?.bronze),
            jogadores = historico.classificacoes.getValue(ano).jogadores.size,
            emAndamento = ano == historico.atual,
        )
    }
}
