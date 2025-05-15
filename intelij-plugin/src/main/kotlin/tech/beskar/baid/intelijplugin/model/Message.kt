package tech.beskar.baid.intelijplugin.model

data class Message(
    val content: String,
    val isUser: Boolean,
    val sessionId: String? = null,
    val timestamp: Long = System.currentTimeMillis()
) {
    fun isThinking(): Boolean {
        return !isUser && content == "Thinking..."
    }
    
    fun isJsonContent(): Boolean {
        return !isUser && content.trim().startsWith("{")
    }
}
