package io.github.gfvdataweb.bolaof1.ui

import io.github.gfvdataweb.bolaof1.apoio.TemporadaReal
import io.github.gfvdataweb.bolaof1.ui.temporada.cartoesDasCorridas
import io.github.gfvdataweb.bolaof1.ui.temporada.linhasDoRanking
import io.github.gfvdataweb.bolaof1.ui.temporada.palpitesDaRodada
import io.github.gfvdataweb.bolaof1.ui.temporada.rodadasPontuadas
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** Regras de exibição das abas, conferidas contra a temporada atual real. */
class ApresentacaoTest {

    private val temporada = TemporadaReal.temporada
    private val topN = temporada.classificacao.formato.topN

    @Test
    fun rankingSegueAOrdemOficial() {
        val linhas = linhasDoRanking(temporada)
        assertEquals(temporada.classificacao.jogadores.map { it.id }, linhas.map { it.id })
        assertEquals(1, linhas.first().posicao)
    }

    @Test
    fun corridasDaMaisRecenteParaAMaisAntiga() {
        val cartoes = cartoesDasCorridas(temporada)
        assertEquals(temporada.classificacao.rodadas.size, cartoes.size)
        assertEquals(cartoes.map { it.numero }.sortedDescending(), cartoes.map { it.numero })
        for (cartao in cartoes) {
            assertEquals("R${cartao.numero}: top N do grid", topN, cartao.topN.size)
            assertEquals((1..topN).toList(), cartao.topN.map { it.posicao })
            assertTrue("R${cartao.numero}: piloto sem cor", cartao.topN.all { it.corHex != null })
        }
    }

    @Test
    fun pontosDaRodadaOrdenadosPorPontosDepoisId() {
        for (cartao in cartoesDasCorridas(temporada)) {
            cartao.pontos.zipWithNext().forEach { (a, b) ->
                assertTrue("R${cartao.numero}: ${a.id} antes de ${b.id}", a.pontos > b.pontos || (a.pontos == b.pontos && a.id < b.id))
            }
        }
    }

    /** Com compensação, somar os pontos de cada corrida dá o total do ranking. */
    @Test
    fun somaDasCorridasFechaComOTotal() {
        if (!temporada.classificacao.formato.compensacao) return
        val cartoes = cartoesDasCorridas(temporada)
        for (jogador in temporada.classificacao.jogadores) {
            val soma = cartoes.sumOf { cartao -> cartao.pontos.firstOrNull { it.id == jogador.id }?.pontos ?: 0 }
            assertEquals("soma das corridas de ${jogador.id}", jogador.total, soma)
        }
    }

    @Test
    fun palpitesDaRodadaMaisRecente() {
        val numero = rodadasPontuadas(temporada).first()
        val rodada = checkNotNull(palpitesDaRodada(temporada, numero))
        assertEquals(topN, rodada.resultado.size)
        assertTrue(rodada.palpites.isNotEmpty())
        rodada.palpites.forEach { assertEquals(topN, it.itens.size) }
        rodada.palpites.zipWithNext().forEach { (a, b) ->
            assertTrue("${a.id} antes de ${b.id}", a.total > b.total || (a.total == b.total && a.id < b.id))
        }
    }

    @Test
    fun rodadaInexistenteNaoTemPalpites() {
        assertNull(palpitesDaRodada(temporada, 999))
    }
}
