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
import java.io.InputStream

class BaidToolWindowPanel(private val project: Project) : JBPanel<BaidToolWindowPanel>(BorderLayout()) {
    private val chatPanel = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(8)))
    private val chatScroll = JBScrollPane(chatPanel)
    private val inputField = JBTextField(30)
    private val consultButton = JButton()

    // Load DM Sans font if available
    private val dmSansRegular: Font? = try {
        val fontStream = javaClass.getResourceAsStream("/fonts/DMSans/DMSans-Regular.ttf")
        if (fontStream != null) {
            val font = Font.createFont(Font.TRUETYPE_FONT, fontStream)
            val scaledFont = font.deriveFont(JBUI.scale(14f))
            // Register the font with the graphics environment
            GraphicsEnvironment.getLocalGraphicsEnvironment().registerFont(font)
            println("Successfully loaded DM Sans font from resources")
            scaledFont
        } else {
            println("Could not find DM Sans font in resources")
            null
        }
    } catch (e: Exception) {
        println("Error loading DM Sans font: ${e.message}")
        null
    }

    private val dmSansBold: Font? = try {
        val fontStream = javaClass.getResourceAsStream("/fonts/DMSans/DMSans-Bold.ttf")
        if (fontStream != null) {
            val font = Font.createFont(Font.TRUETYPE_FONT, fontStream)
            val scaledFont = font.deriveFont(JBUI.scale(14f))
            // Register the font with the graphics environment
            GraphicsEnvironment.getLocalGraphicsEnvironment().registerFont(font)
            println("Successfully loaded DM Sans font from resources")
            scaledFont
        } else {
            println("Could not find DM Sans font in resources")
            null
        }
    } catch (e: Exception) {
        println("Error loading DM Sans font: ${e.message}")
        null
    }

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
                font = dmSansBold?.deriveFont(JBUI.scale(36).toFloat()) ?: UIUtil.getLabelFont().deriveFont(Font.BOLD, JBUI.scale(36).toFloat())
                foreground = JBColor.foreground()
            }

            // Add subtitle
            val subtitleLabel = JLabel("Delegate your tasks, focus on the results").apply {
                font = dmSansRegular?.deriveFont(JBUI.scale(14).toFloat()) ?: UIUtil.getLabelFont().deriveFont(JBUI.scale(14).toFloat())
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
        inputField.font = dmSansRegular?.deriveFont(JBUI.scale(14).toFloat()) ?: UIUtil.getLabelFont().deriveFont(JBUI.scale(14).toFloat())

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
        add(titlePanel, BorderLayout.NORTH)
        add(chatScroll, BorderLayout.CENTER)
        add(inputPanel, BorderLayout.SOUTH)

        // Add welcome message
        appendMessage("Hello! I'm Baid, your AI assistant. How can I help you today?", isUser = false)
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

            // Create message text
            val messageText = JTextPane().apply {
                contentType = "text/html"
                text = "<html><body style='font-family: ${UIUtil.getLabelFont().family}; font-size: ${JBUI.scale(13)}pt;'>${message.replace("\n", "<br>")}</body></html>"
                isEditable = false
                background = if (isUser) JBColor(Color(240, 240, 240), Color(60, 63, 65)) else JBColor.background()
                border = JBUI.Borders.empty()
                caretPosition = 0
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
        // Disable input while processing
        inputField.isEnabled = false
        consultButton.isEnabled = false
        val editor = com.intellij.openapi.fileEditor.FileEditorManager.getInstance(project).selectedTextEditor
        val document = editor?.document
        val fileText = document?.text ?: "No file open."

        // Show thinking message
        appendMessage("Thinking...", isUser = false)
        val apiUrl = "https://ai-consultant-backend-742371152853.asia-south1.run.app/consult"
        val payload = JSONObject(mapOf(
            "prompt" to userPrompt,
            "file_content" to fileText
        )).toString()

        // Make API request in background
        com.intellij.openapi.progress.ProgressManager.getInstance().run(
            object : com.intellij.openapi.progress.Task.Backgroundable(
                project,
                "Consulting AI",
                false
            ) {
                override fun run(indicator: com.intellij.openapi.progress.ProgressIndicator) {
                    try {
                        // Make API request
                        val response = HttpRequests
                            .post(apiUrl, "application/json")
                            .connectTimeout(30000)
                            .readTimeout(30000)
                            .tuner { connection -> 
                                connection.connectTimeout = 30000
                                connection.readTimeout = 30000
                            }
                            .connect { request ->
                                request.write(payload)
                                request.getReader(null).readText()
                            }

                        // Parse response
                        val jsonResponse = JSONObject(response)
                        val aiResponse = jsonResponse.optString("received_file_content_preview", "I'm sorry, I couldn't process that request.")

                        // Update UI with response
                        SwingUtilities.invokeLater {
                            // Remove thinking message
                            chatPanel.remove(chatPanel.componentCount - 1)

                            // Add AI response
                            appendMessage(aiResponse, isUser = false)

                            // Re-enable input
                            inputField.isEnabled = true
                            consultButton.isEnabled = true
                            inputField.requestFocus()
                        }
                    } catch (e: Exception) {
                        // Handle error
                        SwingUtilities.invokeLater {
                            // Remove thinking message
                            chatPanel.remove(chatPanel.componentCount - 1)

                            // Add error message
                            appendMessage("Sorry, I encountered an error: ${e.message}", isUser = false)

                            // Re-enable input
                            inputField.isEnabled = true
                            consultButton.isEnabled = true
                            inputField.requestFocus()
                        }
                    }
                }
            }
        )
    }
}
