package tech.beskar.baid.intelijplugin.api

import com.intellij.openapi.application.ApplicationManager
import com.intellij.util.io.HttpRequests
import org.json.JSONArray
import org.json.JSONObject
import tech.beskar.baid.intelijplugin.auth.GoogleAuthService
import tech.beskar.baid.intelijplugin.config.BaidConfiguration
import java.io.InputStream
import javax.swing.SwingUtilities

class BaidApiServiceImpl(
    private val authService: GoogleAuthService,
    private val config: BaidConfiguration
) : BaidApiService {

    override fun sendPrompt(
        prompt: String,
        context: Map<String, Any>,
        sessionId: String?,
        onStreamStart: (InputStream) -> Unit,
        onStreamComplete: (String?) -> Unit,
        onError: (Exception) -> Unit
    ) {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val accessToken = authService.getCurrentAccessToken()
                if (accessToken == null) {
                    onError(Exception("Authentication required"))
                    return@executeOnPooledThread
                }

                // Create context JSONObject
                val contextJson = JSONObject()
                context.forEach { (key, value) -> contextJson.put(key, value) }

                // Create main payload JSONObject
                val payload = JSONObject()
                payload.put("prompt", prompt)
                payload.put("context", contextJson)

                // Prepare headers
                val headers = mutableMapOf(
                    "Authorization" to "Bearer $accessToken",
                    "Content-Type" to "application/json"
                )

                if (!sessionId.isNullOrBlank()) {
                    headers["session_id"] = sessionId
                }

                // Make HTTP request
                val apiUrl = "${config.backendUrl}${config.apiEndpoint}"
                
                var updatedSessionId: String? = sessionId
                
                HttpRequests
                    .post(apiUrl, "application/json")
                    .connectTimeout(30000)
                    .readTimeout(300000)
                    .tuner { connection ->
                        headers.forEach { (key, value) ->
                            connection.setRequestProperty(key, value)
                        }
                    }
                    .connect { request ->
                        request.write(payload.toString())
                        
                        // Call the stream start callback with the input stream
                        onStreamStart(request.inputStream)
                        
                        // Process the stream to extract session ID
                        request.inputStream.bufferedReader().use { reader ->
                            while (true) {
                                val rawLine = reader.readLine() ?: break
                                if (!rawLine.startsWith("data: ")) continue
                                val data = rawLine.substringAfter("data: ").trim()
                                if (data == "[DONE]") break

                                // Check if this is a session ID response
                                try {
                                    val jsonObj = JSONObject(data)
                                    if (jsonObj.has("session_id")) {
                                        updatedSessionId = jsonObj.optString("session_id", "")
                                        break
                                    }
                                } catch (e: Exception) {
                                    // Not a JSON object or doesn't have session_id, continue
                                }
                            }
                        }
                        
                        // Call the completion callback with the updated session ID
                        onStreamComplete(updatedSessionId)
                    }
            } catch (e: Exception) {
                onError(e)
            }
        }
    }

    override fun fetchSessions(
        userId: String,
        onSuccess: (JSONArray) -> Unit,
        onError: (Exception) -> Unit
    ) {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val accessToken = authService.getCurrentAccessToken()
                if (accessToken == null) {
                    onError(Exception("Authentication required"))
                    return@executeOnPooledThread
                }

                // Fetch sessions from the API
                val apiUrl = "${config.backendUrl}/sessions/$userId"
                val result = HttpRequests
                    .request(apiUrl)
                    .tuner { connection ->
                        connection.setRequestProperty("Authorization", "Bearer $accessToken")
                    }
                    .readString()

                val jsonResponse = JSONObject(result)
                val sessions = jsonResponse.getJSONArray("sessions")
                
                SwingUtilities.invokeLater {
                    onSuccess(sessions)
                }
            } catch (e: Exception) {
                SwingUtilities.invokeLater {
                    onError(e)
                }
            }
        }
    }

    override fun fetchSessionHistory(
        userId: String,
        sessionId: String,
        onSuccess: (JSONArray) -> Unit,
        onError: (Exception) -> Unit
    ) {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val accessToken = authService.getCurrentAccessToken()
                if (accessToken == null) {
                    onError(Exception("Authentication required"))
                    return@executeOnPooledThread
                }

                // Fetch conversation history
                val historyUrl = "${config.backendUrl}/history/$userId/$sessionId"
                val historyResult = HttpRequests
                    .request(historyUrl)
                    .tuner { connection ->
                        connection.setRequestProperty("Authorization", "Bearer $accessToken")
                    }
                    .readString()

                val historyJson = JSONObject(historyResult)
                val messagesArray = historyJson.getJSONArray("history")
                
                SwingUtilities.invokeLater {
                    onSuccess(messagesArray)
                }
            } catch (e: Exception) {
                SwingUtilities.invokeLater {
                    onError(e)
                }
            }
        }
    }

    override fun checkAuthentication(onResult: (Boolean) -> Unit) {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val isAuthenticated = authService.isAuthenticated()
                SwingUtilities.invokeLater {
                    onResult(isAuthenticated)
                }
            } catch (e: Exception) {
                SwingUtilities.invokeLater {
                    onResult(false)
                }
            }
        }
    }

    override fun getCurrentAccessToken(): String? {
        return authService.getCurrentAccessToken()
    }
}
