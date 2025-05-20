package tech.beskar.baid.intelijplugin.model

import org.json.JSONArray
import org.json.JSONObject
import tech.beskar.baid.intelijplugin.model.common.SessionId
import tech.beskar.baid.intelijplugin.model.common.UserId
import java.text.SimpleDateFormat
import java.util.*

class ChatSession {
    var sessionId: SessionId? // Changed to SessionId
    val userId: UserId?       // Changed to UserId
    private val _messages: MutableList<Message> = ArrayList() // Renamed and initialized
    var createdAt: Date?
    var lastUsedAt: Date
    var isActive: Boolean

    constructor(sessionId: SessionId?, userId: UserId?, createdAt: Date?) {
        this.sessionId = sessionId
        this.userId = userId
        // _messages is already initialized
        this.createdAt = createdAt
        this.lastUsedAt = Date() // Default to now, can be updated by addMessage or setMessagesFromJson
        this.isActive = true
    }

    fun addMessage(message: Message) {
        _messages.add(message)
        // Optional: _messages.sortBy { it.timestamp } // If order isn't guaranteed
        this.lastUsedAt = Date() // Update last used timestamp
    }

    fun setMessagesFromJson(messagesArray: JSONArray) {
        _messages.clear()

        if (messagesArray.length() == 0) {
            // If no messages, lastUsedAt might remain the construction time or be explicitly set if needed.
            // For now, if messages are empty, lastUsedAt is not updated from messages.
            // Could also default to createdAt or now.
            this.lastUsedAt = Date() // Or this.createdAt ?: Date()
            return
        }

        for (i in 0..<messagesArray.length()) {
            val messageJson = messagesArray.getJSONObject(i)
            val message = Message.fromJson(messageJson) // Message.fromJson already handles potential null
            _messages.add(message)
        }

        // Update last used timestamp from the last message if available
        // Assuming messages are ordered by timestamp in the JSON array
        val lastMessageJson = messagesArray.getJSONObject(messagesArray.length() - 1)
        if (lastMessageJson.has("timestamp")) {
            try {
                val timestampStr = lastMessageJson.getString("timestamp")
                val format = SimpleDateFormat("yyyy-MM-dd HH:mm:ss") // Consider making format a const or static
                this.lastUsedAt = format.parse(timestampStr)
            } catch (e: Exception) {
                // Log error appropriately
                println("Error parsing timestamp from last message: ${e.message}")
                this.lastUsedAt = Date() // Fallback to current date
            }
        } else {
            this.lastUsedAt = Date() // Fallback if last message has no timestamp
        }
    }

    fun getMessages(): List<Message> { // Return type changed to immutable List
        return _messages.toList() // Returns an immutable copy
    }

    companion object {
        // Consider a date parsing helper if this format is used elsewhere
        private val DATE_FORMAT = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())

        fun fromJson(sessionJson: JSONObject): ChatSession {
            val sessionIdValue = sessionJson.optString("session_id", null)
            val sessionId = sessionIdValue?.let { SessionId(it) }

            val userIdValue = sessionJson.optString("user_id", null)
            val userId = userIdValue?.let { UserId(it) }

            // Parse dates
            var createdAt = Date() // Default to now
            var lastUsedAt = Date() // Default to now
            try {
                if (sessionJson.has("created_at")) {
                    val createdAtStr = sessionJson.getString("created_at")
                    createdAt = DATE_FORMAT.parse(createdAtStr) ?: Date()
                }

                if (sessionJson.has("last_used_at")) {
                    val lastUsedAtStr = sessionJson.getString("last_used_at")
                    lastUsedAt = DATE_FORMAT.parse(lastUsedAtStr) ?: Date()
                }
            } catch (e: Exception) {
                // Log error appropriately
                println("Error parsing session timestamps: ${e.message}")
                // createdAt and lastUsedAt will retain their default 'now' values
            }

            val session = ChatSession(sessionId, userId, createdAt)
            session.lastUsedAt = lastUsedAt // Set lastUsedAt, potentially overriding the constructor's default 'now'

            // If messages are part of the session JSON, parse them here
            if (sessionJson.has("messages") && sessionJson.get("messages") is JSONArray) {
                session.setMessagesFromJson(sessionJson.getJSONArray("messages"))
            }


            return session
        }
    }
}