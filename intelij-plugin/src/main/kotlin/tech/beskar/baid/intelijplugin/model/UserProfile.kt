package tech.beskar.baid.intelijplugin.model

import com.intellij.openapi.application.ApplicationManager
import tech.beskar.baid.intelijplugin.model.common.Email // Added import
import tech.beskar.baid.intelijplugin.model.common.UserId
import com.intellij.util.ui.UIUtil
import org.json.JSONObject
import java.awt.Image
import java.awt.RenderingHints
import java.awt.geom.Ellipse2D
import java.awt.image.BufferedImage
import java.net.URL
import java.util.*
import java.util.function.Consumer
import javax.imageio.ImageIO
import javax.swing.ImageIcon
import javax.swing.SwingUtilities


class UserProfile
(
    val id: UserId?, val name: String?, val email: Email?, val picture: String? // Changed email to Email?
) {
    private var profileImage: ImageIcon? = null
    private var imageLoaded = false

    val initial: String
        get() {
            if (name != null && !name.isEmpty()) {
                return name.substring(0, 1).uppercase(Locale.getDefault())
            }
            return "U"
        }

    fun loadProfileImage(size: Int, callback: Consumer<ImageIcon?>) {
        if (picture == null || picture.isEmpty()) {
            callback.accept(null)
            return
        }


        // If already loaded, return the cached image
        if (imageLoaded && profileImage != null) {
            callback.accept(profileImage)
            return
        }


        // Load image in background
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val url = URL(picture)
                val originalImage = ImageIO.read(url)

                if (originalImage == null) {
                    SwingUtilities.invokeLater { callback.accept(null) }
                    return@executeOnPooledThread
                }


                // Create circular image
                val circularImage = createCircularImage(originalImage, size)
                val icon = ImageIcon(circularImage)


                // Cache the image
                this.profileImage = icon
                this.imageLoaded = true


                // Return the image via callback on EDT
                SwingUtilities.invokeLater { callback.accept(icon) }
            } catch (e: Exception) {
                println("Error loading profile image: " + e.message)
                SwingUtilities.invokeLater { callback.accept(null) }
            }
        }
    }

    private fun createCircularImage(source: BufferedImage, size: Int): BufferedImage {
        val output = UIUtil.createImage(size, size, BufferedImage.TYPE_INT_ARGB)
        val g2d = output.createGraphics()

        try {
            // Configure for high quality
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
            g2d.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC)


            // Create circular shape
            val circle = Ellipse2D.Float(0f, 0f, size.toFloat(), size.toFloat())
            g2d.setClip(circle)


            // Scale the image to fit
            val scaledImage = source.getScaledInstance(size, size, Image.SCALE_SMOOTH)


            // Draw the image centered
            g2d.drawImage(scaledImage, 0, 0, null)
        } finally {
            g2d.dispose() // Always clean up the graphics context
        }

        return output
    }

    companion object {
        fun fromJson(userJson: JSONObject): UserProfile {
            val idValue = userJson.optString("id", userJson.optString("sub", null)) // Get "id" or "sub", default to null if neither
            val userId = idValue?.let { UserId(it) } // Create UserId if idValue is not null

            val name = userJson.optString("name", "")
            val emailString = userJson.optString("email", null) // Get email as string, default to null
            val emailObject = emailString?.takeIf { it.isNotBlank() }?.let { Email(it) } // Create Email?
            val picture = userJson.optString("picture", null)

            return UserProfile(userId, name, emailObject, picture) // Use emailObject
        }
    }
}