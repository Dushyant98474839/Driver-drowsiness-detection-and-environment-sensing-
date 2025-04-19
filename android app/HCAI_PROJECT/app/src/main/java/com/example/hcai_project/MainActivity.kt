package com.example.hcai_project

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.localbroadcastmanager.content.LocalBroadcastManager
import androidx.navigation.NavHostController
import androidx.navigation.compose.*
import com.example.hcai_project.screens.ChatScreen
import com.example.hcai_project.screens.HomeScreen
import com.example.hcai_project.screens.SplashScreen
import com.example.hcai_project.ui.theme.HCAI_PROJECTTheme
import com.google.firebase.messaging.FirebaseMessaging

class MainActivity : ComponentActivity() {
    private lateinit var receiver: BroadcastReceiver

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
            if (!task.isSuccessful) {
                Log.w("FCM", "Fetching FCM token failed", task.exception)
                return@addOnCompleteListener
            }
            val token = task.result
            Log.d("FCM", "FCM Token: $token")
        }

        setContent {
            HCAI_PROJECTTheme {
                val navController = rememberNavController()
                val alertViewModel = viewModel<AlertViewModel>(
                    factory = object : ViewModelProvider.Factory {
                        override fun <T : ViewModel> create(modelClass: Class<T>): T {
                            return AlertViewModel(application) as T
                        }
                    }
                )

                receiver = object : BroadcastReceiver() {
                    override fun onReceive(context: Context, intent: Intent) {
                        val title = intent.getStringExtra(MyFirebaseMessagingService.EXTRA_TITLE) ?: "Alert"
                        val message = intent.getStringExtra(MyFirebaseMessagingService.EXTRA_MESSAGE) ?: "No message"
                        alertViewModel.triggerAlert(title, message)
                    }
                }
                LocalBroadcastManager.getInstance(this).registerReceiver(
                    receiver,
                    IntentFilter(MyFirebaseMessagingService.ACTION_ALERT)
                )

                AppNavigator(navController, alertViewModel)
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        LocalBroadcastManager.getInstance(this).unregisterReceiver(receiver)
    }
}

@Composable
fun AppNavigator(navController: NavHostController, alertViewModel: AlertViewModel) {
    NavHost(navController, startDestination = "splash") {
        composable("splash") { SplashScreen(navController) }
        composable("home") { HomeScreen(navController, alertViewModel) }
        composable("chat") { ChatScreen() }
// <-- New Composable Route
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatBotScreen() {
    Scaffold(
        topBar = {
            TopAppBar(title = { Text("Safety Assistant Chatbot") })
        }
    ) { padding ->
        Column(modifier = Modifier.padding(padding).padding(16.dp)) {
            Text("This is the ChatBot screen. Integrate your chatbot UI here.")
            // You can use Retrofit or HttpClient to connect to your Flask bot endpoint here.
        }
    }
}
