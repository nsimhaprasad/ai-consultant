package tech.beskar.baid.intelijplugin.views

import com.intellij.openapi.util.IconLoader
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBPanel
import com.intellij.ui.components.panels.VerticalLayout
import com.intellij.util.ui.JBUI
import org.jetbrains.rpc.LOG
import org.json.JSONObject
import tech.beskar.baid.intelijplugin.BaidToolWindowPanel
import tech.beskar.baid.intelijplugin.auth.GoogleAuthService
import tech.beskar.baid.intelijplugin.model.Block
import tech.beskar.baid.intelijplugin.model.ContentParser.parseBlock
import tech.beskar.baid.intelijplugin.model.ContentParser.parseJetbrainsResponse
import tech.beskar.baid.intelijplugin.model.ContentParser.parseResponse
import tech.beskar.baid.intelijplugin.model.ContentResponse
import tech.beskar.baid.intelijplugin.model.Message
import tech.beskar.baid.intelijplugin.ui.ContentRenderer
import tech.beskar.baid.intelijplugin.ui.ContentRenderer.renderCallout
import tech.beskar.baid.intelijplugin.ui.ContentRenderer.renderCode
import tech.beskar.baid.intelijplugin.ui.ContentRenderer.renderCommand
import tech.beskar.baid.intelijplugin.ui.ContentRenderer.renderHeading
import tech.beskar.baid.intelijplugin.ui.ContentRenderer.renderParagraph
import tech.beskar.baid.intelijplugin.ui.MessageFormatter
import tech.beskar.baid.intelijplugin.util.createAvatarLabel
import java.awt.*
import java.util.*
import javax.swing.*
import javax.swing.text.html.HTMLEditorKit


class MessageBubblePanel(
    val message: Message
) : JBPanel<MessageBubblePanel>(BorderLayout()) {
    private val isUser: Boolean = message.isUser
    private val googleAuthService: GoogleAuthService = GoogleAuthService.getInstance()

    val id: String? = UUID.randomUUID().toString()
    private var bubbleContainer: JBPanel<JBPanel<*>?>? = null
    private var textPane: JTextPane? = null
    private val blockComponents: MutableList<JComponent?> = ArrayList<JComponent?>()

    init {

        initializeUI()
    }

    private fun initializeUI() {
        setBackground(JBColor.background())
        setBorder(JBUI.Borders.empty(JBUI.scale(4), JBUI.scale(16)))

        if (isUser) {
            println("Creating user message UI")
            createUserMessageUI()
        } else {
            // Check if the message contains JSON blocks
            if (message.containsJsonBlocks()) {
                println("Creating structured message UI")
                createStructuredMessageUI()
            } else {
                println("Creating simple message UI")
                createSimpleMessageUI()
            }
        }
    }

    private fun createUserMessageUI() {
        // Create message bubble container
        bubbleContainer = JBPanel<JBPanel<*>?>(BorderLayout())
        bubbleContainer!!.setBackground(JBColor.GREEN.darker())
        bubbleContainer!!.setBorder(JBUI.Borders.empty(JBUI.scale(8), JBUI.scale(12)))


        // Create message text pane
        textPane = createTextPane()


        // Use MessageFormatter to process the message
        val messageWidth = this.messageWidth
        val content = message.content
        val htmlContent: String?

        if (content.contains("```")) {
            val result  = MessageFormatter.processMessage(content, messageWidth)
            htmlContent = result.first
        } else {
            htmlContent = "<html><body style='width: " + messageWidth + "px; max-width: " + messageWidth +
                    "px;'>" + content.replace("\n", "<br>") + "</body></html>"
        }

        textPane?.text = htmlContent
        bubbleContainer?.apply {
            add(textPane ?: createTextPane(), BorderLayout.CENTER)
        }


        // Create content panel with right-aligned message and avatar
        val contentPanel = JBPanel<JBPanel<*>?>(null)
        contentPanel.setLayout(FlowLayout(FlowLayout.RIGHT, 0, 0))
        contentPanel.setOpaque(false)


        // Add bubble first (on left)
        contentPanel.add(bubbleContainer)


        // Add user avatar (on right)
        // In a real implementation, this would use the user's profile image
        val picture = googleAuthService.getUserInfo()?.picture
        val avatarLabel = createAvatarLabel(picture)
        avatarLabel.setForeground(JBColor.WHITE)
        avatarLabel.preferredSize = Dimension(JBUI.scale(24), JBUI.scale(24))
        avatarLabel.setBorder(JBUI.Borders.emptyLeft(JBUI.scale(8)))
        contentPanel.add(avatarLabel)


        // Add content panel to the message panel
        add(contentPanel, BorderLayout.CENTER)
    }

    private fun createSimpleMessageUI() {
        // Create message bubble container
        bubbleContainer = JBPanel<JBPanel<*>?>(BorderLayout())
        bubbleContainer!!.setBackground(JBColor.gray)
        bubbleContainer!!.setBorder(JBUI.Borders.empty(JBUI.scale(8), JBUI.scale(12)))


        // Create message text pane
        textPane = createTextPane()


        // Use MessageFormatter to process the message
        val messageWidth = this.messageWidth
        val content = message.content
        val htmlContent: String?

        if (content.contains("```")) {
            val result = MessageFormatter.processMessage(content, messageWidth)
            htmlContent = result.first
        } else {
            htmlContent = "<html><body style='width: " + messageWidth + "px; max-width: " + messageWidth +
                    "px;'>" + content.replace("\n", "<br>") + "</body></html>"
        }

        textPane?.text = htmlContent
        bubbleContainer?.apply {
            add(textPane ?: createTextPane(), BorderLayout.CENTER)
        }


        // Create content panel with left-aligned message and avatar
        val contentPanel = JBPanel<JBPanel<*>?>(BorderLayout())
        contentPanel.setOpaque(false)


        // Add AI avatar (on left)
        val avatarLabel = JLabel().apply {
            icon = IconLoader.getIcon("/icons/beskar.svg", MessageBubblePanel::class.java)
            border = JBUI.Borders.emptyRight(JBUI.scale(8))
            verticalAlignment = JLabel.TOP
        }
        contentPanel.add(avatarLabel, BorderLayout.WEST)


        // Add bubble (in center)
        bubbleContainer?.apply {
            contentPanel.add(this, BorderLayout.CENTER)
        }


        // Add spacer on right to keep left-aligned
        val spacer = JPanel()
        spacer.setOpaque(false)
        spacer.preferredSize = Dimension(JBUI.scale(100), 0)
        contentPanel.add(spacer, BorderLayout.EAST)


        // Add content panel to the message panel
        add(contentPanel, BorderLayout.CENTER)
    }

    private fun createStructuredMessageUI() {
        try {
            // Create message bubble container with vertical layout for blocks
            bubbleContainer = JBPanel<JBPanel<*>?>(VerticalLayout(JBUI.scale(8)))
            bubbleContainer!!.setBackground(JBColor.gray)
            bubbleContainer!!.setBorder(JBUI.Borders.empty(JBUI.scale(8), JBUI.scale(12)))


            // Create content panel with avatar and bubble
            val contentPanel = JBPanel<JBPanel<*>?>(BorderLayout())
            contentPanel.setOpaque(false)


            // Add AI avatar
            val avatarLabel = JLabel().apply {
                icon = IconLoader.getIcon("/icons/beskar.svg", MessageBubblePanel::class.java)
                border = JBUI.Borders.emptyRight(JBUI.scale(8))
                verticalAlignment = JLabel.TOP
            }
            contentPanel.add(avatarLabel, BorderLayout.WEST)


            // Add bubble container
            bubbleContainer?.apply {
                contentPanel.add(this, BorderLayout.CENTER)
            }


            // Add spacer on right
            val spacer = JPanel()
            spacer.setOpaque(false)
            spacer.preferredSize = Dimension(JBUI.scale(100), 0)
            contentPanel.add(spacer, BorderLayout.EAST)


            // Parse and render blocks
            val content = message.content
            val jsonObj = JSONObject(content)
            var response: ContentResponse? = null


            // Check response format
            if (jsonObj.has("schema") && jsonObj.getString("schema") == "jetbrains-llm-response") {
                // JetBrains format
                response = parseJetbrainsResponse(content)
            } else if (jsonObj.has("blocks")) {
                // Standard blocks format
                response = parseResponse(content)
            }

            if (response != null) {
                // Render all blocks
                for (block in response.blocks) {
                    val comp = renderBlock(block)
                    if (comp != null) {
                        blockComponents.add(comp)
                        bubbleContainer!!.add(comp)
                    }
                }
            } else {
                // Try to parse as a single block
                val block = parseBlock(jsonObj)
                val comp = renderBlock(block)
                if (comp != null) {
                    blockComponents.add(comp)
                    bubbleContainer!!.add(comp)
                }
            }


            // Add content panel to the message panel
            add(contentPanel, BorderLayout.CENTER)
        } catch (e: Exception) {
            // Fallback to simple message in case of parsing error
            println("Error parsing structured message: " + e.message)
            createSimpleMessageUI()
        }
    }

    private fun renderBlock(block: Block): JComponent? {
        return when (block) {
            is Block.Paragraph -> renderParagraph(block)
            is Block.Code -> renderCode(block)
            is Block.Command -> renderCommand(block)
            is Block.ListBlock -> ContentRenderer.renderList(block)
            is Block.Heading -> renderHeading(block)
            is Block.Callout -> renderCallout(block)
        }
    }

    private fun createTextPane(): JTextPane {
        val textPane = JTextPane()
        textPane.setContentType("text/html")
        textPane.isEditable = false
        textPane.setOpaque(false)
        textPane.setBackground(Color(0, 0, 0, 0)) // Transparent


        // Apply custom styles
        val kit = textPane.getEditorKit() as HTMLEditorKit
        val styleSheet = kit.getStyleSheet()
        styleSheet.addRule("body { font-family: Segoe UI, Helvetica, sans-serif; font-size: 13px; }")
        styleSheet.addRule("pre { background-color: #f5f5f5; padding: 8px; border-radius: 4px; overflow-x: auto; }")
        styleSheet.addRule("code { font-family: 'JetBrains Mono', monospace; font-size: 12px; }")

        return textPane
    }

    private val messageWidth: Int
        get() {
            // Get parent container width
            val parent = getParent()
            var parentWidth = parent?.getWidth() ?: 0


            // Use a sensible default if parent width is not available
            if (parentWidth <= 0) {
                parentWidth = 600
            }


            // Calculate message width (about 70% of parent width)
            return 200.coerceAtLeast((parentWidth * 7 / 10).coerceAtMost(500))
        }

    fun updateWidth(newWidth: Int) {
        if (textPane != null) {
            // Update HTML content width
            val currentText = textPane!!.getText()
            val updatedText: String = currentText.replace(
                Regex("width: \\d+px; max-width: \\d+px;"),
                "width: " + newWidth + "px; max-width: " + newWidth + "px;"
            )


            // Only update if the text actually changed
            if (currentText != updatedText) {
                textPane!!.text = updatedText
            }
        }
    }
}