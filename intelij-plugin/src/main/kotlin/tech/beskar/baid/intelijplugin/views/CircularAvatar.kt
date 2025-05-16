package tech.beskar.baid.intelijplugin.views

import com.intellij.ui.JBColor
import com.intellij.util.ui.GraphicsUtil
import java.awt.Color
import java.awt.Dimension
import java.awt.Graphics
import java.awt.Graphics2D
import java.awt.geom.Ellipse2D
import javax.swing.Icon
import javax.swing.JLabel
import kotlin.math.max


class CircularAvatarLabel : JLabel {
    private var backgroundColor: Color? = null

    constructor(text: String?) : super(text) {
        init()
    }

    constructor(icon: Icon?) : super(icon) {
        init()
    }

    constructor(text: String?, icon: Icon?) : super(text, icon, CENTER) {
        init()
    }

    private fun init() {
        setHorizontalAlignment(CENTER)
        setVerticalAlignment(CENTER)
        setOpaque(false)
        backgroundColor = JBColor.BLUE
    }

    fun setBackgroundColor(color: Color?) {
        this.backgroundColor = color
        repaint()
    }

    override fun paintComponent(g: Graphics) {
        // Set up anti-aliasing for smooth circle edges
        val g2d = g.create() as Graphics2D
        GraphicsUtil.setupAAPainting(g2d)


        // Create circular clipping shape
        val circle = Ellipse2D.Float(0f, 0f, getWidth().toFloat(), getHeight().toFloat())


        // Fill background
        if (icon == null) {
            // For text avatar, fill with background color
            g2d.color = backgroundColor
            g2d.fill(circle)
        }


        // Set clip to circle for icon or text rendering
        g2d.clip = circle

        if (icon != null) {
            // Draw the icon centered
            val iconWidth = icon.iconWidth
            val iconHeight = icon.iconHeight
            val x = (getWidth() - iconWidth) / 2
            val y = (getHeight() - iconHeight) / 2
            icon.paintIcon(this, g2d, x, y)
        } else {
            // Draw text
            g2d.color = getForeground()
            g2d.font = getFont()

            val fm = g2d.fontMetrics
            val text = getText()

            if (text != null && !text.isEmpty()) {
                val textWidth = fm.stringWidth(text)
                val textHeight = fm.ascent
                val x = (getWidth() - textWidth) / 2
                val y = (getHeight() + textHeight) / 2 - fm.descent
                g2d.drawString(text, x, y)
            }
        }

        g2d.dispose()
    }

    override fun isOpaque(): Boolean {
        return false // Always non-opaque for proper rendering
    }

    override fun getPreferredSize(): Dimension? {
        if (isPreferredSizeSet) {
            return super.getPreferredSize()
        }

        val size = max(getFont().getSize() * 2, 24)
        return Dimension(size, size)
    }

    override fun getMinimumSize(): Dimension? {
        if (isMinimumSizeSet) {
            return super.getMinimumSize()
        }
        return Dimension(24, 24)
    }
}