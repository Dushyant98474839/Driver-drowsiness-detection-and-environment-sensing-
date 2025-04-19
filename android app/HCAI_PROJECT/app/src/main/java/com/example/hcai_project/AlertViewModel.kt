package com.example.hcai_project

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.hcai_project.DB.AlertDatabase
import com.example.hcai_project.DB.AlertEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class AlertViewModel(application: Application) : AndroidViewModel(application) {
    private val db = AlertDatabase.getDatabase(application)
    private val dao = db.alertDao()

    val showAlert = MutableStateFlow<Pair<String, String>?>(null)
    val alertHistory: Flow<List<AlertEntity>> = dao.getAllAlerts()

    fun triggerAlert(title: String, message: String) {
        viewModelScope.launch {
            dao.insertAlert(AlertEntity(title = title, message = message))
        }
        showAlert.value = Pair(title, message)
    }

    fun clearAlert() {
        showAlert.value = null
    }
}
