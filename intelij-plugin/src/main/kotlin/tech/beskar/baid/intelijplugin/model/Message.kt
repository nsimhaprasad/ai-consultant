package tech.beskar.baid.intelijplugin.model

import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.*

class Message {
    // Getters
    val content: String
    val isUser: Boolean
    val timestamp: Date?
    val role: String?

    constructor(content: String, isUser: Boolean) {
        this.content = content
        this.isUser = isUser
        this.timestamp = Date()
        this.role = if (isUser) "user" else "assistant"
    }

    constructor(content: String, isUser: Boolean, timestamp: Date?) {
        this.content = content
        this.isUser = isUser
        this.timestamp = timestamp
        this.role = if (isUser) "user" else "assistant"
    }

    constructor(content: String, role: String?, timestamp: Date?) {
        this.content = content
        this.role = role
        this.isUser = "user" == role
        this.timestamp = timestamp
    }

    fun toJson(): JSONObject {
        val json = JSONObject()
        json.put("message", content)
        json.put("role", role)


        // Format timestamp
        val format = SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
        json.put("timestamp", format.format(timestamp))

        return json
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

    companion object {
        fun fromJson(messageJson: JSONObject): Message {
            val content = messageJson.getString("message")
            val role = messageJson.getString("role")


            // Parse timestamp if available
            var timestamp: Date? = Date()
            try {
                if (messageJson.has("timestamp")) {
                    val timestampStr = messageJson.getString("timestamp")
                    val format = SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
                    timestamp = format.parse(timestampStr)
                }
            } catch (e: Exception) {
                // Use current date if parsing fails
            }

            return Message(content, role, timestamp)
        }
    }
}
