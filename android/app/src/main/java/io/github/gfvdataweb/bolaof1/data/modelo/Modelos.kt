package io.github.gfvdataweb.bolaof1.data.modelo

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// Espelho dos JSONs publicados pelo site em docs/data/ (formatos definidos nas
// Etapas 3 e 7). Regras para não quebrar quando o site evoluir:
// - campos novos no JSON são ignorados (Json { ignoreUnknownKeys = true });
// - todo campo que não é identidade tem valor padrão, para um campo que suma
//   não derrubar o app;
// - os nomes do JSON ficam em @SerialName; as propriedades seguem o português do projeto.

/** `seasons.json`: temporada atual e a lista de temporadas publicadas. */
@Serializable
data class Temporadas(
    val atual: Int,
    val temporadas: List<InfoTemporada> = emptyList(),
)

@Serializable
data class InfoTemporada(
    val ano: Int,
    @SerialName("format") val formato: Formato = Formato(),
    val rodadas: Int = 0,
    @SerialName("rodadas_totais") val rodadasTotais: Int = 0,
    val parcial: Boolean = false,
    val faltando: List<String> = emptyList(),
)

/** Regras de pontuação da temporada (`bolao/formats.py`). */
@Serializable
data class Formato(
    @SerialName("top_n") val topN: Int = 6,
    val bonus: Boolean = false,
    @SerialName("bonus_points") val pontosBonus: Int = 0,
    @SerialName("compensation") val compensacao: Boolean = false,
    @SerialName("max_points") val pontosMaximos: Int = 0,
)

/** `<ano>/standings.json`: ranking da temporada. */
@Serializable
data class Classificacao(
    @SerialName("season") val temporada: Int,
    @SerialName("format") val formato: Formato = Formato(),
    @SerialName("rounds") val rodadas: List<Rodada> = emptyList(),
    @SerialName("players") val jogadores: List<JogadorClassificado> = emptyList(),
)

@Serializable
data class Rodada(
    @SerialName("round") val numero: Int,
    @SerialName("race_id") val raceId: String,
    @SerialName("race") val corrida: String,
    @SerialName("circuit") val circuito: String = "",
    @SerialName("date") val data: String = "",
    val sprint: Boolean = false,
    @SerialName("bonus_driver") val pilotoDaRodada: String? = null,
    /** Pontuação de quem não apostou na rodada (compensação). */
    @SerialName("min_score") val pontuacaoMinima: Int = 0,
    /** Ordem em que os palpites chegaram no grupo. */
    @SerialName("bet_order") val ordemPalpites: List<String> = emptyList(),
)

@Serializable
data class JogadorClassificado(
    @SerialName("position") val posicao: Int,
    @SerialName("player_id") val id: String,
    @SerialName("name") val nome: String,
    /** Total oficial, já com a compensação das rodadas sem palpite. */
    val total: Int,
    @SerialName("top6_total") val pontosTop: Int = 0,
    @SerialName("bonus_total") val pontosBonus: Int = 0,
    @SerialName("rounds_played") val rodadasJogadas: Int = 0,
    @SerialName("avg_points") val media: Double = 0.0,
    /** Pontos de cada rodada apostada, chave = número da rodada. */
    @SerialName("per_round") val pontosPorRodada: Map<String, Int> = emptyMap(),
    @SerialName("compensated_rounds") val rodadasCompensadas: List<Int> = emptyList(),
    @SerialName("compensation_total") val pontosCompensacao: Int = 0,
)

/** `<ano>/results.json`: grid real do quali por rodada. */
@Serializable
data class Resultados(
    @SerialName("season") val temporada: Int,
    @SerialName("rounds") val rodadas: Map<String, ResultadoRodada> = emptyMap(),
)

@Serializable
data class ResultadoRodada(
    @SerialName("round") val numero: Int,
    @SerialName("race_id") val raceId: String,
    @SerialName("race") val corrida: String,
    @SerialName("date") val data: String = "",
    val sprint: Boolean = false,
    @SerialName("bonus_driver") val pilotoDaRodada: String? = null,
    /** Códigos dos pilotos na ordem do grid (P1 primeiro). */
    @SerialName("order") val grid: List<String> = emptyList(),
    /** Equipe de cada piloto naquela rodada (chave de `equipes.json`). */
    val equipes: Map<String, String> = emptyMap(),
)

/** `<ano>/bets.json`: palpites pontuados, por jogador e rodada. */
@Serializable
data class Palpites(
    @SerialName("season") val temporada: Int,
    @SerialName("players") val jogadores: Map<String, PalpitesDoJogador> = emptyMap(),
)

@Serializable
data class PalpitesDoJogador(
    @SerialName("player_id") val id: String,
    @SerialName("name") val nome: String,
    @SerialName("rounds") val rodadas: Map<String, Palpite> = emptyMap(),
)

@Serializable
data class Palpite(
    @SerialName("round") val rodada: Int,
    @SerialName("top6_detail") val itens: List<ItemPalpite> = emptyList(),
    @SerialName("top6_points") val pontosTop: Int = 0,
    @SerialName("bonus_driver") val pilotoDaRodada: String? = null,
    /** Posição chutada para o piloto da rodada. */
    @SerialName("bonus_guess") val chuteBonus: Int? = null,
    @SerialName("bonus_real_pos") val posicaoRealBonus: Int? = null,
    @SerialName("bonus_points") val pontosBonus: Int = 0,
    val total: Int = 0,
)

@Serializable
data class ItemPalpite(
    @SerialName("pos") val posicao: Int,
    @SerialName("guess") val chute: String,
    val real: String? = null,
    /** 2 = posição exata · 1 = no top N em outra posição · 0 = fora. */
    @SerialName("points") val pontos: Int = 0,
)

/** `<ano>/calendar.json`: todas as corridas da temporada. */
@Serializable
data class Calendario(
    @SerialName("season") val temporada: Int,
    @SerialName("races") val corridas: List<CorridaDoCalendario> = emptyList(),
)

@Serializable
data class CorridaDoCalendario(
    @SerialName("round") val numero: Int,
    @SerialName("race") val corrida: String,
    @SerialName("date") val data: String = "",
    /** Horário do quali em UTC (ISO-8601), quando conhecido. */
    @SerialName("qualifying_utc") val qualiUtc: String? = null,
    val sprint: Boolean = false,
)

/** Um ano de `equipes.json`: nome/cor das equipes e equipe(s) de cada piloto. */
@Serializable
data class EquipesDoAno(
    val equipes: Map<String, Equipe> = emptyMap(),
    /** Piloto → (equipe → em quantas rodadas correu por ela). */
    val pilotos: Map<String, Map<String, Int>> = emptyMap(),
) {
    /** Cor (#RRGGBB) da equipe em que o piloto mais correu no ano. */
    fun corDoPiloto(piloto: String): String? =
        pilotos[piloto]?.maxByOrNull { it.value }?.key?.let { equipes[it]?.cor }
}

@Serializable
data class Equipe(
    val nome: String,
    val cor: String,
)
