package tech.beskar.baid.intelijplugin.ui

import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBPanel
import com.intellij.ui.components.panels.VerticalLayout
import org.fife.ui.rsyntaxtextarea.RSyntaxTextArea
import org.fife.ui.rsyntaxtextarea.SyntaxConstants
import org.fife.ui.rtextarea.RTextScrollPane
import tech.beskar.baid.intelijplugin.model.Block
import tech.beskar.baid.intelijplugin.model.Parameters
import tech.beskar.baid.intelijplugin.util.getMessageWidth
import java.awt.Dimension
import java.awt.datatransfer.StringSelection
import java.awt.FlowLayout
import java.awt.BorderLayout
import javax.swing.JButton
import javax.swing.JComponent
import com.intellij.openapi.ide.CopyPasteManager
import com.intellij.ui.JBColor
import com.intellij.util.ui.JBUI
import java.awt.Color
import java.awt.Cursor
import java.awt.Font
import javax.swing.BorderFactory
import javax.swing.JScrollPane

/**
 * Renders parsed content blocks into Swing components.
 */
object ContentRenderer {
    fun renderHeading(block: Block.Heading): JComponent {
        val content = block.content
        val label = JBLabel(content)
        val font = when (block.level) {
            1 -> label.font.deriveFont(label.font.style or Font.BOLD, 22f)
            2 -> label.font.deriveFont(label.font.style or Font.BOLD, 18f)
            3 -> label.font.deriveFont(label.font.style or Font.BOLD, 16f)
            4 -> label.font.deriveFont(label.font.style or Font.BOLD, 14f)
            5 -> label.font.deriveFont(label.font.style or Font.BOLD, 12f)
            6 -> label.font.deriveFont(label.font.style or Font.BOLD, 10f)
            else -> label.font.deriveFont(label.font.style, 14f)
        }
        label.font = font
        label.border = getMessageWidth().let { com.intellij.util.ui.JBUI.Borders.empty(6) }
        println("Heading content: $content")
        return label
    }

    fun renderParagraph(block: Block.Paragraph): JComponent {
        try {
            // Process the content to handle markdown-style formatting
            val processedContent = processMarkdownFormatting(block.content)
            
            // Create the HTML with proper width constraints
            val html = "<html><div style='width:${getMessageWidth() - 20}px;'>$processedContent</div></html>"
            
            // Create and configure the label
            val label = JBLabel(html)
            label.border = JBUI.Borders.empty(4)
            return label
        } catch (e: Exception) {
            // Fallback to plain text if HTML rendering fails
            val fallbackPanel = JBPanel<JBPanel<*>>(BorderLayout())
            val plainLabel = JBLabel(block.content)
            plainLabel.border = JBUI.Borders.empty(4)
            fallbackPanel.add(plainLabel, BorderLayout.CENTER)
            return fallbackPanel
        }
    }

    fun renderCode(block: Block.Code): JComponent {
        val style = when (block.language.lowercase()) {
            "kotlin" -> SyntaxConstants.SYNTAX_STYLE_KOTLIN
            "java" -> SyntaxConstants.SYNTAX_STYLE_JAVA
            "javascript", "js" -> SyntaxConstants.SYNTAX_STYLE_JAVASCRIPT
            "xml", "html" -> SyntaxConstants.SYNTAX_STYLE_XML
            "python" -> SyntaxConstants.SYNTAX_STYLE_PYTHON
            "ruby" -> SyntaxConstants.SYNTAX_STYLE_RUBY
            else -> SyntaxConstants.SYNTAX_STYLE_NONE
        }
        val textArea = RSyntaxTextArea().apply {
            syntaxEditingStyle = style
            text = block.content
            isEditable = false
            isCodeFoldingEnabled = true
            antiAliasingEnabled = true
            
            // Dark theme with higher contrast for better readability
            background = JBColor(Color(30, 30, 30), Color(25, 25, 25)) // Darker background
            foreground = JBColor(Color(220, 220, 220), Color(230, 230, 230)) // Brighter text for better contrast
            caretColor = JBColor(Color(220, 220, 220), Color(230, 230, 230))
            currentLineHighlightColor = JBColor(Color(45, 45, 45), Color(40, 40, 40)) // Subtle highlight
            font = Font(Font.MONOSPACED, Font.PLAIN, 13)
            tabSize = 4
            paintTabLines = true
            marginLinePosition = 80
            border = JBUI.Borders.empty(8)
            
            // Enhanced line wrapping settings
            lineWrap = true
            wrapStyleWord = false // Better for code
            
            // Use advanced line wrapping that preserves indentation
            setWrapStyleWord(false) // Don't wrap at word boundaries, but at any character
            setPaintTabLines(true) // Show tab guides
            setWhitespaceVisible(true) // Make whitespace visible for better readability
            setEOLMarkersVisible(false) // Hide EOL markers
            setMarkOccurrences(false) // Disable mark occurrences to avoid confusion
        }
        // Calculate a reasonable height based on content (with minimum and maximum limits)
        val lineCount = block.content.lines().size
        val calculatedHeight = Math.min(500, Math.max(100, lineCount * 20))
        
        val scroll = RTextScrollPane(textArea).apply {
            border = JBUI.Borders.empty()
            lineNumbersEnabled = true
            viewportBorder = JBUI.Borders.empty()
            horizontalScrollBarPolicy = JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED
            verticalScrollBarPolicy = JScrollPane.VERTICAL_SCROLLBAR_ALWAYS // Always show vertical scrollbar
            
            // Set reasonable preferred size that allows scrolling
            preferredSize = Dimension(getMessageWidth(), calculatedHeight)
            
            // Ensure gutter (line numbers area) has proper styling for dark theme
            gutter.background = JBColor(Color(25, 25, 25), Color(20, 20, 20)) // Slightly darker than main background
            gutter.borderColor = JBColor(Color(25, 25, 25), Color(20, 20, 20))
            gutter.lineNumberColor = JBColor(Color(150, 150, 150), Color(160, 160, 160)) // Brighter line numbers
        }
        // Wrap scroll and copy button in a panel
        val wrapper = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            border = BorderFactory.createLineBorder(JBColor(Color(60, 60, 60), Color(50, 50, 50)), 1) // Subtle border
            background = JBColor(Color(30, 30, 30), Color(25, 25, 25)) // Match text area background
            
            // Use the same calculated height as the scroll pane
            preferredSize = Dimension(getMessageWidth(), calculatedHeight)
            add(scroll, BorderLayout.CENTER)
        }
        // Copy button panel
        val copyBtn = JButton("Copy").apply {
            toolTipText = "Copy code"
            addActionListener { CopyPasteManager.getInstance().setContents(StringSelection(block.content)) }
            background = JBColor(Color(86, 156, 214), Color(86, 156, 214)) // VS Code-inspired blue
            foreground = JBColor(Color(255, 255, 255), Color(255, 255, 255)) // White text for better contrast
            border = BorderFactory.createEmptyBorder(3, 8, 3, 8)
            cursor = Cursor(Cursor.HAND_CURSOR)
        }
        val btnPanel = JBPanel<JBPanel<*>>(FlowLayout(FlowLayout.RIGHT)).apply {
            background = JBColor(Color(30, 30, 30), Color(25, 25, 25)) // Match container background
            isOpaque = true
            add(copyBtn)
        }
        wrapper.add(btnPanel, BorderLayout.NORTH)
        return wrapper
    }

    fun renderCommand(block: Block.Command): JComponent {
        val panel = JBPanel<JBPanel<*>>(VerticalLayout(4))
        when (val params = block.parameters) {
            is Parameters.CreateFileParams -> {
                val link = JBLabel("<html><a href=\"#\">Create file: ${params.path}</a></html>")
                link.cursor = java.awt.Cursor.getPredefinedCursor(java.awt.Cursor.HAND_CURSOR)
                panel.add(link)
            }

            is Parameters.ExecuteGradleParams -> {
                val cmd = listOf(params.command).plus(params.args).joinToString(" ")
                val btn = JButton("Run Gradle: $cmd")
                panel.add(btn)
            }
        }
        return panel
    }

    /**
     * Renders list blocks into a vertical panel with bullet or numbered items.
     */
    /**
     * Render a list block (ordered or unordered)
     * Properly handles markdown-style formatting in list items
     */
    fun renderList(block: Block.ListBlock): JComponent {
        val panel = JBPanel<JBPanel<*>>(VerticalLayout(8))
        panel.border = JBUI.Borders.empty(4, 8, 4, 8)
        
        try {
            block.items.forEachIndexed { idx, item ->
                // Create the list item prefix (bullet or number)
                val prefix = if (block.ordered) "${idx + 1}. " else "\u2022 "
                
                // Process the content to handle markdown-style formatting
                val processedContent = processMarkdownFormatting(item.content)
                
                // Create the HTML with proper width constraints and processed content
                val html = "<html><div style='width:${getMessageWidth() - 40}px;'><span style='font-weight:bold;'>$prefix</span> $processedContent</div></html>"
                
                // Create and configure the label
                val label = JBLabel(html)
                label.border = JBUI.Borders.empty(2)
                
                // Add to panel with try-catch to handle any rendering exceptions
                try {
                    panel.add(label)
                } catch (e: Exception) {
                    // Fallback to plain text if HTML rendering fails
                    val plainLabel = JBLabel("$prefix ${item.content}")
                    plainLabel.border = JBUI.Borders.empty(2)
                    panel.add(plainLabel)
                }
            }
        } catch (e: Exception) {
            // Add a fallback component if list rendering completely fails
            val errorLabel = JBLabel("<html><div style='color:red;'>Error rendering list: ${e.message}</div></html>")
            panel.add(errorLabel)
        }
        
        return panel
    }
    
    /**
     * Process markdown-style formatting in text
     * Converts **text** to <b>text</b>, etc.
     */
    private fun processMarkdownFormatting(text: String): String {
        var processed = text
        
        // Handle bold text (**text**)
        processed = processed.replace(Regex("\\*\\*(.*?)\\*\\*"), "<b>$1</b>")
        
        // Handle italic text (*text*)
        processed = processed.replace(Regex("(?<!\\*)\\*((?!\\*).+?)\\*(?!\\*)"), "<i>$1</i>")
        
        // Handle code (`text`)
        processed = processed.replace(Regex("`(.*?)`"), "<code>$1</code>")
        
        return processed
    }

    fun renderCallout(block: Block.Callout): JComponent {
        // Create a panel with vertical layout and some padding
        val panel = JBPanel<JBPanel<*>>(BorderLayout())
        
        // Get background and border colors based on callout style
        val (bgColor, borderColor) = getCalloutColors(block.style)
        
        // Set panel styling
        panel.border = BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(borderColor, 1),
            JBUI.Borders.empty(12)
        )
        panel.background = bgColor
        
        // Create a container for the content with vertical layout
        val contentPanel = JBPanel<JBPanel<*>>(VerticalLayout(8))
        contentPanel.background = bgColor
        
        // Create and style the title
        val titleLabel = JBLabel("<html><b>${block.title}</b></html>")
        titleLabel.font = titleLabel.font.deriveFont(Font.BOLD, 14f)
        titleLabel.foreground = JBColor.foreground()
        
        // Process the content to preserve newlines
        val processedContent = block.content.replace("\n", "<br>")
        val contentLabel = JBLabel("<html><div style='width:${getMessageWidth() - 30}px;'>$processedContent</div></html>")
        contentLabel.foreground = JBColor.foreground()
        
        // Add components to the content panel
        contentPanel.add(titleLabel)
        contentPanel.add(contentLabel)
        
        // Add content panel to the main panel
        panel.add(contentPanel, BorderLayout.CENTER)
        
        return panel
    }
    
    /**
     * Get appropriate colors for a callout based on its style
     */
    private fun getCalloutColors(style: String): Pair<Color, Color> {
        return when (style.lowercase()) {
            "info" -> Pair(
                JBColor(Color(232, 246, 250), Color(38, 70, 83)),
                JBColor(Color(88, 166, 255), Color(56, 114, 159))
            )
            "warning" -> Pair(
                JBColor(Color(255, 244, 229), Color(66, 50, 31)),
                JBColor(Color(247, 174, 45), Color(191, 134, 38))
            )
            "error" -> Pair(
                JBColor(Color(253, 237, 237), Color(61, 35, 35)),
                JBColor(Color(249, 62, 62), Color(204, 55, 55))
            )
            "success" -> Pair(
                JBColor(Color(230, 246, 230), Color(38, 77, 38)),
                JBColor(Color(80, 200, 120), Color(76, 175, 80))
            )
            else -> Pair(
                JBColor(Color(242, 242, 242), Color(50, 50, 50)),
                JBColor(Color(204, 204, 204), Color(100, 100, 100))
            )
        }
    }
}
