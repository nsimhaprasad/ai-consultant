package tech.beskar.baid.intelijplugin.controller

import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.progress.ProgressManager
import com.intellij.openapi.project.Project
import tech.beskar.baid.intelijplugin.model.Block
import tech.beskar.baid.intelijplugin.model.ChatSession
import tech.beskar.baid.intelijplugin.model.Message
import tech.beskar.baid.intelijplugin.model.UserProfile
import tech.beskar.baid.intelijplugin.ui.toolwindow.BaidToolWindowActions
import tech.beskar.baid.intelijplugin.ui.toolwindow.BaidToolWindowView
import javax.swing.SwingUtilities

class BaidToolWindowController(
    private val project: Project,
    private val view: BaidToolWindowView,
    private val apiController: APIController, // Kept as concrete for now
    private val chatController: IChatController,
    private val authController: IAuthController,
    private val sessionController: ISessionController
) : BaidToolWindowActions {

    private var isShowingPastConversations = false // State managed by controller

    init {
        initialAuthCheck()
    }

    override fun sendMessage(prompt: String) {
        val chatView = view.getChatPanelView()

        view.clearInputField()
        chatView.addMessage(Message(prompt, true))
        chatView.startStreamingResponse()
        view.setControlsEnabled(false)

        val task = object : com.intellij.openapi.progress.Task.Backgroundable(project, "Consulting AI", true) {
            private lateinit var indicator: com.intellij.openapi.progress.ProgressIndicator
            
            // Cleanup logic to be called on success, error, or cancellation.
            private fun operationCleanup() = SwingUtilities.invokeLater {
                chatView.endStreamingResponse()
                view.setControlsEnabled(true)
                view.focusInputField()
            }

            override fun run(indicator: com.intellij.openapi.progress.ProgressIndicator) {
                this.indicator = indicator
                indicator.isIndeterminate = true
                indicator.text = "Sending your message..."
                performSendMessage(prompt, chatView)
            }

            override fun onSuccess() {
                // This is called if run() completes without exception.
                indicator.text = "Processing complete"
            }
            
            override fun onFinished() {
                // Called after run (whether it succeeded or failed) and after onSuccess/onThrowable/onCancel.
                operationCleanup()
            }

            override fun onThrowable(error: Throwable) {
                SwingUtilities.invokeLater {
                    chatView.addStreamingBlock(Block.fromError(error))
                }
                indicator.text = "Error: ${error.message}"
            }

            override fun onCancel() {
                indicator.text = "Operation cancelled"
                // Cleanup is handled by onFinished.
            }
        }
        ProgressManager.getInstance().run(task)
    }

    override fun startNewSession() {
        view.setControlsEnabled(false)
        view.clearChat()
        sessionController.clearCurrentSession()
        authController.currentUser?.let {
            view.displayWelcomeMessage(it.name, isNewSession = true)
        }
        view.setControlsEnabled(true)
    }

    override fun togglePastConversations() {
        isShowingPastConversations = !isShowingPastConversations
        view.togglePastConversationsView(isShowingPastConversations)
    }

    override fun selectSession(sessionPreview: tech.beskar.baid.intelijplugin.model.SessionPreview) {
        isShowingPastConversations = false
        view.togglePastConversationsView(false)

        val sessionId = sessionPreview.sessionId
        if (sessionId == null) {
            handleSessionSelectionError("Selected session preview has no ID.")
            return
        }
        
        // Optional UX improvement: view.getChatPanelView().showLoadingState()
        sessionController.loadConversationDetails(sessionId,
            onSuccess = { loadedSession -> handleLoadedSessionSuccess(loadedSession, sessionId) },
            onError = { error -> handleSessionLoadError(error, sessionId) }
        )
    }

    private fun handleLoadedSession(loadedSession: ChatSession?, originalSessionId: tech.beskar.baid.intelijplugin.model.common.SessionId) {
        if (loadedSession == null) {
            handleSessionSelectionError("Could not load details for session ID: ${originalSessionId.value}")
            return
        }
        chatController.setCurrentMessages(loadedSession.getMessages().toMutableList())
        view.loadChatConversation(loadedSession)
        sessionController.currentSessionId = loadedSession.sessionId // Set current session ID on successful load
    }

    private fun handleSessionSelectionError(errorMessage: String) {
        // Consider using a Logger for more structured logging
        println("Session Selection Error: $errorMessage")
        view.addMessageToChat(Message("Error: $errorMessage", false))
    }

    private fun handleSessionLoadError(error: Throwable, sessionId: tech.beskar.baid.intelijplugin.model.common.SessionId) {
        // Consider using a Logger
        println("Error loading session ${sessionId.value}: ${error.message}")
        view.addMessageToChat(Message("Error loading session: ${error.message}", false))
    }

    // Renamed handleLoadedSession to be more specific about success
    private fun handleLoadedSessionSuccess(loadedSession: ChatSession?, originalSessionId: tech.beskar.baid.intelijplugin.model.common.SessionId) {
        if (loadedSession == null) {
            handleSessionSelectionError("Could not load details for session ID: ${originalSessionId.value}")
            return
        }
        chatController.setCurrentMessages(loadedSession.getMessages().toMutableList())
        view.loadChatConversation(loadedSession)
        sessionController.currentSessionId = loadedSession.sessionId
    }


    override fun loginSuccess(userProfile: UserProfile) {
        view.showMainScreen()
        view.updateUserProfile(userProfile)
        view.displayWelcomeMessage(userProfile.name)
    }

    override fun loginError(error: Throwable) {
        view.showLoginScreen()
        view.updateUserProfile(null)
        val errorMessage = extractErrorMessage(error)
        NotificationGroupManager.getInstance()
            .getNotificationGroup("Baid Notifications") // Ensure this notification group is registered
            .createNotification(errorMessage, NotificationType.ERROR)
            .notify(project)
    }

    private fun extractErrorMessage(error: Throwable): String {
        return error.cause?.message?.substringAfter(":")?.trim()?.ifBlank { null }
            ?: error.message?.substringAfter(":")?.trim()?.ifBlank { null }
            ?: "Something went wrong! Please try logging in again."
    }

    override fun signOut() {
        authController.signOut {
            view.showLoginScreen()
            view.updateUserProfile(null) // Ensure user profile is cleared in UI
        }
    }

    override fun showUserProfileMenu() {
        val currentUser = authController.currentUser
        if (currentUser == null) {
            view.showLoginScreen()
            return
        }
        // Call the new method in the view
        view.displayUserProfileMenu(currentUser.name, currentUser.email) { // currentUser.email is Email?
            signOut()
        }
    }

    private fun performSendMessage(prompt: String, chatView: tech.beskar.baid.intelijplugin.views.ChatPanelView) {
        try {
            chatController.sendMessage(
                project = project, // Pass the project instance from BaidToolWindowController
                content = prompt,
                onMessageSent = { /* User message already added to UI, handled by view.addMessage */ },
                onBlockReceived = { block -> SwingUtilities.invokeLater { chatView.addStreamingBlock(block) } },
                onComplete = { /* Handled by Task.onFinished -> operationCleanup */ },
                onError = { error -> throw Exception(error) } // Rethrow to be handled by Task.onThrowable
            )
        } catch (e: Exception) {
            throw e // Propagate to Task.onThrowable for centralized error handling in UI
        }
    }

    override fun initialAuthCheck() {
        apiController.initialize(
            project,
            onAuthenticated = { userProfile -> // Parameter type inferred
                view.showMainScreen()
                view.updateUserProfile(userProfile)
                view.displayWelcomeMessage(userProfile.name)
            },
            onNotAuthenticated = {
                view.showLoginScreen()
                view.updateUserProfile(null) // Ensure user profile is cleared in UI
            }
        )
    }
}
