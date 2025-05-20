package tech.beskar.baid.intelijplugin.controller

import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import tech.beskar.baid.intelijplugin.model.*
import tech.beskar.baid.intelijplugin.service.StreamingResponseHandler
import java.util.function.Consumer

// Constructor updated with all dependencies
class APIController constructor(
    private val authController: IAuthController,
    private val sessionController: ISessionController,
    private val chatController: IChatController // Added, though its direct uses are being removed
    // Removed baidApiService from constructor as it's used by underlying controllers
    // Project is also removed as it's passed directly to methods that need it (like signIn)
) {

    fun initialize(project: Project?, onAuthenticated: Consumer<UserProfile?>, onNotAuthenticated: Runnable) {
        // Project is passed to authController.signIn if needed, not stored here.
        authController.checkAuthenticationStatus { authenticated: Boolean? ->
            if (authenticated == true) {
                val profile = authController.currentUser
                onAuthenticated.accept(profile)
            } else {
                onNotAuthenticated.run()
            }
        }
    }

    // Retained for now, but could be called directly on IAuthController by consumers
    fun signIn(project: Project, onSuccess: Consumer<UserProfile?>, onError: Consumer<Throwable?>) {
        authController.signIn(project, onSuccess, onError)
    }

    fun signOut(onComplete: Runnable) {
        authController.signOut {
            // Session and chat clearing should ideally be handled by observers or higher-level coordination
            // For now, keep it here as per existing logic, but acknowledge it's not purely SRP for Auth.
            sessionController.clearCurrentSession()
            chatController.clearConversation() // Use the injected chatController
            onComplete.run()
        }
    }

    // Delegating to SessionController
    fun loadConversation(sessionId: tech.beskar.baid.intelijplugin.model.common.SessionId?, onSuccess: Consumer<ChatSession?>, onError: Consumer<Throwable?>) {
        // The original also called chatController.setCurrentMessages. This responsibility should move.
        // For now, SessionController.loadConversationDetails is expected to just fetch.
        // The calling context (e.g., BaidToolWindowController) will handle updating the chat.
        sessionController.loadConversationDetails(sessionId, onSuccess, onError)
    }

    // Delegating to SessionController
    fun loadPastConversations(onSuccess: Consumer<List<SessionPreview?>>, onError: Consumer<Throwable?>) {
        // Changed Consumer type to List as SessionController.fetchUserSessionPreviews might return immutable
        sessionController.fetchUserSessionPreviews(onSuccess, onError)
    }

    // Removed sendMessage(...)
    // Removed clearCurrentSession()

    val currentUser: UserProfile?
        get() = authController.currentUser

    // Removed createErrorBlock(error: Throwable): Block

    companion object {
        private val LOG = Logger.getInstance(APIController::class.java)
        // getInstance() and _instance removed
    }
}