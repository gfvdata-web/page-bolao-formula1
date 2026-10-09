package io.github.gfvdataweb.bolaof1.data

import io.github.gfvdataweb.bolaof1.apoio.DadosDoSite
import io.github.gfvdataweb.bolaof1.data.modelo.Calendario
import io.github.gfvdataweb.bolaof1.data.modelo.Classificacao
import io.github.gfvdataweb.bolaof1.data.modelo.EquipesDoAno
import io.github.gfvdataweb.bolaof1.data.modelo.Palpites
import io.github.gfvdataweb.bolaof1.data.modelo.Resultados
import io.github.gfvdataweb.bolaof1.data.modelo.Temporadas
import kotlinx.serialization.decodeFromString
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Lê os JSONs REAIS de docs/data (os mesmos que o site publica) com os modelos
 * do app. Se o site mudar um formato de um jeito que o app não entende, este
 * teste fica vermelho antes de alguém instalar um APK quebrado.
 */
class DadosDoSiteTest {

    private val json = TemporadaRepositorio.json
    private val temporadas = json.decodeFromString<Temporadas>(DadosDoSite.texto("seasons.json"))
    private val equipes = json.decodeFromString<Map<String, EquipesDoAno>>(DadosDoSite.texto("equipes.json"))

    @Test
    fun temporadaAtualEstaPublicada() {
        assertTrue(temporadas.temporadas.any { it.ano == temporadas.atual })
        assertNotNull("equipes.json sem o ano atual", equipes[temporadas.atual.toString()])
    }

    @Test
    fun todasAsTemporadasSaoLidasECoerentes() {
        for (info in temporadas.temporadas) {
            val ano = info.ano
            val classificacao = json.decodeFromString<Classificacao>(DadosDoSite.texto("$ano/standings.json"))
            val resultados = json.decodeFromString<Resultados>(DadosDoSite.texto("$ano/results.json"))
            val palpites = json.decodeFromString<Palpites>(DadosDoSite.texto("$ano/bets.json"))
            val calendario = json.decodeFromString<Calendario>(DadosDoSite.texto("$ano/calendar.json"))

            assertEquals("rodadas no standings de $ano", info.rodadas, classificacao.rodadas.size)
            assertEquals("rodadas no results de $ano", info.rodadas, resultados.rodadas.size)
            assertEquals("corridas no calendário de $ano", info.rodadasTotais, calendario.corridas.size)
            val posicoes = classificacao.jogadores.map { it.posicao }
            assertEquals("ranking de $ano fora de ordem", posicoes.sorted(), posicoes)
            val ids = classificacao.jogadores.map { it.id }.toSet()
            assertTrue("palpite de quem não está no ranking ($ano)", ids.containsAll(palpites.jogadores.keys))

            val doAno = equipes.getValue(ano.toString())
            for (rodada in resultados.rodadas.values) {
                for (piloto in rodada.grid) {
                    val equipe = rodada.equipes[piloto]
                    assertNotNull("$ano R${rodada.numero}: $piloto sem cor de equipe", equipe?.let { doAno.equipes[it] })
                }
            }
        }
    }

    /** Regras de 2025 em diante (com compensação): as contas do site fecham. */
    @Test
    fun pontuacaoDasRegrasAtuaisFecha() {
        for (info in temporadas.temporadas.filter { it.formato.compensacao }) {
            val ano = info.ano
            val classificacao = json.decodeFromString<Classificacao>(DadosDoSite.texto("$ano/standings.json"))
            for (jogador in classificacao.jogadores) {
                assertEquals(
                    "$ano ${jogador.id}: total diferente de rodadas + compensação",
                    jogador.pontosPorRodada.values.sum() + jogador.pontosCompensacao,
                    jogador.total,
                )
            }
            val palpites = json.decodeFromString<Palpites>(DadosDoSite.texto("$ano/bets.json"))
            for (jogador in palpites.jogadores.values) {
                for (palpite in jogador.rodadas.values) {
                    val onde = "$ano ${jogador.id} R${palpite.rodada}"
                    assertEquals("$onde: itens do top N", info.formato.topN, palpite.itens.size)
                    assertEquals("$onde: total", palpite.pontosTop + palpite.pontosBonus, palpite.total)
                    assertTrue("$onde: pontos máximos", palpite.total <= info.formato.pontosMaximos)
                }
            }
        }
    }
}
