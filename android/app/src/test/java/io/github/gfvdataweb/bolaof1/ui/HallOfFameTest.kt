package io.github.gfvdataweb.bolaof1.ui

import io.github.gfvdataweb.bolaof1.apoio.HistoricoReal
import io.github.gfvdataweb.bolaof1.ui.temporada.cartoesDosAnos
import io.github.gfvdataweb.bolaof1.ui.temporada.rankingDoHall
import io.github.gfvdataweb.bolaof1.ui.temporada.universoDeJogadores
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** Hall of Fame conferido contra docs/data/hall_of_fame.json e os rankings finais reais. */
class HallOfFameTest {

    private val historico = HistoricoReal.historico
    private val hall = historico.hall
    private val ranking = rankingDoHall(hall, historico.classificacoes)

    @Test
    fun medalhasSomadasBatemComOsPodios() {
        val esperadas = hall.anos.sumOf { listOfNotNull(it.ouro, it.prata, it.bronze).size }
        assertTrue(esperadas > 0)
        assertEquals(esperadas, ranking.sumOf { it.medalhas })
        assertEquals(hall.anos.size, ranking.sumOf { it.ouro })
    }

    @Test
    fun medalhistasVemPrimeiroNaOrdemOuroPrataBronze() {
        val medalhistas = ranking.filter { it.medalhas > 0 }
        assertEquals(medalhistas, ranking.take(medalhistas.size))
        medalhistas.zipWithNext().forEach { (a, b) ->
            assertTrue(
                "${a.nome} antes de ${b.nome}",
                a.ouro > b.ouro ||
                    (a.ouro == b.ouro && a.prata > b.prata) ||
                    (a.ouro == b.ouro && a.prata == b.prata && a.bronze >= b.bronze),
            )
        }
        // Quem nunca subiu ao pódio vem depois, por pontos somados.
        ranking.drop(medalhistas.size).zipWithNext().forEach { (a, b) -> assertTrue(a.pontos >= b.pontos) }
    }

    @Test
    fun todoMundoQueDisputouApareceComParticipacoesEPontos() {
        val universo = universoDeJogadores(historico.classificacoes)
        assertTrue(ranking.map { it.id }.containsAll(universo.keys))
        for (linha in ranking) {
            assertEquals(universo[linha.id]?.anos?.size ?: 0, linha.participacoes)
            val somaDosTotais = historico.classificacoes.values.sumOf { c -> c.jogadores.filter { it.id == linha.id }.sumOf { it.total } }
            assertEquals(linha.nome, somaDosTotais, linha.pontos)
            linha.acerto?.let { assertTrue("${linha.nome}: $it%", it in 0.0..100.0) }
        }
    }

    @Test
    fun nomesVemDoHallOfFame() {
        for ((id, nome) in hall.nomes) {
            ranking.firstOrNull { it.id == id }?.let { assertEquals(nome, it.nome) }
        }
        assertTrue(ranking.none { it.nome.isBlank() })
    }

    @Test
    fun umCartaoPorAnoDoMaisNovoParaOMaisAntigo() {
        val cartoes = cartoesDosAnos(historico)
        assertEquals(historico.classificacoes.size, cartoes.size)
        assertEquals(cartoes.map { it.ano }.sortedDescending(), cartoes.map { it.ano })
        assertEquals(listOf(historico.atual), cartoes.filter { it.emAndamento }.map { it.ano })
        for (podio in hall.anos) {
            val cartao = cartoes.first { it.ano == podio.ano }
            assertEquals(hall.nomes[podio.ouro], cartao.ouro)
            assertEquals(hall.nomes[podio.prata], cartao.prata)
            assertEquals(hall.nomes[podio.bronze], cartao.bronze)
            assertTrue(cartao.jogadores > 0)
        }
        assertNotNull(cartoes.firstOrNull { it.ano == 2021 })
    }
}
