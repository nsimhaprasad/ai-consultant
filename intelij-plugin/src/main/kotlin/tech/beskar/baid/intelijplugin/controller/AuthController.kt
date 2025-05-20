package tech.beskar.baid.intelijplugin.controller

import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import tech.beskar.baid.intelijplugin.model.UserProfile
import tech.beskar.baid.intelijplugin.service.IAuthenticationService // Changed to interface
import java.util.concurrent.CompletableFuture
import java.util.function.Consumer

class AuthController constructor( // Made constructor public
    private val authService: IAuthenticationService // Changed to interface and added to constructor
    // Project parameter removed for now as it's only used to pass to authService.startSignIn,
    // which will get it from its direct caller.
) : IAuthController { // Implement interface

    override var currentUser: UserProfile? = null // Added override
        private set

    override fun checkAuthenticationStatus(onComplete: Consumer<Boolean?>) { // Added override
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

    override fun loadUserProfile(onSuccess: Consumer<UserProfile?>, onError: Consumer<Throwable?>) { // Added override
        authService.getUserProfile({ profile: UserProfile? ->
            currentUser = profile
            onSuccess.accept(profile)
        }, onError)
    }

    override fun signIn(project: Project, onSuccess: Consumer<UserProfile?>, onError: Consumer<Throwable?>) { // Added override
        authService.startSignIn(project, { profile: UserProfile? ->
            currentUser = profile
            onSuccess.accept(profile)
        }, { it: Throwable? ->
            onError.accept(it)
        })
    }

    override fun signOut(onComplete: Runnable) { // Added override
        authService.signOut {
            currentUser = null
            onComplete.run()
        }
    }

    override val accessToken: CompletableFuture<String?> // Added override
        get() = authService.currentAccessToken

    // Changed return type to CompletableFuture<UserId?>
    override val userId: CompletableFuture<tech.beskar.baid.intelijplugin.model.common.UserId?> // Added override
        get() {
            if (currentUser != null && currentUser!!.id != null) {
                // currentUser.id is already UserId?
                return CompletableFuture.completedFuture(currentUser!!.id)
            }
            // authService.currentUserId returns CompletableFuture<UserId?>
            return authService.currentUserId
        }

    override fun validateAuthentication(onValid: Runnable, onInvalid: Runnable) { // Added override
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

    companion object { // Companion object can be removed if getInstance is gone
        private val LOG = Logger.getInstance(AuthController::class.java)
        // Removed getInstance and _instance
    }
}