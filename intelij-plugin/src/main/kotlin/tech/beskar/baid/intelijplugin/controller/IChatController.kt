package tech.beskar.baid.intelijplugin.controller

import com.intellij.openapi.project.Project
import tech.beskar.baid.intelijplugin.model.Block
import tech.beskar.baid.intelijplugin.model.Message
import java.util.function.Consumer

interface IChatController {
    val isProcessingMessage: Boolean

    fun sendMessage(
        project: Project?,
        content: String,
        onMessageSent: Consumer<Message?>,
        onBlockReceived: Consumer<Block?>,
        onComplete: Runnable?,
        onError: Consumer<Throwable?>
    )

    fun clearConversation()
    fun getCurrentMessages(): MutableList<Message?> // Consider returning List<Message> for immutability if appropriate
    fun setCurrentMessages(messages: MutableList<Message?>) // Consider List<Message>
}
