package tech.beskar.baid.intelijplugin.controller

import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import tech.beskar.baid.intelijplugin.model.*
import tech.beskar.baid.intelijplugin.service.StreamingResponseHandler
import java.util.function.Consumer


class APIController private constructor() {
    private val authController: AuthController = AuthController.getInstance()
    private val chatController: ChatController = ChatController.getInstance()
    private val sessionController: SessionController = SessionController.getInstance()

    fun initialize(project: Project?, onAuthenticated: Consumer<UserProfile?>, onNotAuthenticated: Runnable) {
        authController.checkAuthenticationStatus { authenticated: Boolean? ->
            if (authenticated == true) {
                val profile = authController.currentUser
                onAuthenticated.accept(profile)
            } else {
                onNotAuthenticated.run()
            }
        }
    }

    fun signIn(project: Project, onSuccess: Consumer<UserProfile?>) {
        authController.signIn(project, onSuccess)
    }

    fun signOut(onComplete: Runnable) {
        authController.signOut {
            // Also clear session data
            sessionController.clearCurrentSession()
            chatController.clearConversation()
            onComplete.run()
        }
    }

    fun loadConversation(sessionId: String?, onSuccess: Consumer<ChatSession?>, onError: Consumer<Throwable?>) {
        sessionController.loadSession(sessionId, { session: ChatSession? ->
            chatController.setCurrentMessages(session!!.getMessages())
            onSuccess.accept(session)
        }, onError)
    }

    fun loadPastConversations(onSuccess: Consumer<MutableList<SessionPreview>?>, onError: Consumer<Throwable?>) {
        sessionController.loadSessionPreviews(onSuccess, onError)
    }

    fun sendMessage(
        project: Project?,
        content: String,
        onMessageSent: Consumer<Message?>,
        onBlockReceived: Consumer<Block?>,
        onComplete: Runnable?,
        onError: Consumer<Throwable?>
    ) {
        chatController.sendMessage(
            project,
            content,
            onMessageSent,
            onBlockReceived,
            onComplete,
            onError
        )
    }

    val currentUser: UserProfile?
        get() = authController.currentUser

    fun createErrorBlock(error: Throwable): Block {
        return StreamingResponseHandler.createErrorBlock(error)
    }

    fun clearCurrentSession() {
        sessionController.clearCurrentSession()
    }

    companion object {
        private val LOG = Logger.getInstance(APIController::class.java)

        @get:Synchronized
        var _instance: APIController? = null
            get() {
                if (field == null) {
                    field = APIController()
                }
                return field
            }
        fun getInstance(): APIController {
            if(_instance == null) {
                _instance = APIController()
            }
            return _instance!!
        }
    }
}