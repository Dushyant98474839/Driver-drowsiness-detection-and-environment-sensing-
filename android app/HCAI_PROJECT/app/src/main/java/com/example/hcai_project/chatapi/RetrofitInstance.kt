package com.example.hcai_project.chatapi

import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitInstance {
    private const val BASE_URL = "http://192.168.10.9:5000/" // Ensure trailing slash

    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(0, TimeUnit.MILLISECONDS) // Disable connect timeout
        .readTimeout(0, TimeUnit.MILLISECONDS)    // Disable read timeout
        .writeTimeout(0, TimeUnit.MILLISECONDS)   // Disable write timeout
        .build()

    val api: ChatApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ChatApi::class.java)
    }
}