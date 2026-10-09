package io.github.gfvdataweb.bolaof1.ui.enviar

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import io.github.gfvdataweb.bolaof1.data.Configuracoes
import io.github.gfvdataweb.bolaof1.data.EnviaPalpite
import io.github.gfvdataweb.bolaof1.data.ResultadoDoEnvio
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class EstadoDoEnvio(
    val texto: String = "",
    /** Rodada digitada (só dígitos); em branco = o pipeline descobre pela mensagem. */
    val rodada: String = "",
    val configurado: Boolean = false,
    val enviando: Boolean = false,
    val resultado: ResultadoDoEnvio? = null,
) {
    val rodadaValida: Boolean get() = rodada.isBlank() || rodada.toIntOrNull()?.let { it in 1..RODADA_MAXIMA } == true
    val podeEnviar: Boolean get() = configurado && texto.isNotBlank() && rodadaValida && !enviando

    companion object {
        const val RODADA_MAXIMA = 30
    }
}

/** Aba Enviar: o texto colado do WhatsApp (e a rodada opcional) vai para o Apps Script. */
class EnviarViewModel(
    private val envio: EnviaPalpite,
    private val configuracoes: Configuracoes,
) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoDoEnvio())
    val estado: StateFlow<EstadoDoEnvio> = _estado.asStateFlow()

    init {
        viewModelScope.launch {
            configuracoes.atuais.collect { atuais -> _estado.update { it.copy(configurado = atuais.completas) } }
        }
    }

    fun mudarTexto(texto: String) = _estado.update { it.copy(texto = texto, resultado = null) }

    fun mudarRodada(rodada: String) = _estado.update { it.copy(rodada = rodada.filter(Char::isDigit).take(2), resultado = null) }

    fun enviar() {
        val pedido = _estado.value
        if (!pedido.podeEnviar) return
        _estado.update { it.copy(enviando = true, resultado = null) }
        viewModelScope.launch {
            val resultado = envio.enviar(configuracoes.atuais.first(), pedido.texto, pedido.rodada.toIntOrNull())
            _estado.update {
                if (resultado == ResultadoDoEnvio.Enviado) {
                    it.copy(texto = "", rodada = "", enviando = false, resultado = resultado)
                } else {
                    it.copy(enviando = false, resultado = resultado)
                }
            }
        }
    }

    companion object {
        fun fabrica(envio: EnviaPalpite, configuracoes: Configuracoes): ViewModelProvider.Factory = viewModelFactory {
            initializer { EnviarViewModel(envio, configuracoes) }
        }
    }
}
