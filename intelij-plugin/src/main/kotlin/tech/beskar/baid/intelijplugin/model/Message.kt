package tech.beskar.baid.intelijplugin.model

import org.json.JSONObject
import tech.beskar.baid.intelijplugin.model.common.MessageId
import java.text.SimpleDateFormat
import java.util.*

// Added id field and updated constructors
class Message {
    // Getters
    val id: MessageId // Added ID field
    val content: String
    val isUser: Boolean
    val timestamp: Date?
    val role: String?

    constructor(content: String, isUser: Boolean, id: MessageId = MessageId(UUID.randomUUID().toString())) {
        this.id = id
        this.content = content
        this.isUser = isUser
        this.timestamp = Date()
        this.role = if (isUser) "user" else "assistant"
    }

    constructor(content: String, role: String?, timestamp: Date?, id: MessageId = MessageId(UUID.randomUUID().toString())) {
        this.id = id
        this.content = content
        this.role = role
        this.isUser = "user" == role
        this.timestamp = timestamp
    }

    fun containsJsonBlocks(): Boolean {
        if (!content.trim { it <= ' ' }.startsWith("{")) {
            return false
        }

        try {
            val jsonObj = JSONObject(content)
            return jsonObj.has("blocks") ||
                    (jsonObj.has("schema") && jsonObj.getString("schema") == "jetbrains-llm-response")
        } catch (e: Exception) {
            return false
        }
    }

    fun isJsonContent(): Boolean {
        return !isUser && content.trim().startsWith("{")
    }

    override fun toString(): String {
        return "Message(id=$id, content=$content, isUser=$isUser, timestamp=$timestamp, role=$role)" // Added id to toString
    }

    companion object {
        fun fromJson(messageJson: JSONObject): Message {
            val idValue = messageJson.optString("id", UUID.randomUUID().toString()) // Get ID or generate
            val messageId = MessageId(idValue)
            val content = messageJson.getString("message")
            val role = messageJson.getString("role")

            // Parse timestamp if available
            var timestamp: Date? = Date()
            try {
                if (messageJson.has("timestamp")) {
                    val timestampStr = messageJson.getString("timestamp")
                    val format = SimpleDateFormat("yyyy-MM-dd HH:mm:ss") // Consider making format a const or static
                    timestamp = format.parse(timestampStr)
                }
            } catch (e: Exception) {
                // Log error appropriately
                println("Error parsing timestamp: ${e.message}")
            }

            return Message(content, role, timestamp, messageId) // Pass messageId to constructor
        }
    }
}
