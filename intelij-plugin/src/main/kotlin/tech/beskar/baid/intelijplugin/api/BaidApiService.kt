package tech.beskar.baid.intelijplugin.api

import org.json.JSONArray
import org.json.JSONObject
import java.io.InputStream

interface BaidApiService {
    fun sendPrompt(
        prompt: String,
        context: Map<String, Any>,
        sessionId: String?,
        onStreamStart: (InputStream) -> Unit,
        onStreamComplete: (String?) -> Unit,
        onError: (Exception) -> Unit
    )

    fun fetchSessions(
        userId: String,
        onSuccess: (JSONArray) -> Unit,
        onError: (Exception) -> Unit
    )

    fun fetchSessionHistory(
        userId: String,
        sessionId: String,
        onSuccess: (JSONArray) -> Unit,
        onError: (Exception) -> Unit
    )

    fun checkAuthentication(onResult: (Boolean) -> Unit)

    fun getCurrentAccessToken(): String?
}
