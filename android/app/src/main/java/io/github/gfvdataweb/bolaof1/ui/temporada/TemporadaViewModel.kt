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
 * Estado da temporada atual, compartilhado pelas abas Ranking, Corridas e
 * Palpites (um download só). Carrega ao abrir o app e quando o usuário puxa
 * a tela para atualizar.
 */
class TemporadaViewModel(private val repositorio: TemporadaRepositorio) : ViewModel() {

    private val _estado = MutableStateFlow(
        EstadoDados<Temporada>(dados = null, atualizadoEm = null, atualizando = true, erro = null),
    )
    val estado: StateFlow<EstadoDados<Temporada>> = _estado.asStateFlow()

    private var carga: Job? = null

    init {
        atualizar()
    }

    /** Busca de novo no site; ignora o pedido se já há uma busca em andamento. */
    fun atualizar() {
        if (carga?.isActive == true) return
        carga = viewModelScope.launch {
            repositorio.observar().collect { _estado.value = it }
        }
    }

    companion object {
        fun fabrica(repositorio: TemporadaRepositorio): ViewModelProvider.Factory = viewModelFactory {
            initializer { TemporadaViewModel(repositorio) }
        }
    }
}
