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


    constructor(userId: String?) {
        this.userId = userId
        this.messages = ArrayList<Message>()
        this.createdAt = Date()
        this.lastUsedAt = Date()
        this.isActive = true
    }


    constructor(sessionId: String?, userId: String?, createdAt: Date?) {
        this.sessionId = sessionId
        this.userId = userId
        this.messages = ArrayList<Message>()
        this.createdAt = createdAt
        this.lastUsedAt = Date()
        this.isActive = true
    }


    fun addMessage(message: Message?) {
        messages.add(message!!)
        lastUsedAt = Date()
    }


    fun setMessagesFromJson(messagesArray: JSONArray) {
        messages.clear()

        for (i in 0..<messagesArray.length()) {
            val messageJson = messagesArray.getJSONObject(i)
            val message: Message? = Message.fromJson(messageJson)
            messages.add(message!!)
        }


        // Update last used timestamp
        lastUsedAt = Date()
    }

    val firstUserMessage: Message?
        get() {
            for (message in messages) {
                if (message.isUser) {
                    return message
                }
            }
            return null
        }

    fun getPreviewText(maxLength: Int): String {
        val firstMessage = this.firstUserMessage
        if (firstMessage == null) {
            return "Empty conversation"
        }

        val content = firstMessage.content
        if (content.length > maxLength) {
            return content.substring(0, maxLength) + "..."
        }
        return content
    }

    fun getMessages(): MutableList<Message?> {
        return ArrayList<Message?>(messages)
    }

    val formattedLastUsedDate: String?
        get() {
            try {
                val displayFormat = SimpleDateFormat("MM/dd/yyyy h:mm a")
                return displayFormat.format(lastUsedAt)
            } catch (e: Exception) {
                return lastUsedAt.toString()
            }
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