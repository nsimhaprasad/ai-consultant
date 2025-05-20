package tech.beskar.baid.intelijplugin.controller

import com.intellij.openapi.diagnostic.Logger
import tech.beskar.baid.intelijplugin.model.ChatSession
import tech.beskar.baid.intelijplugin.model.SessionPreview
import tech.beskar.baid.intelijplugin.service.IBaidApiService
import java.util.*
import java.util.concurrent.CompletableFuture
import java.util.function.Consumer
import javax.swing.SwingUtilities


class SessionController constructor(
    private val authController: IAuthController,
    private val apiService: IBaidApiService
) : ISessionController {

    override var currentSessionId: tech.beskar.baid.intelijplugin.model.common.SessionId? = null
    override var currentSession: ChatSession? = null
        set


    override fun loadSession(sessionId: tech.beskar.baid.intelijplugin.model.common.SessionId?, onSuccess: Consumer<ChatSession?>, onError: Consumer<Throwable?>) {
        executeWithAuthentication(onError) { accessToken, userId ->
            apiService.loadConversationHistory(userId, sessionId, accessToken, { session ->
                currentSessionId = sessionId
                currentSession = session
                onSuccess.accept(session)
            }, { error ->
                LOG.error("Error loading session", error)
                onError.accept(error)
            })
        }
    }

    // Renamed from loadSessionPreviews and changed onSuccess type
    override fun loadSessionPreviews(onSuccess: Consumer<List<SessionPreview>?>, onError: Consumer<Throwable?>) {
        executeWithAuthentication(onError) { accessToken, userId ->
            apiService.fetchUserSessions(userId, accessToken, { previews ->
                if (previews != null) {
                    val nonNullablePreviews = previews.filterNotNull().toMutableList()
                    loadPreviewContents(userId, accessToken, nonNullablePreviews, onSuccess, onError)
                } else {
                    onSuccess.accept(emptyList())
                }
            }, { error ->
                LOG.error("Error loading session previews", error)
                onError.accept(error)
            })
        }
    }

    private fun executeWithAuthentication(
        onError: Consumer<Throwable?>,
        action: (accessToken: String, userId: tech.beskar.baid.intelijplugin.model.common.UserId) -> Unit
    ) {
        authController.validateAuthentication({
            CompletableFuture.allOf(
                authController.accessToken,
                authController.userId
            ).thenAccept {
                val accessToken = authController.accessToken.join()
                val userId = authController.userId.join()

                if (accessToken == null || userId == null) {
                    handleAuthenticationError(onError, "Authentication failed: Missing token or user ID.")
                    return@thenAccept
                }
                action(accessToken, userId)
            }.exceptionally { error ->
                handleAuthenticationError(onError, "Error getting authentication info.", error)
                null
            }
        }, {
            handleAuthenticationError(onError, "Authentication validation failed.")
        })
    }

    private fun handleAuthenticationError(onError: Consumer<Throwable?>, message: String, cause: Throwable? = null) {
        LOG.error(message, cause)
        SwingUtilities.invokeLater { onError.accept(IllegalStateException(message, cause)) }
    }

    private fun loadPreviewContents(
        userId: tech.beskar.baid.intelijplugin.model.common.UserId?,
        accessToken: String?,
        previews: MutableList<SessionPreview>,
        onSuccess: Consumer<List<SessionPreview>?>,
        onError: Consumer<Throwable?>? // Nullable if errors in individual previews are non-fatal for the whole op
    ) {
        if (previews.isEmpty()) {
            onSuccess.accept(emptyList())
            return
        }

        val completedCount = intArrayOf(0)
        val totalPreviews = previews.size

        previews.forEach { preview ->
            apiService.loadMessagePreview(
                userId,
                preview.sessionId,
                accessToken,
                { previewText: String? ->
                    preview.setTruncatedPreviewText(previewText, 60)
                    // Check if all previews are loaded
                    completedCount[0]++
                    if (completedCount[0] >= totalPreviews) {
                        onSuccess.accept(previews.toList()) // Return as immutable List
                    }
                },
                { error: Throwable? ->
                    LOG.error("Error loading preview for session ${preview.sessionId?.value}", error)
                    preview.previewText = "Error loading preview" // Update preview text on error

                    // Check completion even on error to avoid hanging
                    completedCount[0]++
                    if (completedCount[0] >= totalPreviews) {
                        onSuccess.accept(previews.toList())
                    }
                    // Optionally, call onError for individual preview load errors if needed:
                    // onError?.accept(error)
                }
            )
        }
    }

    override fun clearCurrentSession() {
        currentSessionId = null
        currentSession = null
    }

    companion object {
        private val LOG = Logger.getInstance(SessionController::class.java)
    }
}