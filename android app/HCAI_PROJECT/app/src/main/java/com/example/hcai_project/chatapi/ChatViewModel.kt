package com.example.hcai_project.chatapi

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class ChatViewModel : ViewModel() {

    private val _messages = MutableStateFlow<List<String>>(emptyList())
    val messages: StateFlow<List<String>> = _messages

    private val _isBotTyping = MutableStateFlow(false)
    val isBotTyping: StateFlow<Boolean> = _isBotTyping

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error

    fun sendMessageToBot(message: String) {
        if (message.isBlank()) return // Prevent sending empty messages

        viewModelScope.launch(Dispatchers.Main) {
            _error.value = null
            _messages.update { it + "User: $message" }
            _isBotTyping.value = true

            val request = ChatRequest(query = message)
            RetrofitInstance.api.getChatResponse(request).enqueue(object : Callback<ChatResponse> {
                override fun onResponse(call: Call<ChatResponse>, response: Response<ChatResponse>) {
                    viewModelScope.launch(Dispatchers.Main) {
                        _isBotTyping.value = false
                        val botMessage = if (response.isSuccessful && response.body() != null) {
                            "Bot: ${response.body()!!.response}"
                        } else {
                            "Bot: Error - HTTP ${response.code()}"
                        }
                        _messages.update { it + botMessage }
                    }
                }

                override fun onFailure(call: Call<ChatResponse>, t: Throwable) {
                    viewModelScope.launch(Dispatchers.Main) {
                        _isBotTyping.value = false
                        _error.value = "Network error: ${t.message}"
                        _messages.update { it + "Bot: Error - ${t.message}" }
                    }
                }
            })

            // Simulate typing delay
            delay(1000) // Adjust as needed
        }
    }

    fun clearChat() {
        viewModelScope.launch {
            _messages.value = emptyList()
            _error.value = null
            _isBotTyping.value = false
        }
    }
}