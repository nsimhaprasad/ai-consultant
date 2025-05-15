package tech.beskar.baid.intelijplugin

import com.intellij.icons.AllIcons
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.project.Project
import com.intellij.openapi.util.IconLoader
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBPanel
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.components.JBTextField
import com.intellij.ui.components.panels.VerticalLayout
import com.intellij.util.io.HttpRequests
import com.intellij.util.ui.GraphicsUtil
import com.intellij.util.ui.JBUI
import org.json.JSONArray
import org.json.JSONObject
import tech.beskar.baid.intelijplugin.auth.GoogleAuthService
import tech.beskar.baid.intelijplugin.auth.LoginPanel
import tech.beskar.baid.intelijplugin.config.BaidConfiguration
import tech.beskar.baid.intelijplugin.model.Block
import tech.beskar.baid.intelijplugin.model.ContentParser
import tech.beskar.baid.intelijplugin.model.ContentResponse
import tech.beskar.baid.intelijplugin.ui.ContentRenderer
import tech.beskar.baid.intelijplugin.ui.MessageFormatter
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

class BaidToolWindowPanel(private val project: Project) : JBPanel<BaidToolWindowPanel>(BorderLayout()) {
    // Update all message bubbles when window is resized
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

    // Update a single bubble's width
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
    private var userProfileButton: JButton

    // SESSION MANAGEMENT
    private var currentSessionId: String? = null
    private var newSessionButton: JButton

    // PAST CONVERSATIONS
    private var pastConversationsButton: JButton
    private val pastConversationsPanel = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(8)))
    private val cardLayout = CardLayout()
    private val chatContainer = JBPanel<JBPanel<*>>()
    private var isShowingPastConversations = false

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

    private fun createMessagePanel(content: String, isUser: Boolean): JBPanel<JBPanel<*>> {
        // Create message panel with WhatsApp-like layout
        val messagePanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            background = JBColor.background()
            border = JBUI.Borders.empty(JBUI.scale(4), JBUI.scale(16))
        }

        if (isUser) {
            // For user messages, use the simple text formatting
            // Create message bubble container
            val bubbleContainer = JBPanel<JBPanel<*>>(BorderLayout()).apply {
                background = JBColor(Color(220, 248, 198), Color(54, 93, 69)) // Light green for user
                border = JBUI.Borders.empty(JBUI.scale(8), JBUI.scale(12))
            }

            // Create message text area
            val messageText = JTextPane().apply {
                contentType = "text/html"
                // Use MessageFormatter to process the message and extract code blocks
                val messageWidth = getMessageWidth()
                val (htmlContent, codeBlocks) = MessageFormatter.processMessage(content, messageWidth)
                text = htmlContent
                font = FontUtil.getBodyFont()
                isEditable = false
                isOpaque = false
                background = Color(0, 0, 0, 0) // Transparent
                foreground = Color.BLACK
                border = JBUI.Borders.empty()
                maximumSize = Dimension(JBUI.scale(400), Int.MAX_VALUE)
            }

            // Add message text to bubble
            bubbleContainer.add(messageText, BorderLayout.CENTER)

            // Create message with avatar container (user message: right-aligned with avatar on right)
            val contentPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
                isOpaque = false
                layout = FlowLayout(FlowLayout.RIGHT, 0, 0)
                
                // First add the bubble
                add(bubbleContainer)
                
                var avatarLabel = JLabel().apply {
                    icon = IconLoader.getIcon("/icons/beskar.svg", BaidToolWindowPanel::class.java)
                    border = JBUI.Borders.emptyRight(JBUI.scale(8))
                    verticalAlignment = JLabel.TOP
                }
                
                val userInfo = authService.getUserInfo()

                // Then add the avatar with profile picture if available
                if (userInfo?.picture != null) {
                    avatarLabel = CircularAvatarLabel("").apply {
                        // Default icon in case profile picture can't be loaded
                        preferredSize = Dimension(24, 24)
                        border = JBUI.Borders.emptyLeft(JBUI.scale(8))
                        verticalAlignment = JLabel.TOP

                        // Try to get user info and profile picture
                        // Load profile image asynchronously to prevent UI freezes
                        ApplicationManager.getApplication().executeOnPooledThread {
                            val profileIcon = loadProfileImage(userInfo.picture, 24)
                            if (profileIcon != null) {
                                // Update UI on EDT
                                ApplicationManager.getApplication().invokeLater {
                                    icon = profileIcon
                                }
                            }
                        }
                    }
                }
                add(avatarLabel)
            }

            messagePanel.add(contentPanel, BorderLayout.CENTER)
        } else {
            // For agent messages, try to parse JSON blocks if possible
            try {
                // Check if the message is in JSON format with blocks
                if (content.trim().startsWith("{")) {
                    // Create agent message with WhatsApp-like layout
                    val bubbleContainer = JBPanel<JBPanel<*>>(VerticalLayout(8)).apply {
                        background = JBColor(Color(255, 255, 255), Color(60, 63, 65))
                        border = JBUI.Borders.empty(JBUI.scale(8), JBUI.scale(12))
                    }

                    // Create message with avatar container for agent response
                    val contentPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
                        isOpaque = false
                    }

                    val avatarLabel = JLabel().apply {
                        icon = IconLoader.getIcon("/icons/beskar.svg", BaidToolWindowPanel::class.java)
                        border = JBUI.Borders.emptyRight(JBUI.scale(8))
                        verticalAlignment = JLabel.TOP
                    }

                    contentPanel.add(avatarLabel, BorderLayout.WEST)
                    contentPanel.add(bubbleContainer, BorderLayout.CENTER)

                    // Add padding on the right
                    val spacer = JPanel().apply {
                        isOpaque = false
                        preferredSize = Dimension(JBUI.scale(100), 0)
                    }
                    contentPanel.add(spacer, BorderLayout.EAST)
                    messagePanel.add(contentPanel, BorderLayout.CENTER)

                    // Parse and render the blocks
                    try {
                        val jsonObj = JSONObject(content)
                        var response: ContentResponse? = null

                        // Check for JetBrains LLM response format
                        if (jsonObj.has("schema") && jsonObj.getString("schema") == "jetbrains-llm-response") {
                            println("Found JetBrains LLM response format")
                            // Parse using the JetBrains response format parser
                            response = ContentParser.parseJetbrainsResponse(content)
                        } else if (jsonObj.has("blocks")) {
                            // Standard blocks format
                            response = ContentParser.parseResponse(content)
                        } else {
                            // Try to parse as a single block
                            val block = ContentParser.parseBlock(jsonObj)
                            val comp = when (block) {
                                is Block.Paragraph -> ContentRenderer.renderParagraph(block)
                                is Block.Code -> ContentRenderer.renderCode(block)
                                is Block.Command -> ContentRenderer.renderCommand(block)
                                is Block.ListBlock -> ContentRenderer.renderList(block)
                                is Block.Heading -> ContentRenderer.renderHeading(block)
                                else -> null
                            }
                            comp?.let {
                                bubbleContainer.add(it)
                            }
                        }

                        // Render all blocks if we have a response with blocks
                        response?.blocks?.forEach { block ->
                            println("Rendering block: $block")
                            val comp = when (block) {
                                is Block.Paragraph -> ContentRenderer.renderParagraph(block)
                                is Block.Code -> ContentRenderer.renderCode(block)
                                is Block.Command -> ContentRenderer.renderCommand(block)
                                is Block.ListBlock -> ContentRenderer.renderList(block)
                                is Block.Heading -> ContentRenderer.renderHeading(block)
                                is Block.Callout -> ContentRenderer.renderCallout(block)
                            }
                            comp.let {
                                bubbleContainer.add(it)
                            }
                        }

                        return messagePanel
                    } catch (e: Exception) {
                        println("Error parsing JSON blocks: ${e.message}")
                        // If JSON parsing fails, fall back to simple message
                        return createSimpleMessagePanel(content, isUser)
                    }
                } else {
                    // Not JSON format, create simple message panel
                    return createSimpleMessagePanel(content, isUser)
                }
            } catch (e: Exception) {
                println("Error creating message panel: ${e.message}")
                // In case of any error, fallback to simple message panel
                return createSimpleMessagePanel(content, isUser)
            }
        }

        return messagePanel
    }

    /**
     * Creates a simple message panel for non-JSON content
     */
    private fun createSimpleMessagePanel(content: String, isUser: Boolean): JBPanel<JBPanel<*>> {
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

        // Create message text area
        val messageText = JTextPane().apply {
            contentType = "text/html"
            // Use MessageFormatter to process the message and extract code blocks
            val messageWidth = getMessageWidth()
            val (htmlContent, codeBlocks) = MessageFormatter.processMessage(content, messageWidth)
            text = htmlContent
            font = FontUtil.getBodyFont()
            isEditable = false
            isOpaque = false
            background = Color(0, 0, 0, 0) // Transparent
            foreground = if (isUser) Color.BLACK else JBColor.foreground()
            border = JBUI.Borders.empty()
            maximumSize = Dimension(JBUI.scale(400), Int.MAX_VALUE)
        }

        // Add message text to bubble
        bubbleContainer.add(messageText, BorderLayout.CENTER)

        // Create message with avatar container
        val contentPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            isOpaque = false

            if (isUser) {
                // User message: right-aligned with avatar on right
                layout = FlowLayout(FlowLayout.RIGHT, 0, 0)
                add(bubbleContainer)
                add(CircularAvatarLabel("").apply {
                    preferredSize = Dimension(24, 24)
                    border = JBUI.Borders.emptyLeft(JBUI.scale(8))
                    verticalAlignment = JLabel.TOP
                })
            } else {
                // Agent message: avatar on left, bubble on right
                val avatarLabel = JLabel().apply {
                    icon = IconLoader.getIcon("/icons/beskar.svg", BaidToolWindowPanel::class.java)
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
        return messagePanel
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

                // Create a list to hold all message panels in order
                val messagePanels = mutableListOf<JBPanel<JBPanel<*>>>()
                
                // Process all messages first and create panels
                for (i in 0 until messagesArray.length()) {
                    val message = messagesArray.getJSONObject(i)
                    val role = message.getString("role")
                    val content = message.getString("message")
                    val isUser = role == "user"
                    println("Processing message: role=$role, isUser=$isUser")
                    
                    // Create panel for this message
                    val panel = createMessagePanel(content, isUser)
                    messagePanels.add(panel)
                }
                
                // Remove loading message and add all panels in the correct order
                SwingUtilities.invokeLater {
                    // Remove loading indicator
                    removeLastMessageIfThinking()
                    
                    // Add all message panels in order
                    for (panel in messagePanels) {
                        chatPanel.add(panel)
                    }
                    
                    // Add a separator to indicate where new messages will start
                    val separatorPanel = createSimpleMessagePanel(
                        "Continuing this conversation. Any new messages will be part of this session.",
                        isUser = false
                    )
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
            } catch (e: Exception) {
                SwingUtilities.invokeLater {
                    removeLastMessageIfThinking()
                    appendMessage("Error loading conversation: ${e.message}", isUser = false)
                }
            }
        }
    }

    private fun loadProfileImage(imageUrl: String, size: Int): ImageIcon? {
        return try {
            // Download the image from URL
            val url = URL(imageUrl)
            val originalImage = ImageIO.read(url) ?: return null

            // Create a clean circular image with transparency
            val outputImage = BufferedImage(size, size, BufferedImage.TYPE_INT_ARGB)
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

                            if (userInfo.picture != null) {
                                avatarLabel =
                                    CircularAvatarLabel(userInfo.name.firstOrNull()?.toString() ?: "U").apply {
                                        font = Font(Font.SANS_SERIF, Font.BOLD, 14)
                                        foreground = Color.WHITE
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
        // Create message panel using our helper method
        val messagePanel = createMessagePanel(message, isUser)

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
        println("Starting API request with sessionId: $sessionId")

        inputField.isEnabled = false
        consultButton.isEnabled = false

        // Get the currently open file from the editor
        val fileEditorManager = com.intellij.openapi.fileEditor.FileEditorManager.getInstance(project)
        val editor = fileEditorManager.selectedTextEditor
        val document = editor?.document
        val virtualFile = fileEditorManager.selectedFiles.firstOrNull()

        // Get file content and metadata
        val fileText = document?.text ?: "No file open."
        val filePath = virtualFile?.path ?: "No file path available"
        val fileName = virtualFile?.name ?: "No file name available"

        // Show thinking message
        appendMessage("Thinking...", isUser = false)
        val apiUrl = "${config.backendUrl}${config.apiEndpoint}"

        // Create context JSONObject first
        val contextJson = JSONObject()
        contextJson.put("file_content", fileText)
        contextJson.put("file_path", filePath)
        contextJson.put("file_name", fileName)
        contextJson.put("is_open", document != null)

        // Create main payload JSONObject
        val payload = JSONObject()
        payload.put("prompt", userPrompt)
        payload.put("context", contextJson)

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
                                val bubbleContainer = JBPanel<JBPanel<*>>(VerticalLayout(8)).apply {
                                    background = JBColor(Color(255, 255, 255), Color(60, 63, 65))
                                    border = JBUI.Borders.empty(JBUI.scale(8), JBUI.scale(12))
                                }

                                // Initialize empty container for structured content blocks
                                val contentPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
                                    isOpaque = false
                                }

                                // Create message with avatar container for agent response
                                val avatarLabel = JLabel().apply {
                                    icon = IconLoader.getIcon("/icons/beskar.svg", BaidToolWindowPanel::class.java)
                                    border = JBUI.Borders.emptyRight(JBUI.scale(8))
                                    verticalAlignment = JLabel.TOP
                                }
                                contentPanel.add(avatarLabel, BorderLayout.WEST)
                                contentPanel.add(bubbleContainer, BorderLayout.CENTER)

                                // Add padding on the right
                                val spacer = JPanel().apply {
                                    isOpaque = false
                                    preferredSize = Dimension(JBUI.scale(100), 0)
                                }
                                contentPanel.add(spacer, BorderLayout.EAST)

                                messagePanel.add(contentPanel, BorderLayout.CENTER)

                                // Add the message panel to chat
                                SwingUtilities.invokeLater {
                                    chatPanel.add(messagePanel)
                                    chatPanel.revalidate()
                                    chatPanel.repaint()
                                }

                                request.inputStream.bufferedReader().use { reader ->
                                    while (true) {
                                        val rawLine = reader.readLine() ?: break
                                        lineCount++
                                        println("[STREAM] line: $rawLine")
                                        if (!rawLine.startsWith("data: ")) continue
                                        val data = rawLine.substringAfter("data: ").trim()
                                        println("[STREAM] data: $data")
                                        if (data == "[DONE]") break

                                        // Accumulate JSON block, handling multi-line objects
                                        val sb = StringBuilder().append(data)
                                        var braceCount = data.count { it == '{' } - data.count { it == '}' }
                                        while (braceCount > 0) {
                                            val nextLine = reader.readLine() ?: break
                                            println("[STREAM] continuation: $nextLine")
                                            sb.append(nextLine)
                                            braceCount += nextLine.count { it == '{' } - nextLine.count { it == '}' }
                                        }
                                        val jsonStr = sb.toString()
                                        println("[STREAM] complete JSON: $jsonStr")

                                        // Parse and render the block
                                        try {
                                            val jsonObj = JSONObject(jsonStr)
                                            if (jsonObj.has("session_id")) {
                                                updatedSessionId = jsonObj.optString("session_id", "")
                                                break
                                            }
                                            if (jsonObj.has("blocks")) {
                                                val response = ContentParser.parseResponse(jsonStr)
                                                response.blocks.forEach { block ->
                                                    println("[STREAM] parsed block: $block")
                                                    val comp = when (block) {
                                                        is Block.Paragraph -> ContentRenderer.renderParagraph(block)
                                                        is Block.Code -> ContentRenderer.renderCode(block)
                                                        is Block.Command -> ContentRenderer.renderCommand(block)
                                                        is Block.ListBlock -> ContentRenderer.renderList(block)
                                                        is Block.Heading -> ContentRenderer.renderHeading(block)
                                                        is Block.Callout -> ContentRenderer.renderCallout(block)
                                                    }
                                                    comp.let {
                                                        SwingUtilities.invokeLater {
                                                            bubbleContainer.add(it)
                                                            messagePanel.revalidate()
                                                            messagePanel.repaint()
                                                        }
                                                    }
                                                }
                                            } else {
                                                val block = ContentParser.parseBlock(jsonObj)
                                                val comp = when (block) {
                                                    is Block.Paragraph -> ContentRenderer.renderParagraph(block)
                                                    is Block.Code -> ContentRenderer.renderCode(block)
                                                    is Block.Command -> ContentRenderer.renderCommand(block)
                                                    is Block.ListBlock -> ContentRenderer.renderList(block)
                                                    is Block.Heading -> ContentRenderer.renderHeading(block)
                                                    else -> null
                                                }
                                                comp?.let {
                                                    SwingUtilities.invokeLater {
                                                        bubbleContainer.add(it)
                                                        messagePanel.revalidate()
                                                        messagePanel.repaint()
                                                    }
                                                }
                                            }
                                        } catch (e: Exception) {
                                            println("Error parsing block: $e")
                                            val comp =
                                                ContentRenderer.renderParagraph(Block.Paragraph("Something went wrong! Please try again"))
                                            SwingUtilities.invokeLater {
                                                bubbleContainer.add(comp)
                                                messagePanel.revalidate()
                                                messagePanel.repaint()
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
                    // If structure doesn't match, ignore
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