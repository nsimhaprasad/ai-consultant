package tech.beskar.baid.intelijplugin.service

import org.json.JSONObject
import tech.beskar.baid.intelijplugin.model.ChatSession
import tech.beskar.baid.intelijplugin.model.FileContext
import tech.beskar.baid.intelijplugin.model.SessionPreview
import tech.beskar.baid.intelijplugin.model.common.SessionId
import tech.beskar.baid.intelijplugin.model.common.UserId
import java.util.function.Consumer

interface IBaidApiService {
    fun sendMessage(
        userPrompt: String?,
        fileContext: FileContext,
        accessToken: String?,
        sessionId: SessionId?,
        onStreamedBlock: Consumer<JSONObject?>,
        onComplete: Consumer<SessionId?>,
        onError: Consumer<Throwable?>
    )

    fun fetchUserSessions(
        userId: UserId?,
        accessToken: String?,
        onSuccess: Consumer<MutableList<SessionPreview?>?>,
        onError: Consumer<Throwable?>
    )

    fun loadConversationHistory(
        userId: UserId?,
        sessionId: SessionId?,
        accessToken: String?,
        onSuccess: Consumer<ChatSession?>,
        onError: Consumer<Throwable?>
    )

    fun loadMessagePreview(
        userId: UserId?,
        sessionId: SessionId?,
        accessToken: String?,
        onSuccess: Consumer<String?>,
        onError: Consumer<Throwable?>
    )
}
