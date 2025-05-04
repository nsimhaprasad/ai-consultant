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
import org.json.JSONArray
import org.json.JSONObject
import tech.beskar.baid.intelijplugin.auth.GoogleAuthService
import tech.beskar.baid.intelijplugin.auth.LoginPanel
import tech.beskar.baid.intelijplugin.config.BaidConfiguration
import tech.beskar.baid.intelijplugin.util.FontUtil
import java.awt.*
import java.awt.event.MouseAdapter
import java.awt.event.MouseEvent
import javax.swing.*
import com.intellij.openapi.editor.EditorFactory
import com.intellij.openapi.editor.ex.EditorEx
import com.intellij.openapi.editor.highlighter.EditorHighlighterFactory
import com.intellij.openapi.fileTypes.FileTypeManager
import com.intellij.openapi.fileTypes.PlainTextFileType
import com.intellij.openapi.fileTypes.FileType
import java.util.regex.Pattern
import java.awt.Toolkit
import java.awt.datatransfer.StringSelection
import javax.swing.Timer
import javax.swing.JLabel
import javax.swing.JButton
import com.intellij.psi.PsiFileFactory
import com.intellij.openapi.command.WriteCommandAction
import com.intellij.psi.codeStyle.CodeStyleManager

/**
 * Capitalize the first letter of a string
 */
private fun String.capitalize(): String {
    return if (this.isEmpty()) this
    else this.substring(0, 1).toUpperCase() + this.substring(1)
}

class BaidToolWindowPanel(private val project: Project) : JBPanel<BaidToolWindowPanel>(BorderLayout()) {
    private val chatPanel = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(8)))
    private val chatScroll = JBScrollPane(chatPanel)
    private val inputField = JBTextField(30)
    private val consultButton = JButton()

    // Add auth service
    private val authService = GoogleAuthService.getInstance()
    private val config = BaidConfiguration.getInstance()

    // Add content panel to switch between login and main UI
    private val contentPanel = JBPanel<JBPanel<*>>(CardLayout())
    private var loginPanel: LoginPanel
    private val mainPanel = JBPanel<JBPanel<*>>(BorderLayout())

    // User profile button reference
    private lateinit var userProfileButton: JButton

    // SESSION MANAGEMENT
    private var currentSessionId: String? = null
    private lateinit var newSessionButton: JButton

    // PAST CONVERSATIONS
    private lateinit var pastConversationsButton: JButton
    private val pastConversationsPanel = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(8)))
    private val cardLayout = CardLayout()
    private val chatContainer = JBPanel<JBPanel<*>>()
    private var isShowingPastConversations = false

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

        // Setup chat container with card layout to switch between chat and past conversations
        chatContainer.layout = cardLayout
        chatContainer.add(chatScroll, "chat")
        chatContainer.add(createPastConversationsPanel(), "pastConversations")

        // Create header panel with Baid branding and buttons
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

            // Add new session (+) button and past conversations button to header
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

            pastConversationsButton = JButton(AllIcons.General.ArrowRight).apply {
                toolTipText = "Past conversations"
                isContentAreaFilled = false
                isBorderPainted = false
                preferredSize = Dimension(JBUI.scale(32), JBUI.scale(32))
                addActionListener {
                    togglePastConversationsPanel()
                }
            }

            val buttonsPanel = JBPanel<JBPanel<*>>().apply {
                isOpaque = false
                layout = BoxLayout(this, BoxLayout.X_AXIS)
                add(pastConversationsButton)
                add(Box.createHorizontalStrut(JBUI.scale(8)))
                add(newSessionButton)
            }

            val rightPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
                isOpaque = false
                add(buttonsPanel, BorderLayout.EAST)
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
        mainPanel.add(chatContainer, BorderLayout.CENTER)
        mainPanel.add(inputAreaPanel, BorderLayout.SOUTH)

        // Set up content panel with both login and main panels
        contentPanel.add(loginPanel, "login")
        contentPanel.add(mainPanel, "main")

        // Add content panel to the main panel
        add(contentPanel, BorderLayout.CENTER)

        // Check if user is already authenticated in background
        checkAuthenticationStatus()
    }

    private fun createPastConversationsPanel(): JComponent {
        val scrollPane = JBScrollPane(pastConversationsPanel)
        scrollPane.border = JBUI.Borders.empty()
        scrollPane.verticalScrollBar.unitIncrement = JBUI.scale(16)

        // Title for Past Conversations
        val titleLabel = JLabel("Past Conversations").apply {
            font = FontUtil.getTitleFont()
            foreground = JBColor.foreground()
            border = JBUI.Borders.empty(JBUI.scale(16))
            horizontalAlignment = SwingConstants.LEFT
        }

        // Panel to hold everything
        val container = JBPanel<JBPanel<*>>(BorderLayout())
        container.add(titleLabel, BorderLayout.NORTH)
        container.add(scrollPane, BorderLayout.CENTER)

        return container
    }

    private fun togglePastConversationsPanel() {
        isShowingPastConversations = !isShowingPastConversations

        if (isShowingPastConversations) {
            loadPastConversations()
            cardLayout.show(chatContainer, "pastConversations")
            pastConversationsButton.icon = AllIcons.General.ArrowLeft
            pastConversationsButton.toolTipText = "Back to current chat"
        } else {
            cardLayout.show(chatContainer, "chat")
            pastConversationsButton.icon = AllIcons.General.ArrowRight
            pastConversationsButton.toolTipText = "Past conversations"
        }
    }

    private fun loadPastConversations() {
        // Clear previous conversations
        pastConversationsPanel.removeAll()

        // Add loading indicator
        val loadingLabel = JLabel("Loading conversations...", SwingConstants.CENTER)
        pastConversationsPanel.add(loadingLabel)
        pastConversationsPanel.revalidate()
        pastConversationsPanel.repaint()

        // Get current user ID
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val userInfo = authService.getUserInfo()
                if (userInfo != null) {
                    val userId = userInfo.email
                    fetchUserSessions(userId)
                } else {
                    SwingUtilities.invokeLater {
                        loadingLabel.text = "Please sign in to view past conversations"
                    }
                }
            } catch (e: Exception) {
                SwingUtilities.invokeLater {
                    loadingLabel.text = "Error loading conversations: ${e.message}"
                }
            }
        }
    }

    private fun fetchUserSessions(userId: String) {
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val accessToken = authService.getCurrentAccessToken()
                if (accessToken == null) {
                    SwingUtilities.invokeLater {
                        pastConversationsPanel.removeAll()
                        pastConversationsPanel.add(JLabel("Session expired. Please sign in again."))
                        pastConversationsPanel.revalidate()
                        pastConversationsPanel.repaint()
                    }
                    return@executeOnPooledThread
                }

                // Fetch sessions from the API
                val apiUrl = "${config.backendUrl}/sessions/$userId"
                val result = HttpRequests
                    .request(apiUrl)
                    .tuner { connection ->
                        connection.setRequestProperty("Authorization", "Bearer $accessToken")
                    }
                    .readString()

                val jsonResponse = JSONObject(result)
                val sessions = jsonResponse.getJSONArray("sessions")

                SwingUtilities.invokeLater {
                    pastConversationsPanel.removeAll()

                    if (sessions.length() == 0) {
                        pastConversationsPanel.add(JLabel("No past conversations found"))
                    } else {
                        displaySessionsList(sessions, userId)
                    }

                    pastConversationsPanel.revalidate()
                    pastConversationsPanel.repaint()
                }
            } catch (e: Exception) {
                SwingUtilities.invokeLater {
                    pastConversationsPanel.removeAll()
                    pastConversationsPanel.add(JLabel("Error loading conversations: ${e.message}"))
                    pastConversationsPanel.revalidate()
                    pastConversationsPanel.repaint()
                }
            }
        }
    }

    private fun displaySessionsList(sessions: JSONArray, userId: String) {
        // Add title
        val titleLabel = JLabel("Select a conversation to continue", SwingConstants.LEFT).apply {
            font = FontUtil.getSubTitleFont()
            foreground = JBColor.foreground().darker()
            border = JBUI.Borders.empty(JBUI.scale(8), JBUI.scale(16))
        }
        pastConversationsPanel.add(titleLabel)

        // Add each session as a clickable panel
        for (i in 0 until sessions.length()) {
            val session = sessions.getJSONObject(i)
            val sessionId = session.getString("session_id")
            val lastUsed = session.getString("last_used_at")

            // Format the date
            val dateString = try {
                val formatter = java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
                val date = formatter.parse(lastUsed)
                val displayFormat = java.text.SimpleDateFormat("MM/dd/yyyy h:mm a")
                displayFormat.format(date)
            } catch (e: Exception) {
                lastUsed
            }

            // Create a button-like panel for each session
            val sessionPanel = JPanel(BorderLayout()).apply {
                background = JBColor.background()
                border = BorderFactory.createCompoundBorder(
                    BorderFactory.createMatteBorder(0, 0, 1, 0, JBColor.border()),
                    JBUI.Borders.empty(JBUI.scale(12), JBUI.scale(16))
                )
                cursor = Cursor(Cursor.HAND_CURSOR)

                // Get session history preview
                ApplicationManager.getApplication().executeOnPooledThread {
                    try {
                        val accessToken = authService.getCurrentAccessToken() ?: return@executeOnPooledThread
                        val historyUrl = "${config.backendUrl}/history/$userId/$sessionId"
                        val historyResult = HttpRequests
                            .request(historyUrl)
                            .tuner { connection ->
                                connection.setRequestProperty("Authorization", "Bearer $accessToken")
                            }
                            .readString()

                        val historyJson = JSONObject(historyResult)
                        val messagesArray = historyJson.getJSONArray("history")

                        // Find the first message from user and agent
                        var firstUserMessage = ""

                        for (j in 0 until messagesArray.length()) {
                            val message = messagesArray.getJSONObject(j)
                            if (message.getString("role") == "user") {
                                firstUserMessage = message.getString("message")
                                break
                            }
                        }

                        // Create a preview of the conversation
                        val previewText = if (firstUserMessage.isNotEmpty()) {
                            if (firstUserMessage.length > 60) {
                                "${firstUserMessage.substring(0, 60)}..."
                            } else {
                                firstUserMessage
                            }
                        } else {
                            "Empty conversation"
                        }

                        SwingUtilities.invokeLater {
                            val preview = JLabel(previewText).apply {
                                foreground = JBColor.foreground()
                            }
                            add(preview, BorderLayout.CENTER)
                            revalidate()
                            repaint()
                        }
                    } catch (e: Exception) {
                        SwingUtilities.invokeLater {
                            val preview = JLabel("Failed to load preview: ${e.message}").apply {
                                foreground = JBColor.foreground()
                            }
                            add(preview, BorderLayout.CENTER)
                            revalidate()
                            repaint()
                        }
                    }
                }

                // Add date as a secondary label
                val dateLabel = JLabel(dateString).apply {
                    foreground = JBColor.foreground().darker()
                    font = font.deriveFont(Font.PLAIN, font.size - 1f)
                    border = JBUI.Borders.emptyTop(JBUI.scale(4))
                }
                add(dateLabel, BorderLayout.SOUTH)

                // Add click handler to load the conversation
                addMouseListener(object : MouseAdapter() {
                    override fun mouseClicked(e: MouseEvent) {
                        loadConversation(userId, sessionId)
                    }

                    override fun mouseEntered(e: MouseEvent) {
                        background = JBColor.background().brighter()
                    }

                    override fun mouseExited(e: MouseEvent) {
                        background = JBColor.background()
                    }
                })
            }

            pastConversationsPanel.add(sessionPanel)
        }
    }

    private fun loadConversation(userId: String, sessionId: String) {
        // Set current session ID
        currentSessionId = sessionId

        // Close past conversations panel and return to chat
        isShowingPastConversations = false
        cardLayout.show(chatContainer, "chat")
        pastConversationsButton.icon = AllIcons.General.ArrowRight
        pastConversationsButton.toolTipText = "Past conversations"

        // Clear current chat
        clearChat()

        // Show loading message
        appendMessage("Loading conversation history...", isUser = false)

        // Load conversation history
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val accessToken = authService.getCurrentAccessToken()
                if (accessToken == null) {
                    SwingUtilities.invokeLater {
                        removeLastMessageIfThinking()
                        appendMessage("Session expired. Please sign in again.", isUser = false)
                    }
                    return@executeOnPooledThread
                }

                // Fetch conversation history
                val historyUrl = "${config.backendUrl}/history/$userId/$sessionId"
                val historyResult = HttpRequests
                    .request(historyUrl)
                    .tuner { connection ->
                        connection.setRequestProperty("Authorization", "Bearer $accessToken")
                    }
                    .readString()

                val historyJson = JSONObject(historyResult)
                val messagesArray = historyJson.getJSONArray("history")

                // Remove loading message
                SwingUtilities.invokeLater {
                    removeLastMessageIfThinking()

                    // Display conversation history
                    for (i in 0 until messagesArray.length()) {
                        val message = messagesArray.getJSONObject(i)
                        val role = message.getString("role")
                        val content = message.getString("message")

                        appendMessage(content, isUser = role == "user")
                    }

                    // Add a separator to indicate where the new messages will start
                    appendMessage(
                        "Continuing this conversation. Any new messages will be part of this session.",
                        isUser = false
                    )
                }
            } catch (e: Exception) {
                SwingUtilities.invokeLater {
                    removeLastMessageIfThinking()
                    appendMessage("Error loading conversation: ${e.message}", isUser = false)
                }
            }
        }
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

        // Reset session when logging out
        currentSessionId = null

        // Show the login panel
        layout.show(contentPanel, "login")
    }

    private fun showMainPanel() {
        val layout = contentPanel.layout as CardLayout
        layout.show(contentPanel, "main")
    }

    fun appendMessage(message: String, isUser: Boolean) {
        // Create message panel with WhatsApp-like layout
        val messagePanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            background = JBColor.background()
            border = JBUI.Borders.empty(JBUI.scale(4), JBUI.scale(16))
        }

        // Create message bubble container
        val bubbleContainer = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            background = if (isUser) {
                JBColor(Color(220, 248, 198), Color(54, 93, 69)) // Light green for user
            } else {
                JBColor(Color(255, 255, 255), Color(60, 63, 65)) // White/dark for agent
            }
            border = JBUI.Borders.empty(JBUI.scale(8), JBUI.scale(12))
        }

        // Create message with avatar container
        val contentPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            isOpaque = false

            if (isUser) {
                // User message: avatar on right, bubble on left
                add(bubbleContainer, BorderLayout.CENTER)

                val avatarLabel = JLabel().apply {
                    icon = AllIcons.General.User
                    border = JBUI.Borders.emptyLeft(JBUI.scale(8))
                    verticalAlignment = JLabel.TOP
                }
                add(avatarLabel, BorderLayout.EAST)

                // Add padding on the left to push message right
                val spacer = JPanel().apply {
                    isOpaque = false
                    preferredSize = Dimension(JBUI.scale(100), 0) // Adjust width as needed
                }
                add(spacer, BorderLayout.WEST)
            } else {
                // Agent message: avatar on left, bubble on right
                val avatarLabel = JLabel().apply {
                    icon = AllIcons.General.BalloonInformation
                    border = JBUI.Borders.emptyRight(JBUI.scale(8))
                    verticalAlignment = JLabel.TOP
                }
                add(avatarLabel, BorderLayout.WEST)
                add(bubbleContainer, BorderLayout.CENTER)

                // Add padding on the right to keep message left-aligned
                val spacer = JPanel().apply {
                    isOpaque = false
                    preferredSize = Dimension(JBUI.scale(100), 0) // Adjust width as needed
                }
                add(spacer, BorderLayout.EAST)
            }
        }

        messagePanel.add(contentPanel, BorderLayout.CENTER)

        // Check if the message contains code blocks
        if (message.contains("```")) {
            // Create a panel with vertical layout to hold text and code segments
            val mixedContentPanel = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(8)))
            mixedContentPanel.isOpaque = false

            // Process the text to separate code blocks from regular text
            processTextWithCodeBlocks(message, mixedContentPanel)

            // Add the mixed content panel to the bubble container
            bubbleContainer.add(mixedContentPanel, BorderLayout.CENTER)
        } else {
            // Just regular text, use a JTextArea
            val messageText = JTextArea().apply {
                setText(message)
                font = FontUtil.getBodyFont()
                lineWrap = true
                wrapStyleWord = true
                isEditable = false
                isOpaque = false
                background = Color(0, 0, 0, 0) // Transparent
                foreground = if (isUser) Color.BLACK else JBColor.foreground()
                border = JBUI.Borders.empty()
                minimumSize = Dimension(0, preferredSize.height)
                maximumSize = Dimension(JBUI.scale(400), Int.MAX_VALUE)
            }

            // Add message text to bubble
            bubbleContainer.add(messageText, BorderLayout.CENTER)
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

    /**
     * Process text that contains code blocks and regular text, creating appropriate
     * components for each segment
     */
    private fun processTextWithCodeBlocks(text: String, containerPanel: JBPanel<*>) {
        // Pattern to match code blocks with language specified: ```language code ```
        // Using non-greedy matching and proper multi-line support
        val codeBlockPattern = Pattern.compile("```(\\w*)\\s*\\n?([\\s\\S]*?)```", Pattern.DOTALL)
        val matcher = codeBlockPattern.matcher(text)

        var lastEnd = 0
        var foundValidCode = false

        while (matcher.find()) {
            // Add the text before the code block
            val textBefore = text.substring(lastEnd, matcher.start())
            if (textBefore.isNotBlank()) {
                addTextSegment(containerPanel, textBefore)
            }

            // Get the language and code
            var language = matcher.group(1).trim().toLowerCase()
            val code = matcher.group(2).trim()

            // Validate that we have actual code content
            if (code.isNotBlank()) {
                foundValidCode = true

                // If language is empty, try to detect it from the code
                if (language.isEmpty()) {
                    language = detectCodeLanguage(code)
                }

                // Add the code block with syntax highlighting
                addCodeSegment(containerPanel, code, language)
            } else {
                // If code is empty, just add a message
                addTextSegment(containerPanel, "[Empty code block]")
            }

            lastEnd = matcher.end()
        }

        // If no valid code was found but the pattern was matched, show a friendly message
        if (!foundValidCode && lastEnd > 0) {
            addTextSegment(containerPanel, "Note: Code block was detected but no valid code content was found.")
        }

        // Add any remaining text after the last code block
        if (lastEnd < text.length) {
            val textAfter = text.substring(lastEnd)
            if (textAfter.isNotBlank()) {
                addTextSegment(containerPanel, textAfter)
            }
        }
    }

    /**
     * Attempt to detect the language of code based on its content
     */
    private fun detectCodeLanguage(code: String): String {
        // Look for language clues in the code
        return when {
            // Java patterns
            code.contains("public class") || code.contains("private class") ||
                    code.contains("protected class") || code.contains("import java.") ||
                    (code.contains("public static void main") && code.contains(";")) -> "java"

            // Kotlin patterns
            code.contains("fun ") || code.contains("val ") || code.contains("var ") ||
                    code.contains("suspend ") || code.contains("import kotlin.") -> "kotlin"

            // Python patterns
            code.contains("def ") || code.contains("import ") && !code.contains(";") ||
                    code.contains("class ") && !code.contains(";") -> "python"

            // JavaScript/TypeScript patterns
            code.contains("function ") || code.contains("const ") || code.contains("let ") ||
                    code.contains("var ") && code.contains(";") || code.contains("=>") ||
                    code.contains("import React") -> {
                if (code.contains(": ") && code.contains("interface ") ||
                    code.contains("<") && code.contains(">") && code.contains("extends")
                ) {
                    "typescript"
                } else {
                    "javascript"
                }
            }

            // HTML pattern
            code.contains("<html") || code.contains("<!DOCTYPE html") ||
                    (code.contains("<div") && code.contains("</div>")) -> "html"

            // CSS pattern
            code.matches(".*\\{[^{}]*\\}.*".toRegex(RegexOption.DOT_MATCHES_ALL)) &&
                    (code.contains(": ") && code.contains(";")) -> "css"

            // SQL pattern
            code.contains("SELECT ") || code.contains("UPDATE ") ||
                    code.contains("INSERT INTO ") || code.contains("CREATE TABLE ") -> "sql"

            // Shell/Bash pattern
            code.contains("#!/bin/bash") || code.contains("#!/bin/sh") ||
                    code.contains("echo ") && code.contains("$") -> "bash"

            // JSON pattern
            code.trim().startsWith("{") && code.trim().endsWith("}") &&
                    code.contains("\":") -> "json"

            // XML pattern
            code.contains("<?xml") || (code.contains("<") && code.contains("</") &&
                    code.contains("/>")) -> "xml"

            // C/C++ patterns
            code.contains("#include <") ||
                    (code.contains("int main(") && code.contains("return 0;")) -> {
                if (code.contains("std::") || code.contains("template<")) {
                    "cpp"
                } else {
                    "c"
                }
            }

            // Default if no pattern matches
            else -> "text"
        }
    }

    private fun addTextSegment(containerPanel: JBPanel<*>, textContent: String) {
        val textArea = JTextArea().apply {
            setText(textContent)
            font = FontUtil.getBodyFont()
            lineWrap = true
            wrapStyleWord = true
            isEditable = false
            isOpaque = false
            background = Color(0, 0, 0, 0)
            foreground = JBColor.foreground()
            border = JBUI.Borders.empty()
        }

        containerPanel.add(textArea)
    }


    // A simpler, thread-safe approach to code formatting
    private fun formatCodeSafely(code: String, language: String): String {
        // If code already has line breaks, assume it's already formatted
        if (code.contains("\n")) {
            return code
        }

        try {
            // Simple but effective formatting for Java-like languages
            return when (language.toLowerCase()) {
                "java", "kotlin", "c", "cpp", "c++", "csharp", "javascript", "typescript" -> {
                    var formattedCode = code
                        // Format class declarations
                        .replace("public class ", "public class \n")
                        .replace("class ", "class \n")

                        // Format method declarations and blocks
                        .replace("{ ", "{\n    ")
                        .replace("} ", "}\n")
                        .replace(";", ";\n    ")

                        // Format constructors
                        .replace(") {", ") {\n    ")

                        // Format method parameters
                        .replace("this.", "\n    this.")

                        // Format return statements
                        .replace("return ", "\n    return ")

                    // Clean up any double newlines
                    formattedCode = formattedCode
                        .replace("\n\n", "\n")
                        .replace("\n    \n", "\n")

                    // Make sure closing braces are properly aligned
                    formattedCode = formattedCode
                        .replace("\n    }", "\n}")
                        .replace(";\n}", ";\n    }")

                    formattedCode
                }

                "python" -> {
                    code.replace(": ", ":\n    ")
                        .replace("def ", "\ndef ")
                        .replace("class ", "\nclass ")
                }

                else -> {
                    // Basic formatting for other languages
                    code.replace("; ", ";\n")
                        .replace(" { ", " {\n    ")
                        .replace(" } ", "\n}\n")
                }
            }
        } catch (e: Exception) {
            println("Error formatting code: ${e.message}")
            return code // Return original if formatting fails
        }
    }

    private fun addCodeSegment(containerPanel: JBPanel<*>, code: String, language: String) {
        try {
            // Format the code safely without using IntelliJ's formatter
            val formattedCode = formatCodeSafely(code, language)

            // Create an editor for the code
            val editorFactory = EditorFactory.getInstance()
            val document = editorFactory.createDocument(formattedCode)

            // Set read-only
            document.setReadOnly(true)

            // Create the editor with syntax highlighting
            val editor = editorFactory.createViewer(document, project)

            // Configure the editor
            if (editor is EditorEx) {
                // Get appropriate file type for syntax highlighting based on language
                val fileType = getFileTypeForLanguage(language)

                // Apply syntax highlighting
                editor.highlighter = EditorHighlighterFactory.getInstance().createEditorHighlighter(project, fileType)

                // Configure editor appearance
                editor.settings.apply {
                    isLineNumbersShown = true
                    isLineMarkerAreaShown = false
                    isIndentGuidesShown = true
                    isVirtualSpace = false
                    isFoldingOutlineShown = true
                    additionalLinesCount = 0
                    additionalColumnsCount = 0
                    isUseSoftWraps = false
                }

                // Hide some UI elements
                editor.settings.isRightMarginShown = false
                editor.setBorder(JBUI.Borders.empty(4))

                // Set background color
                editor.backgroundColor = JBColor(
                    Color(245, 245, 245), // Light theme
                    Color(43, 43, 43)     // Dark theme
                )

                // Store editor in client properties for later disposal
                editor.component.putClientProperty("EDITOR_KEY", editor)
            }

            // Calculate proper height based on number of lines
            val lineCount = formattedCode.split("\n").size
            val editorHeight = Math.min(
                Math.max(JBUI.scale(20 + lineCount * 20), JBUI.scale(100)),
                JBUI.scale(400) // Max height
            )

            // Create a header panel with language badge and copy button
            val headerPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
                background = JBColor(
                    Color(230, 230, 230), // Light theme
                    Color(60, 63, 65)      // Dark theme
                )
                border = JBUI.Borders.empty(4, 8)

                // Add language badge
                val languageBadge = JLabel(language.capitalize()).apply {
                    font = Font(Font.SANS_SERIF, Font.BOLD, 12)
                    foreground = JBColor.foreground()
                }
                add(languageBadge, BorderLayout.WEST)

                // Add copy button
                val copyButton = JButton("Copy").apply {
                    putClientProperty("JButton.buttonType", "flat")
                    addActionListener {
                        // Copy code to clipboard
                        val clipboard = Toolkit.getDefaultToolkit().systemClipboard
                        val selection = StringSelection(code) // Copy original unformatted code
                        clipboard.setContents(selection, selection)

                        // Show temporary "Copied!" feedback
                        text = "Copied!"
                        isEnabled = false

                        // Reset button after delay
                        Timer(1500) {
                            text = "Copy"
                            isEnabled = true
                        }.apply {
                            isRepeats = false
                            start()
                        }
                    }
                }
                add(copyButton, BorderLayout.EAST)
            }

            // Create a scroll pane for the editor
            val scrollPane = JBScrollPane(editor.component).apply {
                border = JBUI.Borders.empty()
                verticalScrollBarPolicy = ScrollPaneConstants.VERTICAL_SCROLLBAR_AS_NEEDED
                horizontalScrollBarPolicy = ScrollPaneConstants.HORIZONTAL_SCROLLBAR_AS_NEEDED
            }

            // Create a panel for the editor with proper sizing
            val editorPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
                add(headerPanel, BorderLayout.NORTH)
                add(scrollPane, BorderLayout.CENTER)
                preferredSize = Dimension(JBUI.scale(400), editorHeight + JBUI.scale(30))
                minimumSize = Dimension(JBUI.scale(380), JBUI.scale(100))
                border = BorderFactory.createLineBorder(JBColor.border(), 1)
            }

            containerPanel.add(editorPanel)

        } catch (e: Exception) {
            println("Error creating editor: ${e.message}")
            e.printStackTrace()

            // Fall back to simple text area display
            addFallbackCodeDisplay(containerPanel, code, language)
        }
    }

    // Add this method to use IntelliJ's built-in code formatter
    private fun formatCodeUsingIntelliJFormatter(code: String, language: String): String {
        try {
            // If code already contains line breaks, it might already be formatted
            if (code.contains("\n")) {
                return code
            }

            // Determine the file type based on language
            val fileTypeManager = FileTypeManager.getInstance()
            val fileType = getFileTypeForLanguage(language)

            // Create a temporary file with the correct extension to apply formatting
            val extension = when (language.toLowerCase()) {
                "java" -> ".java"
                "kotlin", "kt" -> ".kt"
                "python", "py" -> ".py"
                "javascript", "js" -> ".js"
                "typescript", "ts" -> ".ts"
                "html" -> ".html"
                "css" -> ".css"
                "xml" -> ".xml"
                "json" -> ".json"
                "c", "cpp", "c++" -> ".cpp"
                "csharp", "cs" -> ".cs"
                else -> ".txt"
            }

            // Create a temporary PSI file to use IntelliJ's formatter
            val project = project
            val psiFileFactory = com.intellij.psi.PsiFileFactory.getInstance(project)

            // Create a PSI file with the code content
            val psiFile = psiFileFactory.createFileFromText(
                "temp$extension",
                fileType,
                code,
                System.currentTimeMillis(),
                true
            )

            // Apply code formatting using IntelliJ's formatter
            com.intellij.openapi.command.WriteCommandAction.runWriteCommandAction(project) {
                com.intellij.psi.codeStyle.CodeStyleManager.getInstance(project).reformat(psiFile)
            }

            // Get the formatted code
            val formattedCode = psiFile.text

            return formattedCode
        } catch (e: Exception) {
            // Log error and return original code if formatting fails
            println("Error using IntelliJ formatter: ${e.message}")
            e.printStackTrace()

            // Apply a simple fallback formatting for Java-like languages
            if (language.toLowerCase() in listOf("java", "kotlin", "c", "cpp", "csharp", "javascript")) {
                return applySimpleFormatting(code)
            }

            return code
        }
    }

    // Simple fallback formatter for when IntelliJ formatter fails
    private fun applySimpleFormatting(code: String): String {
        if (code.contains("\n")) {
            return code
        }

        // Simplified formatting for Java-like languages
        return code
            .replace("{", "{\n  ")
            .replace("}", "\n}")
            .replace(";", ";\n  ")
            .replace("\n  \n", "\n")
            .replace("{\n  \n", "{\n")
    }


    // Add a fallback method in case editor creation fails
    private fun addFallbackCodeDisplay(containerPanel: JBPanel<*>, code: String, language: String) {
        // Create a header panel with language badge and copy button
        val headerPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            background = JBColor(
                Color(230, 230, 230), // Light theme
                Color(60, 63, 65)      // Dark theme
            )
            border = JBUI.Borders.empty(4, 8)

            // Add language badge
            val languageBadge = JLabel(language.capitalize()).apply {
                font = Font(Font.SANS_SERIF, Font.BOLD, 12)
                foreground = JBColor.foreground()
            }
            add(languageBadge, BorderLayout.WEST)

            // Add copy button
            val copyButton = JButton("Copy").apply {
                putClientProperty("JButton.buttonType", "flat")
                addActionListener {
                    // Copy code to clipboard
                    val clipboard = Toolkit.getDefaultToolkit().systemClipboard
                    val selection = StringSelection(code)
                    clipboard.setContents(selection, selection)

                    // Show temporary "Copied!" feedback
                    text = "Copied!"
                    isEnabled = false

                    // Reset button after delay
                    Timer(1500) {
                        text = "Copy"
                        isEnabled = true
                    }.apply {
                        isRepeats = false
                        start()
                    }
                }
            }
            add(copyButton, BorderLayout.EAST)
        }

        // Create a text area with monospaced font for code
        val codeTextArea = JTextArea().apply {
            setText(code)
            font = Font(Font.MONOSPACED, Font.PLAIN, 13)
            lineWrap = false
            wrapStyleWord = false
            isEditable = false
            border = JBUI.Borders.empty(8)
            background = JBColor(
                Color(245, 245, 245), // Light theme
                Color(43, 43, 43)     // Dark theme
            )
            foreground = JBColor.foreground()
            caretPosition = 0 // Ensure scrolled to top
        }

        // Create a scroll pane for the text area
        val scrollPane = JBScrollPane(codeTextArea).apply {
            verticalScrollBarPolicy = JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED
            horizontalScrollBarPolicy = JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED
            border = JBUI.Borders.empty()
        }

        // Calculate proper height based on number of lines
        val lineCount = code.split("\n").size
        val displayHeight = Math.min(
            JBUI.scale(20 + lineCount * 20), // Adjust multiplier for line height
            JBUI.scale(300) // Max height
        )

        // Create the container panel
        val codePanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            add(headerPanel, BorderLayout.NORTH)
            add(scrollPane, BorderLayout.CENTER)
            preferredSize = Dimension(JBUI.scale(400), displayHeight)
            border = BorderFactory.createLineBorder(JBColor.border(), 1)
        }

        containerPanel.add(codePanel)
    }

    /**
     * Get the appropriate FileType for syntax highlighting based on language string
     */
    private fun getFileTypeForLanguage(language: String): FileType {
        val fileTypeManager = FileTypeManager.getInstance()

        // Normalize the language string
        val normalizedLanguage = language.toLowerCase().trim()

        return when (normalizedLanguage) {
            "java" -> fileTypeManager.findFileTypeByName("JAVA") ?: PlainTextFileType.INSTANCE
            "kotlin", "kt" -> fileTypeManager.findFileTypeByName("Kotlin") ?: PlainTextFileType.INSTANCE
            "python", "py" -> fileTypeManager.findFileTypeByName("Python") ?: PlainTextFileType.INSTANCE
            "javascript", "js" -> fileTypeManager.findFileTypeByName("JavaScript") ?: PlainTextFileType.INSTANCE
            "typescript", "ts" -> fileTypeManager.findFileTypeByName("TypeScript") ?: PlainTextFileType.INSTANCE
            "html" -> fileTypeManager.findFileTypeByName("HTML") ?: PlainTextFileType.INSTANCE
            "css" -> fileTypeManager.findFileTypeByName("CSS") ?: PlainTextFileType.INSTANCE
            "xml" -> fileTypeManager.findFileTypeByName("XML") ?: PlainTextFileType.INSTANCE
            "json" -> fileTypeManager.findFileTypeByName("JSON") ?: PlainTextFileType.INSTANCE
            "sql" -> fileTypeManager.findFileTypeByName("SQL") ?: PlainTextFileType.INSTANCE
            "c", "cpp", "c++" -> fileTypeManager.findFileTypeByName("C/C++") ?: PlainTextFileType.INSTANCE
            "csharp", "cs" -> fileTypeManager.findFileTypeByName("C#") ?: PlainTextFileType.INSTANCE
            "go" -> fileTypeManager.findFileTypeByName("Go") ?: PlainTextFileType.INSTANCE
            "rust", "rs" -> fileTypeManager.findFileTypeByName("Rust") ?: PlainTextFileType.INSTANCE
            "php" -> fileTypeManager.findFileTypeByName("PHP") ?: PlainTextFileType.INSTANCE
            "ruby", "rb" -> fileTypeManager.findFileTypeByName("Ruby") ?: PlainTextFileType.INSTANCE
            "shell", "sh", "bash" -> fileTypeManager.findFileTypeByName("Shell Script") ?: PlainTextFileType.INSTANCE
            "yaml", "yml" -> fileTypeManager.findFileTypeByName("YAML") ?: PlainTextFileType.INSTANCE
            "markdown", "md" -> fileTypeManager.findFileTypeByName("Markdown") ?: PlainTextFileType.INSTANCE
            "groovy" -> fileTypeManager.findFileTypeByName("Groovy") ?: PlainTextFileType.INSTANCE
            "swift" -> fileTypeManager.findFileTypeByName("Swift") ?: PlainTextFileType.INSTANCE
            "dart" -> fileTypeManager.findFileTypeByName("Dart") ?: PlainTextFileType.INSTANCE
            "scala" -> fileTypeManager.findFileTypeByName("Scala") ?: PlainTextFileType.INSTANCE
            "haskell", "hs" -> fileTypeManager.findFileTypeByName("Haskell") ?: PlainTextFileType.INSTANCE
            "r" -> fileTypeManager.findFileTypeByName("R") ?: PlainTextFileType.INSTANCE
            "perl", "pl" -> fileTypeManager.findFileTypeByName("Perl") ?: PlainTextFileType.INSTANCE
            "lua" -> fileTypeManager.findFileTypeByName("Lua") ?: PlainTextFileType.INSTANCE
            "clojure", "clj" -> fileTypeManager.findFileTypeByName("Clojure") ?: PlainTextFileType.INSTANCE
            "dockerfile", "docker" -> fileTypeManager.findFileTypeByName("Dockerfile") ?: PlainTextFileType.INSTANCE
            "vue" -> fileTypeManager.findFileTypeByName("Vue.js") ?: fileTypeManager.findFileTypeByName("HTML")
            ?: PlainTextFileType.INSTANCE

            // Add fallback detection by extension for unspecified languages
            else -> {
                // Try to find by extension if language wasn't recognized
                val extension = normalizedLanguage.takeIf { it.isNotEmpty() } ?: "txt"
                val fileType = fileTypeManager.getFileTypeByExtension(extension)

                // Only return the found file type if it's not the default or unknown type
                if (fileType != PlainTextFileType.INSTANCE &&
                    fileType != fileTypeManager.getFileTypeByExtension("txt")
                ) {
                    fileType
                } else {
                    PlainTextFileType.INSTANCE
                }
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
        println("Starting API request with sessionId: $sessionId")

        inputField.isEnabled = false
        consultButton.isEnabled = false
        val editor = com.intellij.openapi.fileEditor.FileEditorManager.getInstance(project).selectedTextEditor
        val document = editor?.document
        val fileText = document?.text ?: "No file open."

        // Show thinking message
        appendMessage("Thinking...", isUser = false)
        val apiUrl = "${config.backendUrl}${config.apiEndpoint}"

        val payload = JSONObject(
            mapOf(
                "prompt" to userPrompt,
                "file_content" to fileText
            )
        )

        // Make streaming API request in background
        com.intellij.openapi.progress.ProgressManager.getInstance().run(
            object : com.intellij.openapi.progress.Task.Backgroundable(
                project,
                "Consulting AI",
                false
            ) {
                override fun run(indicator: com.intellij.openapi.progress.ProgressIndicator) {
                    try {
                        // First, remove thinking message before streaming starts
                        SwingUtilities.invokeLater {
                            removeLastMessageIfThinking()
                        }

                        // Prepare headers
                        val headers = mutableMapOf(
                            "Authorization" to "Bearer $accessToken",
                            "Content-Type" to "application/json"
                        )

                        if (!sessionId.isNullOrBlank()) {
                            headers["session_id"] = sessionId
                        }

                        // Create a streaming response handler
                        var fullResponse = ""
                        var updatedSessionId: String? = sessionId
                        var lineCount = 0

                        // Make HTTP request with custom streaming handling
                        HttpRequests
                            .post(apiUrl, "application/json")
                            .connectTimeout(30000)
                            .readTimeout(300000)
                            .tuner { connection ->
                                headers.forEach { (key, value) ->
                                    connection.setRequestProperty(key, value)
                                }
                            }
                            .connect { request ->
                                request.write(payload.toString())

                                val messagePanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
                                    background = JBColor.background()
                                    border = JBUI.Borders.empty(JBUI.scale(4), JBUI.scale(16))
                                }

                                // Create agent message with WhatsApp-like layout
                                val bubbleContainer = JBPanel<JBPanel<*>>(BorderLayout()).apply {
                                    background = JBColor(Color(255, 255, 255), Color(60, 63, 65))
                                    border = JBUI.Borders.empty(JBUI.scale(8), JBUI.scale(12))
                                }

                                // Create message with avatar container for agent response
                                val contentPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
                                    isOpaque = false

                                    val avatarLabel = JLabel().apply {
                                        icon = AllIcons.General.BalloonInformation
                                        border = JBUI.Borders.emptyRight(JBUI.scale(8))
                                        verticalAlignment = JLabel.TOP
                                    }
                                    add(avatarLabel, BorderLayout.WEST)
                                    add(bubbleContainer, BorderLayout.CENTER)

                                    // Add padding on the right
                                    val spacer = JPanel().apply {
                                        isOpaque = false
                                        preferredSize = Dimension(JBUI.scale(100), 0)
                                    }
                                    add(spacer, BorderLayout.EAST)
                                }

                                messagePanel.add(contentPanel, BorderLayout.CENTER)

                                // Add the message panel to chat
                                SwingUtilities.invokeLater {
                                    chatPanel.add(messagePanel)
                                    chatPanel.revalidate()
                                    chatPanel.repaint()
                                }

                                request.inputStream.bufferedReader().use { reader ->
                                    var line: String?
                                    while (reader.readLine().also { line = it } != null) {
                                        lineCount++

                                        if (line?.startsWith("data: ") == true) {
                                            val data = line?.substring(6) ?: ""

                                            if (data == "[DONE]") {
                                                break
                                            } else if (data.startsWith("{") && data.endsWith("}")) {
                                                try {
                                                    val jsonData = JSONObject(data)
                                                    val sessionIdInJson = jsonData.optString("session_id", null)
                                                    if (sessionIdInJson != null && sessionIdInJson.isNotEmpty()) {
                                                        updatedSessionId = sessionIdInJson
                                                    }
                                                } catch (e: Exception) {
                                                    fullResponse += data
                                                    updateMessagePanel(messagePanel, fullResponse)
                                                }
                                            } else {
                                                fullResponse += data
                                                updateMessagePanel(messagePanel, fullResponse)
                                            }
                                        }
                                    }
                                }

                                println("Stream complete. Processed $lineCount lines")
                            }

                        // Update session tracking and enable input
                        SwingUtilities.invokeLater {
                            currentSessionId = updatedSessionId
                            inputField.isEnabled = true
                            consultButton.isEnabled = true
                            inputField.requestFocus()
                        }

                    } catch (e: Exception) {
                        println("API request error: ${e.message}")

                        SwingUtilities.invokeLater {
                            removeLastMessageIfThinking()
                            if (e.message?.contains("401") == true || e.message?.contains("403") == true) {
                                appendMessage("Your session has expired. Please sign in again.", isUser = false)
                                authService.signOut()
                                showLoginPanel()
                            } else {
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

    // Helper method to update message panel with streaming text
    private fun updateMessagePanel(messagePanel: JBPanel<*>, text: String) {
        SwingUtilities.invokeLater {
            try {
                // Navigate through the panel structure
                val contentPanel = messagePanel.getComponent(0) as JBPanel<*>
                val bubbleContainer = contentPanel.getComponent(1) as JBPanel<*>

                // Check if the text contains code blocks
                if (text.contains("```")) {
                    // Handle code blocks
                    if (bubbleContainer.componentCount == 0 ||
                        (bubbleContainer.componentCount == 1 && !(bubbleContainer.getComponent(0) is JBPanel<*>))
                    ) {
                        // Create new panel for mixed content
                        bubbleContainer.removeAll()
                        val mixedContentPanel = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(8)))
                        mixedContentPanel.isOpaque = false
                        bubbleContainer.add(mixedContentPanel, BorderLayout.CENTER)
                        processTextWithCodeBlocks(text, mixedContentPanel)
                    } else if (bubbleContainer.componentCount == 1 && bubbleContainer.getComponent(0) is JBPanel<*>) {
                        // Update existing panel
                        val mixedContentPanel = bubbleContainer.getComponent(0) as JBPanel<*>
                        mixedContentPanel.removeAll()
                        processTextWithCodeBlocks(text, mixedContentPanel)
                    }
                } else {
                    // Regular text without code blocks
                    if (bubbleContainer.componentCount == 0 ||
                        (bubbleContainer.componentCount == 1 && !(bubbleContainer.getComponent(0) is JTextArea))
                    ) {
                        // Create new text area
                        bubbleContainer.removeAll()
                        val messageText = JTextArea().apply {
                            setText(text)
                            font = FontUtil.getBodyFont()
                            lineWrap = true
                            wrapStyleWord = true
                            isEditable = false
                            isOpaque = false
                            background = Color(0, 0, 0, 0)
                            foreground = JBColor.foreground()
                            border = JBUI.Borders.empty()
                            minimumSize = Dimension(0, preferredSize.height)
                            maximumSize = Dimension(JBUI.scale(400), Int.MAX_VALUE)
                        }
                        bubbleContainer.add(messageText, BorderLayout.CENTER)
                    } else if (bubbleContainer.componentCount == 1 && bubbleContainer.getComponent(0) is JTextArea) {
                        // Update existing text area
                        val messageText = bubbleContainer.getComponent(0) as JTextArea
                        messageText.setText(text)
                    }
                }

                // Ensure scrolling works properly
                chatPanel.revalidate()
                chatPanel.repaint()

                // Scroll to bottom - schedule after the UI updates
                SwingUtilities.invokeLater {
                    val vertical = chatScroll.verticalScrollBar
                    vertical.value = vertical.maximum
                }
            } catch (e: Exception) {
                println("Error updating message panel: ${e.message}")
                e.printStackTrace()
            }
        }
    }

    private fun findAndScrollCodeEditors(container: Container) {
        // Recursively look for editors in the component hierarchy
        for (i in 0 until container.componentCount) {
            val component = container.getComponent(i)

            if (component is JScrollPane) {
                // Found a scroll pane, scroll to appropriate position
                SwingUtilities.invokeLater {
                    // For code display, scroll to top
                    component.verticalScrollBar.value = 0
                    component.horizontalScrollBar.value = 0
                }
            } else if (component is JComponent) {
                // Check if this is an editor component
                val editorData = component.getClientProperty("EDITOR_KEY")
                if (editorData is EditorEx) {
                    // Found an editor, ensure it's scrolled to top
                    SwingUtilities.invokeLater {
                        editorData.scrollingModel.scrollVertically(0)
                        editorData.scrollingModel.scrollHorizontally(0)
                    }
                }
            }

            // Continue searching recursively
            if (component is Container) {
                findAndScrollCodeEditors(component)
            }
        }
    }

    private fun removeLastMessageIfThinking() {
        if (chatPanel.componentCount > 0) {
            val lastMessage = chatPanel.getComponent(chatPanel.componentCount - 1)
            if (lastMessage is JBPanel<*> && lastMessage.border == JBUI.Borders.empty(JBUI.scale(4), JBUI.scale(16))) {
                // Navigate through the panel structure to find the text area
                try {
                    val contentPanel = lastMessage.getComponent(0) as JBPanel<*>
                    val bubbleContainer = contentPanel.getComponent(1) as JBPanel<*>
                    val messageText = bubbleContainer.getComponent(0) as JTextArea
                    if (messageText.text == "Thinking...") {
                        chatPanel.remove(lastMessage)
                        chatPanel.revalidate()
                        chatPanel.repaint()
                    }
                } catch (e: Exception) {
                    // If structure doesn't match, ignore
                }
            }
        }
    }

    // Clear all chat messages from chatPanel and dispose editors
    private fun clearChat() {
        SwingUtilities.invokeLater {
            // Dispose all editors before clearing the chat panel
            disposeAllEditors()

            chatPanel.removeAll()
            chatPanel.revalidate()
            chatPanel.repaint()
        }
    }

    // Helper method to dispose all editors
    private fun disposeAllEditors() {
        // Find and dispose all editors in the chat panel
        fun findAndDisposeEditors(container: Container) {
            for (i in 0 until container.componentCount) {
                val component = container.getComponent(i)

                if (component is JComponent) {
                    // Check if this component is an editor
                    val editorData = component.getClientProperty("EDITOR_KEY")
                    if (editorData is EditorEx) {
                        EditorFactory.getInstance().releaseEditor(editorData)
                    }
                }

                if (component is Container) {
                    findAndDisposeEditors(component)
                }
            }
        }

        findAndDisposeEditors(chatPanel)
    }
}