package tech.beskar.baid.intelijplugin.model

import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.*

class ChatSession {
    var sessionId: String? = null
    val userId: String?
    private val messages: MutableList<Message>
    var createdAt: Date?
    var lastUsedAt: Date
    var isActive: Boolean


    constructor(sessionId: String?, userId: String?, createdAt: Date?) {
        this.sessionId = sessionId
        this.userId = userId
        this.messages = ArrayList<Message>()
        this.createdAt = createdAt
        this.lastUsedAt = Date()
        this.isActive = true
    }


    fun setMessagesFromJson(messagesArray: JSONArray) {
        messages.clear()

        for (i in 0..<messagesArray.length()) {
            val messageJson = messagesArray.getJSONObject(i)
            val message: Message? = Message.fromJson(messageJson)
            messages.add(message!!)
        }


        // Update last used timestamp
        val timestampStr = messagesArray.getJSONObject(messagesArray.length() - 1).getString("timestamp")
        try {
            val format = SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
            lastUsedAt = format.parse(timestampStr)
        } catch (e: Exception) {
            println("Error parsing timestamp: ${e.message}")
            lastUsedAt = Date()
        }
    }

    fun getMessages(): MutableList<Message?> {
        return ArrayList<Message?>(messages)
    }

    companion object {
        fun fromJson(sessionJson: JSONObject): ChatSession {
            val sessionId = sessionJson.getString("session_id")
            val userId = sessionJson.optString("user_id", "")


            // Parse dates
            var createdAt = Date()
            var lastUsedAt = Date()
            try {
                if (sessionJson.has("created_at")) {
                    val createdAtStr = sessionJson.getString("created_at")
                    val format = SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
                    createdAt = format.parse(createdAtStr)
                }

                if (sessionJson.has("last_used_at")) {
                    val lastUsedAtStr = sessionJson.getString("last_used_at")
                    val format = SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
                    lastUsedAt = format.parse(lastUsedAtStr)
                }
            } catch (e: Exception) {
                // Use current date if parsing fails
            }

            val session = ChatSession(sessionId, userId, createdAt)
            session.lastUsedAt = lastUsedAt

            return session
        }
    }
}