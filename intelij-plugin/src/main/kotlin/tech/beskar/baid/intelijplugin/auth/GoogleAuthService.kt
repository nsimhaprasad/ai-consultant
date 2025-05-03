package tech.beskar.baid.intelijplugin.auth

import com.intellij.credentialStore.CredentialAttributes
import com.intellij.credentialStore.Credentials
import com.intellij.credentialStore.generateServiceName
import com.intellij.ide.BrowserUtil
import com.intellij.ide.passwordSafe.PasswordSafe
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.application.ModalityState
import com.intellij.openapi.components.service
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBPanel
import com.intellij.util.io.HttpRequests
import com.intellij.util.ui.JBUI
import org.json.JSONObject
import tech.beskar.baid.intelijplugin.config.BaidConfiguration
import tech.beskar.baid.intelijplugin.util.FontUtil
import java.awt.BorderLayout
import java.awt.Dimension
import java.awt.FlowLayout
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import java.time.Instant
import java.util.*
import java.util.concurrent.CompletableFuture
import javax.swing.JButton
import javax.swing.SwingUtilities

class GoogleAuthService {
    companion object {
        private val LOG = Logger.getInstance(GoogleAuthService::class.java)

        // Instance for service access
        fun getInstance(): GoogleAuthService = service()
    }

    private val config = BaidConfiguration.getInstance()
    private var userInfo: UserInfo? = null

    data class UserInfo(
        val email: String,
        val name: String,
        val picture: String?
    )

    data class TokenInfo(
        val accessToken: String,
        val refreshToken: String?,
        val expiresIn: Long
    )

    data class BackendTokenInfo(
        val backendToken: String,
        val expiresIn: Long,
        val userInfo: UserInfo
    )

    // Check if user is authenticated
    fun isAuthenticated(): Boolean {
        val backendToken = getBackendToken()
        val expiry = getTokenExpiry()
        return backendToken != null && expiry != null &&
                Instant.now().epochSecond < expiry
    }

    // Get cached user info or fetch from API
    fun getUserInfo(): UserInfo? {
        if (userInfo != null) return userInfo
        // Optionally: Fetch from backend if needed
        return null
    }

    // Start the OAuth flow and send code to backend for token exchange
    fun startAuthFlow(project: Project): CompletableFuture<UserInfo> {
        val resultFuture = CompletableFuture<UserInfo>()
        val state = UUID.randomUUID().toString()
        val authUrl = buildAuthUrl(state)
        ApplicationManager.getApplication().invokeLater({
            BrowserUtil.browse(authUrl)
        }, ModalityState.any())
        // Poll for session
        Thread {
            val maxWait = 60_000L // 60 seconds
            val pollInterval = 2000L
            val startTime = System.currentTimeMillis()
            while (System.currentTimeMillis() - startTime < maxWait) {
                try {
                    val response = HttpRequests.request("${config.backendUrl}/api/auth/session?state=$state")
                        .accept("application/json")
                        .connectTimeout(5000)
                        .readTimeout(5000)
                        .readString()

                    val json = JSONObject(response)
                    if (json.has("error") && !json.isNull("error")) {
                        resultFuture.completeExceptionally(RuntimeException(json.getString("error")))
                        return@Thread
                    }
                    if (json.has("access_token")) {
                        val user = UserInfo(
                            email = json.getString("email"),
                            name = json.getString("name"),
                            picture = if (json.has("picture")) json.getString("picture") else null
                        )
                        saveBackendToken(
                            BackendTokenInfo(
                                backendToken = json.getString("access_token"),
                                expiresIn = json.getLong("expires_in"),
                                userInfo = user
                            )
                        )
                        userInfo = user
                        resultFuture.complete(user)
                        return@Thread
                    }
                } catch (e: Exception) {
                    // Ignore and retry
                }
                Thread.sleep(pollInterval)
            }
            resultFuture.completeExceptionally(RuntimeException("Login timed out. Please try again."))
        }.start()
        return resultFuture
    }

    // Build the authorization URL
    private fun buildAuthUrl(state: String): String {
        val params = mapOf(
            "client_id" to config.clientId,
            "redirect_uri" to config.redirectUri,
            "response_type" to "code",
            "scope" to config.scope,
            "state" to state,
            "access_type" to config.accessType,
            "prompt" to config.prompt
        )
        val queryString = params.entries.joinToString("&") { (key, value) ->
            "$key=${URLEncoder.encode(value, StandardCharsets.UTF_8)}"
        }
        return "${config.authEndpoint}?$queryString"
    }

    // Save backend token to secure storage
    private fun saveBackendToken(tokenInfo: BackendTokenInfo) {
        val backendTokenAttributes = CredentialAttributes(
            generateServiceName("Baid", config.backendTokenKey)
        )
        val backendTokenCredential = Credentials("", tokenInfo.backendToken)
        PasswordSafe.instance.set(backendTokenAttributes, backendTokenCredential)
        val expiresAt = Instant.now().epochSecond + tokenInfo.expiresIn
        val expiryAttributes = CredentialAttributes(
            generateServiceName("Baid", config.tokenExpiryKey)
        )
        val expiryCredential = Credentials("", expiresAt.toString())
        PasswordSafe.instance.set(expiryAttributes, expiryCredential)
    }

    // Get backend token
    fun getCurrentAccessToken(): String? {
        if (!isAuthenticated()) return null
        return getBackendToken()
    }

    private fun getBackendToken(): String? {
        val attributes = CredentialAttributes(
            generateServiceName("Baid", config.backendTokenKey)
        )
        return PasswordSafe.instance.getPassword(attributes)
    }

    private fun getTokenExpiry(): Long? {
        val attributes = CredentialAttributes(
            generateServiceName("Baid", config.tokenExpiryKey)
        )
        return PasswordSafe.instance.getPassword(attributes)?.toLongOrNull()
    }

    // Sign out the user
    fun signOut() {
        clearTokens()
        userInfo = null
    }

    // Clear all saved tokens
    private fun clearTokens() {
        val backendTokenAttributes = CredentialAttributes(
            generateServiceName("Baid", config.backendTokenKey)
        )
        PasswordSafe.instance.set(backendTokenAttributes, null)
        val expiryAttributes = CredentialAttributes(
            generateServiceName("Baid", config.tokenExpiryKey)
        )
        PasswordSafe.instance.set(expiryAttributes, null)
    }
}

// UI Components for auth
class LoginPanel(private val project: Project, private val onLoginComplete: (GoogleAuthService.UserInfo) -> Unit) :
    JBPanel<LoginPanel>(BorderLayout()) {

    init {
        background = JBColor.background()
        border = JBUI.Borders.empty(JBUI.scale(20))

        val centerPanel = JBPanel<JBPanel<*>>().apply {
            layout = BorderLayout()
            background = JBColor.background()

            // Title
            val titleLabel = JBLabel("Sign in to Baid").apply {
                font = FontUtil.getTitleFont()
                horizontalAlignment = JBLabel.CENTER
            }

            // Subtitle
            val subtitleLabel = JBLabel("Connect with your Google account to get started").apply {
                font = FontUtil.getSubTitleFont()
                horizontalAlignment = JBLabel.CENTER
            }

            // Login button
            val loginButton = JButton("Sign in with Google").apply {
                font = FontUtil.getBodyFont()
                preferredSize = Dimension(JBUI.scale(200), JBUI.scale(40))
                addActionListener {
                    isEnabled = false
                    text = "Connecting..."

                    val authService = GoogleAuthService.getInstance()
                    authService.startAuthFlow(project)
                        .thenAccept { userInfo ->
                            SwingUtilities.invokeLater {
                                onLoginComplete(userInfo)
                            }
                        }
                        .exceptionally { e ->
                            SwingUtilities.invokeLater {
                                isEnabled = true
                                text = "Sign in with Google"
                                // Show error message
                                val errorLabel = JBLabel("Authentication failed: ${e.message}").apply {
                                    foreground = JBColor.RED
                                }
                                this@LoginPanel.add(errorLabel, BorderLayout.SOUTH)
                                this@LoginPanel.revalidate()
                                this@LoginPanel.repaint()
                            }
                            null
                        }
                }
            }

            val titlePanel = JBPanel<JBPanel<*>>().apply {
                layout = BorderLayout(0, JBUI.scale(8))
                isOpaque = false
                add(titleLabel, BorderLayout.NORTH)
                add(subtitleLabel, BorderLayout.CENTER)
            }

            val buttonPanel = JBPanel<JBPanel<*>>(FlowLayout(FlowLayout.CENTER)).apply {
                isOpaque = false
                add(loginButton)
            }

            add(titlePanel, BorderLayout.NORTH)
            add(buttonPanel, BorderLayout.CENTER)
        }

        add(centerPanel, BorderLayout.CENTER)
    }
}

class UserProfilePanel(
    private val userInfo: GoogleAuthService.UserInfo,
    private val onSignOut: () -> Unit
) : JBPanel<UserProfilePanel>(BorderLayout()) {

    init {
        background = JBColor.background()
        border = JBUI.Borders.empty(JBUI.scale(16))

        // User info panel
        val userInfoPanel = JBPanel<JBPanel<*>>().apply {
            layout = BorderLayout(0, JBUI.scale(8))
            isOpaque = false

            // User name
            val nameLabel = JBLabel(userInfo.name).apply {
                font = FontUtil.getLabelFont(isBold = true, size = 14f)
            }

            // User email
            val emailLabel = JBLabel(userInfo.email).apply {
                font = FontUtil.getBodyFont()
            }

            add(nameLabel, BorderLayout.NORTH)
            add(emailLabel, BorderLayout.CENTER)
        }

        // Sign out button
        val signOutButton = JButton("Sign Out").apply {
            font = FontUtil.getBodyFont()
            addActionListener {
                GoogleAuthService.getInstance().signOut()
                onSignOut()
            }
        }

        val buttonPanel = JBPanel<JBPanel<*>>(FlowLayout(FlowLayout.LEFT)).apply {
            isOpaque = false
            add(signOutButton)
        }

        add(userInfoPanel, BorderLayout.NORTH)
        add(buttonPanel, BorderLayout.CENTER)
    }
}