package io.github.gfvdataweb.bolaof1.ui.enviar

import io.github.gfvdataweb.bolaof1.data.modelo.SitePipeline

// Regras de exibição do andamento do pipeline (funções puras, testadas em JVM).
// Nomes e estados seguem o app do painel-status (src/etapas_bolao.py).

/** Estado de uma etapa do pipeline. */
enum class EstadoDaEtapa { OK, ANDAMENTO, AGUARDANDO, ERRO, PENDENTE, PULADO, DESCONHECIDO }

fun estadoDaEtapa(estado: String): EstadoDaEtapa = when (estado) {
    "ok" -> EstadoDaEtapa.OK
    "andamento" -> EstadoDaEtapa.ANDAMENTO
    "aguardando" -> EstadoDaEtapa.AGUARDANDO
    "erro" -> EstadoDaEtapa.ERRO
    "pendente" -> EstadoDaEtapa.PENDENTE
    "pulado" -> EstadoDaEtapa.PULADO
    else -> EstadoDaEtapa.DESCONHECIDO
}

/** Cor da etapa: verde (ok), amarelo (em curso), vermelho (erro) ou cinza (o resto). */
enum class TomDaEtapa { OK, AVISO, ERRO, NEUTRO }

fun tomDaEtapa(estado: EstadoDaEtapa): TomDaEtapa = when (estado) {
    EstadoDaEtapa.OK -> TomDaEtapa.OK
    EstadoDaEtapa.ANDAMENTO, EstadoDaEtapa.AGUARDANDO -> TomDaEtapa.AVISO
    EstadoDaEtapa.ERRO -> TomDaEtapa.ERRO
    EstadoDaEtapa.PENDENTE, EstadoDaEtapa.PULADO, EstadoDaEtapa.DESCONHECIDO -> TomDaEtapa.NEUTRO
}

/**
 * Vale a pena consultar de novo em 60 s? Sim se o pipeline está em vigília, a
 * execução ainda roda ou alguma etapa está em andamento/aguardando/pendente.
 * "Pendente" só conta se nenhuma etapa falhou (depois de um erro, as seguintes
 * ficam pendentes para sempre).
 */
fun deveContinuarAcompanhando(site: SitePipeline?): Boolean {
    if (site == null) return false
    val estados = site.etapas.map { estadoDaEtapa(it.estado) }
    val execucao = site.execucao
    val rodando = execucao != null && execucao.status != null && execucao.status != "completed"
    val emCurso = estados.any { it == EstadoDaEtapa.ANDAMENTO || it == EstadoDaEtapa.AGUARDANDO }
    val faltando = EstadoDaEtapa.ERRO !in estados && EstadoDaEtapa.PENDENTE in estados
    return site.emVigilia || rodando || emCurso || faltando
}

/** Só endereços web abrem no navegador (o que vem no JSON não é executado). */
fun linkSeguro(url: String?): String? =
    url?.takeIf { it.startsWith("https://") || it.startsWith("http://") }
