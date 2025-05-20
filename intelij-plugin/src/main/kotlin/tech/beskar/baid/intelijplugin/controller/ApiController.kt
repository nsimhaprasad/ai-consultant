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

    companion object {
        private val LOG = Logger.getInstance(APIController::class.java)
        // getInstance() and _instance removed
    }
}