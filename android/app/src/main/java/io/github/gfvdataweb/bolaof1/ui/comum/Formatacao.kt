package io.github.gfvdataweb.bolaof1.ui.comum

import io.github.gfvdataweb.bolaof1.data.modelo.Calendario
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.ZonedDateTime
import java.time.format.DateTimeFormatter
import java.util.Locale

// Formatação pura (testada em JVM). O app é em português, independente do
// idioma do celular.

private val PT_BR: Locale = Locale.forLanguageTag("pt-BR")
private val DIA_MES = DateTimeFormatter.ofPattern("dd/MM", PT_BR)
private val DIA_MES_HORA = DateTimeFormatter.ofPattern("dd/MM HH:mm", PT_BR)
private val QUALI = DateTimeFormatter.ofPattern("EEE dd/MM · HH:mm", PT_BR)

/** `2026-09-13` → `13/09`; texto inesperado volta como veio. */
fun dataCurta(isoData: String): String =
    runCatching { LocalDate.parse(isoData).format(DIA_MES) }.getOrDefault(isoData)

/** Idade dos dados exibidos, para a linha "atualizado há…". */
sealed interface Idade {
    data object AgoraMesmo : Idade
    data class Minutos(val quantos: Long) : Idade
    data class Horas(val quantas: Long) : Idade
    /** Mais de um dia: mostra a data e hora (`13/09 18:40`). */
    data class EmData(val texto: String) : Idade
}

fun idadeDosDados(agora: Long, quando: Long, fuso: ZoneId): Idade {
    val minutos = (agora - quando).coerceAtLeast(0) / 60_000
    return when {
        minutos < 1 -> Idade.AgoraMesmo
        minutos < 60 -> Idade.Minutos(minutos)
        minutos < 24 * 60 -> Idade.Horas(minutos / 60)
        else -> Idade.EmData(Instant.ofEpochMilli(quando).atZone(fuso).format(DIA_MES_HORA))
    }
}

data class ProximoQuali(val numero: Int, val corrida: String, val quando: ZonedDateTime) {
    /** `sáb. 03/10 · 09:00` no fuso do celular. */
    val quandoFormatado: String get() = quando.format(QUALI)
}

/** O próximo quali do calendário depois de [agora], ou null se a temporada acabou. */
fun proximoQuali(calendario: Calendario, agora: Instant, fuso: ZoneId): ProximoQuali? =
    calendario.corridas
        .mapNotNull { corrida ->
            val horario = corrida.qualiUtc?.let { runCatching { Instant.parse(it) }.getOrNull() }
            horario?.takeIf { it.isAfter(agora) }?.let { corrida to it }
        }
        .minByOrNull { it.second }
        ?.let { (corrida, horario) -> ProximoQuali(corrida.numero, corrida.corrida, horario.atZone(fuso)) }

/** `#E8002D` → ARGB opaco (`0xFFE8002D`); null se o texto não for uma cor. */
fun argbDeHex(hex: String?): Long? {
    val digitos = hex?.removePrefix("#") ?: return null
    if (digitos.length != 6) return null
    return digitos.toLongOrNull(16)?.let { 0xFF000000L or it }
}
