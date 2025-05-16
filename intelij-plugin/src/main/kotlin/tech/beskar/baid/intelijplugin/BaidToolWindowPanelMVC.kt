package tech.beskar.baid.intelijplugin
import com.intellij.icons.AllIcons
import com.intellij.openapi.project.Project
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBPanel
import com.intellij.ui.components.JBTextField
import com.intellij.util.ui.JBUI
import tech.beskar.baid.intelijplugin.controller.APIController
import tech.beskar.baid.intelijplugin.model.Block
import tech.beskar.baid.intelijplugin.model.ChatSession
import tech.beskar.baid.intelijplugin.model.Message
import tech.beskar.baid.intelijplugin.model.UserProfile
import tech.beskar.baid.intelijplugin.views.ChatPanelView
import tech.beskar.baid.intelijplugin.views.CircularAvatarLabel
import tech.beskar.baid.intelijplugin.views.LoginPanelView
import tech.beskar.baid.intelijplugin.views.PastConversationsView
import java.awt.*
import java.awt.event.*
import javax.swing.*


class BaidToolWindowPanelMVC(private val project: Project) : JBPanel<BaidToolWindowPanel?>(BorderLayout()) {
    private val apiController: APIController = APIController.getInstance()

    // UI Components
    private val cardLayout: CardLayout = CardLayout()
    private val contentPanel: JBPanel<JBPanel<*>?> = JBPanel<JBPanel<*>?>(cardLayout)
    private val loginPanel: LoginPanelView
    private val mainPanel: JBPanel<JBPanel<*>?>
    private val chatPanel: ChatPanelView
    private val pastConversationsView: PastConversationsView
    private val inputField: JBTextField
    private val sendButton: JButton
    private val newSessionButton: JButton
    private val pastConversationsButton: JButton
    private val userProfileButton: JButton

    private var isShowingPastConversations = false

    init {

        // Create panels
        this.loginPanel = LoginPanelView(project) { userProfile: UserProfile? -> this.onLoginSuccess(userProfile!!) }
        this.mainPanel = JBPanel<JBPanel<*>?>(BorderLayout())
        this.chatPanel = ChatPanelView(project)
        this.pastConversationsView = PastConversationsView(project) { session: ChatSession? ->
            this.onSessionSelected(
                session!!
            )
        }


        this.inputField = JBTextField(30)
        this.sendButton = JButton("Send")
        this.newSessionButton = JButton(AllIcons.General.Add)
        this.pastConversationsButton = JButton(AllIcons.General.ArrowRight)
        this.userProfileButton = JButton()

        initializeUI()
        initializeListeners()
        checkAuthenticationStatus()
    }

    private fun initializeUI() {
        // Set up login panel
        contentPanel.add(loginPanel, "login")


        // Set up main panel
        setupMainPanel()
        contentPanel.add(mainPanel, "main")


        // Add content panel to tool window
        add(contentPanel, BorderLayout.CENTER)
    }

    private fun setupMainPanel() {
        // Set up header panel
        val headerPanel = setupHeaderPanel()
        mainPanel.add(headerPanel, BorderLayout.NORTH)


        // Set up card container for chat and past conversations
        val chatCardLayout = CardLayout()
        val chatContainer = JBPanel<JBPanel<*>?>(chatCardLayout)
        chatContainer.add(chatPanel, "chat")
        chatContainer.add(pastConversationsView, "pastConversations")
        mainPanel.add(chatContainer, BorderLayout.CENTER)


        // Set up input panel
        val inputPanel = setupInputPanel()
        mainPanel.add(inputPanel, BorderLayout.SOUTH)


        // Configure past conversations toggle
        pastConversationsButton.addActionListener { e: ActionEvent? ->
            isShowingPastConversations = !isShowingPastConversations
            if (isShowingPastConversations) {
                pastConversationsView.loadConversations()
                chatCardLayout.show(chatContainer, "pastConversations")
                pastConversationsButton.setIcon(AllIcons.General.ArrowLeft)
                pastConversationsButton.setToolTipText("Back to current chat")
            } else {
                chatCardLayout.show(chatContainer, "chat")
                pastConversationsButton.setIcon(AllIcons.General.ArrowRight)
                pastConversationsButton.setToolTipText("Past conversations")
            }
        }


        // Configure back button in past conversations view
        pastConversationsView.setBackAction {
            isShowingPastConversations = false
            chatCardLayout.show(chatContainer, "chat")
            pastConversationsButton.setIcon(AllIcons.General.ArrowRight)
            pastConversationsButton.setToolTipText("Past conversations")
        }
    }

    private fun setupHeaderPanel(): JBPanel<JBPanel<*>?> {
        val headerPanel = JBPanel<JBPanel<*>?>(BorderLayout())
        headerPanel.setBorder(JBUI.Borders.empty(JBUI.scale(16), JBUI.scale(16), JBUI.scale(8), JBUI.scale(16)))


        // Add Baid title
        val titleLabel = JLabel("Baid")
        titleLabel.setFont(Font(titleLabel.getFont().getName(), Font.BOLD, JBUI.scale(18)))


        // Add subtitle
        val subtitleLabel = JLabel("Transform ideas into outcomes, instantly")
        subtitleLabel.setFont(Font(subtitleLabel.getFont().getName(), Font.PLAIN, JBUI.scale(12)))
        subtitleLabel.setForeground(UIManager.getColor("Label.disabledForeground"))

        val titleContainer = JBPanel<JBPanel<*>?>(BorderLayout(0, JBUI.scale(4)))
        titleContainer.setOpaque(false)
        titleContainer.add(titleLabel, BorderLayout.NORTH)
        titleContainer.add(subtitleLabel, BorderLayout.CENTER)


        // Add buttons
        newSessionButton.setToolTipText("Start new session")
        newSessionButton.setContentAreaFilled(false)
        newSessionButton.setBorderPainted(false)
        newSessionButton.setFocusPainted(false)

        pastConversationsButton.setToolTipText("Past conversations")
        pastConversationsButton.setContentAreaFilled(false)
        pastConversationsButton.setBorderPainted(false)
        pastConversationsButton.setFocusPainted(false)

        val buttonsPanel = JBPanel<JBPanel<*>?>()
        buttonsPanel.setOpaque(false)
        buttonsPanel.setLayout(BoxLayout(buttonsPanel, BoxLayout.X_AXIS))
        buttonsPanel.add(pastConversationsButton)
        buttonsPanel.add(Box.createHorizontalStrut(JBUI.scale(8)))
        buttonsPanel.add(newSessionButton)

        headerPanel.add(titleContainer, BorderLayout.WEST)
        headerPanel.add(buttonsPanel, BorderLayout.EAST)

        return headerPanel
    }

    private fun setupInputPanel(): JBPanel<JBPanel<*>?> {
        val inputPanel = JBPanel<JBPanel<*>?>(null)
        inputPanel.setBorder(JBUI.Borders.empty(0, JBUI.scale(16), JBUI.scale(8), JBUI.scale(16)))
        inputPanel.preferredSize = Dimension(0, JBUI.scale(110))


        // Set up input field
        inputField.setBorder(JBUI.Borders.empty(JBUI.scale(12)))
        inputField.emptyText.text = "Type your task here, press Enter to send prompt"


        // Set up send button
        sendButton.setFocusPainted(false)


        // Create input container
        val inputContainer = JBPanel<JBPanel<*>?>(BorderLayout())
        inputContainer.setBounds(0, 0, Int.Companion.MAX_VALUE, JBUI.scale(42))
        inputContainer.add(inputField, BorderLayout.CENTER)
        inputContainer.add(sendButton, BorderLayout.EAST)


        // Set up user profile button
        userProfileButton.setHorizontalAlignment(SwingConstants.LEFT)
        userProfileButton.setContentAreaFilled(false)
        userProfileButton.setBorderPainted(false)
        userProfileButton.setFocusPainted(false)
        userProfileButton.setBounds(0, JBUI.scale(54), JBUI.scale(200), JBUI.scale(36))


        // Add component listener to adjust bounds when panel is resized
        inputPanel.addComponentListener(object : ComponentAdapter() {
            override fun componentResized(e: ComponentEvent?) {
                val width = inputPanel.getWidth()
                inputContainer.setBounds(0, 0, width, JBUI.scale(42))
                userProfileButton.setBounds(0, JBUI.scale(54), JBUI.scale(200), JBUI.scale(36))
            }
        })

        inputPanel.add(inputContainer)
        inputPanel.add(userProfileButton)

        return inputPanel
    }

    private fun initializeListeners() {
        // Input field enter key
        inputField.addKeyListener(object : KeyAdapter() {
            override fun keyPressed(e: KeyEvent) {
                if (e.getKeyCode() == KeyEvent.VK_ENTER) {
                    sendMessage()
                    e.consume()
                }
            }
        })


        // Send button
        sendButton.addActionListener { e: ActionEvent? -> sendMessage() }


        // New session button
        newSessionButton.addActionListener { e: ActionEvent? -> startNewSession() }


        // User profile button
        userProfileButton.addActionListener { e: ActionEvent? -> showUserProfileMenu() }
    }

    private fun sendMessage() {
        val message = inputField.getText().trim { it <= ' ' }
        if (!message.isEmpty()) {
            // Clear input field
            inputField.setText("")


            // Send message to chat panel
            chatPanel.sendMessage(message)
        }
    }

    private fun startNewSession() {
        // Disable buttons
        setControlsEnabled(false)
        chatPanel.clearChat()
        // Add welcome message
        chatPanel.addStreamingBlock(Block.Paragraph("Started a new session."))
        // Re-enable controls
        setControlsEnabled(true)
    }

    private fun setControlsEnabled(enabled: Boolean) {
        SwingUtilities.invokeLater {
            inputField.setEnabled(enabled)
            sendButton.setEnabled(enabled)
            newSessionButton.setEnabled(enabled)
            pastConversationsButton.setEnabled(enabled)
        }
    }

    private fun showUserProfileMenu() {
        val currentUser = apiController.currentUser

        if (currentUser != null) {
            // Create popup menu
            val menu = JPopupMenu()


            // Add user info
            val nameItem = JMenuItem(currentUser.name)
            nameItem.setEnabled(false)
            nameItem.setFont(Font(nameItem.getFont().getName(), Font.BOLD, nameItem.getFont().getSize()))
            menu.add(nameItem)

            val emailItem = JMenuItem(currentUser.email)
            emailItem.setEnabled(false)
            emailItem.setFont(Font(emailItem.getFont().getName(), Font.PLAIN, emailItem.getFont().getSize()))
            emailItem.setForeground(UIManager.getColor("Label.disabledForeground"))
            menu.add(emailItem)

            menu.addSeparator()


            // Add sign out option
            val signOutItem = JMenuItem("Sign Out", AllIcons.Actions.Exit)
            signOutItem.addActionListener { e: ActionEvent? -> signOut() }
            menu.add(signOutItem)


            // Show menu
            menu.show(userProfileButton, 0, userProfileButton.getHeight())
        } else {
            // Show login panel if not logged in
            showLoginPanel()
        }
    }

    private fun signOut() {
        apiController.signOut {
            // Show login panel
            showLoginPanel()


            // Update UI
            updateUserProfileButton()
        }
    }

    private fun onLoginSuccess(userProfile: UserProfile) {
        showMainPanel()
        updateUserProfileButton()

        // Add welcome message
        chatPanel.clearChat()
        chatPanel.addMessage(Message("Welcome back, " + userProfile.name + "! How can I help you today?", isUser = false))
    }

    private fun onSessionSelected(session: ChatSession) {
        // Switch to chat view
        isShowingPastConversations = false
        val contentComponent = mainPanel.getComponent(1) as Container
        (contentComponent.layout as CardLayout).first(contentComponent)
        pastConversationsButton.setIcon(AllIcons.General.ArrowRight)
        pastConversationsButton.setToolTipText("Past conversations")


        // Load conversation
        chatPanel.loadConversation(session)
    }

    private fun showLoginPanel() {
        cardLayout.show(contentPanel, "login")
    }

    private fun showMainPanel() {
        cardLayout.show(contentPanel, "main")
    }

    private fun updateUserProfileButton() {
        val userProfile = apiController.currentUser

        if (userProfile != null) {
            // Create panel with user avatar and name
            val buttonPanel = JPanel(BorderLayout(JBUI.scale(4), 0))
            buttonPanel.setOpaque(false)


            // Create avatar label
            val avatarLabel = CircularAvatarLabel(userProfile.initial)
            avatarLabel.preferredSize = Dimension(JBUI.scale(24), JBUI.scale(24))
            avatarLabel.setFont(Font(Font.SANS_SERIF, Font.BOLD, JBUI.scale(14)))
            avatarLabel.setForeground(JBColor.WHITE)
            avatarLabel.setBackgroundColor(Color(56, 114, 159))


            // Try to load profile image if available
            if (userProfile.picture != null) {
                userProfile.loadProfileImage(JBUI.scale(24)) { icon: ImageIcon? ->
                    if (icon != null) {
                        avatarLabel.setText("")
                        avatarLabel.setIcon(icon)
                        avatarLabel.repaint()
                    }
                }
            }


            // Create name label
            val nameLabel = JLabel(userProfile.name)
            nameLabel.setFont(Font(Font.SANS_SERIF, Font.PLAIN, JBUI.scale(14)))

            buttonPanel.add(avatarLabel, BorderLayout.WEST)
            buttonPanel.add(nameLabel, BorderLayout.CENTER)

            userProfileButton.removeAll()
            userProfileButton.setText("")
            userProfileButton.setIcon(null)
            userProfileButton.add(buttonPanel)
        } else {
            // Not logged in
            userProfileButton.removeAll()
            userProfileButton.setText("Sign In")
            userProfileButton.setIcon(AllIcons.General.User)
        }

        userProfileButton.revalidate()
        userProfileButton.repaint()
    }

    private fun checkAuthenticationStatus() {
        apiController.initialize(
            project,
            { userProfile: UserProfile? ->
                // User is authenticated
                showMainPanel()
                updateUserProfileButton()


                // Add welcome message
                chatPanel.clearChat()
                chatPanel.addStreamingBlock(
                    Block.Paragraph(
                        "Welcome back, " + userProfile!!.name + "! How can I help you today?"
                    )
                )
            },
            {
                // User is not authenticated
                showLoginPanel()
                updateUserProfileButton()
            }
        )
    }
}