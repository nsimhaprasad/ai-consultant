package tech.beskar.baid.intelijplugin

import com.intellij.openapi.project.Project
import com.intellij.util.io.HttpRequests
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.components.JBTextField
import com.intellij.ui.components.JBPanel
import com.intellij.ui.JBColor
import com.intellij.util.ui.JBUI
import com.intellij.util.ui.UIUtil
import com.intellij.ui.components.panels.VerticalLayout
import com.intellij.openapi.actionSystem.ActionToolbar
import com.intellij.openapi.actionSystem.ActionManager
import com.intellij.openapi.actionSystem.DefaultActionGroup
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.icons.AllIcons
import java.awt.*
import javax.swing.*
import org.json.JSONObject

class AIConsultantToolWindowPanel(private val project: Project) : JBPanel<AIConsultantToolWindowPanel>(BorderLayout()) {
    private val chatPanel = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(8)))
    private val chatScroll = JBScrollPane(chatPanel)
    private val inputField = JBTextField(30)
    private val consultButton = JButton()

    init {
        // Set up the chat panel
        chatPanel.background = JBColor.background()
        chatPanel.border = JBUI.Borders.empty(8)

        // Set up the scroll pane
        chatScroll.verticalScrollBar.unitIncrement = JBUI.scale(16)
        chatScroll.border = JBUI.Borders.empty()

        // Create toolbar actions
        val actionGroup = DefaultActionGroup().apply {
            add(object : AnAction("Clear Chat", "Clear all messages", AllIcons.Actions.GC) {
                override fun actionPerformed(e: AnActionEvent) {
                    chatPanel.removeAll()
                    chatPanel.revalidate()
                    chatPanel.repaint()
                }
            })
        }

        // Create toolbar
        val toolbar = ActionManager.getInstance().createActionToolbar(
            "BaidToolbar", 
            actionGroup, 
            true
        )
        toolbar.targetComponent = this

        // Create title panel with Junie branding
        val titlePanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            background = JBColor.background()
            border = JBUI.Borders.empty(JBUI.scale(16), JBUI.scale(16), JBUI.scale(8), JBUI.scale(16))

            // Add Junie title
            val titleLabel = JLabel("Baid").apply {
                font = UIUtil.getLabelFont().deriveFont(Font.BOLD, JBUI.scale(36).toFloat())
                foreground = JBColor.foreground()
            }

            // Add subtitle
            val subtitleLabel = JLabel("Delegate your tasks, focus on the results").apply {
                font = UIUtil.getLabelFont().deriveFont(JBUI.scale(14).toFloat())
                foreground = JBColor.foreground().darker()
            }

            val titleContainer = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(4))).apply {
                isOpaque = false
                add(titleLabel)
                add(subtitleLabel)
            }

            add(titleContainer, BorderLayout.WEST)
            add(toolbar.component, BorderLayout.EAST)
        }

        // Set up the input field
        inputField.border = JBUI.Borders.empty(JBUI.scale(12))
        inputField.emptyText.text = "Type your task here, press Enter to send prompt"
        inputField.font = UIUtil.getLabelFont().deriveFont(JBUI.scale(13).toFloat())

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
        consultButton.apply {
            putClientProperty("JButton.buttonType", "borderless")
            isFocusable = false
            icon = AllIcons.Actions.Forward
            text = ""
            toolTipText = "Send prompt"
        }

        // Create input panel
        val inputPanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            border = JBUI.Borders.customLine(JBColor.border(), 1, 0, 0, 0)
            add(inputField, BorderLayout.CENTER)
            add(consultButton, BorderLayout.EAST)
            preferredSize = Dimension(preferredSize.width, JBUI.scale(50))
        }

        // Add components to main panel
        add(titlePanel, BorderLayout.NORTH)
        add(chatScroll, BorderLayout.CENTER)
        add(inputPanel, BorderLayout.SOUTH)

        consultButton.addActionListener {
            val userMessage = inputField.text.trim()
            if (userMessage.isNotEmpty()) {
                appendMessage(userMessage, isUser = true)
                inputField.text = ""
                consultWithAPI(userMessage)
            }
        }
    }

    private fun appendMessage(message: String, isUser: Boolean) {
        // Create message bubble with IntelliJ styling
        val bubbleColor = if (isUser) 
            JBColor(JBColor(0xE3F2FD, 0x2B3940), JBColor(0xE3F2FD, 0x2B3940)) 
        else 
            JBColor.background().brighter()

        val bubble = JBPanel<JBPanel<*>>().apply {
            layout = BorderLayout()
            background = bubbleColor
            border = JBUI.Borders.compound(
                JBUI.Borders.customLine(JBColor.border().darker(), 0, 0, 1, 0),
                JBUI.Borders.empty(JBUI.scale(8), JBUI.scale(12))
            )

            // Add avatar/icon for non-user messages
            if (!isUser) {
                add(JLabel(AllIcons.Plugins.PluginLogo).apply {
                    border = JBUI.Borders.emptyRight(JBUI.scale(8))
                }, BorderLayout.WEST)
            }

            // Add message text with proper styling
            val textComponent = JEditorPane("text/html", 
                "<html><body style='font-family: ${UIUtil.getLabelFont().family}; font-size: ${UIUtil.getLabelFont().size}pt;'>${
                    message.replace("\n", "<br>")
                }</body></html>"
            ).apply {
                isEditable = false
                isOpaque = false
                border = JBUI.Borders.empty()
                putClientProperty(JEditorPane.HONOR_DISPLAY_PROPERTIES, true)
            }

            add(textComponent, BorderLayout.CENTER)
            maximumSize = Dimension(JBUI.scale(300), Int.MAX_VALUE)
        }

        // Create wrapper panel for alignment
        val wrapper = JBPanel<JBPanel<*>>().apply {
            layout = BorderLayout()
            isOpaque = false
            border = JBUI.Borders.empty(JBUI.scale(4), JBUI.scale(8))
            add(bubble, if (isUser) BorderLayout.EAST else BorderLayout.WEST)
        }

        // Add timestamp
        val timestamp = JLabel(java.text.SimpleDateFormat("HH:mm").format(java.util.Date())).apply {
            font = UIUtil.getFont(UIUtil.FontSize.MINI, font)
            foreground = JBColor.gray
            border = JBUI.Borders.empty(JBUI.scale(2), 0)
            alignmentX = if (isUser) Component.RIGHT_ALIGNMENT else Component.LEFT_ALIGNMENT
        }

        val timestampWrapper = JBPanel<JBPanel<*>>().apply {
            layout = BorderLayout()
            isOpaque = false
            add(timestamp, if (isUser) BorderLayout.EAST else BorderLayout.WEST)
        }

        // Add components to chat panel
        chatPanel.add(wrapper)
        chatPanel.add(timestampWrapper)
        chatPanel.add(Box.createVerticalStrut(JBUI.scale(8)))

        // Scroll to bottom
        SwingUtilities.invokeLater {
            chatPanel.revalidate()
            chatPanel.repaint()
            chatScroll.verticalScrollBar.value = chatScroll.verticalScrollBar.maximum
        }
    }

    private fun consultWithAPI(userPrompt: String) {
        val editor = com.intellij.openapi.fileEditor.FileEditorManager.getInstance(project).selectedTextEditor
        val document = editor?.document
        val fileText = document?.text ?: "No file open."

        // Show "thinking" message with loading indicator
        val loadingMessageId = "loading-${System.currentTimeMillis()}"
        appendMessage("<i>Thinking...</i>", isUser = false)

        // Make API call to FastAPI backend using IntelliJ's background task API
        val apiUrl = "https://ai-consultant-backend-742371152853.asia-south1.run.app/consult"
        val payload = JSONObject(mapOf(
            "prompt" to userPrompt,
            "file_content" to fileText
        )).toString()

        // Use IntelliJ's background task API
        com.intellij.openapi.progress.ProgressManager.getInstance().run(
            object : com.intellij.openapi.progress.Task.Backgroundable(project, "Consulting Baid", false) {
                override fun run(indicator: com.intellij.openapi.progress.ProgressIndicator) {
                    indicator.isIndeterminate = true
                    indicator.text = "Consulting Baid..."

                    try {
                        val response = HttpRequests
                            .post(apiUrl, "application/json")
                            .connectTimeout(10000)
                            .readTimeout(30000)
                            .tuner { connection -> 
                                connection.connectTimeout = 10000
                                connection.readTimeout = 30000
                            }
                            .connect { request ->
                                request.write(payload)
                                request.getReader(null).readText()
                            }

                        // Update UI on EDT
                        com.intellij.openapi.application.ApplicationManager.getApplication().invokeLater {
                            appendMessage(response, isUser = false)
                        }
                    } catch (e: Exception) {
                        // Show error in UI
                        com.intellij.openapi.application.ApplicationManager.getApplication().invokeLater {
                            appendMessage("Error: ${e.message ?: "Unknown error"}", isUser = false)

                            // Also show notification
                            com.intellij.notification.NotificationGroupManager.getInstance()
                                .getNotificationGroup("Baid Notifications")
                                .createNotification(
                                    "Error consulting Baid",
                                    e.message ?: "Unknown error",
                                    com.intellij.notification.NotificationType.ERROR
                                )
                                .notify(project)
                        }
                    }
                }
            }
        )
    }
}
