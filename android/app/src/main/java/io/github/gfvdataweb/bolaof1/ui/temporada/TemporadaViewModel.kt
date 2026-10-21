package io.github.gfvdataweb.bolaof1.ui.temporada

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import io.github.gfvdataweb.bolaof1.data.EstadoDados
import io.github.gfvdataweb.bolaof1.data.Temporada
import io.github.gfvdataweb.bolaof1.data.TemporadaRepositorio
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * Estado da temporada exibida, compartilhado pelas abas Ranking, Corridas e
 * Palpites (um download só). Mostra a atual até o usuário abrir outro ano
 * ([abrirAno]); carrega ao abrir o app e quando ele puxa a tela para atualizar.
 */
class TemporadaViewModel(private val repositorio: TemporadaRepositorio) : ViewModel() {

    private val _estado = MutableStateFlow(
        EstadoDados<Temporada>(dados = null, atualizadoEm = null, atualizando = true, erro = null),
    )
    val estado: StateFlow<EstadoDados<Temporada>> = _estado.asStateFlow()

    private val _anoEscolhido = MutableStateFlow<Int?>(null)

    /** Ano que o usuário abriu; null = a temporada atual. */
    val anoEscolhido: StateFlow<Int?> = _anoEscolhido.asStateFlow()

    private var carga: Job? = null

    init {
        atualizar()
    }

    /** Busca de novo no site; ignora o pedido se já há uma busca em andamento. */
    fun atualizar() {
        if (carga?.isActive == true) return
        iniciarCarga()
    }

    /** Troca a temporada exibida, cancelando a carga em andamento. */
    fun abrirAno(ano: Int) {
        if (_anoEscolhido.value == ano) return
        _anoEscolhido.value = ano
        recarregarDoZero()
    }

    fun voltarParaAtual() {
        if (_anoEscolhido.value == null) return
        _anoEscolhido.value = null
        recarregarDoZero()
    }

    private fun recarregarDoZero() {
        carga?.cancel()
        // Não mostra os dados do ano anterior enquanto o novo carrega.
        _estado.value = EstadoDados(dados = null, atualizadoEm = null, atualizando = true, erro = null)
        iniciarCarga()
    }

    private fun iniciarCarga() {
        val ano = _anoEscolhido.value
        carga = viewModelScope.launch {
            repositorio.observar(ano).collect { _estado.value = it }
        }
    }

    companion object {
        fun fabrica(repositorio: TemporadaRepositorio): ViewModelProvider.Factory = viewModelFactory {
            initializer { TemporadaViewModel(repositorio) }
        }
    }
}
