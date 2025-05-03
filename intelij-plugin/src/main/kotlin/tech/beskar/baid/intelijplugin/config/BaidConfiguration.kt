package tech.beskar.baid.intelijplugin.config

import com.intellij.openapi.diagnostic.Logger
import java.util.*

class BaidConfiguration {
    companion object {
        private val LOG = Logger.getInstance(BaidConfiguration::class.java)
        private const val DEFAULT_PROPERTIES_FILE = "/baid-config.properties"

        @Volatile
        private var instance: BaidConfiguration? = null

        fun getInstance(): BaidConfiguration {
            return instance ?: synchronized(this) {
                instance ?: BaidConfiguration().also { instance = it }
            }
        }
    }

    private val properties = Properties()

    // OAuth Configuration
    val clientId: String
    val redirectUri: String
    val authEndpoint: String
    val scope: String
    val accessType: String
    val prompt: String

    // Backend Configuration
    val backendUrl: String
    val apiEndpoint: String

    // Credential Keys
    val backendTokenKey: String
    val tokenExpiryKey: String

    init {
        // Load properties from resources
        val resourceStream = javaClass.getResourceAsStream(DEFAULT_PROPERTIES_FILE)
        resourceStream?.use { stream ->
            properties.load(stream)
        }

        // Override with environment variables if present
        clientId = getConfigValue("BAID_CLIENT_ID", "google.client.id")
        redirectUri = getConfigValue("BAID_REDIRECT_URI", "google.redirect.uri")
        authEndpoint = getConfigValue("BAID_AUTH_ENDPOINT", "google.auth.endpoint")
        scope = getConfigValue("BAID_SCOPE", "google.scope")
        accessType = getConfigValue("BAID_ACCESS_TYPE", "google.access.type")
        prompt = getConfigValue("BAID_PROMPT", "google.prompt")

        backendUrl = getConfigValue("BAID_BACKEND_URL", "backend.url")
        apiEndpoint = getConfigValue("BAID_API_ENDPOINT", "backend.api.endpoint")

        backendTokenKey = getConfigValue("BAID_BACKEND_TOKEN_KEY", "credential.backend.token.key")
        tokenExpiryKey = getConfigValue("BAID_TOKEN_EXPIRY_KEY", "credential.token.expiry.key")

        LOG.info("BaidConfiguration initialized with backend URL: $backendUrl")
    }

    private fun getConfigValue(envKey: String, propertyKey: String): String {
        return System.getenv(envKey)
            ?: properties.getProperty(propertyKey)
            ?: throw IllegalStateException("Configuration missing for $envKey/$propertyKey")
    }

    fun getAccessToken(): String? {
        return System.getenv("BAID_ACCESS_TOKEN")
    }
}