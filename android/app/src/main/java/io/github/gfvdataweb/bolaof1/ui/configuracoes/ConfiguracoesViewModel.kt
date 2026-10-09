package io.github.gfvdataweb.bolaof1.ui.configuracoes

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import io.github.gfvdataweb.bolaof1.data.Configuracoes
import io.github.gfvdataweb.bolaof1.data.ConfiguracoesDeEnvio
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class EstadoDasConfiguracoes(
    val url: String = "",
    val chave: String = "",
    /** Os valores salvos já foram lidos (antes disso, não deixa salvar por cima). */
    val carregado: Boolean = false,
    val salvo: Boolean = false,
) {
    val urlValida: Boolean get() = url.isBlank() || ConfiguracoesDeEnvio(url = url).urlValida
    val podeSalvar: Boolean get() = carregado && urlValida
}

/** Tela Configurações: URL do app da web do Apps Script e a chave de envio. */
class ConfiguracoesViewModel(private val configuracoes: Configuracoes) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoDasConfiguracoes())
    val estado: StateFlow<EstadoDasConfiguracoes> = _estado.asStateFlow()

    init {
        viewModelScope.launch {
            val salvas = configuracoes.atuais.first()
            _estado.value = EstadoDasConfiguracoes(url = salvas.url, chave = salvas.chave, carregado = true)
        }
    }

    fun mudarUrl(url: String) = _estado.update { it.copy(url = url, salvo = false) }

    fun mudarChave(chave: String) = _estado.update { it.copy(chave = chave, salvo = false) }

    fun salvar() {
        val atual = _estado.value
        if (!atual.podeSalvar) return
        viewModelScope.launch {
            configuracoes.salvar(ConfiguracoesDeEnvio(url = atual.url, chave = atual.chave))
            _estado.update { it.copy(salvo = true) }
        }
    }

    companion object {
        fun fabrica(configuracoes: Configuracoes): ViewModelProvider.Factory = viewModelFactory {
            initializer { ConfiguracoesViewModel(configuracoes) }
        }
    }
}
