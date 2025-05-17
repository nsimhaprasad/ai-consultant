package tech.beskar.baid.intelijplugin.model

import org.json.JSONObject
import java.util.*


class SessionPreview
 (
    val sessionId: String?, val userId: String?, val lastUsedAt: Date
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
            val sessionId = sessionJson.getString("session_id")
            val userId = sessionJson.optString("user_id", "")

            // Parse last used date
            var lastUsedAt = Date()
            try {
                if (sessionJson.has("last_used_at")) {
                    val lastUsedAtStr = sessionJson.getString("last_used_at")
                    val formatter = java.time.format.DateTimeFormatter.ISO_OFFSET_DATE_TIME
                    lastUsedAt = Date.from(java.time.Instant.from(formatter.parse(lastUsedAtStr)))
                }
            } catch (e: Exception) {
                println("Error parsing last used date: ${e.message}")
            }

            return SessionPreview(sessionId, userId, lastUsedAt)
        }
    }
}