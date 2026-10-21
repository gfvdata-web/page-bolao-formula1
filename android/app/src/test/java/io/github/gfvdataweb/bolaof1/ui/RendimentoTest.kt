package io.github.gfvdataweb.bolaof1.ui

import io.github.gfvdataweb.bolaof1.apoio.TemporadaReal
import io.github.gfvdataweb.bolaof1.ui.temporada.coletarRendimento
import io.github.gfvdataweb.bolaof1.ui.temporada.coletarRendimentoPorJogador
import io.github.gfvdataweb.bolaof1.ui.temporada.diferencaParaGeral
import io.github.gfvdataweb.bolaof1.ui.temporada.jogadoresDoRendimento
import io.github.gfvdataweb.bolaof1.ui.temporada.linhasPorJogador
import io.github.gfvdataweb.bolaof1.ui.temporada.linhasPorPiloto
import io.github.gfvdataweb.bolaof1.ui.temporada.pilotosApostados
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** Contas da aba Rendimento conferidas contra os palpites reais (docs/data/<ano>/bets.json). */
class RendimentoTest {

    private val palpites = TemporadaReal.temporada.palpites
    private val itens = palpites.jogadores.values.flatMap { jogador -> jogador.rodadas.values.flatMap { it.itens } }

    @Test
    fun apostasPorPilotoBatemComAContagemDireta() {
        val linhas = linhasPorPiloto(palpites, null)
        assertEquals(itens.size, linhas.sumOf { it.registro.apostas })
        for (linha in linhas) {
            val doPiloto = itens.filter { it.chute == linha.codigo }
            val registro = linha.registro
            assertEquals(linha.codigo, doPiloto.size, registro.apostas)
            assertEquals(linha.codigo, doPiloto.sumOf { it.pontos }, registro.pontos)
            assertEquals(linha.codigo, doPiloto.count { it.pontos >= 2 }, registro.exatas)
            assertEquals(linha.codigo, doPiloto.count { it.pontos == 1 }, registro.dentro)
            assertEquals(registro.apostas, registro.exatas + registro.dentro + registro.fora)
            assertEquals(2 * registro.exatas + registro.dentro, registro.pontos)
        }
    }

    @Test
    fun pilotosOrdenadosPorMediaDepoisApostasDepoisCodigo() {
        val linhas = linhasPorPiloto(palpites, null)
        linhas.zipWithNext().forEach { (a, b) ->
            val onde = "${a.codigo} antes de ${b.codigo}"
            val ordemOk = a.registro.media > b.registro.media ||
                (a.registro.media == b.registro.media && a.registro.apostas > b.registro.apostas) ||
                (a.registro.media == b.registro.media && a.registro.apostas == b.registro.apostas && a.codigo < b.codigo)
            assertTrue(onde, ordemOk)
        }
    }

    @Test
    fun semFiltroNaoHaComparacaoDiferenteDeSiMesmo() {
        for (linha in linhasPorPiloto(palpites, null)) {
            assertEquals(linha.registro.apostas, linha.apostasGeral)
            assertEquals(linha.registro.media, linha.mediaGeral ?: Double.NaN, 1e-9)
        }
    }

    @Test
    fun filtroDeJogadorContaSoOsPalpitesDele() {
        val (id, jogador) = palpites.jogadores.entries.first { it.value.rodadas.isNotEmpty() }
        val dele = jogador.rodadas.values.flatMap { it.itens }
        val linhas = linhasPorPiloto(palpites, setOf(id))

        assertEquals(dele.size, linhas.sumOf { it.registro.apostas })
        for (linha in linhas) {
            assertEquals(dele.count { it.chute == linha.codigo }, linha.registro.apostas)
            // A comparação é com todos os jogadores.
            assertTrue(linha.apostasGeral >= linha.registro.apostas)
            assertNotNull(linha.mediaGeral)
        }
    }

    @Test
    fun filtroVazioNaoTemLinhas() {
        assertTrue(linhasPorPiloto(palpites, emptySet()).isEmpty())
        assertTrue(coletarRendimento(palpites, emptySet()).isEmpty())
    }

    @Test
    fun todosOsJogadoresAparecemENaOrdemCerta() {
        val linhas = linhasPorJogador(palpites, null)
        assertEquals(palpites.jogadores.keys, linhas.map { it.id }.toSet())
        assertEquals(itens.size, linhas.sumOf { it.registro.apostas })
        for (linha in linhas) {
            val dele = palpites.jogadores.getValue(linha.id).rodadas.values.flatMap { it.itens }
            assertEquals(linha.id, dele.size, linha.registro.apostas)
            assertEquals(linha.id, dele.sumOf { it.pontos }, linha.registro.pontos)
        }
        linhas.zipWithNext().forEach { (a, b) ->
            if (a.registro.apostas == 0) assertEquals("${b.id} sem apostas antes de quem tem", 0, b.registro.apostas)
            else if (b.registro.apostas > 0) assertTrue(a.registro.media >= b.registro.media)
        }
    }

    @Test
    fun filtroDePilotoContaSoAsApostasNele() {
        val codigo = pilotosApostados(palpites).first()
        val linhas = linhasPorJogador(palpites, setOf(codigo))

        assertEquals(itens.count { it.chute == codigo }, linhas.sumOf { it.registro.apostas })
        assertEquals(palpites.jogadores.size, linhas.size) // todos aparecem, mesmo sem apostas no piloto
        for (linha in linhas) {
            val dele = palpites.jogadores.getValue(linha.id).rodadas.values.flatMap { it.itens }
            assertEquals(dele.count { it.chute == codigo }, linha.registro.apostas)
        }
        val geral = coletarRendimentoPorJogador(palpites, null)
        for (linha in linhas) {
            if (geral[linha.id] == null) assertNull(linha.mediaGeral) else assertNotNull(linha.mediaGeral)
        }
    }

    @Test
    fun listasDoFiltroSaoOrdenadas() {
        val pilotos = pilotosApostados(palpites)
        assertEquals(pilotos.sorted(), pilotos)
        assertEquals(palpites.jogadores.keys, jogadoresDoRendimento(palpites).map { it.first }.toSet())
    }

    @Test
    fun diferencaParaGeralTemSinal() {
        assertEquals(0.25, diferencaParaGeral(1.25, 1.0), 1e-9)
        assertEquals(-0.5, diferencaParaGeral(0.5, 1.0), 1e-9)
    }
}
