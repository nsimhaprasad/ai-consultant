package tech.beskar.baid.intelijplugin.controller

import tech.beskar.baid.intelijplugin.model.ChatSession
import tech.beskar.baid.intelijplugin.model.SessionPreview
import tech.beskar.baid.intelijplugin.model.common.SessionId
import java.util.function.Consumer

interface ISessionController {
    var currentSessionId: SessionId?
    var currentSession: ChatSession? // Changed to var

    fun loadSession(
        sessionId: SessionId?,
        onSuccess: Consumer<ChatSession?>,
        onError: Consumer<Throwable?>
    )

    fun loadSessionPreviews(
        onSuccess: Consumer<MutableList<SessionPreview>?>, // Consider List for immutability
        onError: Consumer<Throwable?>
    )

    fun clearCurrentSession()
}
