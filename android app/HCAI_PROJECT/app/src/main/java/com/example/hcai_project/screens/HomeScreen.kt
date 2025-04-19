package com.example.hcai_project.screens

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import com.example.hcai_project.AlertViewModel
import com.example.hcai_project.DB.AlertEntity

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(navController: NavController, alertViewModel: AlertViewModel = viewModel()) {
    val alertData by alertViewModel.showAlert.collectAsState()
    val alertHistory by alertViewModel.alertHistory.collectAsState(initial = emptyList())

    alertData?.let { (title, message) ->
        FullScreenAlertDialog(
            title = title,
            message = message,
            onDismiss = { alertViewModel.clearAlert() }
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(title = { Text("Driver Safety Monitor") })
        },
        content = { paddingValues ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(16.dp),
                verticalArrangement = Arrangement.SpaceBetween
            ) {
                Column(
                    modifier = Modifier.weight(1f)
                ) {
                    Text(
                        text = "History",
                        style = MaterialTheme.typography.headlineSmall,
                        modifier = Modifier.padding(bottom = 16.dp)
                    )

                    if (alertHistory.isEmpty()) {
                        Box(
                            modifier = Modifier.fillMaxWidth().weight(1f),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "No records yet",
                                style = MaterialTheme.typography.bodyLarge,
                                textAlign = TextAlign.Center
                            )
                        }
                    } else {
                        LazyColumn(
                            modifier = Modifier.weight(1f),
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            items(alertHistory) { alert ->
                                HistoryItem("${alert.title}: ${alert.message}")
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                Button(
                    onClick = { navController.navigate("chat") },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Open Chatbot")
                }
            }
        }
    )

}

@Composable
fun FullScreenAlertDialog(
    title: String,
    message: String,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    var callInitiated by remember { mutableStateOf(false) }

    Dialog(
        onDismissRequest = { /* No dismiss */ },
        properties = DialogProperties(dismissOnBackPress = false, dismissOnClickOutside = false)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.headlineMedium,
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(20.dp))
            Text(text = message, textAlign = TextAlign.Center)

            LaunchedEffect(Unit) {
                kotlinx.coroutines.delay(10000)
                if (!callInitiated) {
                    makePhoneCall(context, "7667248232")
                    callInitiated = true
                }
            }

            Spacer(modifier = Modifier.height(20.dp))
            Button(onClick = onDismiss) {
                Text("Dismiss Alert")
            }
        }
    }
}

fun makePhoneCall(context: Context, phoneNumber: String) {
    val intent = Intent(Intent.ACTION_CALL).apply {
        data = Uri.parse("tel:$phoneNumber")
    }
    if (ContextCompat.checkSelfPermission(context, Manifest.permission.CALL_PHONE)
        == PackageManager.PERMISSION_GRANTED
    ) {
        context.startActivity(intent)
    } else if (context is androidx.activity.ComponentActivity) {
        ActivityCompat.requestPermissions(
            context,
            arrayOf(Manifest.permission.CALL_PHONE),
            100
        )
    }
}

@Composable
fun HistoryItem(text: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        shape = MaterialTheme.shapes.medium
    ) {
        Text(
            text = text,
            modifier = Modifier.padding(16.dp),
            style = MaterialTheme.typography.bodyMedium
        )
    }
}
