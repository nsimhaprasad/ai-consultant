package tech.beskar.baid.intelijplugin.api

import tech.beskar.baid.intelijplugin.auth.GoogleAuthService
import tech.beskar.baid.intelijplugin.config.BaidConfiguration

object ApiServiceFactory {
    
    fun createApiService(
        authService: GoogleAuthService,
        config: BaidConfiguration
    ): BaidApiService {
        return BaidApiServiceImpl(authService, config)
    }
    

    fun createSessionManager(): SessionManager {
        return SessionManager()
    }
    

    fun createConversationRepository(
        apiService: BaidApiService
    ): ConversationRepository {
        return ConversationRepository(apiService)
    }

    fun createResponseHandler(
        onSessionIdReceived: (String?) -> Unit,
        onErrorReceived: (Exception, Boolean) -> Unit
    ): ResponseHandler {
        return StreamingResponseHandler(onSessionIdReceived, onErrorReceived)
    }
}
