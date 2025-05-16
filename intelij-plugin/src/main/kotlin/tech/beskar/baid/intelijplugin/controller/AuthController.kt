package tech.beskar.baid.intelijplugin.controller

import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import tech.beskar.baid.intelijplugin.model.UserProfile
import tech.beskar.baid.intelijplugin.service.AuthenticationService
import java.util.concurrent.CompletableFuture
import java.util.function.Consumer

class AuthController private constructor() {
    private val authService: AuthenticationService = AuthenticationService.getInstance()

    var currentUser: UserProfile? = null
        private set

    fun checkAuthenticationStatus(onComplete: Consumer<Boolean?>) {
        authService.isAuthenticated { authenticated: Boolean? ->
            if (authenticated == true && currentUser == null) {
                // If authenticated but user profile not loaded, load it
                loadUserProfile({ profile: UserProfile? ->
                    currentUser = profile
                    onComplete.accept(true)
                }, { error: Throwable? ->
                    LOG.warn("Failed to load user profile", error)
                    onComplete.accept(false)
                })
            } else {
                onComplete.accept(authenticated)
            }
        }
    }

    fun loadUserProfile(onSuccess: Consumer<UserProfile?>, onError: Consumer<Throwable?>) {
        authService.getUserProfile({ profile: UserProfile? ->
            currentUser = profile
            onSuccess.accept(profile)
        }, onError)
    }

    fun signIn(project: Project, onSuccess: Consumer<UserProfile?>) {
        authService.startSignIn(project) { profile: UserProfile? ->
            currentUser = profile
            onSuccess.accept(profile)
        }
    }

    fun signOut(onComplete: Runnable) {
        authService.signOut {
            currentUser = null
            onComplete.run()
        }
    }

    val accessToken: CompletableFuture<String?>
        get() = authService.currentAccessToken

    val userId: CompletableFuture<String?>
        get() {
            if (currentUser != null) {
                return CompletableFuture.completedFuture<String?>(currentUser!!.id)
            }
            return authService.currentUserId
        }

    fun validateAuthentication(onValid: Runnable, onInvalid: Runnable) {
        authService.isAuthenticated { authenticated: Boolean? ->
            if (authenticated == true) {
                // Also check if token is expired
                authService.isTokenExpired { expired: Boolean? ->
                    onValid.run()
                }
            } else {
                onInvalid.run()
            }
        }
    }

    companion object {
        private val LOG = Logger.getInstance(AuthController::class.java)

        @get:Synchronized
        var _instance: AuthController? = null
            get() {
                if (field == null) {
                    field = AuthController()
                }
                return field
            }
        fun getInstance(): AuthController {
            if (_instance == null) {
                _instance = AuthController()
            }
            return _instance!!
        }
    }
}