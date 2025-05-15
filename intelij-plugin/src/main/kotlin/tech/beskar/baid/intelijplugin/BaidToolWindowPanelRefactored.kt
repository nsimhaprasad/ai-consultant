package tech.beskar.baid.intelijplugin

import com.intellij.icons.AllIcons
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.project.Project
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBPanel
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.components.JBTextField
import com.intellij.ui.components.panels.VerticalLayout
import com.intellij.util.ui.GraphicsUtil
import com.intellij.util.ui.JBUI
import com.intellij.util.ui.UIUtil
import tech.beskar.baid.intelijplugin.api.ConversationRepository
import tech.beskar.baid.intelijplugin.auth.GoogleAuthService
import tech.beskar.baid.intelijplugin.auth.LoginPanel
import tech.beskar.baid.intelijplugin.model.Message
import tech.beskar.baid.intelijplugin.ui.ChatController
import tech.beskar.baid.intelijplugin.util.FontUtil
import tech.beskar.baid.intelijplugin.util.getMessageWidth
import java.awt.*
import java.awt.event.MouseAdapter
import java.awt.event.MouseEvent
import java.awt.geom.Ellipse2D
import java.awt.image.BufferedImage
import java.net.URL
import javax.imageio.ImageIO
import javax.swing.*


class BaidToolWindowPanelRefactored(private val project: Project) : JBPanel<BaidToolWindowPanel>(BorderLayout()) {
    private val chatPanel = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(8)))
    private val chatScroll = JBScrollPane(chatPanel)
    private val inputField = JBTextField(30)
    private val consultButton = JButton()

    // Authentication and configuration
    private val authService = GoogleAuthService.getInstance()

    // Content panels
    private val contentPanel = JBPanel<JBPanel<*>>(CardLayout())
    private var loginPanel: LoginPanel
    private val mainPanel = JBPanel<JBPanel<*>>(BorderLayout())

    // User profile button
    private lateinit var userProfileButton: JButton

    // Session management
    private lateinit var newSessionButton: JButton

    // Past conversations
    private lateinit var pastConversationsButton: JButton
    private val pastConversationsPanel = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(8)))
    private val cardLayout = CardLayout()
    private val chatContainer = JBPanel<JBPanel<*>>()
    private var isShowingPastConversations = false

    // Chat controller for API calls
    private val chatController: ChatController
    private val maxWidth = getMessageWidth() + JBUI.scale(40) // Add some padding

    // Initialize the controller
    init {
        chatController = ChatController(
            project = project,
            onMessageReceived = { message ->
                appendMessage(message.content, message.isUser)
            },
            onThinkingMessageRemoved = {
                removeLastMessageIfThinking()
            },
            onAuthenticationRequired = {
                authService.signOut()
                showLoginPanel()
            },
            onSessionIdUpdated = { sessionId ->
                // No need to store session ID in this class anymore
                // It's managed by the SessionManager in the ChatController
            }
        )

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
        
        // Add maximum width constraint to prevent horizontal scrolling
        val maxWidth = getMessageWidth() + JBUI.scale(40) // Add some padding
        chatPanel.maximumSize = Dimension(maxWidth, Int.MAX_VALUE)

        // Add component listener to handle window resizing
        chatPanel.addComponentListener(object : java.awt.event.ComponentAdapter() {
            override fun componentResized(e: java.awt.event.ComponentEvent) {
                // Update message widths when the chat panel is resized
                updateAllMessageWidths()
            }
        })

        // Set up the scroll pane
        chatScroll.verticalScrollBar.unitIncrement = JBUI.scale(16)
        chatScroll.border = JBUI.Borders.empty()

        // Setup chat container with card layout to switch between chat and past conversations
        chatContainer.layout = cardLayout
        chatContainer.add(chatScroll, "chat")
        chatContainer.add(createPastConversationsPanel(), "pastConversations")

        // Create header panel with Baid branding and buttons
        val headerPanel = createHeaderPanel()

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
        val inputAreaPanel = createInputAreaPanel()

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

    private fun consultWithAPI(userPrompt: String) {
        // Disable input while processing
        inputField.isEnabled = false
        consultButton.isEnabled = false

        // Create a message panel for the response with "Thinking..." message
        val messagePanel = chatController.createMessagePanel(Message("Thinking...", isUser = false))

        // Add the thinking message panel
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

        // Send the prompt to the API via the controller
        chatController.sendPrompt(userPrompt, messagePanel)

        // Re-enable input
        SwingUtilities.invokeLater {
            inputField.isEnabled = true
            consultButton.isEnabled = true
            inputField.requestFocus()
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
        
        // Load conversations using the controller
        chatController.loadPastConversations(
            onSuccess = { conversations ->
                SwingUtilities.invokeLater {
                    pastConversationsPanel.removeAll()
                    
                    if (conversations.isEmpty()) {
                        pastConversationsPanel.add(JLabel("No past conversations found"))
                    } else {
                        displaySessionsList(conversations)
                    }
                    
                    pastConversationsPanel.revalidate()
                    pastConversationsPanel.repaint()
                }
            },
            onError = { error ->
                SwingUtilities.invokeLater {
                    pastConversationsPanel.removeAll()
                    pastConversationsPanel.add(JLabel("Error loading conversations: ${error.message}"))
                    pastConversationsPanel.revalidate()
                    pastConversationsPanel.repaint()
                }
            }
        )
    }

    private fun displaySessionsList(conversations: List<ConversationRepository.Conversation>) {
        // Add title
        val titleLabel = JLabel("Select a conversation to continue", SwingConstants.LEFT).apply {
            font = FontUtil.getSubTitleFont()
            foreground = JBColor.foreground().darker()
            border = JBUI.Borders.empty(JBUI.scale(8), JBUI.scale(16))
        }
        pastConversationsPanel.add(titleLabel)
        
        // Add each session as a clickable panel
        for (conversation in conversations) {
            val sessionId = conversation.sessionId
            val lastUsed = conversation.lastUsedAt
            val previewText = conversation.previewText ?: "Empty conversation"
            
            // Format the date
            val dateString = try {
                val formatter = java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
                val date = formatter.parse(lastUsed)
                val displayFormat = java.text.SimpleDateFormat("MM/dd/yyyy h:mm a")
                displayFormat.format(date)
            } catch (e: Exception) {
                println("Error formatting date: ${e.message}")
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
                
                // Set width constraints
                maximumSize = Dimension(maxWidth, Int.MAX_VALUE)
                preferredSize = Dimension(maxWidth, preferredSize.height)
                
                // Add preview text with HTML wrapping
                val preview = JLabel("<html><div style='width:${maxWidth - JBUI.scale(30)}px;'>$previewText</div></html>").apply {
                    foreground = JBColor.foreground()
                }
                add(preview, BorderLayout.CENTER)
                
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
                        loadConversation(sessionId)
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

    private fun loadConversation(sessionId: String) {
        // Close past conversations panel and return to chat
        isShowingPastConversations = false
        cardLayout.show(chatContainer, "chat")
        pastConversationsButton.icon = AllIcons.General.ArrowRight
        pastConversationsButton.toolTipText = "Past conversations"
        
        // Clear current chat
        clearChat()
        
        // Show loading message
        appendMessage("Loading conversation history...", isUser = false)
        
        // Load conversation using the controller
        chatController.loadConversation(
            sessionId = sessionId,
            onSuccess = { messages ->
                SwingUtilities.invokeLater {
                    // Remove loading indicator
                    removeLastMessageIfThinking()
                    
                    // Add all message panels in order
                    for (message in messages) {
                        val panel = chatController.createMessagePanel(message)
                        chatPanel.add(panel)
                    }
                    
                    // Add a separator to indicate where new messages will start
                    val separatorMessage = Message(
                        "Continuing this conversation. Any new messages will be part of this session.",
                        isUser = false
                    )
                    val separatorPanel = chatController.createMessagePanel(separatorMessage)
                    chatPanel.add(separatorPanel)
                    
                    // Revalidate and repaint the chat panel
                    chatPanel.revalidate()
                    chatPanel.repaint()
                    
                    // Scroll to bottom
                    SwingUtilities.invokeLater {
                        val vertical = chatScroll.verticalScrollBar
                        vertical.value = vertical.maximum
                    }
                }
            },
            onError = { error ->
                SwingUtilities.invokeLater {
                    removeLastMessageIfThinking()
                    appendMessage("Error loading conversation: ${error.message}", isUser = false)
                }
            }
        )
    }

    private fun checkAuthenticationStatus() {
        chatController.checkAuthentication { isAuthenticated ->
            try {
                val userInfo = if (isAuthenticated) authService.getUserInfo() else null
                
                SwingUtilities.invokeLater {
                    if (isAuthenticated) {
                        showMainPanel()
                        updateUserProfileButton()
                        // Add welcome message
                        // Only show welcome message if this is the first time loading
                        // (not when switching between panels)
                        if (chatPanel.componentCount == 0) {
                            if (userInfo != null) {
                                appendMessage("Welcome back, ${userInfo.name}! How can I help you today?", isUser = false)
                            } else {
                                appendMessage("Hello! I'm Baid, your AI assistant. How can I help you today?", isUser = false)
                            }
                        }
                    } else {
                        // Show login panel
                        showLoginPanel()
                        updateUserProfileButton()
                    }
                }
            } catch (e: Exception) {
                println("Error checking authentication status: ${e.message}")
                SwingUtilities.invokeLater {
                    // Show login panel on error
                    showLoginPanel()
                    updateUserProfileButton()
                }
            }
        }
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

    private fun createPastConversationsPanel(): JComponent {
        // Apply width constraints to the conversations panel
        pastConversationsPanel.maximumSize = Dimension(maxWidth, Int.MAX_VALUE)
        
        val scrollPane = JBScrollPane(pastConversationsPanel)
        scrollPane.border = JBUI.Borders.empty()
        scrollPane.verticalScrollBar.unitIncrement = JBUI.scale(16)
        scrollPane.maximumSize = Dimension(maxWidth, Int.MAX_VALUE)

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
        
        // Apply consistent width constraints
        container.maximumSize = Dimension(maxWidth, Int.MAX_VALUE)
        container.preferredSize = Dimension(maxWidth, container.preferredSize.height)

        return container
    }

    private fun createHeaderPanel(): JPanel {
        return JBPanel<JBPanel<*>>(BorderLayout()).apply {
            background = JBColor.background()
            border = JBUI.Borders.empty(JBUI.scale(16), JBUI.scale(16), JBUI.scale(8), JBUI.scale(16))
            
            // Add maximum width constraint to prevent horizontal scrolling
            maximumSize = Dimension(maxWidth, Int.MAX_VALUE)
            preferredSize = Dimension(maxWidth, preferredSize.height)
            
            // Add Baid title
            val titleLabel = JLabel("Baid").apply {
                font = FontUtil.getTitleFont()
                foreground = JBColor.foreground()
            }

            // Add subtitle
            val subtitleLabel = JLabel("<html><div style='width:${maxWidth - JBUI.scale(120)}px;'>Transform ideas into outcomes, instantly</div></html>").apply {
                font = FontUtil.getSubTitleFont()
                foreground = JBColor.foreground().darker()
                // Set preferred and maximum width to prevent horizontal scrolling
                preferredSize = Dimension(maxWidth - JBUI.scale(120), preferredSize.height)
                maximumSize = Dimension(maxWidth - JBUI.scale(120), preferredSize.height)
            }

            val titleContainer = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(4))).apply {
                isOpaque = false
                add(titleLabel)
                add(subtitleLabel)
                // Set maximum width to prevent horizontal scrolling
                maximumSize = Dimension(maxWidth - JBUI.scale(100), Int.MAX_VALUE)
                preferredSize = Dimension(maxWidth - JBUI.scale(100), preferredSize.height)
            }

            // Add new session (+) button and past conversations button to header
            newSessionButton = JButton(AllIcons.General.Add).apply {
                toolTipText = "Start new session"
                isContentAreaFilled = false
                isBorderPainted = false
                preferredSize = Dimension(JBUI.scale(32), JBUI.scale(32))
                addActionListener {
                    chatController.startNewConversation()
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
    }

    private fun createInputAreaPanel(): JPanel {
        return JBPanel<JBPanel<*>>(null).apply {
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

                            // Create a CircularAvatarLabel instance for the profile avatar
                            var avatarLabel = JLabel(userInfo.name.firstOrNull()?.toString() ?: "U").apply {
                                font = Font(Font.SANS_SERIF, Font.BOLD, 14)
                                foreground = JBColor.WHITE
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

                            if (userInfo.picture != null) {
                                avatarLabel =
                                    CircularAvatarLabel(userInfo.name.firstOrNull()?.toString() ?: "U").apply {
                                        font = Font(Font.SANS_SERIF, Font.BOLD, 14)
                                        foreground = JBColor.WHITE
                                        background = JBColor(Color(56, 114, 159), Color(56, 114, 159))
                                        isOpaque = true
                                        horizontalAlignment = SwingConstants.CENTER
                                        verticalAlignment = SwingConstants.CENTER
                                        preferredSize = Dimension(24, 24)
                                        border = BorderFactory.createEmptyBorder()

                                        // Load profile image in background thread
                                        ApplicationManager.getApplication().executeOnPooledThread {
                                            val profileIcon = loadProfileImage(userInfo.picture, 24)
                                            if (profileIcon != null) {
                                                // Update UI on EDT
                                                SwingUtilities.invokeLater {
                                                    text = "" // Clear the text (initial letter)
                                                    icon = profileIcon
                                                    // Keep isOpaque true for proper clipping
                                                    repaint()
                                                }
                                            }
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
                        userProfileButton.text = ""
                        userProfileButton.icon = null
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
        chatController.startNewConversation()

        // Show the login panel
        layout.show(contentPanel, "login")
    }

    private fun showMainPanel() {
        val layout = contentPanel.layout as CardLayout
        layout.show(contentPanel, "main")
    }

    fun appendMessage(message: String, isUser: Boolean) {
        // Create message panel using the controller
        val messagePanel = chatController.createMessagePanel(Message(message, isUser))

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

    private fun removeLastMessageIfThinking() {
        if (chatPanel.componentCount > 0) {
            val lastMessage = chatPanel.getComponent(chatPanel.componentCount - 1)
            if (lastMessage is JBPanel<*> && lastMessage.border == JBUI.Borders.empty(JBUI.scale(4), JBUI.scale(16))) {
                // Navigate through the panel structure to find the text area
                try {
                    val contentPanel = lastMessage.getComponent(0) as JBPanel<*>
                    val bubbleContainer = contentPanel.getComponent(1) as JBPanel<*>
                    val messageText = bubbleContainer.getComponent(0) as JTextPane
                    if (messageText.text.contains("Thinking...")) {
                        chatPanel.remove(lastMessage)
                        chatPanel.revalidate()
                        chatPanel.repaint()
                    }
                } catch (e: Exception) {
                    println("Error removing last message: ${e.message}")
                    // If structure doesn't match, ignore
                }
            }
        }
    }

    private fun clearChat() {
        SwingUtilities.invokeLater {
            chatPanel.removeAll()
            chatPanel.revalidate()
            chatPanel.repaint()
        }
    }

    private fun updateAllMessageWidths() {
        // Only proceed if there are messages
        if (chatPanel.componentCount == 0) return

        // Get the new width
        val newWidth = getMessageWidth()

        // Update each message bubble
        for (i in 0 until chatPanel.componentCount) {
            try {
                val messagePanel = chatPanel.getComponent(i) as? JBPanel<*> ?: continue
                val contentPanel = messagePanel.getComponent(0) as? JBPanel<*> ?: continue

                // Handle both user and AI messages
                if (contentPanel.layout is FlowLayout) {
                    // User message with FlowLayout
                    for (j in 0 until contentPanel.componentCount) {
                        val component = contentPanel.getComponent(j)
                        if (component is JBPanel<*>) {
                            updateBubbleWidth(component, newWidth)
                        }
                    }
                } else if (contentPanel.layout is BorderLayout) {
                    // AI message with BorderLayout
                    val bubbleContainer = contentPanel.getComponent(1) as? JBPanel<*> ?: continue
                    updateBubbleWidth(bubbleContainer, newWidth)
                }
            } catch (e: Exception) {
                // Skip this message if there's an error
                println("Error updating message width: ${e.message}")
            }
        }

        // Revalidate and repaint the chat panel
        chatPanel.revalidate()
        chatPanel.repaint()
    }

    private fun updateBubbleWidth(bubbleContainer: JBPanel<*>, newWidth: Int) {
        try {
            val messageText = bubbleContainer.getComponent(0) as? JTextPane ?: return

            // Update the HTML content with new width
            val currentText = messageText.text
            val updatedText = currentText.replace(
                Regex("width: \\d+px; max-width: \\d+px;"),
                "width: ${newWidth}px; max-width: ${newWidth}px;"
            )

            // Only update if the text actually changed
            if (currentText != updatedText) {
                messageText.text = updatedText
            }
        } catch (e: Exception) {
            println("Error updating bubble width: ${e.message}")
        }
    }

    private fun loadProfileImage(imageUrl: String, size: Int): ImageIcon? {
        return try {
            // Download the image from URL
            val url = URL(imageUrl)
            val originalImage = ImageIO.read(url) ?: return null

            // Create a clean circular image with transparency
            val outputImage = UIUtil.createImage(size, size, BufferedImage.TYPE_INT_ARGB)
            val g2d = outputImage.createGraphics()

            try {
                // Configure for high quality
                g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
                g2d.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC)

                // Scale the image preserving aspect ratio
                val scaledImage = originalImage.getScaledInstance(size, size, Image.SCALE_SMOOTH)

                // Create circular mask
                val circle = Ellipse2D.Float(0f, 0f, size.toFloat(), size.toFloat())
                g2d.clip = circle

                // Draw the image centered in the circle
                g2d.drawImage(scaledImage, 0, 0, null)
            } finally {
                g2d.dispose() // Always clean up graphics context
            }

            // Return as an ImageIcon
            ImageIcon(outputImage)
        } catch (e: Exception) {
            println("Error loading profile image: ${e.message}")
            null
        }
    }

    private inner class CircularAvatarLabel(text: String) : JLabel(text) {
        init {
            horizontalAlignment = CENTER
            verticalAlignment = CENTER
            isOpaque = false
        }

        override fun paintComponent(g: Graphics) {
            val config = GraphicsUtil.setupAAPainting(g)
            val g2d = g as Graphics2D

            // Don't fill the background at all - make it fully transparent
            if (icon == null) {
                // For text avatar
                g2d.color = background
                g2d.fillOval(0, 0, width, height)
                super.paintComponent(g)
            } else {
                // For image avatar
                val circle = Ellipse2D.Float(0f, 0f, width.toFloat(), height.toFloat())
                g2d.clip = circle

                // Center the icon
                val iconWidth = icon.iconWidth
                val iconHeight = icon.iconHeight
                val x = (width - iconWidth) / 2
                val y = (height - iconHeight) / 2

                icon.paintIcon(this, g2d, x, y)
            }

            config.restore()
        }

        // Override isOpaque to ensure transparency
        override fun isOpaque(): Boolean {
            return false
        }
    }
}
