package tech.beskar.baid.intelijplugin.model

import org.json.JSONObject
import tech.beskar.baid.intelijplugin.model.common.SessionId
import tech.beskar.baid.intelijplugin.model.common.UserId
import java.util.*


class SessionPreview
 (
    val sessionId: SessionId?, val userId: UserId?, val lastUsedAt: Date // Changed types
) {
    var previewText: String? = "Loading preview..."

    val formattedLastUsedDate: String?
        get() {
            try {
                return lastUsedAt.toString()
            } catch (e: Exception) {
                println("Error formatting last used date: ${e.message}")
                return Date().toString()
            }
        }

    fun setTruncatedPreviewText(fullText: String?, maxLength: Int) {
        if (fullText == null || fullText.isEmpty()) {
            this.previewText = "Empty conversation"
            return
        }

        if (fullText.length > maxLength) {
            this.previewText = fullText.substring(0, maxLength) + "..."
        } else {
            this.previewText = fullText
        }
    }

    companion object {
        fun fromJson(sessionJson: JSONObject): SessionPreview {
            val sessionIdValue = sessionJson.optString("session_id", null)
            val sessionId = sessionIdValue?.let { SessionId(it) }

            val userIdValue = sessionJson.optString("user_id", null)
            val userId = userIdValue?.let { UserId(it) }

            // Parse last used date
            var lastUsedAt = Date() // Default to now
            try {
                if (sessionJson.has("last_used_at")) {
                    val lastUsedAtStr = sessionJson.getString("last_used_at")
                    // Assuming ISO_OFFSET_DATE_TIME or similar. Adjust if format is different.
                    // For consistency with other models, let's assume SimpleDateFormat if that's the standard.
                    // However, the original used DateTimeFormatter.ISO_OFFSET_DATE_TIME. Keep that for now.
                    val formatter = java.time.format.DateTimeFormatter.ISO_OFFSET_DATE_TIME
                    lastUsedAt = Date.from(java.time.Instant.from(formatter.parse(lastUsedAtStr)))
                }
            } catch (e: Exception) {
                // Log error appropriately
                println("Error parsing last used date for SessionPreview: ${e.message}")
            }

            return SessionPreview(sessionId, userId, lastUsedAt)
        }
    }
}