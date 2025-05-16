package tech.beskar.baid.intelijplugin.service

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import tech.beskar.baid.intelijplugin.auth.GoogleAuthService
import tech.beskar.baid.intelijplugin.model.UserProfile
import java.util.concurrent.CompletableFuture
import java.util.function.Consumer
import javax.swing.SwingUtilities


class AuthenticationService private constructor() {
    private val authService: GoogleAuthService = GoogleAuthService.getInstance()

    fun isAuthenticated(onComplete: Consumer<Boolean?>) {
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

    fun getUserProfile(onSuccess: Consumer<UserProfile?>, onError: Consumer<Throwable?>) {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val userInfo: GoogleAuthService.UserInfo? = authService.getUserInfo()
                if (userInfo != null) {
                    val profile = UserProfile(
                        userInfo.email,  // Using email as ID
                        userInfo.name,
                        userInfo.email,
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

    val currentAccessToken: CompletableFuture<String?>
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

    fun signOut(onComplete: Runnable?) {
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

    fun startSignIn(project: Project, onSuccess: Consumer<UserProfile?>) {
        authService.startAuthFlow(project).thenAccept {
            getUserProfile(onSuccess) {}
        }
    }

    fun isTokenExpired(onComplete: Consumer<Boolean?>) {
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

    val currentUserId: CompletableFuture<String?>
        get() {
            val future = CompletableFuture<String?>()

            ApplicationManager.getApplication().executeOnPooledThread {
                try {
                    val userInfo: GoogleAuthService.UserInfo? = authService.getUserInfo()
                    if (userInfo != null) {
                        future.complete(userInfo.email)
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


    companion object {
        private val LOG = Logger.getInstance(AuthenticationService::class.java)

        @get:Synchronized
        var _instance: AuthenticationService? = null
            get() {
                if (field == null) {
                    field = AuthenticationService()
                }
                return field
            }

        fun getInstance(): AuthenticationService {
            if (_instance == null) {
                _instance = AuthenticationService()
            }
            return _instance!!
        }
    }
}