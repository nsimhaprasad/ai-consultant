package tech.beskar.baid.intelijplugin.controller

import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import org.json.JSONObject
import tech.beskar.baid.intelijplugin.model.Block
import tech.beskar.baid.intelijplugin.model.FileContext
import tech.beskar.baid.intelijplugin.model.Message
import tech.beskar.baid.intelijplugin.service.BaidAPIService
import tech.beskar.baid.intelijplugin.service.DiffService // Added import
import tech.beskar.baid.intelijplugin.service.StreamingResponseHandler
import java.io.File // Added import
import java.util.*
import java.util.function.Consumer
import java.util.function.Function
import javax.swing.SwingUtilities

class ChatController private constructor() {
    private val apiService: BaidAPIService = BaidAPIService.getInstance()
    private val authController: AuthController = AuthController.getInstance()
    private val sessionController: SessionController = SessionController.getInstance()

    private val currentMessages: MutableList<Message?> = ArrayList()

    var isProcessingMessage: Boolean = false
        private set

    fun sendMessage(
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


        // Create and add user message
        val userMessage = Message(content, true)
        currentMessages.add(userMessage)
        onMessageSent.accept(userMessage)


        // Validate authentication before proceeding
        authController.validateAuthentication({
            // Get required tokens and session info
            authController.accessToken.thenAccept(Consumer { accessToken: String? ->
                if (accessToken == null) {
                    isProcessingMessage = false
                    onError.accept(IllegalStateException("Authentication failed"))
                    return@Consumer
                }
                // Get file context
                val fileContext = FileContext.fromCurrentEditor(project!!)


                // Get current session ID
                val sessionId: String? = sessionController.currentSessionId


                // Create a list to collect blocks for the final message
                val responseBlocks: MutableList<Block> = ArrayList()

                // Instantiate DiffService here, as project is available
                val diffService = DiffService(project)


                // Send the message to the API
                apiService.sendMessage(
                    content,
                    fileContext,
                    accessToken,
                    sessionId,
                    { jsonBlock: JSONObject? ->
                        // Process each block as it arrives
                        StreamingResponseHandler.processJsonBlock(
                            jsonBlock!!,
                            { block: Block? -> // This is the onBlockReceived lambda we are modifying
                                if (block is Block.Code && block.filename != null) {
                                    // For Code blocks with a filename, show the diff
                                    val file = File(project.basePath, block.filename) // Construct file path relative to project root
                                    var oldContent = ""
                                    if (file.exists()) {
                                        oldContent = file.readText(Charsets.UTF_8)
                                    }
                                    
                                    val onApplyAction = { appliedCodeBlock: tech.beskar.baid.intelijplugin.model.Block.Code ->
                                        responseBlocks.add(appliedCodeBlock)
                                        onBlockReceived.accept(appliedCodeBlock) // Call the original UI update callback
                                    }
                                    
                                    // Ensure DiffService is available or instantiated (already done above)
                                    diffService.showDiff(
                                        block, // Pass the original Block.Code object
                                        oldContent,
                                        onApplyAction // Pass the callback
                                    )
                                    
                                    // We will handle adding the block to responseBlocks after user accepts the diff.
                                    // For now, we will not call onBlockReceived.accept(block) here to prevent duplicate display.
                                    // The DiffDialog's "accept" action will eventually trigger adding the block or its modified version.
                                } else {
                                    // For other block types, or Code blocks without a filename, process as before
                                    responseBlocks.add(block!!)
                                    onBlockReceived.accept(block)
                                }
                            },
                            { updatedSessionId: String? ->
                                sessionController.currentSessionId = updatedSessionId
                            }
                        )
                    },
                    { updatedSessionId: String? ->
                        // Create and add AI message with all blocks
                        if (responseBlocks.isNotEmpty()) {
                            // Convert blocks to JSON and create a message
                            val messageContent = JSONObject().apply {
                                put("blocks", Block.toJsonArray(responseBlocks))
                            }
                            val aiMessage = Message(messageContent.toString(), false)
                            currentMessages.add(aiMessage)
                        }

                        isProcessingMessage = false
                        sessionController.currentSessionId = updatedSessionId
                        SwingUtilities.invokeLater(onComplete)
                    },
                    { error: Throwable? ->
                        isProcessingMessage = false
                        SwingUtilities.invokeLater { onError.accept(error) }
                    }
                )
            }).exceptionally(Function { error: Throwable? ->
                isProcessingMessage = false
                SwingUtilities.invokeLater { onError.accept(error) }
                null
            })
        }, {
            // Authentication invalid
            isProcessingMessage = false
            onError.accept(IllegalStateException("Authentication failed"))
        })
    }

    fun clearConversation() {
        currentMessages.clear()
    }

    fun getCurrentMessages(): MutableList<Message?> {
        return ArrayList<Message?>(currentMessages)
    }

    fun setCurrentMessages(messages: MutableList<Message?>) {
        currentMessages.clear()
        currentMessages.addAll(messages)
    }

    companion object {
        private val LOG = Logger.getInstance(ChatController::class.java)

        @get:Synchronized
        var _instance: ChatController? = null
            get() {
                if (field == null) {
                    field = ChatController()
                }
                return field
            }
        fun getInstance(): ChatController {
            if (_instance == null) {
                _instance = ChatController()
            }
            return _instance!!
        }
    }
}