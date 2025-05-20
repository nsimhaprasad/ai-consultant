package tech.beskar.baid.intelijplugin.ui.toolwindow

import com.intellij.icons.AllIcons
import com.intellij.openapi.project.Project
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBPanel
import tech.beskar.baid.intelijplugin.controller.APIController
import tech.beskar.baid.intelijplugin.controller.IAuthController
import tech.beskar.baid.intelijplugin.controller.ISessionController
import tech.beskar.baid.intelijplugin.model.common.Email
import com.intellij.ui.components.JBTextField
import com.intellij.util.ui.JBUI
import tech.beskar.baid.intelijplugin.model.ChatSession
import tech.beskar.baid.intelijplugin.model.UserProfile
import tech.beskar.baid.intelijplugin.views.ChatPanelView
import tech.beskar.baid.intelijplugin.views.CircularAvatarLabel
import tech.beskar.baid.intelijplugin.views.LoginPanelView
import tech.beskar.baid.intelijplugin.views.PastConversationsView
import java.awt.*
import java.awt.event.*
import javax.swing.*

import tech.beskar.baid.intelijplugin.model.SessionPreview

interface BaidToolWindowActions {
    fun sendMessage(prompt: String)
    fun startNewSession()
    fun togglePastConversations()
    fun selectSession(sessionPreview: SessionPreview)
    fun loginSuccess(userProfile: UserProfile)
    fun loginError(error: Throwable)
    fun signOut()
    fun showUserProfileMenu()
    fun initialAuthCheck()
}

class BaidToolWindowView(
    private val project: Project,
    private val authController: IAuthController,
    private val apiController: APIController, // Kept for LoginPanelView for now, or if other direct uses exist
    private val sessionController: ISessionController
) : JBPanel<BaidToolWindowView>(BorderLayout()) {

    lateinit var actions: BaidToolWindowActions

    // UI Components
    private val cardLayout: CardLayout = CardLayout()
    val contentPanel: JBPanel<JBPanel<*>?> = JBPanel<JBPanel<*>?>(cardLayout) // Panel made public for BaidToolWindowPanelMVC to add
    private val loginPanel: LoginPanelView
    private val mainPanel: JBPanel<JBPanel<*>?>(BorderLayout())
    private val chatPanel: ChatPanelView
    private val pastConversationsView: PastConversationsView
    private val inputField: JBTextField = JBTextField(30)
    private val sendButton: JButton
    private val newSessionButton: JButton
    private val pastConversationsButton: JButton
    private val userProfileButton: JButton

    private var isShowingPastConversations = false // This state might be better managed by the controller

    init {
        this.loginPanel = LoginPanelView(project, authController, { userProfile -> actions.loginSuccess(userProfile) }, { e -> actions.loginError(e) })
        this.chatPanel = ChatPanelView(project)
        this.pastConversationsView = PastConversationsView(project, sessionController) { sessionPreview -> actions.selectSession(sessionPreview) }

        // Initialize buttons after other components
        this.sendButton = createStyledButton("Send", isFocusPainted = false)
        this.newSessionButton = createStyledButton(icon = AllIcons.General.Add, tooltip = "Start new session")
        this.pastConversationsButton = createStyledButton(icon = AllIcons.General.ArrowRight, tooltip = "Past conversations")
        this.userProfileButton = createStyledButton(horizontalAlignment = SwingConstants.LEFT)
        
        val buttonSize = Dimension(JBUI.scale(24), JBUI.scale(24))
        this.pastConversationsButton.preferredSize = buttonSize
        this.newSessionButton.preferredSize = buttonSize


        initializeUI()
        initializeListeners()
        // The controller calls initialAuthCheck after the view is fully initialized.
    }
    
    private fun createStyledButton(text: String? = null, icon: Icon? = null, tooltip: String? = null, isFocusPainted: Boolean = false, horizontalAlignment: Int = JButton.CENTER): JButton {
        return JButton(text, icon).apply {
            toolTipText = tooltip
            isContentAreaFilled = false
            isBorderPainted = false
            this.isFocusPainted = isFocusPainted
            this.horizontalAlignment = horizontalAlignment
        }
    }

    private fun initializeUI() {
        contentPanel.add(loginPanel, "login")
        setupMainPanel()
        contentPanel.add(mainPanel, "main")
    }

    private fun setupMainPanel() {
        mainPanel.add(createHeaderPanel(), BorderLayout.NORTH) // Use create method directly
        
        val chatCardLayout = CardLayout()
        val chatContainer = JBPanel<JBPanel<*>?>(chatCardLayout).apply {
            add(chatPanel, "chat")
            add(pastConversationsView, "pastConversations")
        }
        mainPanel.add(chatContainer, BorderLayout.CENTER)
        mainPanel.add(createInputPanel(), BorderLayout.SOUTH) // Use create method directly

        pastConversationsButton.addActionListener { actions.togglePastConversations() }
    }

    private fun createHeaderPanel(): JBPanel<JBPanel<*>> { // Return type changed
        val headerPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            border = JBUI.Borders.empty(JBUI.scale(16), JBUI.scale(16), JBUI.scale(8), JBUI.scale(16))
        }

        val titleLabel = JLabel("Baid").apply {
            font = Font(this.font.name, Font.BOLD, JBUI.scale(18))
        }

        val subtitleLabel = JLabel("Transform ideas into outcomes, instantly").apply {
            font = Font(this.font.name, Font.PLAIN, JBUI.scale(12))
            foreground = UIManager.getColor("Label.disabledForeground")
        }

        val titleContainer = JBPanel<JBPanel<*>>(BorderLayout(0, JBUI.scale(4))).apply {
            isOpaque = false
            add(titleLabel, BorderLayout.NORTH)
            add(subtitleLabel, BorderLayout.CENTER)
        }
        
        val buttonsPanel = JBPanel<JBPanel<*>>(FlowLayout(FlowLayout.RIGHT, 0, 0)).apply {
            isOpaque = false
            add(pastConversationsButton)
            add(newSessionButton)
        }
        
        val topActionsPanel = JPanel(FlowLayout(FlowLayout.RIGHT, 0,0)).apply {
            isOpaque = false
            add(buttonsPanel)
        }

        headerPanel.add(titleContainer, BorderLayout.WEST)
        headerPanel.add(topActionsPanel, BorderLayout.EAST)
        return headerPanel
    }

    private fun createInputPanel(): JBPanel<JBPanel<*>> { // Return type changed
        val inputPanel = JBPanel<JBPanel<*>>(null).apply {
            border = JBUI.Borders.empty(0, JBUI.scale(16), JBUI.scale(8), JBUI.scale(16))
            preferredSize = Dimension(0, JBUI.scale(110))
        }

        inputField.apply {
            border = JBUI.Borders.empty(JBUI.scale(12))
            emptyText.text = "Type your task here, press Enter to send prompt"
        }

        val inputContainer = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            // bounds are set by componentResized listener
            add(inputField, BorderLayout.CENTER)
            add(sendButton, BorderLayout.EAST)
        }
        
        // userProfileButton bounds are set by componentResized listener
        // userProfileButton itself is already styled by createStyledButton

        inputPanel.addComponentListener(object : ComponentAdapter() {
            override fun componentResized(e: ComponentEvent?) {
                val width = inputPanel.width
                inputContainer.setBounds(0, 0, width, JBUI.scale(42))
                userProfileButton.setBounds(0, JBUI.scale(54), width.coerceAtMost(JBUI.scale(200)), JBUI.scale(36))
            }
        })

        inputPanel.add(inputContainer)
        inputPanel.add(userProfileButton)
        return inputPanel
    }

    private fun initializeListeners() {
        inputField.addKeyListener(object : KeyAdapter() {
            override fun keyPressed(e: KeyEvent) {
                if (e.keyCode == KeyEvent.VK_ENTER && inputField.text.isNotBlank()) {
                    actions.sendMessage(inputField.text.trim())
                    e.consume()
                }
            }
        })

        sendButton.addActionListener {
            if (inputField.text.isNotBlank()) {
                actions.sendMessage(inputField.text.trim())
            }
        }

        newSessionButton.addActionListener { actions.startNewSession() }
        userProfileButton.addActionListener { actions.showUserProfileMenu() }
    }

    // --- Public methods to update UI state ---

    fun showLoginScreen() {
        cardLayout.show(contentPanel, "login")
    }

    fun showMainScreen() {
        cardLayout.show(contentPanel, "main")
    }
    
    fun togglePastConversationsView(showPastConversations: Boolean) {
        // Assuming chatContainer is always the second component in mainPanel's center area
        val chatContainer = mainPanel.getComponent(1) as? JBPanel<*> ?: return 
        val chatCardLayout = chatContainer.layout as? CardLayout ?: return

        if (showPastConversations) {
            pastConversationsView.loadConversations() // View is responsible for initiating its content load
            chatCardLayout.show(chatContainer, "pastConversations")
            pastConversationsButton.icon = AllIcons.General.ArrowLeft
            pastConversationsButton.toolTipText = "Back to current chat"
        } else {
            chatCardLayout.show(chatContainer, "chat")
            pastConversationsButton.icon = AllIcons.General.ArrowRight
            pastConversationsButton.toolTipText = "Past conversations"
        }
        this.isShowingPastConversations = showPastConversations // State update
    }

    fun updateUserProfile(userProfile: UserProfile?) {
        if (userProfile != null) {
            val buttonPanel = JPanel(BorderLayout(JBUI.scale(4), 0))
            buttonPanel.isOpaque = false

            val avatarLabel = CircularAvatarLabel(userProfile.initial)
            avatarLabel.preferredSize = Dimension(JBUI.scale(24), JBUI.scale(24))
            avatarLabel.font = Font(Font.SANS_SERIF, Font.BOLD, JBUI.scale(14))
            avatarLabel.foreground = JBColor.WHITE
            avatarLabel.backgroundColor = Color(56, 114, 159)

            if (userProfile.picture != null) {
                userProfile.loadProfileImage(JBUI.scale(24)) { icon: ImageIcon? ->
                    if (icon != null) {
                        avatarLabel.text = ""
                        avatarLabel.icon = icon
                        avatarLabel.repaint()
                    }
                }
            }

            val nameLabel = JLabel(userProfile.name)
            nameLabel.font = Font(Font.SANS_SERIF, Font.PLAIN, JBUI.scale(14))

            buttonPanel.add(avatarLabel, BorderLayout.WEST)
            buttonPanel.add(nameLabel, BorderLayout.CENTER)

            userProfileButton.removeAll() // Clear previous content
            userProfileButton.layout = BorderLayout() // Ensure buttonPanel fills userProfileButton
            userProfileButton.add(buttonPanel, BorderLayout.CENTER)
            userProfileButton.text = "" // Clear text if icon/panel is set
            userProfileButton.icon = null
        } else {
            userProfileButton.removeAll()
            userProfileButton.text = "Sign In"
            userProfileButton.icon = AllIcons.General.User
            userProfileButton.layout = FlowLayout(FlowLayout.CENTER) // Center text and icon
        }
        userProfileButton.revalidate()
        userProfileButton.repaint()
    }

    fun setControlsEnabled(enabled: Boolean) {
        SwingUtilities.invokeLater {
            inputField.isEnabled = enabled
            sendButton.isEnabled = enabled
            newSessionButton.isEnabled = enabled
            pastConversationsButton.isEnabled = enabled
            // userProfileButton is always enabled for sign in/out
        }
    }

    fun displayWelcomeMessage(name: String?, isNewSession: Boolean = false) { // name can be null
        chatPanel.clearChat()
        val welcomeName = name ?: "User"
        val messageText = if (isNewSession) "Hello $welcomeName, How can I help you today?" else "Welcome back, $welcomeName! How can I help you today?"
        chatPanel.addMessage(tech.beskar.baid.intelijplugin.model.Message(messageText, isUser = false))
    }
    
    fun clearChat() {
        chatPanel.clearChat()
    }

    fun clearInputField() {
        inputField.text = ""
    }
    
    fun focusInputField() {
        inputField.requestFocusInWindow()
    }

    fun getChatPanelView(): ChatPanelView {
        return chatPanel
    }

    // Delegate methods for chat interactions, called by BaidToolWindowController
    fun addMessageToChat(message: tech.beskar.baid.intelijplugin.model.Message) {
        chatPanel.addMessage(message)
    }
    
    fun addStreamingBlockToChat(block: tech.beskar.baid.intelijplugin.model.Block) {
        chatPanel.addStreamingBlock(block)
    }
    
    // These methods were previously in BaidToolWindowView for chatPanel delegation,
    // but ChatPanelView now handles its own streaming display.
    // Removing streamMessageToChat and loadChatConversation from BaidToolWindowView
    // as BaidToolWindowController now interacts directly with ChatPanelView for these.
    // Wait, BaidToolWindowController calls view.loadChatConversation(loadedSession).
    // This means loadChatConversation needs to remain.
    // streamMessageToChat was used by BaidToolWindowController before ChatController refactor.
    // It is no longer needed here as BaidToolWindowController calls ChatController.sendMessage,
    // which then calls ChatPanelView methods like addStreamingBlock.

    fun loadChatConversation(session: ChatSession) {
        chatPanel.loadConversation(session)
    }

    fun displayUserProfileMenu(
        userName: String?, 
        userEmail: Email?, 
        onSignOutSelected: () -> Unit
    ) {
        val menu = JPopupMenu()

        val nameItem = JMenuItem(userName ?: "Unknown User").apply { 
            isEnabled = false
            font = Font(this.font.name, Font.BOLD, this.font.size)
        }
        menu.add(nameItem)

        val emailItem = JMenuItem(userEmail?.value ?: "No email provided").apply {
            isEnabled = false
            font = Font(this.font.name, Font.PLAIN, this.font.size)
            foreground = UIManager.getColor("Label.disabledForeground")
        }
        menu.add(emailItem)

        menu.addSeparator()

        val signOutItem = JMenuItem("Sign Out", AllIcons.Actions.Exit).apply {
            addActionListener { onSignOutSelected() }
        }
        menu.add(signOutItem)

        menu.show(userProfileButton, 0, userProfileButton.height)
    }
}
