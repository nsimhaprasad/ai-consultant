package tech.beskar.baid.intelijplugin.views

import com.intellij.openapi.project.Project
import com.intellij.openapi.util.IconLoader
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBPanel
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.components.panels.VerticalLayout
import com.intellij.util.ui.JBUI
import org.jetbrains.rpc.LOG
import tech.beskar.baid.intelijplugin.controller.APIController
import tech.beskar.baid.intelijplugin.model.Block
import tech.beskar.baid.intelijplugin.model.ChatSession
import tech.beskar.baid.intelijplugin.model.Message
import tech.beskar.baid.intelijplugin.ui.ContentRenderer
import tech.beskar.baid.intelijplugin.ui.ContentRenderer.renderCallout
import tech.beskar.baid.intelijplugin.ui.ContentRenderer.renderCode
import tech.beskar.baid.intelijplugin.ui.ContentRenderer.renderCommand
import tech.beskar.baid.intelijplugin.ui.ContentRenderer.renderHeading
import tech.beskar.baid.intelijplugin.ui.ContentRenderer.renderParagraph
import tech.beskar.baid.intelijplugin.ui.RoundedBorder
import java.awt.BorderLayout
import java.awt.Dimension
import java.awt.event.ActionEvent
import java.awt.event.ComponentAdapter
import java.awt.event.ComponentEvent
import java.util.concurrent.ConcurrentHashMap
import javax.swing.*
import kotlin.math.max
import kotlin.math.min


class ChatPanelView(private val project: Project?) :
    JBPanel<ChatPanelView>(BorderLayout()) {


    private val messagesPanel: JBPanel<JBPanel<*>> = JBPanel<JBPanel<*>>(VerticalLayout(JBUI.scale(8)))
    private val scrollPane: JBScrollPane
    private val apiController: APIController = APIController.getInstance()

    // Track message bubbles by ID for updating
    private val bubbles: MutableMap<String?, MessageBubblePanel> = ConcurrentHashMap<String?, MessageBubblePanel>()

    // Track components for the current streaming response
    private var currentStreamingPanel: JBPanel<JBPanel<*>?>? = null
    private var currentBubbleContainer: JBPanel<JBPanel<*>?>? = null
    private var thinkingBubble: MessageBubblePanel? = null

    init {
        messagesPanel.setBackground(JBColor.background())
        messagesPanel.setBorder(JBUI.Borders.empty(8))


        // Create scroll pane
        scrollPane = JBScrollPane(messagesPanel)
        scrollPane.setVerticalScrollBarPolicy(JBScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED)
        scrollPane.setHorizontalScrollBarPolicy(JBScrollPane.HORIZONTAL_SCROLLBAR_NEVER)
        scrollPane.setBorder(JBUI.Borders.empty())
        scrollPane.getVerticalScrollBar().setUnitIncrement(16)


        // Add scroll pane to chat panel
        add(scrollPane, BorderLayout.CENTER)


        // Add component listener to handle resizing
        messagesPanel.addComponentListener(object : ComponentAdapter() {
            override fun componentResized(e: ComponentEvent?) {
                updateAllMessageWidths()
            }
        })
    }

    private fun updateAllMessageWidths() {
        val newWidth = this.messageWidth

        for (bubble in bubbles.values) {
            bubble.updateWidth(newWidth)
        }


        // Revalidate and repaint the panel
        messagesPanel.revalidate()
        messagesPanel.repaint()
    }

    private val messageWidth: Int
        get() {
            var panelWidth = messagesPanel.getWidth()
            if (panelWidth <= 0) {
                panelWidth = 600 // Default width
            }


            return max(200, min(panelWidth * 7 / 10, 500))
        }

    fun addMessage(message: Message) {
        val bubble = MessageBubblePanel(message)
        bubbles.put(bubble.id, bubble)

        SwingUtilities.invokeLater {
            messagesPanel.add(bubble)
            messagesPanel.revalidate()
            messagesPanel.repaint()
            scrollToBottom()
        }
    }

    fun startStreamingResponse() {
        SwingUtilities.invokeLater {
            // Clear any existing streaming panel
            currentStreamingPanel?.let { panel ->
                messagesPanel.remove(panel)
                currentStreamingPanel = null
                currentBubbleContainer = null
            }

            // Add a 'Thinking...' message
            thinkingBubble = addLoadingMessage("Thinking...")

            // Create container for the streaming response
            currentStreamingPanel = JBPanel<JBPanel<*>?>(BorderLayout())
            currentStreamingPanel!!.setOpaque(false)

            // Create bubble container for blocks
            currentBubbleContainer = JBPanel<JBPanel<*>?>(VerticalLayout(JBUI.scale(8)))
            currentBubbleContainer!!.setOpaque(false)
            currentBubbleContainer!!.setBackground(JBColor.gray)
            currentBubbleContainer!!.isOpaque = false
            currentBubbleContainer!!.setBorder(
                BorderFactory.createCompoundBorder(
                    RoundedBorder(JBColor.gray, 12),
                    JBUI.Borders.empty(JBUI.scale(8), JBUI.scale(12))
                )
            )

            // Create content panel with avatar and bubble
            val contentPanel = JBPanel<JBPanel<*>?>(BorderLayout())
            contentPanel.setOpaque(false)
            contentPanel.setBorder(JBUI.Borders.empty(JBUI.scale(4), JBUI.scale(16)))

            // Add AI avatar
            var avatarLabel: JLabel
            try {
                avatarLabel = JLabel()
                avatarLabel.icon = IconLoader.getIcon("/icons/beskar.svg", javaClass)
                avatarLabel.verticalAlignment = JLabel.TOP
                // Add some padding to ensure proper positioning
                avatarLabel.setBorder(JBUI.Borders.emptyRight(JBUI.scale(8)))
            } catch (e: Exception) {
                LOG.warn("Failed to load Beskar icon", e)
                avatarLabel = JLabel("AI")
            }

            contentPanel.add(avatarLabel, BorderLayout.WEST)

            // Add bubble container
            currentBubbleContainer?.apply {
                contentPanel.add(this, BorderLayout.CENTER)
            }

            // Add spacer on right
            val spacer = JPanel()
            spacer.setOpaque(false)
            spacer.preferredSize = Dimension(JBUI.scale(100), 0)
            contentPanel.add(spacer, BorderLayout.EAST)

            // Add to streaming panel
            currentStreamingPanel!!.add(contentPanel, BorderLayout.CENTER)

            // Don't add to messages panel yet - we'll replace the thinking bubble with this
        }
    }

    fun addStreamingBlock(block: Block?) {
        SwingUtilities.invokeLater {
            if (currentBubbleContainer == null) return@invokeLater

            // If this is the first block, replace the thinking bubble with the streaming panel
            if (thinkingBubble != null) {
                thinkingBubble?.let { bubble ->
                    // Find the index of the thinking bubble
                    val index = messagesPanel.components.indexOfFirst { it == bubble }
                    if (index >= 0) {
                        // Remove the thinking bubble
                        messagesPanel.remove(bubble)
                        // Add the streaming panel at the same position
                        messagesPanel.add(currentStreamingPanel, null, index)
                    }
                    thinkingBubble = null
                }
                // Ensure the panel is visible
                currentStreamingPanel?.isVisible = true
                messagesPanel.revalidate()
                messagesPanel.repaint()
            }

            // Add the block to the container
            // Render the block
            val comp = when (block) {
                is Block.Paragraph -> renderParagraph(block)
                is Block.Code -> renderCode(block)
                is Block.Command -> renderCommand(block)
                is Block.ListBlock -> ContentRenderer.renderList(block)
                is Block.Heading -> renderHeading(block)
                is Block.Callout -> renderCallout(block)
                else -> null
            }

            if (comp != null) {
                currentBubbleContainer!!.add(comp)
                currentBubbleContainer!!.revalidate()
                currentBubbleContainer!!.repaint()
                scrollToBottom()
            }
        }
    }

    fun endStreamingResponse() {
        SwingUtilities.invokeLater {
            // Reset streaming panel references
            currentStreamingPanel = null
            currentBubbleContainer = null


            // Ensure updated layout
            messagesPanel.revalidate()
            messagesPanel.repaint()
            scrollToBottom()
        }
    }

    fun sendMessage(
        content: String,
        onComplete: () -> Unit = {},
        onError: (Throwable) -> Unit = {}
    ) {
        // Create and add user message
        val userMessage = Message(content, true)
        addMessage(userMessage)

        // Start streaming response
        startStreamingResponse()

        // Send to backend
        apiController.sendMessage(
            project,
            content,
            { message: Message? -> },
            { block: Block? -> this.addStreamingBlock(block) },
            {
                endStreamingResponse()
                onComplete()
            },
            { error: Throwable? ->
                val errorBlock = apiController.createErrorBlock(error!!)
                addStreamingBlock(errorBlock)
                endStreamingResponse()
                onError(error)
            }
        )
    }

    fun clearChat() {
        SwingUtilities.invokeLater {
            messagesPanel.removeAll()
            bubbles.clear()
            currentStreamingPanel = null
            currentBubbleContainer = null
            messagesPanel.revalidate()
            messagesPanel.repaint()
        }
    }

    fun loadConversation(session: ChatSession) {
        SwingUtilities.invokeLater {
            clearChat()
            // Add messages from session
            for (message in session.getMessages()) {
                addMessage(message!!)
            }
        }
    }

    fun addLoadingMessage(message: String): MessageBubblePanel {
        val loadingMessage = Message(message, false)
        val bubble = MessageBubblePanel(loadingMessage)
        bubbles.put(bubble.id, bubble)

        SwingUtilities.invokeLater {
            messagesPanel.add(bubble)
            messagesPanel.revalidate()
            messagesPanel.repaint()
            scrollToBottom()
        }

        return bubble
    }

    fun removeMessageBubble(bubbleId: String?) {
        val bubble = bubbles.remove(bubbleId)
        if (bubble != null) {
            SwingUtilities.invokeLater {
                messagesPanel.remove(bubble)
                messagesPanel.revalidate()
                messagesPanel.repaint()
            }
        }
    }

    fun scrollToBottom() {
        SwingUtilities.invokeLater {
            val scrollBar = scrollPane.getVerticalScrollBar()
            scrollBar.setValue(scrollBar.maximum)


            // Schedule another scroll after a short delay to ensure completeness
            val timer = Timer(50) { e: ActionEvent? ->
                scrollBar.setValue(scrollBar.maximum)
            }
            timer.isRepeats = false
            timer.start()
        }
    }


}