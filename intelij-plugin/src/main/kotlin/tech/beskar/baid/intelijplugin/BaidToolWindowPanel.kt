package tech.beskar.baid.intelijplugin

import com.intellij.icons.AllIcons
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.project.Project
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBPanel
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.components.JBTextField
import com.intellij.ui.components.panels.VerticalLayout
import com.intellij.util.io.HttpRequests
import com.intellij.util.ui.JBUI
import org.json.JSONObject
import tech.beskar.baid.intelijplugin.auth.GoogleAuthService
import tech.beskar.baid.intelijplugin.auth.LoginPanel
import tech.beskar.baid.intelijplugin.auth.UserProfilePanel
import tech.beskar.baid.intelijplugin.util.FontUtil
import java.awt.BorderLayout
import java.awt.CardLayout
import java.awt.Color
import java.awt.Dimension
import javax.swing.*

class BaidToolWindowPanel(private val project: Project) : JBPanel<BaidToolWindowPanel>(BorderLayout()) {
    private val chatPanel = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(8)))
    private val chatScroll = JBScrollPane(chatPanel)
    private val inputField = JBTextField(30)
    private val consultButton = JButton()

    // Add auth service
    private val authService = GoogleAuthService.getInstance()
    private val backendUrl = "http://localhost:8080" // Use backend root, not /api/auth/google-login

    // Add content panel to switch between login and main UI
    private val contentPanel = JBPanel<JBPanel<*>>(CardLayout())
    private val loginPanel: LoginPanel
    private val mainPanel = JBPanel<JBPanel<*>>(BorderLayout())

    init {
        // Set up the login panel
        loginPanel = LoginPanel(project) { userInfo ->
            // User successfully logged in, switch to main panel
            showMainPanel()
            appendMessage("Welcome, ${userInfo.name}! How can I help you today?", isUser = false)
        }

        // Set up the chat panel
        chatPanel.background = JBColor.background()
        chatPanel.border = JBUI.Borders.empty(8)

        // Set up the scroll pane
        chatScroll.verticalScrollBar.unitIncrement = JBUI.scale(16)
        chatScroll.border = JBUI.Borders.empty()

        // Create header panel with Baid branding and user profile
        val headerPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            background = JBColor.background()
            border = JBUI.Borders.empty(JBUI.scale(16), JBUI.scale(16), JBUI.scale(8), JBUI.scale(16))

            // Add Baid title
            val titleLabel = JLabel("Baid").apply {
                font = FontUtil.getTitleFont()
                foreground = JBColor.foreground()
            }

            // Add subtitle
            val subtitleLabel = JLabel("Delegate your tasks, focus on the results").apply {
                font = FontUtil.getSubTitleFont()
                foreground = JBColor.foreground().darker()
            }

            val titleContainer = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(4))).apply {
                isOpaque = false
                add(titleLabel)
                add(subtitleLabel)
            }

            // User profile container - will be updated when user logs in
            val userProfileContainer = JBPanel<JBPanel<*>>(BorderLayout()).apply {
                isOpaque = false
                border = JBUI.Borders.emptyLeft(JBUI.scale(16))
            }

            add(titleContainer, BorderLayout.WEST)
            add(userProfileContainer, BorderLayout.EAST)
        }

        // Set up the input field
        inputField.border = JBUI.Borders.empty(JBUI.scale(12))
        inputField.emptyText.text = "Type your task here, press Enter to send prompt"
        inputField.font = FontUtil.getBodyFont()

        // Add key listener to handle Enter key
        inputField.addKeyListener(object : java.awt.event.KeyAdapter() {
            override fun keyPressed(e: java.awt.event.KeyEvent) {
                if (e.keyCode == java.awt.event.KeyEvent.VK_ENTER) {
                    val userMessage = inputField.text.trim()
                    if (userMessage.isNotEmpty()) {
                        appendMessage(userMessage, isUser = true)
                        inputField.text = ""
                        consultWithAPI(userMessage)
                    }
                    e.consume()
                }
            }
        })

        // Set up the consult button
        consultButton.text = "Send"
        consultButton.addActionListener {
            val userMessage = inputField.text.trim()
            if (userMessage.isNotEmpty()) {
                appendMessage(userMessage, isUser = true)
                inputField.text = ""
                consultWithAPI(userMessage)
            }
        }

        // Create input panel
        val inputPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            background = JBColor.background()
            border = JBUI.Borders.empty(0, JBUI.scale(16), JBUI.scale(16), JBUI.scale(16))
            add(inputField, BorderLayout.CENTER)
            add(consultButton, BorderLayout.EAST)
        }

        // Add components to the main panel
        mainPanel.add(headerPanel, BorderLayout.NORTH)
        mainPanel.add(chatScroll, BorderLayout.CENTER)
        mainPanel.add(inputPanel, BorderLayout.SOUTH)

        // Set up content panel with both login and main panels
        contentPanel.add(loginPanel, "login")
        contentPanel.add(mainPanel, "main")

        // Add content panel to the main panel
        add(contentPanel, BorderLayout.CENTER)

        // Check if user is already authenticated in background
        checkAuthenticationStatus()
    }

    // Move authentication check to background
    private fun checkAuthenticationStatus() {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val isAuthenticated = authService.isAuthenticated()
                val userInfo = if (isAuthenticated) authService.getUserInfo() else null

                SwingUtilities.invokeLater {
                    if (isAuthenticated) {
                        showMainPanel()
                        // Add welcome message
                        if (userInfo != null) {
                            appendMessage("Welcome back, ${userInfo.name}! How can I help you today?", isUser = false)
                        } else {
                            appendMessage("Hello! I'm Baid, your AI assistant. How can I help you today?", isUser = false)
                        }
                    } else {
                        // Show login panel
                        showLoginPanel()
                    }
                }
            } catch (e: Exception) {
                SwingUtilities.invokeLater {
                    // Show login panel on error
                    showLoginPanel()
                }
            }
        }
    }

    private fun showLoginPanel() {
        val layout = contentPanel.layout as CardLayout
        layout.show(contentPanel, "login")
    }

    private fun showMainPanel() {
        val layout = contentPanel.layout as CardLayout
        layout.show(contentPanel, "main")

        // Update the header with user info
        updateUserProfileInHeader()
    }

    private fun updateUserProfileInHeader() {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val userInfo = authService.getUserInfo()
                SwingUtilities.invokeLater {
                    val headerPanel = mainPanel.getComponent(0) as JPanel
                    val userProfileContainer = headerPanel.getComponent(1) as JPanel

                    userProfileContainer.removeAll()

                    if (userInfo != null) {
                        val userProfilePanel = UserProfilePanel(userInfo) {
                            // Sign out callback
                            showLoginPanel()
                        }
                        userProfileContainer.add(userProfilePanel, BorderLayout.CENTER)
                    }

                    userProfileContainer.revalidate()
                    userProfileContainer.repaint()
                }
            } catch (e: Exception) {
                // Handle error if needed
            }
        }
    }

    fun appendMessage(message: String, isUser: Boolean) {
        // Create message panel
        val messagePanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            background = if (isUser) JBColor(Color(240, 240, 240), Color(60, 63, 65)) else JBColor.background()
            border = JBUI.Borders.empty(JBUI.scale(12), JBUI.scale(16))

            // Create avatar label
            val avatarLabel = JLabel().apply {
                icon = if (isUser) AllIcons.General.User else AllIcons.General.BalloonInformation
                border = JBUI.Borders.emptyRight(JBUI.scale(12))
                verticalAlignment = JLabel.TOP
            }

            // Create message text with wrapping
            val messageText = JTextArea().apply {
                text = message
                font = FontUtil.getBodyFont()
                lineWrap = true
                wrapStyleWord = true
                isEditable = false
                isOpaque = false
                background = if (isUser) JBColor(Color(240, 240, 240), Color(60, 63, 65)) else JBColor.background()
                border = JBUI.Borders.empty()
                minimumSize = Dimension(0, preferredSize.height)
                maximumSize = Dimension(400, Int.MAX_VALUE)
            }

            // Add components to message panel
            add(avatarLabel, BorderLayout.WEST)
            add(messageText, BorderLayout.CENTER)
        }

        // Add message panel to chat panel
        SwingUtilities.invokeLater {
            chatPanel.add(messagePanel)
            chatPanel.revalidate()
            chatPanel.repaint()

            // Scroll to bottom
            SwingUtilities.invokeLater {
                val vertical = chatScroll.verticalScrollBar
                vertical.value = vertical.maximum
            }
        }
    }

    fun consultWithAPI(userPrompt: String) {
        // Check if user is authenticated
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val isAuthenticated = authService.isAuthenticated()
                SwingUtilities.invokeLater {
                    if (!isAuthenticated) {
                        appendMessage("Please sign in to use Baid", isUser = false)
                        showLoginPanel()
                        return@invokeLater
                    }

                    // Get the backend token
                    ApplicationManager.getApplication().executeOnPooledThread {
                        try {
                            val accessToken = authService.getCurrentAccessToken()
                            SwingUtilities.invokeLater {
                                if (accessToken == null) {
                                    appendMessage("Your session has expired. Please sign in again.", isUser = false)
                                    showLoginPanel()
                                    return@invokeLater
                                }

                                // Continue with API request
                                performAPIRequest(userPrompt, accessToken)
                            }
                        } catch (e: Exception) {
                            SwingUtilities.invokeLater {
                                appendMessage("Authentication check failed. Please sign in again.", isUser = false)
                                showLoginPanel()
                            }
                        }
                    }
                }
            } catch (e: Exception) {
                SwingUtilities.invokeLater {
                    appendMessage("Authentication check failed. Please sign in again.", isUser = false)
                    showLoginPanel()
                }
            }
        }
    }

    private fun performAPIRequest(userPrompt: String, accessToken: String) {
        inputField.isEnabled = false
        consultButton.isEnabled = false
        val editor = com.intellij.openapi.fileEditor.FileEditorManager.getInstance(project).selectedTextEditor
        val document = editor?.document
        val fileText = document?.text ?: "No file open."

        // Show thinking message
        appendMessage("Thinking...", isUser = false)
        val apiUrl = "$backendUrl/consult"
        val payload = JSONObject(mapOf(
            "prompt" to userPrompt,
            "file_content" to fileText
        ))

        // Make API request in background
        com.intellij.openapi.progress.ProgressManager.getInstance().run(
            object : com.intellij.openapi.progress.Task.Backgroundable(
                project,
                "Consulting AI",
                false
            ) {
                override fun run(indicator: com.intellij.openapi.progress.ProgressIndicator) {
                    try {
                        // Make API request with auth header
                        val response = HttpRequests
                            .post(apiUrl, "application/json")
                            .connectTimeout(30000)
                            .readTimeout(30000)
                            .tuner { connection ->
                                connection.connectTimeout = 30000
                                connection.readTimeout = 30000
                                connection.setRequestProperty("Authorization", "Bearer $accessToken")
                            }
                            .connect { request ->
                                request.write(payload.toString())
                                request.getReader(null).readText()
                            }
                        SwingUtilities.invokeLater {
                            // Remove thinking message
                            removeLastMessageIfThinking()
                            appendMessage(JSONObject(response).optString("response", response), isUser = false)
                            inputField.isEnabled = true
                            consultButton.isEnabled = true
                            inputField.requestFocus()
                        }
                    } catch (e: Exception) {
                        SwingUtilities.invokeLater {
                            removeLastMessageIfThinking()
                            if (e.message?.contains("401") == true || e.message?.contains("403") == true) {
                                // Auth error - token might be invalid
                                appendMessage("Your session has expired. Please sign in again.", isUser = false)
                                authService.signOut()
                                showLoginPanel()
                            } else {
                                // Other error
                                appendMessage("Sorry, I encountered an error: ${e.message}", isUser = false)
                            }
                            inputField.isEnabled = true
                            consultButton.isEnabled = true
                            inputField.requestFocus()
                        }
                    }
                }
            }
        )
    }

    private fun removeLastMessageIfThinking() {
        if (chatPanel.componentCount > 0) {
            val lastMessage = chatPanel.getComponent(chatPanel.componentCount - 1)
            if (lastMessage is JBPanel<*> && lastMessage.border == JBUI.Borders.empty(JBUI.scale(12), JBUI.scale(16))) {
                val messageText = lastMessage.getComponent(1) as JTextArea
                if (messageText.text == "Thinking...") {
                    chatPanel.remove(lastMessage)
                    chatPanel.revalidate()
                    chatPanel.repaint()
                }
            }
        }
    }
}