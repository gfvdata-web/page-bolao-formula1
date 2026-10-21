package io.github.gfvdataweb.bolaof1.ui.hall

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import io.github.gfvdataweb.bolaof1.data.EstadoDados
import io.github.gfvdataweb.bolaof1.data.Historico
import io.github.gfvdataweb.bolaof1.data.HistoricoRepositorio
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** Estado do histórico (aba Hall of Fame): carrega ao abrir o app e quando o usuário puxa a tela. */
class HistoricoViewModel(private val repositorio: HistoricoRepositorio) : ViewModel() {

    private val _estado = MutableStateFlow(
        EstadoDados<Historico>(dados = null, atualizadoEm = null, atualizando = true, erro = null),
    )
    val estado: StateFlow<EstadoDados<Historico>> = _estado.asStateFlow()

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
        fun fabrica(repositorio: HistoricoRepositorio): ViewModelProvider.Factory = viewModelFactory {
            initializer { HistoricoViewModel(repositorio) }
        }
    }
}
