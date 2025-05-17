package tech.beskar.baid.intelijplugin.controller

import com.intellij.openapi.diagnostic.Logger
import tech.beskar.baid.intelijplugin.model.ChatSession
import tech.beskar.baid.intelijplugin.model.SessionPreview
import tech.beskar.baid.intelijplugin.service.BaidAPIService
import java.util.*
import java.util.concurrent.CompletableFuture
import java.util.function.Consumer
import java.util.function.Function
import javax.swing.SwingUtilities


class SessionController private constructor() {
    private val apiService: BaidAPIService = BaidAPIService.getInstance()
    private val authController: AuthController = AuthController.getInstance()
    var currentSessionId: String? = null

    var currentSession: ChatSession? = null
        private set


    fun loadSession(sessionId: String?, onSuccess: Consumer<ChatSession?>, onError: Consumer<Throwable?>) {
        authController.validateAuthentication({
            CompletableFuture.allOf(
                authController.accessToken,
                authController.userId
            ).thenAccept(Consumer { v: Void? ->
                val accessToken = authController.accessToken.join()
                val userId = authController.userId.join()

                if (accessToken == null || userId == null) {
                    SwingUtilities.invokeLater(Runnable { onError.accept(IllegalStateException("Authentication failed")) })
                    return@Consumer
                }
                apiService.loadConversationHistory(userId, sessionId, accessToken, { session: ChatSession? ->
                    currentSessionId = sessionId
                    currentSession = session
                    onSuccess.accept(session)
                }, { error: Throwable? ->
                    LOG.error("Error loading session", error)
                    onError.accept(error)
                })
            }).exceptionally(Function { error: Throwable? ->
                LOG.error("Error getting authentication info", error)
                SwingUtilities.invokeLater(Runnable { onError.accept(error) })
                null
            })
        }, {
            onError.accept(IllegalStateException("Authentication failed"))
        })
    }

    fun loadSessionPreviews(onSuccess: Consumer<MutableList<SessionPreview>?>, onError: Consumer<Throwable?>) {
        authController.validateAuthentication({
            CompletableFuture.allOf(
                authController.accessToken,
                authController.userId
            ).thenAccept(Consumer { v: Void? ->
                val accessToken = authController.accessToken.join()
                val userId = authController.userId.join()

                if (accessToken == null || userId == null) {
                    SwingUtilities.invokeLater(Runnable { onError.accept(IllegalStateException("Authentication failed")) })
                    return@Consumer
                }
                apiService.fetchUserSessions(userId, accessToken, { previews: MutableList<SessionPreview?>? ->
                    // Load message previews for each session
                    if (previews != null) {
                        val nonNullablePreviews = previews.filterNotNull().toMutableList()
                        loadPreviewContents(userId, accessToken, nonNullablePreviews, onSuccess, onError)
                    } else {
                        onSuccess.accept(mutableListOf())
                    }
                }, { error: Throwable? ->
                    LOG.error("Error loading session previews", error)
                    onError.accept(error)
                })
            }).exceptionally(Function { error: Throwable? ->
                LOG.error("Error getting authentication info", error)
                SwingUtilities.invokeLater(Runnable { onError.accept(error) })
                null
            })
        }, {
            onError.accept(IllegalStateException("Authentication failed"))
        })
    }

    private fun loadPreviewContents(
        userId: String?,
        accessToken: String?,
        previews: MutableList<SessionPreview>,
        onSuccess: Consumer<MutableList<SessionPreview>?>,
        onError: Consumer<Throwable?>?
    ) {
        if (previews.isEmpty()) {
            onSuccess.accept(previews)
            return
        }


        // Create a counter to track completed preview loads
        val completed = intArrayOf(0)
        val total = previews.size


        // Load preview for each session
        for (preview in previews) {
            apiService.loadMessagePreview(
                userId,
                preview.sessionId,
                accessToken,
                { previewText: String? ->
                    preview.setTruncatedPreviewText(previewText, 60)
                    // Check if all previews are loaded
                    completed[0]++
                    if (completed[0] >= total) {
                        onSuccess.accept(previews)
                    }
                },
                { error: Throwable? ->
                    LOG.error("Error loading preview for session " + preview.sessionId, error)
                    preview.previewText = "Error loading preview"


                    // Still count this as completed
                    completed[0]++
                    if (completed[0] >= total) {
                        onSuccess.accept(previews)
                    }
                }
            )
        }
    }

    fun clearCurrentSession() {
        currentSessionId = null
        currentSession = null
    }

    companion object {
        private val LOG = Logger.getInstance(SessionController::class.java)

        @get:Synchronized
        var _instance: SessionController? = null
            get() {
                if (field == null) {
                    field = SessionController()
                }
                return field
            }

        fun getInstance(): SessionController {
            if(_instance == null) {
                _instance = SessionController()
            }
            return _instance!!
        }
    }
}