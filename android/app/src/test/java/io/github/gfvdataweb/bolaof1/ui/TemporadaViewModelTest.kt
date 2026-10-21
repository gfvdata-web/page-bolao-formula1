package io.github.gfvdataweb.bolaof1.ui

import io.github.gfvdataweb.bolaof1.apoio.SiteLocal
import io.github.gfvdataweb.bolaof1.data.CacheDeArquivos
import io.github.gfvdataweb.bolaof1.data.FonteRemota
import io.github.gfvdataweb.bolaof1.data.TemporadaRepositorio
import io.github.gfvdataweb.bolaof1.ui.temporada.TemporadaViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import okhttp3.OkHttpClient
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

/** Troca de temporada no ViewModel, com um site local e tudo rodando na thread do teste. */
@OptIn(ExperimentalCoroutinesApi::class)
class TemporadaViewModelTest {

    @get:Rule
    val pasta = TemporaryFolder()

    private val site = SiteLocal()

    @Before
    fun prepara() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun encerra() {
        Dispatchers.resetMain()
        site.close()
    }

    private fun viewModel() = TemporadaViewModel(
        TemporadaRepositorio(
            fonte = FonteRemota(OkHttpClient(), site.urlDosDados),
            cache = CacheDeArquivos(File(pasta.root, "cache")),
            io = Dispatchers.Unconfined,
        ),
    )

    @Test
    fun comecaNaTemporadaAtual() {
        val vm = viewModel()
        assertNull(vm.anoEscolhido.value)
        val dados = checkNotNull(vm.estado.value.dados)
        assertEquals(dados.atual, dados.ano)
    }

    @Test
    fun abrirAnoTrocaAsTelasEVoltarParaAtualDesfaz() {
        val vm = viewModel()
        val atual = checkNotNull(vm.estado.value.dados).atual

        vm.abrirAno(2025)
        assertEquals(2025, vm.anoEscolhido.value)
        assertEquals(2025, checkNotNull(vm.estado.value.dados).ano)
        assertFalse(vm.estado.value.atualizando)

        vm.voltarParaAtual()
        assertNull(vm.anoEscolhido.value)
        assertEquals(atual, checkNotNull(vm.estado.value.dados).ano)
    }

    @Test
    fun atualizarRecarregaOAnoEscolhido() {
        val vm = viewModel()
        vm.abrirAno(2024)
        vm.atualizar()
        assertEquals(2024, checkNotNull(vm.estado.value.dados).ano)
    }

    @Test
    fun anoSemDadosNemInternetFicaSemDadosMasMantemAEscolha() {
        val vm = viewModel()
        site.foraDoAr = true
        vm.abrirAno(2023)
        assertEquals(2023, vm.anoEscolhido.value)
        assertNull(vm.estado.value.dados)
        assertFalse(vm.estado.value.atualizando)
    }
}
