package tech.beskar.baid.intelijplugin.util

import com.intellij.icons.AllIcons
import com.intellij.openapi.application.ApplicationManager
import com.intellij.util.ui.JBUI
import com.intellij.util.ui.UIUtil
import tech.beskar.baid.intelijplugin.views.CircularAvatarLabel
import java.awt.Dimension
import java.awt.Image
import java.awt.RenderingHints
import java.awt.geom.Ellipse2D
import java.awt.image.BufferedImage
import java.net.URL
import javax.imageio.ImageIO
import javax.swing.ImageIcon
import javax.swing.JLabel

fun getMessageWidth(): Int {
    // Use a reasonable default width that works well for code blocks
    val defaultWidth = JBUI.scale(200)
    
    // Use 80% of default width for better fit, with min and max constraints
    return defaultWidth.coerceAtLeast(JBUI.scale(200)).coerceAtMost(JBUI.scale(500))
}


fun createAvatarLabel(picture: String?, size: Int = 24, leftPadding: Boolean = true): JLabel {
    return try {
        // Try to load the user profile
        CircularAvatarLabel("").apply {
            preferredSize = Dimension(size, size)
            border = if (leftPadding) {
                JBUI.Borders.emptyLeft(JBUI.scale(8))
            } else {
                JBUI.Borders.emptyRight(JBUI.scale(8))
            }
            verticalAlignment = JLabel.TOP

            ApplicationManager.getApplication().executeOnPooledThread {
                val profileIcon = picture?.let { loadProfileImage(it, size) }
                if (profileIcon != null) {
                    // Update UI on EDT
                    ApplicationManager.getApplication().invokeLater {
                        icon = profileIcon
                    }
                }
            }
        }
    } catch (e: Exception) {
        JLabel().apply {
            icon = AllIcons.General.User
            border = if (leftPadding) {
                JBUI.Borders.emptyLeft(JBUI.scale(8))
            } else {
                JBUI.Borders.emptyRight(JBUI.scale(8))
            }
            verticalAlignment = JLabel.TOP
            preferredSize = Dimension(size, size)
        }
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