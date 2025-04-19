package com.example.hcai_project.screens

import android.os.Handler
import android.os.Looper
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.example.hcai_project.R

@Composable
fun SplashScreen(navController: NavController) {
    LaunchedEffect(Unit) {
        Handler(Looper.getMainLooper()).postDelayed({
            navController.navigate("home") {
                popUpTo("splash") { inclusive = true }
            }
        }, 2000)
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            // ✅ Logo Image (place your logo in res/drawable and use it here)
            Image(
                painter = painterResource(id = R.drawable.logo), // replace 'logo' with your actual image name
                contentDescription = "App Logo",
//                modifier = Modifier
////                    .size(100.dp)
//                    .padding(bottom = 24.dp),
                colorFilter = ColorFilter.tint(MaterialTheme.colorScheme.primary)
            )

            Text(
                text = "Driver Alert",
                fontSize = 28.sp,
                style = MaterialTheme.typography.headlineMedium
            )

            Spacer(modifier = Modifier.height(24.dp))

            // ✅ Loading spinner
            CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
        }
    }
}
