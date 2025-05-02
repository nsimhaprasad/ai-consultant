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
import tech.beskar.baid.intelijplugin.util.FontUtil
import java.awt.*
import javax.swing.*

class BaidToolWindowPanel(private val project: Project) : JBPanel<BaidToolWindowPanel>(BorderLayout()) {
    private val chatPanel = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(8)))
    private val chatScroll = JBScrollPane(chatPanel)
    private val inputField = JBTextField(30)
    private val consultButton = JButton()

    // Add auth service
    private val authService = GoogleAuthService.getInstance()
    private val backendUrl = "http://localhost:8080"

    // Add content panel to switch between login and main UI
    private val contentPanel = JBPanel<JBPanel<*>>(CardLayout())
    private var loginPanel: LoginPanel
    private val mainPanel = JBPanel<JBPanel<*>>(BorderLayout())

    // User profile button reference
    private lateinit var userProfileButton: JButton

    // --- SESSION MANAGEMENT ---
    private var currentSessionId: String? = null
    private lateinit var newSessionButton: JButton

    init {
        // Set up the login panel
        loginPanel = LoginPanel(project) { userInfo ->
            // User successfully logged in, switch to main panel
            showMainPanel()
            updateUserProfileButton()
            appendMessage("Welcome, ${userInfo.name}! How can I help you today?", isUser = false)
        }

        contentPanel.add(loginPanel, "login")
        contentPanel.add(mainPanel, "main")
        add(contentPanel, BorderLayout.CENTER)
        checkAuthenticationStatus()

        // Set up the chat panel
        chatPanel.background = JBColor.background()
        chatPanel.border = JBUI.Borders.empty(8)

        // Set up the scroll pane
        chatScroll.verticalScrollBar.unitIncrement = JBUI.scale(16)
        chatScroll.border = JBUI.Borders.empty()

        // Create header panel with only Baid branding
        val headerPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            background = JBColor.background()
            border = JBUI.Borders.empty(JBUI.scale(16), JBUI.scale(16), JBUI.scale(8), JBUI.scale(16))

            // Add Baid title
            val titleLabel = JLabel("Baid").apply {
                font = FontUtil.getTitleFont()
                foreground = JBColor.foreground()
            }

            // Add subtitle
            val subtitleLabel = JLabel("Transform ideas into outcomes, instantly").apply {
                font = FontUtil.getSubTitleFont()
                foreground = JBColor.foreground().darker()
            }

            val titleContainer = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(4))).apply {
                isOpaque = false
                add(titleLabel)
                add(subtitleLabel)
            }

            // --- Add new session (+) button to header ---
            newSessionButton = JButton(AllIcons.General.Add).apply {
                toolTipText = "Start new session"
                isContentAreaFilled = false
                isBorderPainted = false
                preferredSize = Dimension(JBUI.scale(32), JBUI.scale(32))
                addActionListener {
                    currentSessionId = null
                    clearChat()
                    appendMessage("Started a new session.", isUser = false)
                }
            }
            val rightPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
                isOpaque = false
                add(newSessionButton, BorderLayout.EAST)
            }

            add(titleContainer, BorderLayout.WEST)
            add(rightPanel, BorderLayout.EAST)
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

        // Create input panel with user profile at bottom
        val inputAreaPanel = JBPanel<JBPanel<*>>(null).apply {
            background = JBColor.background()
            border = JBUI.Borders.empty(0, JBUI.scale(16), JBUI.scale(8), JBUI.scale(16))

            // Set preferred height for the whole panel
            preferredSize = Dimension(0, JBUI.scale(110))

            // Create components with fixed bounds
            val inputContainer = JBPanel<JBPanel<*>>(BorderLayout()).apply {
                bounds = Rectangle(0, 0, Int.MAX_VALUE, JBUI.scale(42))
                add(inputField, BorderLayout.CENTER)
                add(consultButton, BorderLayout.EAST)
            }

            // Create user profile button with fixed position
            userProfileButton = JButton().apply {
                bounds = Rectangle(0, JBUI.scale(54), JBUI.scale(200), JBUI.scale(36))
                horizontalAlignment = SwingConstants.LEFT
                isContentAreaFilled = false
                isBorderPainted = false

                addActionListener {
                    // Only show popup if user is authenticated
                    ApplicationManager.getApplication().executeOnPooledThread {
                        if (authService.isAuthenticated()) {
                            SwingUtilities.invokeLater {
                                showUserProfileMenu(this)
                            }
                        } else {
                            SwingUtilities.invokeLater {
                                showLoginPanel()
                            }
                        }
                    }
                }
            }

            // Add a component listener to adjust bounds when panel is resized
            addComponentListener(object : java.awt.event.ComponentAdapter() {
                override fun componentResized(e: java.awt.event.ComponentEvent) {
                    val width = width
                    inputContainer.bounds = Rectangle(0, 0, width, JBUI.scale(42))
                    userProfileButton.bounds = Rectangle(0, JBUI.scale(54), JBUI.scale(200), JBUI.scale(36))
                }
            })

            add(inputContainer)
            add(userProfileButton)
        }

        // Add components to the main panel
        mainPanel.add(headerPanel, BorderLayout.NORTH)
        mainPanel.add(chatScroll, BorderLayout.CENTER)
        mainPanel.add(inputAreaPanel, BorderLayout.SOUTH)

        // Set up content panel with both login and main panels
        contentPanel.add(loginPanel, "login")
        contentPanel.add(mainPanel, "main")

        // Add content panel to the main panel
        add(contentPanel, BorderLayout.CENTER)

        // Check if user is already authenticated in background
        checkAuthenticationStatus()
    }

    private fun updateUserProfileButton() {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val userInfo = authService.getUserInfo()
                val isAuthenticated = authService.isAuthenticated()

                SwingUtilities.invokeLater {
                    if (isAuthenticated && userInfo != null) {
                        // Create a panel with user avatar and name
                        val buttonPanel = JPanel(BorderLayout(4, 0)).apply {
                            isOpaque = false

                            // Create avatar label
                            val avatarLabel = JLabel(userInfo.name.firstOrNull()?.toString() ?: "U").apply {
                                font = Font(Font.SANS_SERIF, Font.BOLD, 14)
                                foreground = Color.WHITE
                                background = JBColor(Color(70, 130, 180), Color(100, 149, 237))
                                isOpaque = true
                                horizontalAlignment = SwingConstants.CENTER
                                preferredSize = Dimension(JBUI.scale(24), JBUI.scale(24))

                                // Make it circular
                                val circleSize = JBUI.scale(24)
                                object : JLabel() {
                                    override fun paintComponent(g: Graphics) {
                                        g.color = background
                                        g.fillOval(0, 0, circleSize, circleSize)
                                        super.paintComponent(g)
                                    }
                                }
                            }

                            add(avatarLabel, BorderLayout.WEST)

                            // Create name label
                            val nameLabel = JLabel(userInfo.name).apply {
                                font = Font(Font.SANS_SERIF, Font.PLAIN, 14)
                                foreground = JBColor.foreground()
                            }
                            add(nameLabel, BorderLayout.CENTER)
                        }

                        userProfileButton.removeAll()
                        userProfileButton.add(buttonPanel)
                    } else {
                        // Not logged in
                        userProfileButton.removeAll()
                        userProfileButton.text = "Sign In"
                        userProfileButton.icon = AllIcons.General.User
                    }
                    userProfileButton.revalidate()
                    userProfileButton.repaint()
                }
            } catch (e: Exception) {
                e.printStackTrace()
                SwingUtilities.invokeLater {
                    userProfileButton.removeAll()
                    userProfileButton.text = "Sign In"
                    userProfileButton.icon = AllIcons.General.User
                    userProfileButton.revalidate()
                    userProfileButton.repaint()
                }
            }
        }
    }

    private fun showUserProfileMenu(button: JComponent) {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val userInfo = authService.getUserInfo()

                SwingUtilities.invokeLater {
                    val popup = JPopupMenu()

                    if (userInfo != null) {
                        // Add user info
                        val nameItem = JMenuItem(userInfo.name).apply {
                            isEnabled = false
                            font = Font(Font.SANS_SERIF, Font.BOLD, 14)
                        }
                        popup.add(nameItem)

                        val emailItem = JMenuItem(userInfo.email).apply {
                            isEnabled = false
                            font = Font(Font.SANS_SERIF, Font.PLAIN, 12)
                            foreground = JBColor.GRAY
                        }
                        popup.add(emailItem)

                        popup.addSeparator()

                        // Add sign out option
                        val signOutItem = JMenuItem("Sign Out", AllIcons.Actions.Exit).apply {
                            addActionListener {
                                ApplicationManager.getApplication().executeOnPooledThread {
                                    authService.signOut()
                                    SwingUtilities.invokeLater {
                                        showLoginPanel()
                                        updateUserProfileButton()
                                    }
                                }
                            }
                        }
                        popup.add(signOutItem)
                    } else {
                        val notLoggedInItem = JMenuItem("Not logged in").apply {
                            isEnabled = false
                        }
                        popup.add(notLoggedInItem)

                        popup.addSeparator()

                        val signInItem = JMenuItem("Sign In").apply {
                            addActionListener {
                                showLoginPanel()
                            }
                        }
                        popup.add(signInItem)
                    }

                    // Show the popup below the button
                    popup.show(button, 0, button.height)
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
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
                        updateUserProfileButton()
                        // Add welcome message
                        if (userInfo != null) {
                            appendMessage("Welcome back, ${userInfo.name}! How can I help you today?", isUser = false)
                        } else {
                            appendMessage(
                                "Hello! I'm Baid, your AI assistant. How can I help you today?",
                                isUser = false
                            )
                        }
                    } else {
                        // Show login panel
                        showLoginPanel()
                        updateUserProfileButton()
                    }
                }
            } catch (e: Exception) {
                SwingUtilities.invokeLater {
                    // Show login panel on error
                    showLoginPanel()
                    updateUserProfileButton()
                }
            }
        }
    }

    private fun showLoginPanel() {
        val layout = contentPanel.layout as CardLayout

        // Remove the old login panel
        contentPanel.remove(loginPanel)

        // Create a new login panel
        loginPanel = LoginPanel(project) { userInfo ->
            // User successfully logged in, switch to main panel
            showMainPanel()
            updateUserProfileButton()
            appendMessage("Welcome, ${userInfo.name}! How can I help you today?", isUser = false)
        }

        // Add it back
        contentPanel.add(loginPanel, "login", 0)

        // --- Reset session when logging out ---
        currentSessionId = null

        // Show the login panel
        layout.show(contentPanel, "login")
    }

    private fun showMainPanel() {
        val layout = contentPanel.layout as CardLayout
        layout.show(contentPanel, "main")
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
                                // Continue with API request, pass sessionId
                                // Debug log to track currentSessionId value
                                println("Debug: Sending request with sessionId: $currentSessionId")
                                performAPIRequest(userPrompt, accessToken, currentSessionId)
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

    private fun performAPIRequest(userPrompt: String, accessToken: String, sessionId: String?) {
        inputField.isEnabled = false
        consultButton.isEnabled = false
        val editor = com.intellij.openapi.fileEditor.FileEditorManager.getInstance(project).selectedTextEditor
        val document = editor?.document
        val fileText = document?.text ?: "No file open."

        // Show thinking message
        appendMessage("Thinking...", isUser = false)
        val apiUrl = "$backendUrl/consult"
        val payload = JSONObject(
            mapOf(
                "prompt" to userPrompt,
                "file_content" to fileText
            )
        )

        // Make API request in background
        com.intellij.openapi.progress.ProgressManager.getInstance().run(
            object : com.intellij.openapi.progress.Task.Backgroundable(
                project,
                "Consulting AI",
                false
            ) {
                override fun run(indicator: com.intellij.openapi.progress.ProgressIndicator) {
                    try {
                        // Make API request with auth header and session_id header
                        val response = HttpRequests
                            .post(apiUrl, "application/json")
                            .connectTimeout(30000)
                            .readTimeout(30000)
                            .tuner { connection ->
                                connection.connectTimeout = 30000
                                connection.readTimeout = 30000
                                connection.setRequestProperty("Authorization", "Bearer $accessToken")
                                // Add session_id header only if sessionId is not null or empty
                                if (!sessionId.isNullOrBlank()) {
                                    connection.setRequestProperty("session_id", sessionId)
                                    println("Debug: Setting session_id header to: $sessionId")
                                } else {
                                    println("Debug: No session_id to set")
                                }
                            }
                            .connect { request ->
                                request.write(payload.toString())
                                request.getReader(null).readText()
                            }
                        SwingUtilities.invokeLater {
                            // Remove thinking message
                            removeLastMessageIfThinking()
                            val json = JSONObject(response)
                            appendMessage(json.optString("response", response), isUser = false)

                            // --- Update session tracking ---
                            val returnedSessionId = json.optString("session_id", null)
                            if (!returnedSessionId.isNullOrBlank()) {
                                currentSessionId = returnedSessionId
                                println("Debug: Updated currentSessionId to: $currentSessionId")
                            } else {
                                println("Debug: No session_id returned in response")
                            }
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

    // Clear all chat messages from chatPanel
    private fun clearChat() {
        SwingUtilities.invokeLater {
            chatPanel.removeAll()
            chatPanel.revalidate()
            chatPanel.repaint()
        }
    }
}