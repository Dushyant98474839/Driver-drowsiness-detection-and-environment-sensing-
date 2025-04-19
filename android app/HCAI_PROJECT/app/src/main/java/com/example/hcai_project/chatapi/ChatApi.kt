package com.example.hcai_project.chatapi

import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.POST

interface ChatApi {
    @POST("/chat")
    fun getChatResponse(@Body request: ChatRequest): Call<ChatResponse>
}
