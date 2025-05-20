package tech.beskar.baid.intelijplugin.model.common

import com.google.gson.annotations.SerializedName

// Using @JvmInline for inline classes could be an option for performance,
// but data classes are fine for now and offer `copy()` and `componentN()` if needed.

data class MessageId(
    @SerializedName("message_id") // Ensure GSON uses this name for serialization if needed
    val value: String
)

data class SessionId(
    @SerializedName("session_id") // Ensure GSON uses this name for serialization if needed
    val value: String
)

data class UserId(
    @SerializedName("user_id") // Ensure GSON uses this name for serialization if needed
    val value: String
)
