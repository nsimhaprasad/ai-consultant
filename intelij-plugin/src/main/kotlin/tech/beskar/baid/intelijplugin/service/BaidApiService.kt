package tech.beskar.baid.intelijplugin.service

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.diagnostic.Logger
import com.intellij.util.io.HttpRequests
import org.json.JSONObject
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


class BaidAPIService constructor() : IBaidApiService {
    private val config: BaidConfiguration = BaidConfiguration.getInstance() // This will be addressed later if BaidConfiguration is also refactored

    override fun sendMessage(
        userPrompt: String?,
        fileContext: FileContext,
        accessToken: String?,
        sessionId: tech.beskar.baid.intelijplugin.model.common.SessionId?,
        onStreamedBlock: Consumer<JSONObject?>,
        onComplete: Consumer<tech.beskar.baid.intelijplugin.model.common.SessionId?>,
        onError: Consumer<Throwable?>
    ) {
        executeApiCall(
            call = {
                val contextJson = fileContext.toJson()
                val payload = JSONObject().apply {
                    put("prompt", userPrompt)
                    put("context", contextJson)
                }
                val apiUrl = config.backendUrl + config.apiEndpoint
                val responseSessionIdString = streamAPIRequest(
                    apiUrl,
                    payload,
                    accessToken,
                    sessionId?.value,
                    onStreamedBlock
                )
                responseSessionIdString?.let { tech.beskar.baid.intelijplugin.model.common.SessionId(it) }
            },
            onSuccess = onComplete, // Renamed for clarity in this context
            onError = { error ->
                LOG.error("API sendMessage error", error) // Specific logging
                onError.accept(error)
            }
        )
    }

@Throws( ApiException::class)
private fun streamAPIRequest(
    apiUrl: String,
    payload: JSONObject,
    accessToken: String?,
    sessionIdString: String?,
    onStreamedBlock: Consumer<JSONObject?>
): String? { // Return type remains String? as it's the raw ID from API
    val headers = createHeaders(accessToken, sessionIdString)
    val updatedSessionId = arrayOf(sessionIdString) // Workaround for mutable string in lambda

    try {
        val connection = setupConnection(apiUrl, headers, payload)
        handleResponseCode(connection, apiUrl) 
        readAndProcessStream(connection, onStreamedBlock, updatedSessionId)
        return updatedSessionId[0]
    } catch (e: Throwable) {
        logApiError(e) // Centralized error logging for streamAPIRequest
        throw e // Rethrow to be handled by executeApiCall's catch block
    }
}

private fun createHeaders(accessToken: String?, sessionIdString: String?): MutableMap<String?, String?> {
    val headers: MutableMap<String?, String?> = HashMap()
    headers["Authorization"] = "Bearer $accessToken"
    headers["Content-Type"] = "application/json"
    sessionIdString?.takeIf { it.isNotBlank() }?.let { headers["session_id"] = it }
    return headers
}

@Throws(IOException::class)
private fun setupConnection(apiUrl: String, headers: Map<String?, String?>, payload: JSONObject): HttpURLConnection {
    val url = URL(apiUrl)
    val connection = url.openConnection() as HttpURLConnection
    connection.requestMethod = "POST"
    connection.connectTimeout = 30000
    connection.readTimeout = 300000
    connection.doOutput = true
    connection.instanceFollowRedirects = true
    headers.forEach { (key, value) -> key?.let { connection.setRequestProperty(it, value) } }
    connection.outputStream.use { os ->
        os.write(payload.toString().toByteArray(StandardCharsets.UTF_8))
        os.flush()
    }
    return connection
}

@Throws(ApiException::class, IOException::class)
private fun handleResponseCode(connection: HttpURLConnection, apiUrl: String) {
    val responseCode = connection.responseCode
    if (responseCode < 400) return

    val errorResponseText = connection.errorStream?.use { stream ->
        BufferedReader(InputStreamReader(stream)).use { reader -> reader.readText() }
    } ?: "No error details available from server."

    val errorResponse = parseErrorResponse(errorResponseText)
    LOG.error("HTTP Error: Status code $responseCode. URL: $apiUrl. Response: $errorResponse")
    throw ApiException(errorResponse.detail ?: "Unknown API error", responseCode, apiUrl)
}

private fun processCompleteJsonBlock(
    jsonStr: String,
    onStreamedBlock: Consumer<JSONObject?>,
    updatedSessionId: Array<String?>
): StringBuilder { // Returns new buffer to reset
    try {
        val jsonObj = JSONObject(jsonStr)
        if (jsonObj.has("session_id")) {
            updatedSessionId[0] = jsonObj.optString("session_id", null) // Allow null propagation
            return StringBuilder() 
        }
        if (jsonObj.has("error")) {
            throw Exception(jsonObj.getString("error")) // Let outer catch handle this
        }
        SwingUtilities.invokeLater { onStreamedBlock.accept(jsonObj) }
    } catch (e: Exception) {
        LOG.error("Error parsing or processing JSON block: $jsonStr", e)
        // Optionally, could call onError consumer here for individual block errors
    }
    return StringBuilder()
}

private fun logApiError(e: Throwable) { // Simplified logging, specific details logged at source
    when (e) {
        is IOException -> LOG.error("Network error during API request: ${e.message}", e)
        is ApiException -> LOG.error("API exception during request: ${e.message}", e) // Already logged by handleResponseCode
        else -> LOG.error("Unexpected error during API request: ${e.message}", e)
    }
}

@Throws(IOException::class)
private fun readAndProcessStream(
    connection: HttpURLConnection,
    onStreamedBlock: Consumer<JSONObject?>,
    updatedSessionId: Array<String?>
) {
    connection.inputStream.use { inputStream ->
        BufferedReader(InputStreamReader(inputStream)).use { reader ->
            var currentLine: String?
            var jsonBuffer = StringBuilder()
            var braceCount = 0
            var inJson = false 

            while (reader.readLine().also { currentLine = it } != null) {
                val line = currentLine ?: continue 
                if (!line.startsWith("data: ")) continue

                val data = line.substring(6).trim()
                if ("[DONE]" == data) break

                if (!inJson && data.startsWith("{")) {
                    jsonBuffer = StringBuilder(data)
                    braceCount = countBraces(data)
                    inJson = true
                } else if (inJson) {
                    jsonBuffer.append(data)
                    braceCount += countBraces(data)
                }

                if (inJson && braceCount == 0) {
                    jsonBuffer = processCompleteJsonBlock(jsonBuffer.toString(), onStreamedBlock, updatedSessionId)
                    inJson = false 
                }
            }
        }
    }
}

    private fun countBraces(text: String): Int = text.count { it == '{' } - text.count { it == '}' }

    override fun fetchUserSessions(
        userId: tech.beskar.baid.intelijplugin.model.common.UserId?,
        accessToken: String?,
        onSuccess: Consumer<MutableList<SessionPreview?>?>,
        onError: Consumer<Throwable?>
    ) {
        executeApiCall(
            call = {
                val apiUrl = config.backendUrl + "/sessions/" + (userId?.value ?: throw IllegalArgumentException("User ID cannot be null"))
                val result = HttpRequests.request(apiUrl)
                    .tuner { conn -> conn.setRequestProperty("Authorization", "Bearer $accessToken") }
                    .readString()
                val jsonResponse = JSONObject(result)
                val sessionsArray = jsonResponse.getJSONArray("sessions")
                val sessionPreviews = (0..<sessionsArray.length())
                    .map { SessionPreview.fromJson(sessionsArray.getJSONObject(it)) as SessionPreview? }
                    .toMutableList()
                sessionPreviews
            },
            onSuccess = onSuccess,
            onError = { error ->
                LOG.error("Error fetching user sessions", error)
                onError.accept(error)
            }
        )
    }

    override fun loadConversationHistory(
        userId: tech.beskar.baid.intelijplugin.model.common.UserId?,
        sessionId: tech.beskar.baid.intelijplugin.model.common.SessionId?,
        accessToken: String?,
        onSuccess: Consumer<ChatSession?>,
        onError: Consumer<Throwable?>
    ) {
        executeApiCall(
            call = {
                val uid = userId?.value ?: throw IllegalArgumentException("User ID cannot be null")
                val sid = sessionId?.value ?: throw IllegalArgumentException("Session ID cannot be null")
                val historyUrl = "${config.backendUrl}/history/$uid/$sid"
                val historyResult = HttpRequests.request(historyUrl)
                    .tuner { conn -> conn.setRequestProperty("Authorization", "Bearer $accessToken") }
                    .readString()
                val historyJson = JSONObject(historyResult)
                val messagesArray = historyJson.getJSONArray("history")
                ChatSession(sessionId, userId, Date()).apply { setMessagesFromJson(messagesArray) }
            },
            onSuccess = onSuccess,
            onError = { error ->
                LOG.error("Error loading conversation history", error)
                onError.accept(error)
            }
        )
    }

    override fun loadMessagePreview(
        userId: tech.beskar.baid.intelijplugin.model.common.UserId?,
        sessionId: tech.beskar.baid.intelijplugin.model.common.SessionId?,
        accessToken: String?,
        onSuccess: Consumer<String?>,
        onError: Consumer<Throwable?>
    ) {
        executeApiCall(
            call = {
                val uid = userId?.value ?: throw IllegalArgumentException("User ID cannot be null")
                val sid = sessionId?.value ?: throw IllegalArgumentException("Session ID cannot be null")
                val historyUrl = "${config.backendUrl}/history/$uid/$sid"
                val historyResult = HttpRequests.request(historyUrl)
                    .tuner { conn -> conn.setRequestProperty("Authorization", "Bearer $accessToken") }
                    .readString()
                val historyJson = JSONObject(historyResult)
                val messagesArray = historyJson.getJSONArray("history")
                var firstUserMessage = ""
                for (i in 0..<messagesArray.length()) {
                    val message = messagesArray.getJSONObject(i)
                    if ("user" == message.getString("role")) {
                        firstUserMessage = message.getString("message")
                        break
                    }
                }
                firstUserMessage.ifEmpty { "Empty conversation" }
            },
            onSuccess = onSuccess,
            onError = { error ->
                LOG.error("Error loading message preview", error)
                onError.accept(error)
            }
        )
    }
    
    // Helper function to encapsulate the common executeOnPooledThread and try-catch logic
    private fun <T> executeApiCall(
        call: () -> T,
        onSuccess: Consumer<T?>, // Changed T to T? to allow null success results (e.g. for SessionId)
        onError: Consumer<Throwable?>
    ) {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val result = call()
                SwingUtilities.invokeLater { onSuccess.accept(result) }
            } catch (e: Throwable) {
                // Generic error logging, specific logging should be done in the call() or onError lambda if needed
                // LOG.error("API call error", e) // This might be too generic here
                SwingUtilities.invokeLater { onError.accept(e) }
            }
        }
    }


    companion object {
        private val LOG = Logger.getInstance(BaidAPIService::class.java)
    }

    private fun parseErrorResponse(jsonString: String): ApiErrorResponse {
        return try {
            val jsonObject = JSONObject(jsonString)
            val detail = jsonObject.optString("detail", null) // Use optString for safety
            ApiErrorResponse(detail)
            // If you're using Gson
            // Gson().fromJson(jsonString, ApiErrorResponse::class.java)
            // If you're using Jackson
            // ObjectMapper().readValue(jsonString, ApiErrorResponse::class.java)
        } catch (e: Exception) {
            LOG.warn("Failed to parse error response: $jsonString", e)
            ApiErrorResponse("Failed to parse error: $jsonString") // Provide more context
        }
    }

}


data class ApiErrorResponse(
    val detail: String? = null,
)