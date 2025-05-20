package tech.beskar.baid.intelijplugin.controller

import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import org.json.JSONObject
import tech.beskar.baid.intelijplugin.model.Block
import tech.beskar.baid.intelijplugin.model.FileContext
import tech.beskar.baid.intelijplugin.model.Message
import tech.beskar.baid.intelijplugin.service.IBaidApiService // Changed to interface
import tech.beskar.baid.intelijplugin.service.StreamingResponseHandler
import java.util.*
import java.util.function.Consumer
import java.util.function.Function
import javax.swing.SwingUtilities

class ChatController constructor( // Made constructor public
    private val project: Project?, // Added project to constructor (already used)
    private val apiService: IBaidApiService, // Changed to interface and added to constructor
    private val authController: IAuthController, // Changed to interface and added to constructor
    private val sessionController: ISessionController // Changed to interface and added to constructor
) : IChatController { // Implement interface

    private val currentMessages: MutableList<Message?> = ArrayList()

    override var isProcessingMessage: Boolean = false // Added override
        private set

    override fun sendMessage( // Added override
        project: Project?,
        content: String,
        onMessageSent: Consumer<Message?>,
        onBlockReceived: Consumer<Block?>,
        onComplete: Runnable?,
        onError: Consumer<Throwable?>
    ) {
        if (isProcessingMessage) {
            onError.accept(IllegalStateException("Already processing a message"))
            return
        }

        isProcessingMessage = true

        val userMessage = Message(content, true)
        currentMessages.add(userMessage)
        onMessageSent.accept(userMessage)

        authController.validateAuthentication(
            onValid = {
                authController.accessToken.thenAccept { accessToken ->
                    if (accessToken == null) {
                        handleAuthFailure(onError, "Authentication failed: Access token is null.")
                        return@thenAccept
                    }
                    proceedWithSendMessage(project, content, accessToken, onBlockReceived, onComplete, onError)
                }.exceptionally { error ->
                    handleAuthFailure(onError, "Failed to retrieve access token: ${error.message}", error)
                    null // Required by exceptionally block
                }
            },
            onInvalid = { handleAuthFailure(onError, "Authentication failed: Validation returned invalid.") }
        )
    }

    private fun proceedWithSendMessage(
        project: Project?,
        content: String,
        accessToken: String,
        onBlockReceived: Consumer<Block?>,
        onComplete: Runnable?,
        onError: Consumer<Throwable?>
    ) {
        val fileContext = FileContext.fromCurrentEditor(project ?: error("Project context is required for sending messages."))
        val sessionId = sessionController.currentSessionId
        val responseBlocks = mutableListOf<Block>()

        apiService.sendMessage(
            content,
            fileContext,
            accessToken,
            sessionId,
            { jsonBlock -> // Assuming jsonBlock is JSONObject? from IBaidApiService
                jsonBlock?.let { // Ensure jsonBlock is not null before processing
                    StreamingResponseHandler.processJsonBlock(
                        it, // Now non-null
                        { block -> // Assuming block is Block?
                            block?.let { b -> responseBlocks.add(b) } // Add if not null
                            onBlockReceived.accept(block) // Pass original block (nullable)
                        },
                        { updatedSessionIdString ->
                            sessionController.currentSessionId = updatedSessionIdString?.let { tech.beskar.baid.intelijplugin.model.common.SessionId(it) }
                        }
                    )
                }
            },
            { updatedSessionIdString ->
                if (responseBlocks.isNotEmpty()) {
                    val messageContent = JSONObject().apply { put("blocks", Block.toJsonArray(responseBlocks)) }
                    currentMessages.add(Message(messageContent.toString(), false))
                }
                isProcessingMessage = false
                sessionController.currentSessionId = updatedSessionIdString?.let { tech.beskar.baid.intelijplugin.model.common.SessionId(it) }
                SwingUtilities.invokeLater(onComplete)
            },
            { error ->
                isProcessingMessage = false
                SwingUtilities.invokeLater { onError.accept(error) }
            }
        )
    }

    private fun handleAuthFailure(onError: Consumer<Throwable?>, message: String, cause: Throwable? = null) {
        isProcessingMessage = false
        val exception = IllegalStateException(message, cause)
        SwingUtilities.invokeLater { onError.accept(exception) }
    }

    override fun clearConversation() {
        currentMessages.clear()
    }

    override fun getCurrentMessages(): MutableList<Message?> {
        return ArrayList(currentMessages) // Return a copy
    }

    override fun setCurrentMessages(messages: MutableList<Message?>) {
        currentMessages.clear()
        currentMessages.addAll(messages.filterNotNull()) // Filter out null messages if any
    }

    companion object {
        private val LOG = Logger.getInstance(ChatController::class.java)
    }
}