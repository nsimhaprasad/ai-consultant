package tech.beskar.baid.intelijplugin.controller

import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import org.json.JSONObject
import tech.beskar.baid.intelijplugin.model.Block
import tech.beskar.baid.intelijplugin.model.FileContext
import tech.beskar.baid.intelijplugin.model.Message
import tech.beskar.baid.intelijplugin.service.BaidAPIService
// Removed: import tech.beskar.baid.intelijplugin.service.DiffService
import tech.beskar.baid.intelijplugin.service.InlineDiffService // Added
import tech.beskar.baid.intelijplugin.service.StreamingResponseHandler
import tech.beskar.baid.intelijplugin.ui.InlineDiffDisplayManager // Added
import com.intellij.openapi.fileEditor.FileEditorManager // Added
import com.intellij.openapi.fileEditor.FileDocumentManager // Added
import com.intellij.openapi.editor.Editor // Added (ensure it's this one)
// Removed: import java.io.File - no longer used directly here for diff
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

                // Instantiate new services (or get them if they become properties/project services)
                // No, project is not nullable here. It is project!! earlier.
                val inlineDiffService = InlineDiffService() 
                val inlineDiffDisplayManager = InlineDiffDisplayManager(project!!)


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
                            { block: Block? ->
                                if (block is Block.Code && block.filename != null) {
                                    val editor = FileEditorManager.getInstance(project)?.selectedTextEditor
                                    if (editor != null) {
                                        val currentFile = FileDocumentManager.getInstance().getFile(editor.document)
                                        // More robust filename check:
                                        // Consider block.filename could be relative or absolute.
                                        // For now, using endsWith as a basic check.
                                        // A truly robust check might involve resolving block.filename against project.basePath
                                        // and comparing VirtualFile objects.
                                        val targetFilename = block.filename.replace("\\", "/") // Normalize separators
                                        val currentFilePath = currentFile?.path?.replace("\\", "/")

                                        if (currentFile != null && currentFilePath != null && currentFilePath.endsWith(targetFilename, ignoreCase = true)) {
                                            val documentText = editor.document.text
                                            val newContent = block.content
                                            
                                            LOG.info("Showing inline diff for ${block.filename} in editor ${currentFile.path}")
                                            inlineDiffDisplayManager.showInlineDiffs(editor, documentText, newContent, inlineDiffService)
                                            
                                            // NOTE: Block is NOT added to responseBlocks or passed to onBlockReceived.
                                            // Interaction is handled by inline diff UI.
                                        } else {
                                            LOG.warn("Inline diff skipped: Editor not showing target file ${block.filename}. Current file: ${currentFile?.path}")
                                            responseBlocks.add(block)
                                            onBlockReceived.accept(block)
                                        }
                                    } else {
                                        LOG.warn("Inline diff skipped: No suitable active editor for ${block.filename}.")
                                        responseBlocks.add(block)
                                        onBlockReceived.accept(block)
                                    }
                                } else {
                                    if (block != null) {
                                        responseBlocks.add(block)
                                    }
                                    onBlockReceived.accept(block) // block can be null
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