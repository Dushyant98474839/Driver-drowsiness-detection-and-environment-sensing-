package com.example.hcai_project.screens

import android.R.color.white
import android.annotation.SuppressLint
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.hcai_project.chatapi.ChatViewModel

@SuppressLint("ResourceAsColor")
@Composable
fun ChatScreen(viewModel: ChatViewModel = viewModel()) {
    val messages by viewModel.messages.collectAsState()
    val isTyping by viewModel.isBotTyping.collectAsState()
    val error by viewModel.error.collectAsState()
    var userInput by remember { mutableStateOf(TextFieldValue("")) }

    val listState = rememberLazyListState()

    // Scroll to top (latest message) when messages change or typing starts
    LaunchedEffect(messages, isTyping) {
        listState.animateScrollToItem(0)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .statusBarsPadding()
            .imePadding() // Adjust for keyboard
            .padding(horizontal = 16.dp)
            .background(Color(white))
    ) {
        // Header
        Text(
            text = "AI Driving Assistant",
            style = MaterialTheme.typography.headlineSmall.copy(
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary
            ),
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 16.dp),
            textAlign = TextAlign.Center
        )

        // Messages List
        LazyColumn(
            state = listState,
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(8.dp),
            reverseLayout = true
        ) {
            items(messages.reversed()) { message ->
                val isUser = message.startsWith("User:")
                ChatMessage(
                    message = message.removePrefix("User:").removePrefix("Bot:"),
                    isUser = isUser
                )
            }
        }

        // Typing Indicator
        AnimatedVisibility(visible = isTyping) {
            ChatMessage(message = "Assistant is typing...", isUser = false)
        }

        // Error Message
        if (error != null) {
            Text(
                text = error ?: "Error occurred",
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier
                    .padding(vertical = 8.dp)
                    .fillMaxWidth()
            )
        }

        // Input Section
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 16.dp, top = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = userInput,
                onValueChange = { userInput = it },
                modifier = Modifier
                    .weight(1f)
                    .padding(end = 8.dp),
                placeholder = { Text("Type your message...") },
                shape = RoundedCornerShape(24.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = MaterialTheme.colorScheme.primary,
                    unfocusedBorderColor = MaterialTheme.colorScheme.outline,
                    focusedTextColor = Color.Black,
                    unfocusedTextColor = Color.Black
                ),
                singleLine = false,
                maxLines = 3
            )

            Button(
                onClick = {
                    if (userInput.text.isNotBlank()) {
                        viewModel.sendMessageToBot(userInput.text)
                        userInput = TextFieldValue("")
                    }
                },
                shape = RoundedCornerShape(24.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primary
                ),
                modifier = Modifier.height(56.dp)
            ) {
                Text("Send", fontWeight = FontWeight.Medium)
            }
        }
    }
}

@Composable
fun ChatMessage(message: String, isUser: Boolean) {
    val backgroundColor = if (isUser) MaterialTheme.colorScheme.primaryContainer
    else MaterialTheme.colorScheme.surfaceVariant
    val textColor = if (isUser) MaterialTheme.colorScheme.onPrimaryContainer
    else MaterialTheme.colorScheme.onSurfaceVariant

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 4.dp, vertical = 4.dp),
        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
    ) {
        Box(
            modifier = Modifier
                .background(
                    color = backgroundColor,
                    shape = RoundedCornerShape(
                        topStart = 16.dp,
                        topEnd = 16.dp,
                        bottomStart = if (isUser) 16.dp else 4.dp,
                        bottomEnd = if (isUser) 4.dp else 16.dp
                    )
                )
                .padding(horizontal = 16.dp, vertical = 12.dp)
                .widthIn(max = 300.dp)
        ) {
            // Parse the message into styled segments
            val parsedMessage = buildAnnotatedString {
                val regex = Regex("\\*\\*(.*?)\\*\\*")
                val matches = regex.findAll(message)
                var lastIndex = 0

                matches.forEach { match ->
                    val normalText = message.substring(lastIndex, match.range.first)
                    if (normalText.isNotEmpty()) {
                        append(normalText)
                    }
                    val boldText = match.groupValues[1]
                    withStyle(style = SpanStyle(fontWeight = FontWeight.Bold)) {
                        append(boldText)
                    }
                    lastIndex = match.range.last + 1
                }

                val remainingText = message.substring(lastIndex)
                append(remainingText)
            }

            Text(
                text = parsedMessage,
                color = textColor,
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}
