package tech.beskar.baid.intelijplugin.api

import java.io.InputStream
import javax.swing.JPanel

interface ResponseHandler {
    fun handleStreamingResponse(responseStream: InputStream, messagePanel: JPanel): String?
    
    fun handleError(error: Exception, isAuthError: Boolean = false)
    
    fun onSessionIdReceived(sessionId: String?)
}
