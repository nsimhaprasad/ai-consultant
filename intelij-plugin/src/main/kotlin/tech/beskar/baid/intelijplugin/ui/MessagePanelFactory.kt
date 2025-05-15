package tech.beskar.baid.intelijplugin.ui

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.util.IconLoader
import com.intellij.ui.Gray
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBPanel
import com.intellij.ui.components.panels.VerticalLayout
import com.intellij.util.ui.GraphicsUtil
import com.intellij.util.ui.JBUI
import tech.beskar.baid.intelijplugin.BaidToolWindowPanel
import tech.beskar.baid.intelijplugin.auth.GoogleAuthService
import tech.beskar.baid.intelijplugin.model.Message
import tech.beskar.baid.intelijplugin.util.FontUtil
import tech.beskar.baid.intelijplugin.util.getMessageWidth
import java.awt.*
import java.awt.geom.Ellipse2D
import java.awt.image.BufferedImage
import java.net.URL
import javax.imageio.ImageIO
import javax.swing.*

class MessagePanelFactory(private val authService: GoogleAuthService) {

    fun createMessagePanel(message: Message): JBPanel<JBPanel<*>> {
        return if (message.isUser) {
            createUserMessagePanel(message.content)
        } else if (message.isJsonContent()) {
            createJsonMessagePanel(message.content)
        } else {
            createSimpleMessagePanel(message.content, false)
        }
    }

    fun createThinkingPanel(): JBPanel<JBPanel<*>> {
        return createSimpleMessagePanel("Thinking...", false)
    }

    private fun createUserMessagePanel(content: String): JBPanel<JBPanel<*>> {
        // Create message panel with WhatsApp-like layout
        val messagePanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            background = JBColor.background()
            border = JBUI.Borders.empty(JBUI.scale(4), JBUI.scale(16))
        }

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
            val (htmlContent, _) = MessageFormatter.processMessage(content, messageWidth)
            text = htmlContent
            font = FontUtil.getBodyFont()
            isEditable = false
            isOpaque = false
            background = Color(0, 0, 0, 0) // Transparent
            foreground = JBColor.BLACK
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
        return messagePanel
    }

    private fun createJsonMessagePanel(content: String): JBPanel<JBPanel<*>> {
        // Create message panel with WhatsApp-like layout
        val messagePanel = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            background = JBColor.background()
            border = JBUI.Borders.empty(JBUI.scale(4), JBUI.scale(16))
        }

        // Create agent message with WhatsApp-like layout
        val bubbleContainer = JBPanel<JBPanel<*>>(VerticalLayout(8)).apply {
            background = JBColor(Gray._255, Color(60, 63, 65))
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

        return messagePanel
    }



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
                JBColor(Gray._255, Color(60, 63, 65)) // White/dark for agent
            }
            border = JBUI.Borders.empty(JBUI.scale(8), JBUI.scale(12))
        }

        // Create message text area
        val messageText = JTextPane().apply {
            contentType = "text/html"
            // Use MessageFormatter to process the message and extract code blocks
            val messageWidth = getMessageWidth()
            val (htmlContent, _) = MessageFormatter.processMessage(content, messageWidth)
            text = htmlContent
            font = FontUtil.getBodyFont()
            isEditable = false
            isOpaque = false
            background = Color(0, 0, 0, 0) // Transparent
            foreground = if (isUser) JBColor.BLACK else JBColor.foreground()
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
