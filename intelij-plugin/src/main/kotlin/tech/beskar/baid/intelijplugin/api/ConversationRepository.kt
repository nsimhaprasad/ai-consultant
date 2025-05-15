package tech.beskar.baid.intelijplugin.api

import org.json.JSONArray
import org.json.JSONObject
import tech.beskar.baid.intelijplugin.model.Message
import javax.swing.SwingUtilities

class ConversationRepository(private val apiService: BaidApiService) {
    
    data class Conversation(
        val sessionId: String,
        val lastUsedAt: String,
        val previewText: String? = null
    )
    

    fun loadConversations(
        userId: String,
        onSuccess: (List<Conversation>) -> Unit,
        onError: (Exception) -> Unit
    ) {
        apiService.fetchSessions(
            userId = userId,
            onSuccess = { sessionsArray ->
                val conversations = mutableListOf<Conversation>()
                
                // Process each session
                for (i in 0 until sessionsArray.length()) {
                    val session = sessionsArray.getJSONObject(i)
                    val sessionId = session.getString("session_id")
                    val lastUsed = session.getString("last_used_at")
                    
                    conversations.add(Conversation(sessionId, lastUsed))
                }
                
                // Load preview text for each conversation
                loadConversationPreviews(userId, conversations, onSuccess, onError)
            },
            onError = { error ->
                SwingUtilities.invokeLater {
                    onError(error)
                }
            }
        )
    }
    

    private fun loadConversationPreviews(
        userId: String,
        conversations: List<Conversation>,
        onSuccess: (List<Conversation>) -> Unit,
        onError: (Exception) -> Unit
    ) {
        // Count how many previews we've loaded
        var completedPreviews = 0
        val totalConversations = conversations.size
        val result = conversations.toMutableList()
        
        // If no conversations, return immediately
        if (totalConversations == 0) {
            SwingUtilities.invokeLater {
                onSuccess(result)
            }
            return
        }
        
        // Load preview for each conversation
        conversations.forEachIndexed { index, conversation ->
            apiService.fetchSessionHistory(
                userId = userId,
                sessionId = conversation.sessionId,
                onSuccess = { messagesArray ->
                    var previewText = "Empty conversation"
                    
                    // Find the first user message
                    for (j in 0 until messagesArray.length()) {
                        val message = messagesArray.getJSONObject(j)
                        if (message.getString("role") == "user") {
                            val messageText = message.getString("message")
                            previewText = if (messageText.length > 60) {
                                "${messageText.substring(0, 60)}..."
                            } else {
                                messageText
                            }
                            break
                        }
                    }
                    
                    // Update the conversation with preview text
                    result[index] = conversation.copy(previewText = previewText)
                    
                    // Check if all previews are loaded
                    completedPreviews++
                    if (completedPreviews >= totalConversations) {
                        SwingUtilities.invokeLater {
                            onSuccess(result)
                        }
                    }
                },
                onError = { error ->
                    // Update with error message
                    result[index] = conversation.copy(previewText = "Failed to load preview")
                    
                    // Check if all previews are loaded
                    completedPreviews++
                    if (completedPreviews >= totalConversations) {
                        SwingUtilities.invokeLater {
                            onSuccess(result)
                        }
                    }
                }
            )
        }
    }
    
    fun loadConversation(
        userId: String,
        sessionId: String,
        onSuccess: (List<Message>) -> Unit,
        onError: (Exception) -> Unit
    ) {
        apiService.fetchSessionHistory(
            userId = userId,
            sessionId = sessionId,
            onSuccess = { messagesArray ->
                val messages = mutableListOf<Message>()
                
                // Process all messages
                for (i in 0 until messagesArray.length()) {
                    val message = messagesArray.getJSONObject(i)
                    val role = message.getString("role")
                    val content = message.getString("message")
                    val isUser = role == "user"
                    
                    val processedContent = if (!isUser && content.trim().startsWith("{")) {
                        try {
                            val jsonObj = JSONObject(content)
                            val blocks = jsonObj.optJSONObject("response")?.optJSONObject("content")?.optJSONArray("blocks")
                                
                            if (blocks != null) {
                                val extractedContent = StringBuilder()
                                for (j in 0 until blocks.length()) {
                                    blocks.optJSONObject(j)?.optString("content")?.let { 
                                        extractedContent.append(it).append("\n\n")
                                    }
                                }
                                
                                if (extractedContent.isNotEmpty()) extractedContent.toString().trim() else content
                            } else {
                                content
                            }
                        } catch (e: Exception) {
                            content
                        }
                    } else {
                        content
                    }
                    
                    messages.add(Message(processedContent, isUser, sessionId))
                }
                
                SwingUtilities.invokeLater {
                    onSuccess(messages)
                }
            },
            onError = { error ->
                SwingUtilities.invokeLater {
                    onError(error)
                }
            }
        )
    }
}
