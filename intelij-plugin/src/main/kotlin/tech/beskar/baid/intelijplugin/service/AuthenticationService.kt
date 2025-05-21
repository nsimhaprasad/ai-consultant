package tech.beskar.baid.intelijplugin.service

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import tech.beskar.baid.intelijplugin.auth.GoogleAuthService
import tech.beskar.baid.intelijplugin.model.UserProfile
import tech.beskar.baid.intelijplugin.model.common.UserId // Added import
import java.util.concurrent.CompletableFuture
import java.util.function.Consumer
import javax.swing.SwingUtilities


class AuthenticationService constructor( // Made constructor public
    private val authService: GoogleAuthService // Injected dependency
) : IAuthenticationService { // Implement interface

    override fun isAuthenticated(onComplete: Consumer<Boolean?>) { // Added override
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val result = authService.isAuthenticated()
                SwingUtilities.invokeLater { onComplete.accept(result) }
            } catch (e: Exception) {
                LOG.error("Error checking authentication status", e)
                SwingUtilities.invokeLater { onComplete.accept(false) }
            }
        }
    }

    override fun getUserProfile(onSuccess: Consumer<UserProfile?>, onError: Consumer<Throwable?>) { // Added override
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val userInfo: GoogleAuthService.UserInfo? = authService.getUserInfo()
                if (userInfo != null) {
                    // UserId should be derived from a stable unique ID from Google, typically 'sub'.
                    // GoogleAuthService.UserInfo currently only has email, name, picture.
                    // Assuming for this step that the email's string value is used as the basis for UserId.
                    // If GoogleAuthService.UserInfo gets an 'id' or 'sub' field later, that should be used for UserId.
                    val userIdFromEmail = userInfo.email?.value?.let { UserId(it) }
                    val profile = UserProfile(
                        userIdFromEmail, // Pass the derived UserId
                        userInfo.name,
                        userInfo.email, // This is of type Email?
                        userInfo.picture
                    )
                    SwingUtilities.invokeLater { onSuccess.accept(profile) }
                } else {
                    SwingUtilities.invokeLater {
                        onError.accept(
                            Exception("User not authenticated")
                        )
                    }
                }
            } catch (e: Exception) {
                LOG.error("Error getting user profile", e)
                SwingUtilities.invokeLater { onError.accept(e) }
            }
        }
    }

    override val currentAccessToken: CompletableFuture<String?> // Added override
        get() {
            val future = CompletableFuture<String?>()

            ApplicationManager.getApplication().executeOnPooledThread {
                try {
                    val token = authService.getCurrentAccessToken()
                    future.complete(token)
                } catch (e: Exception) {
                    LOG.error("Error getting access token", e)
                    future.completeExceptionally(e)
                }
            }

            return future
        }

    override fun signOut(onComplete: Runnable?) { // Added override
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                authService.signOut()
                SwingUtilities.invokeLater(onComplete)
            } catch (e: Exception) {
                LOG.error("Error signing out", e)
                SwingUtilities.invokeLater(onComplete)
            }
        }
    }

    override fun startSignIn(project: Project, onSuccess: Consumer<UserProfile?>, onError: Consumer<Throwable?>) { // Added override
        authService.startAuthFlow(project).thenAccept {
            getUserProfile(onSuccess) { error -> onError.accept(error) }
        }.exceptionally { error ->
            onError.accept(error)
            null
        }
    }

    override fun isTokenExpired(onComplete: Consumer<Boolean?>) { // Added override
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val token = authService.getCurrentAccessToken()
                val isExpired = token == null
                SwingUtilities.invokeLater { onComplete.accept(isExpired) }
            } catch (e: Exception) {
                LOG.error("Error checking token expiration", e)
                SwingUtilities.invokeLater { onComplete.accept(true) }
            }
        }
    }

    override val currentUserId: CompletableFuture<UserId?> // Added override
        get() {
            val future = CompletableFuture<UserId?>() // Changed type

            ApplicationManager.getApplication().executeOnPooledThread {
                try {
                    val userInfo: GoogleAuthService.UserInfo? = authService.getUserInfo()
                    // userInfo.email is now Email?
                    if (userInfo != null && userInfo.email != null && userInfo.email!!.value.isNotBlank()) {
                        future.complete(UserId(userInfo.email!!.value)) // Use .value to get string for UserId
                    } else {
                        future.complete(null)
                    }
                } catch (e: Exception) {
                    LOG.error("Error getting user ID", e)
                    future.completeExceptionally(e)
                }
            }

            return future
        }


    companion object { // Companion object can be removed if getInstance is gone
        private val LOG = Logger.getInstance(AuthenticationService::class.java)
        // Removed getInstance and _instance
    }
}