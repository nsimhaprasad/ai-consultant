package tech.beskar.baid.intelijplugin.ui

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.project.Project
import com.intellij.ui.components.JBPanel
import org.json.JSONArray
import tech.beskar.baid.intelijplugin.api.*
import tech.beskar.baid.intelijplugin.auth.GoogleAuthService
import tech.beskar.baid.intelijplugin.config.BaidConfiguration
import tech.beskar.baid.intelijplugin.model.Message
import java.io.InputStream
import javax.swing.JPanel
import javax.swing.SwingUtilities

class ChatController(
    private val project: Project,
    private val onMessageReceived: (Message) -> Unit,
    private val onThinkingMessageRemoved: () -> Unit,
    private val onAuthenticationRequired: () -> Unit,
    private val onSessionIdUpdated: (String?) -> Unit
) {
    // API services
    private val authService = GoogleAuthService.getInstance()
    private val config = BaidConfiguration.getInstance()
    private val apiService: BaidApiService
    private val sessionManager: SessionManager
    private val conversationRepository: ConversationRepository
    private val messagePanelFactory: MessagePanelFactory
    
    // Initialize services
    init {
        apiService = ApiServiceFactory.createApiService(authService, config)
        sessionManager = ApiServiceFactory.createSessionManager()
        conversationRepository = ApiServiceFactory.createConversationRepository(apiService)
        messagePanelFactory = MessagePanelFactory(authService)
    }
    
    fun sendPrompt(prompt: String, messagePanel: JPanel) {
        // Check authentication first
        apiService.checkAuthentication { isAuthenticated ->
            if (!isAuthenticated) {
                SwingUtilities.invokeLater {
                    onAuthenticationRequired()
                }
                return@checkAuthentication
            }
            
            // Get the currently open file from the editor
            val fileEditorManager = com.intellij.openapi.fileEditor.FileEditorManager.getInstance(project)
            val editor = fileEditorManager.selectedTextEditor
            val document = editor?.document
            val virtualFile = fileEditorManager.selectedFiles.firstOrNull()

            // Get file content and metadata
            val fileText = document?.text ?: "No file open."
            val filePath = virtualFile?.path ?: "No file path available"
            val fileName = virtualFile?.name ?: "No file name available"
            
            // Create context map
            val context = mapOf(
                "file_content" to fileText,
                "file_path" to filePath,
                "file_name" to fileName,
                "is_open" to (document != null)
            )
            
            // Create response handler
            val responseHandler = ApiServiceFactory.createResponseHandler(
                onSessionIdReceived = { sessionId ->
                    sessionManager.setSessionId(sessionId)
                    onSessionIdUpdated(sessionId)
                },
                onErrorReceived = { error, isAuthError ->
                    SwingUtilities.invokeLater {
                        if (isAuthError) {
                            onAuthenticationRequired()
                        } else {
                            onMessageReceived(Message(
                                "Sorry, I encountered an error: ${error.message}",
                                isUser = false
                            ))
                        }
                    }
                }
            )
            
            // Send the prompt to the API
            apiService.sendPrompt(
                prompt = prompt,
                context = context,
                sessionId = sessionManager.currentSessionId,
                onStreamStart = { stream ->
                    // Handle the streaming response directly
                    responseHandler.handleStreamingResponse(stream, messagePanel)
                },
                onStreamComplete = { sessionId ->
                    // Session ID is already handled by the response handler
                },
                onError = { error ->
                    responseHandler.handleError(
                        error,
                        error.message?.contains("401") == true || error.message?.contains("403") == true
                    )
                }
            )
        }
    }
    
    
    fun loadPastConversations(
        onSuccess: (List<ConversationRepository.Conversation>) -> Unit,
        onError: (Exception) -> Unit
    ) {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val userInfo = authService.getUserInfo()
                if (userInfo != null) {
                    val userId = userInfo.email
                    conversationRepository.loadConversations(
                        userId = userId,
                        onSuccess = onSuccess,
                        onError = onError
                    )
                } else {
                    onError(Exception("User not authenticated"))
                }
            } catch (e: Exception) {
                onError(e)
            }
        }
    }
    
    fun loadConversation(
        sessionId: String,
        onSuccess: (List<Message>) -> Unit,
        onError: (Exception) -> Unit
    ) {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val userInfo = authService.getUserInfo()
                if (userInfo != null) {
                    val userId = userInfo.email
                    
                    // Update session ID
                    sessionManager.setSessionId(sessionId)
                    onSessionIdUpdated(sessionId)
                    
                    // Load conversation history using the repository
                    conversationRepository.loadConversation(
                        userId = userId,
                        sessionId = sessionId,
                        onSuccess = { messages ->
                            // Process messages and return them in the correct order
                            // This matches the behavior in the original implementation
                            val processedMessages = messages.map { message ->
                                // Ensure message has the correct session ID
//                                if (message.sessionId != sessionId) {
//                                    message.copy(sessionId = sessionId)
//                                } else {
                                    message
//                                }
                            }
                            
                            // Call the success callback with the processed messages
                            onSuccess(processedMessages)
                        },
                        onError = { error ->
                            // Pass the error to the caller
                            onError(error)
                        }
                    )
                } else {
                    onError(Exception("User not authenticated"))
                }
            } catch (e: Exception) {
                onError(e)
            }
        }
    }
    
    fun startNewConversation() {
        sessionManager.startNewSession()
        onSessionIdUpdated(null)
    }
    
    fun checkAuthentication(onResult: (Boolean) -> Unit) {
        apiService.checkAuthentication(onResult)
    }
    

    fun createMessagePanel(message: Message): JBPanel<JBPanel<*>> {
        return messagePanelFactory.createMessagePanel(message)
    }
    

    fun createThinkingPanel(): JBPanel<JBPanel<*>> {
        return messagePanelFactory.createThinkingPanel()
    }
}
