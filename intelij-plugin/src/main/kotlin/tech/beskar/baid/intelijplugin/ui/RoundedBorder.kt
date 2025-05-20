package tech.beskar.baid.intelijplugin.ui

import com.intellij.ui.JBColor
import java.awt.*
import javax.swing.border.AbstractBorder

class RoundedBorder(
    private val color: Color = JBColor.GRAY,
    private val radius: Int = 12
) : AbstractBorder() {

    override fun paintBorder(c: Component, g: Graphics, x: Int, y: Int, width: Int, height: Int) {
        val g2d = g as Graphics2D
        g2d.setRenderingHint(
            RenderingHints.KEY_ANTIALIASING,
            RenderingHints.VALUE_ANTIALIAS_ON
        )
        
        val oldColor = g2d.color
        
        // Fill the background with rounded corners using the provided color
        g2d.color = color
        g2d.fillRoundRect(x, y, width, height, radius, radius)
        
        g2d.color = oldColor
    }

    override fun getBorderInsets(c: Component): Insets {
        return Insets(radius / 2, radius / 2, radius / 2, radius / 2)
    }

    override fun getBorderInsets(c: Component, insets: Insets): Insets {
        insets.left = radius / 2
        insets.top = radius / 2
        insets.right = radius / 2
        insets.bottom = radius / 2
        return insets
    }
}
