package tech.beskar.baid.intelijplugin.service

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.diagnostic.Logger
import com.intellij.util.io.HttpRequests
import org.json.JSONObject
import java.net.URI
import tech.beskar.baid.intelijplugin.config.BaidConfiguration
import tech.beskar.baid.intelijplugin.model.ChatSession
import tech.beskar.baid.intelijplugin.model.FileContext
import tech.beskar.baid.intelijplugin.model.SessionPreview
import tech.beskar.baid.intelijplugin.service.exceptions.ApiException
import java.io.BufferedReader
import java.io.IOException
import java.io.InputStreamReader
import java.net.URLConnection
import java.util.*
import java.util.function.Consumer
import javax.swing.SwingUtilities
import java.net.HttpURLConnection
import java.net.URL
import java.nio.charset.StandardCharsets


class BaidAPIService private constructor() {
    private val config: BaidConfiguration = BaidConfiguration.getInstance()

    fun sendMessage(
        userPrompt: String?,
        fileContext: FileContext,
        accessToken: String?,
        sessionId: String?,
        onStreamedBlock: Consumer<JSONObject?>,
        onComplete: Consumer<String?>,
        onError: Consumer<Throwable?>
    ) {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                // Create context JSON object
                val contextJson = fileContext.toJson()

                // Create main payload JSON object
                val payload = JSONObject()
                payload.put("prompt", userPrompt)
                payload.put("context", contextJson)

                // Prepare headers
                val apiUrl = config.backendUrl + config.apiEndpoint


                // Make streaming API request
                val updatedSessionId = streamAPIRequest(
                    apiUrl,
                    payload,
                    accessToken,
                    sessionId,
                    onStreamedBlock
                )

                // Notify completion with updated session ID
                SwingUtilities.invokeLater { onComplete.accept(updatedSessionId) }
            } catch (e: Throwable) {
                LOG.error("API request error", e)

                SwingUtilities.invokeLater { onError.accept(e) }
            }
        }
    }

    @Throws(ApiException::class)
    private fun streamAPIRequest(
        apiUrl: String,
        payload: JSONObject,
        accessToken: String?,
        sessionId: String?,
        onStreamedBlock: Consumer<JSONObject?>
    ): String? {
        // Prepare headers
        val headers: MutableMap<String?, String?> = HashMap<String?, String?>()
        headers.put("Authorization", "Bearer $accessToken")
        headers.put("Content-Type", "application/json")

        if (sessionId != null && !sessionId.isBlank()) {
            headers.put("session_id", sessionId)
        }

        // Track updated session ID
        val updatedSessionId = arrayOf(sessionId)

        try {
            // Create a custom URL connection that allows us to access error streams
            val uri = URI.create(apiUrl)
            val connection = uri.toURL().openConnection() as HttpURLConnection

            // Configure connection
            connection.requestMethod = "POST"
            connection.connectTimeout = 30000
            connection.readTimeout = 300000
            connection.doOutput = true
            connection.instanceFollowRedirects = true

            // Set headers
            headers.forEach { (key: String?, value: String?) ->
                key?.let { connection.setRequestProperty(it, value) }
            }

            // Send payload
            connection.outputStream.use { os ->
                os.write(payload.toString().toByteArray(StandardCharsets.UTF_8))
                os.flush()
            }

            // Check response code
            val responseCode = connection.responseCode

            if (responseCode >= 400) {
                // Read error response
                val errorResponseText = connection.errorStream?.use { errorStream ->
                    BufferedReader(InputStreamReader(errorStream)).use { reader ->
                        reader.readText()
                    }
                } ?: "No error details available"

                val errorResponse = this.parseErrorResponse(errorResponseText)

                LOG.error("HTTP Error: Status code $responseCode. Response: $errorResponse")
                throw ApiException(
                    errorResponse.detail.toString(),
                    responseCode,
                    apiUrl
                )
            }

            // Process successful response
            connection.inputStream.use { inputStream ->
                BufferedReader(InputStreamReader(inputStream)).use { reader ->
                    var currentLine: String?
                    var jsonBuffer = StringBuilder()
                    var braceCount = 0
                    var inJson = false
                    while (reader.readLine().also { currentLine = it } != null) {
                        // Skip lines that don't start with "data: "
                        if (currentLine == null || !currentLine!!.startsWith("data: ")) {
                            continue
                        }

                        val data = currentLine!!.substring(6).trim { it <= ' ' }  // Remove "data: " prefix

                        // Check for end of stream marker
                        if ("[DONE]" == data) {
                            break
                        }

                        // Start or continue JSON object
                        if (!inJson && data.startsWith("{")) {
                            jsonBuffer = StringBuilder(data)
                            braceCount = countBraces(data)
                            inJson = true
                        } else if (inJson) {
                            jsonBuffer.append(data)
                            braceCount += countBraces(data)
                        }

                        // If we have a complete JSON object
                        if (inJson && braceCount == 0) {
                            val jsonStr = jsonBuffer.toString()
                            try {
                                val jsonObj = JSONObject(jsonStr)

                                // Check for session ID update
                                if (jsonObj.has("session_id")) {
                                    updatedSessionId[0] = jsonObj.optString("session_id", "")
                                } else {
                                    // Process content block
                                    if (jsonObj.has("error")) {
                                        throw Exception(jsonObj.getString("error"))
                                    }
                                    SwingUtilities.invokeLater { onStreamedBlock.accept(jsonObj) }
                                }
                            } catch (e: Exception) {
                                LOG.error("Error parsing JSON response: $jsonStr", e)
                            }

                            // Reset for next JSON object
                            inJson = false
                            jsonBuffer = StringBuilder()
                        }
                    }
                }
            }

            return updatedSessionId[0]
        } catch (e: Throwable) {
            when (e) {
                is IOException -> {
                    if (e.message?.contains("Server returned HTTP response code:") == true) {
                        // We already logged the detailed error above
                        LOG.error("API request failed", e)
                    } else {
                        LOG.error("Network error when connecting to backend: ${e.message}", e)
                    }
                }

                else -> {
                    LOG.error("Error from backend: ${e.message}", e)
                }
            }
            throw e
        }
    }

    private fun countBraces(text: String): Int {
        var count = 0
        for (c in text.toCharArray()) {
            if (c == '{') count++
            else if (c == '}') count--
        }
        return count
    }

    fun fetchUserSessions(
        userId: String?,
        accessToken: String?,
        onSuccess: Consumer<MutableList<SessionPreview?>?>,
        onError: Consumer<Throwable?>
    ) {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val apiUrl = config.backendUrl + "/sessions/" + userId

                val result = HttpRequests
                    .request(apiUrl)
                    .tuner { connection: URLConnection? ->
                        connection!!.setRequestProperty("Authorization", "Bearer $accessToken")
                    }
                    .readString()

                val jsonResponse = JSONObject(result)
                val sessions = jsonResponse.getJSONArray("sessions")

                val sessionPreviews: MutableList<SessionPreview?> = ArrayList<SessionPreview?>()
                for (i in 0..<sessions.length()) {
                    val sessionJson = sessions.getJSONObject(i)
                    val preview: SessionPreview? = SessionPreview.fromJson(sessionJson)
                    sessionPreviews.add(preview)
                }

                SwingUtilities.invokeLater { onSuccess.accept(sessionPreviews) }
            } catch (e: Throwable) {
                LOG.error("Error fetching user sessions", e)
                SwingUtilities.invokeLater { onError.accept(e) }
            }
        }
    }

    fun loadConversationHistory(
        userId: String?,
        sessionId: String?,
        accessToken: String?,
        onSuccess: Consumer<ChatSession?>,
        onError: Consumer<Throwable?>
    ) {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val historyUrl = config.backendUrl + "/history/" + userId + "/" + sessionId

                val historyResult = HttpRequests
                    .request(historyUrl)
                    .tuner { connection: URLConnection? ->
                        connection!!.setRequestProperty("Authorization", "Bearer $accessToken")
                    }
                    .readString()

                val historyJson = JSONObject(historyResult)
                val messagesArray = historyJson.getJSONArray("history")


                // Create a session and populate with messages
                val session = ChatSession(sessionId, userId, Date())
                session.setMessagesFromJson(messagesArray)

                SwingUtilities.invokeLater { onSuccess.accept(session) }
            } catch (e: Throwable) {
                LOG.error("Error loading conversation history", e)
                SwingUtilities.invokeLater { onError.accept(e) }
            }
        }
    }

    fun loadMessagePreview(
        userId: String?,
        sessionId: String?,
        accessToken: String?,
        onSuccess: Consumer<String?>,
        onError: Consumer<Throwable?>
    ) {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val historyUrl = config.backendUrl + "/history/" + userId + "/" + sessionId

                val historyResult = HttpRequests
                    .request(historyUrl)
                    .tuner { connection: URLConnection? ->
                        connection!!.setRequestProperty("Authorization", "Bearer $accessToken")
                    }
                    .readString()

                val historyJson = JSONObject(historyResult)
                val messagesArray = historyJson.getJSONArray("history")


                // Find first user message
                var firstUserMessage = ""
                for (i in 0..<messagesArray.length()) {
                    val message = messagesArray.getJSONObject(i)
                    if ("user" == message.getString("role")) {
                        firstUserMessage = message.getString("message")
                        break
                    }
                }


                // Handle empty conversations
                val previewText = firstUserMessage.ifEmpty { "Empty conversation" }

                SwingUtilities.invokeLater { onSuccess.accept(previewText) }
            } catch (e: Throwable) {
                LOG.error("Error loading message preview", e)
                SwingUtilities.invokeLater { onError.accept(e) }
            }
        }
    }


    companion object {
        private val LOG = Logger.getInstance(BaidAPIService::class.java)

        @get:Synchronized
        var _instance: BaidAPIService? = null
            get() {
                if (field == null) {
                    field = BaidAPIService()
                }
                return field
            }

        fun getInstance(): BaidAPIService {
            if (_instance == null) {
                _instance = BaidAPIService()
            }
            return _instance!!
        }
    }

    private fun parseErrorResponse(jsonString: String): ApiErrorResponse {
        return try {
            // If you're using org.json
            val jsonObject = JSONObject(jsonString)
            val detail = if (jsonObject.has("detail")) jsonObject.getString("detail") else null
            ApiErrorResponse(detail)

            // If you're using Gson
            // Gson().fromJson(jsonString, ApiErrorResponse::class.java)

            // If you're using Jackson
            // ObjectMapper().readValue(jsonString, ApiErrorResponse::class.java)
        } catch (e: Exception) {
            LOG.warn("Failed to parse error response: $jsonString", e)
            ApiErrorResponse("Failed to parse error: $jsonString")
        }
    }

}


data class ApiErrorResponse(
    val detail: String? = null,
)