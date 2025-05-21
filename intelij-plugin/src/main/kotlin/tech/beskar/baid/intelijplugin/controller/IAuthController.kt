package tech.beskar.baid.intelijplugin.controller

import com.intellij.openapi.project.Project
import tech.beskar.baid.intelijplugin.model.UserProfile
import tech.beskar.baid.intelijplugin.model.common.UserId
import java.util.concurrent.CompletableFuture
import java.util.function.Consumer

interface IAuthController {
    val currentUser: UserProfile?
    val accessToken: CompletableFuture<String?>
    val userId: CompletableFuture<UserId?>

    fun checkAuthenticationStatus(onComplete: Consumer<Boolean?>)
    fun loadUserProfile(onSuccess: Consumer<UserProfile?>, onError: Consumer<Throwable?>)
    fun signIn(project: Project, onSuccess: Consumer<UserProfile?>, onError: Consumer<Throwable?>)
    fun signOut(onComplete: Runnable)
    fun validateAuthentication(onValid: Runnable, onInvalid: Runnable)
}
