package tech.beskar.baid.intelijplugin.service

import com.intellij.openapi.project.Project
import tech.beskar.baid.intelijplugin.model.UserProfile
import tech.beskar.baid.intelijplugin.model.common.UserId
import java.util.concurrent.CompletableFuture
import java.util.function.Consumer

interface IAuthenticationService {
    fun isAuthenticated(onComplete: Consumer<Boolean?>)
    fun getUserProfile(onSuccess: Consumer<UserProfile?>, onError: Consumer<Throwable?>)
    val currentAccessToken: CompletableFuture<String?>
    fun signOut(onComplete: Runnable?)
    fun startSignIn(project: Project, onSuccess: Consumer<UserProfile?>, onError: Consumer<Throwable?>)
    fun isTokenExpired(onComplete: Consumer<Boolean?>)
    val currentUserId: CompletableFuture<UserId?>
}
