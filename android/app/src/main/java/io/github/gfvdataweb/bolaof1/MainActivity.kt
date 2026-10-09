package io.github.gfvdataweb.bolaof1

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import io.github.gfvdataweb.bolaof1.ui.AppBolao
import io.github.gfvdataweb.bolaof1.ui.theme.BolaoF1Theme

/** Única Activity do app; as telas são Compose, com navegação por abas. */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        val container = (application as BolaoApp).container
        setContent {
            BolaoF1Theme {
                AppBolao(container, versao = BuildConfig.VERSION_NAME, build = BuildConfig.VERSION_CODE)
            }
        }
    }
}
