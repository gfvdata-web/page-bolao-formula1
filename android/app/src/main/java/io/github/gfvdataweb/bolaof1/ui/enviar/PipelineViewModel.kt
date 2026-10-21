package io.github.gfvdataweb.bolaof1.ui.enviar

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import io.github.gfvdataweb.bolaof1.data.PipelineRepositorio
import io.github.gfvdataweb.bolaof1.data.modelo.SitePipeline
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.serialization.SerializationException
import java.io.IOException

/** O que a seção "Última atualização" mostra: o último andamento lido e se a consulta falhou. */
data class EstadoDoPipeline(
    val site: SitePipeline? = null,
    val carregando: Boolean = false,
    val falhou: Boolean = false,
)

/** Andamento do pipeline (aba Enviar). Quem decide quando recarregar é a tela. */
class PipelineViewModel(private val repositorio: PipelineRepositorio) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoDoPipeline())
    val estado: StateFlow<EstadoDoPipeline> = _estado.asStateFlow()

    private var carga: Job? = null

    /** Consulta o painel; ignora o pedido se já há uma consulta em andamento. */
    fun atualizar() {
        if (carga?.isActive == true) return
        _estado.update { it.copy(carregando = true) }
        carga = viewModelScope.launch {
            val novo = try {
                EstadoDoPipeline(site = repositorio.carregar())
            } catch (e: CancellationException) {
                throw e
            } catch (e: IOException) {
                _estado.value.copy(carregando = false, falhou = true)
            } catch (e: SerializationException) {
                _estado.value.copy(carregando = false, falhou = true)
            }
            _estado.value = novo
        }
    }

    companion object {
        fun fabrica(repositorio: PipelineRepositorio): ViewModelProvider.Factory = viewModelFactory {
            initializer { PipelineViewModel(repositorio) }
        }
    }
}
