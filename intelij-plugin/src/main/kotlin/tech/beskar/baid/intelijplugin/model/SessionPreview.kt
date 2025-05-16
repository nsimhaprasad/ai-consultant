package tech.beskar.baid.intelijplugin.model

import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.*


class SessionPreview
 (
    val sessionId: String?, val userId: String?, val lastUsedAt: Date
) {
    var previewText: String? = "Loading preview..."

    val formattedLastUsedDate: String?
        get() {
            try {
                val displayFormat = SimpleDateFormat("MM/dd/yyyy h:mm a")
                return displayFormat.format(lastUsedAt)
            } catch (e: Exception) {
                return lastUsedAt.toString()
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
                    val format = SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
                    lastUsedAt = format.parse(lastUsedAtStr)
                }
            } catch (e: Exception) {
                // Use current date if parsing fails
            }

            return SessionPreview(sessionId, userId, lastUsedAt)
        }
    }
}