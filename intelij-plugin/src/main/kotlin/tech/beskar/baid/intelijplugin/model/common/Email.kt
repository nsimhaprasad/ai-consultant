package tech.beskar.baid.intelijplugin.model.common

import com.google.gson.annotations.SerializedName

data class Email(
    @SerializedName("email_address") // Ensure GSON uses this name for serialization if needed
    val value: String
) {
    init {
        // Basic email validation
        require(value.contains("@") && value.length > 3 && !value.startsWith("@") && !value.endsWith("@")) {
            "Invalid email format: $value"
        }
    }

    // Optional: Override toString() if you don't want the default data class representation
    // override fun toString(): String = value
}
