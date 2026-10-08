package io.github.gfvdataweb.bolaof1

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import io.github.gfvdataweb.bolaof1.ui.home.HomeScreen
import io.github.gfvdataweb.bolaof1.ui.theme.BolaoF1Theme

/** Única Activity do app; as telas são Compose (navegação entra na 9d). */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        setContent {
            BolaoF1Theme {
                HomeScreen(versao = BuildConfig.VERSION_NAME, build = BuildConfig.VERSION_CODE)
            }
        }
    }
}
