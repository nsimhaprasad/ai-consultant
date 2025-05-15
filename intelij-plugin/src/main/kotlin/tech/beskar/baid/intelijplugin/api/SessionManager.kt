package tech.beskar.baid.intelijplugin.api

class SessionManager {
    var currentSessionId: String? = null

    fun startNewSession() {
        currentSessionId = null
    }
    
    fun setSessionId(sessionId: String?) {
        currentSessionId = sessionId
    }
}
