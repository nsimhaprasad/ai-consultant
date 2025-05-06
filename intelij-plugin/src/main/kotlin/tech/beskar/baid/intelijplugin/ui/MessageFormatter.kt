package tech.beskar.baid.intelijplugin.ui

import com.intellij.ui.JBColor
import com.intellij.util.ui.JBUI
import com.vladsch.flexmark.html.HtmlRenderer
import com.vladsch.flexmark.parser.Parser
import com.vladsch.flexmark.util.ast.Node
import com.vladsch.flexmark.util.data.MutableDataSet
import org.fife.ui.rsyntaxtextarea.RSyntaxTextArea
import tech.beskar.baid.intelijplugin.util.getMessageWidth
import org.fife.ui.rsyntaxtextarea.SyntaxConstants
import org.fife.ui.rtextarea.RTextScrollPane
import java.awt.BorderLayout
import java.awt.Color
import java.awt.Cursor
import java.awt.Dimension
import java.awt.FlowLayout
import java.awt.Font
import javax.swing.BorderFactory
import javax.swing.JButton
import javax.swing.JComponent
import javax.swing.JPanel
import javax.swing.JScrollPane

/**
 * Handles message formatting, styling, and code block rendering
 */
class MessageFormatter {
    companion object {
        // HTML styling for message content - base style without width (added dynamically)
        private const val HTML_WRAPPER_STYLE = "word-wrap: break-word; margin: 0; padding: 0; overflow-wrap: break-word;"
        
        // Markdown parser and renderer
        private val options = MutableDataSet()
        private val parser = Parser.builder(options).build()
        private val htmlRenderer = HtmlRenderer.builder(options).build()
        
        /**
         * Process a message and extract code blocks
         * @param message The raw message text
         * @return Pair of processed HTML and extracted code blocks
         */
        fun processMessage(message: String, messageWidth: Int): Pair<String, List<Triple<String, String, String>>> {
            // Step 1: Extract code blocks for separate handling with RSyntaxTextArea
            val codeBlockPattern = "```(?:([a-zA-Z0-9]+)\\s+)?([\\s\\S]*?)```".toRegex()
            val codeBlocks = mutableListOf<Triple<String, String, String>>()
            var codeBlockCounter = 0
            
            // Replace code blocks with unique placeholders that won't be processed by Markdown
            var processedMessage = message.replace(codeBlockPattern) { matchResult ->
                val language = matchResult.groupValues[1].ifEmpty { "text" } // Language identifier (default to "text")
                val codeContent = matchResult.groupValues[2].trim()
                val placeholder = "CODE_BLOCK_PLACEHOLDER_${codeBlockCounter++}"
                codeBlocks.add(Triple(placeholder, language, codeContent))
                // Use a special HTML comment that won't be affected by Markdown processing
                "<!-- ${placeholder} -->"
            }
            
            // Step 2: Pre-process numbered lists and bullet points before Markdown processing
            processedMessage = preProcessLists(processedMessage)
            
            // Step 3: Parse and render the processed text with Markdown
            val htmlrenderer = HtmlRenderer.builder(options).build()        
            val document: Node = parser.parse(processedMessage)
            var html: String = htmlrenderer.render(document) ?: ""
            
            // Step 4: Post-process the HTML to improve formatting and handle placeholders
            val cleanedHtml = postProcessHtml(html, codeBlocks)
            
            // Wrap the HTML in proper structure with styling
            val wrappedHtml = """
                <html>
                    <head>
                        <style>
                            body {$HTML_WRAPPER_STYLE width: ${messageWidth}px; max-width: ${messageWidth}px;}
                            p { margin: 0.5em 0; }
                            ol, ul { margin-top: 0.5em; margin-bottom: 0.5em; padding-left: 2em; }
                            li { margin-bottom: 0.8em; } /* Increased spacing between list items */
                            .list-item { display: block; margin-bottom: 1em; padding: 0.2em 0; } /* Custom list items with more spacing */
                            .list-marker { font-weight: bold; margin-right: 0.5em; } /* Make list markers stand out */
                            br + br { display: none; } /* Remove double line breaks */
                            .code-placeholder-wrapper { display: block; margin: 0.5em 0; } /* Wrapper for code placeholders */
                            .code-placeholder { display: none; } /* Hide code placeholders */
                        </style>
                    </head>
                    <body>$cleanedHtml</body>
                </html>
            """.trimIndent()
            
            return Pair(wrappedHtml, codeBlocks)
        }
        
        /**
         * Pre-process lists to ensure proper formatting
         * @param text The text to format
         * @return Text with list items properly marked for HTML rendering
         */
        private fun preProcessLists(text: String): String {
            var result = text
            
            // Process ordered lists (1., 2., etc.)
            val orderedListPattern = Regex("(^|\\n)(\\d+\\.)\\s(.+)")
            result = orderedListPattern.replace(result) { matchResult ->
                val prefix = matchResult.groupValues[1] // newline or start of text
                val number = matchResult.groupValues[2] // number with dot
                val content = matchResult.groupValues[3] // The actual list item content
                "${prefix}ORDERED_LIST_ITEM_${number}_START ${content} ORDERED_LIST_ITEM_END"
            }
            
            // Process unordered lists (* or -)
            val unorderedListPattern = Regex("(^|\\n)(\\*|-)\\s(.+)")
            result = unorderedListPattern.replace(result) { matchResult ->
                val prefix = matchResult.groupValues[1] // newline or start of text
                val marker = matchResult.groupValues[2] // * or -
                val content = matchResult.groupValues[3] // The actual list item content
                "${prefix}UNORDERED_LIST_ITEM_${marker}_START ${content} UNORDERED_LIST_ITEM_END"
            }
            
            // Replace standalone asterisks with newline markers
            // This handles cases like "* This is a point" where the asterisk is not at the start of a line
            result = result.replace(" * ", " STANDALONE_ASTERISK ") // Mark standalone asterisks
                      .replace("\\n * ", "\\n STANDALONE_ASTERISK ") // Mark asterisks after newline with space
            
            return result
        }
        
        /**
         * Post-process the HTML to improve formatting and handle placeholders
         * @param html The HTML to process
         * @param codeBlocks The list of code blocks to insert
         * @return Processed HTML with improved formatting
         */
        private fun postProcessHtml(html: String, codeBlocks: List<Triple<String, String, String>>): String {
            var result = html
            
            // Step 1: Fix common HTML spacing issues
            result = result
                .replace("<p><br></p>", "<br>") // Remove excessive paragraph spacing
                .replace("<br><br>", "<br>") // Fix double line breaks
                .replace("<body>\n<p>", "<body><p>") // Remove extra space at the top
                .replace("<body>\n<br>", "<body>") // Remove extra space at the top
            
            // Step 2: Process ordered list items
            val orderedListPattern = Regex("ORDERED_LIST_ITEM_(\\d+\\.)_START\\s(.+?)\\sORDERED_LIST_ITEM_END")
            result = orderedListPattern.replace(result) { matchResult ->
                val number = matchResult.groupValues[1]
                val content = matchResult.groupValues[2]
                "<div class='list-item'><span class='list-marker'>$number</span> $content</div>"
            }
            
            // Step 3: Process unordered list items
            val unorderedListPattern = Regex("UNORDERED_LIST_ITEM_([\\*-])_START\\s(.+?)\\sUNORDERED_LIST_ITEM_END")
            result = unorderedListPattern.replace(result) { matchResult ->
                val marker = if (matchResult.groupValues[1] == "*") "•" else "-"
                val content = matchResult.groupValues[2]
                "<div class='list-item'><span class='list-marker'>$marker</span> $content</div>"
            }
            
            // Step 3.5: Replace standalone asterisks with line breaks and bullet points
            result = result.replace(" STANDALONE_ASTERISK ", "<br>• ")
            
            // Step 4: Ensure code blocks are preserved as placeholders
            for ((placeholder, _, _) in codeBlocks) {
                // Convert HTML comments back to actual placeholders
                result = result.replace("<!-- ${placeholder} -->", "<div class='code-placeholder-wrapper' id='${placeholder}'>${placeholder}</div>")
                // Also handle any direct placeholders that might have escaped the HTML comments
                result = result.replace("<p>${placeholder}</p>", "<div class='code-placeholder-wrapper' id='${placeholder}'>${placeholder}</div>")
            }
            
            return result
        }
        
        /**
         * Create a syntax highlighted code block component
         * @param code The code content
         * @param language The programming language
         * @return A Swing component with the formatted code
         */
        fun createCodeBlock(code: String, language: String): JComponent {

            val messageWidth = getMessageWidth()

            // Pre-process code to handle long comments and strings better
            val processedCode = preprocessCode(code)
            
            val textArea = RSyntaxTextArea(processedCode).apply {
                syntaxEditingStyle = getSyntaxStyle(language)
                isEditable = false
                isCodeFoldingEnabled = true
                antiAliasingEnabled = true
                background = JBColor(Color(40, 44, 52), Color(40, 44, 52)) // Dark background
                foreground = JBColor(Color(171, 178, 191), Color(171, 178, 191)) // Light text
                caretColor = JBColor(Color(171, 178, 191), Color(171, 178, 191))
                currentLineHighlightColor = JBColor(Color(44, 49, 58), Color(44, 49, 58))
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

            val scrollPane = RTextScrollPane(textArea).apply {
                border = JBUI.Borders.empty()
                lineNumbersEnabled = true
                viewportBorder = JBUI.Borders.empty()
                horizontalScrollBarPolicy = JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED
                verticalScrollBarPolicy = JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED
                
                // Set height to fit all content without restriction
                val lineCount = processedCode.lines().size
                // Use 20 pixels per line to ensure all content is visible
                val optimalHeight = lineCount * 20 + 10

                // Set preferred size with calculated height
                preferredSize = Dimension(messageWidth, optimalHeight)
                
                // Ensure gutter (line numbers area) has proper styling
                gutter.background = JBColor(Color(30, 33, 39), Color(30, 33, 39))
                gutter.borderColor = JBColor(Color(30, 33, 39), Color(30, 33, 39))
                gutter.lineNumberColor = JBColor(Color(128, 128, 128), Color(128, 128, 128))
            }

            // Create a container with copy button
            val container = JPanel(BorderLayout()).apply {
                border = BorderFactory.createLineBorder(JBColor.border(), 1)
                background = JBColor(Color(40, 44, 52), Color(40, 44, 52))
                // Set maximum width to prevent code blocks from expanding too much
                // but allow unlimited height to show all content
                maximumSize = Dimension(JBUI.scale(600), Integer.MAX_VALUE)
                preferredSize = Dimension(messageWidth, Integer.MAX_VALUE)
            }
            container.add(scrollPane, BorderLayout.CENTER)
            
            val copyButton = JButton("Copy").apply {
                addActionListener {
                    textArea.selectAll()
                    textArea.copy()
                    textArea.select(0, 0)
                }
                background = JBColor(Color(97, 175, 239), Color(97, 175, 239))
                foreground = JBColor.BLACK
                border = BorderFactory.createEmptyBorder(3, 8, 3, 8)
                cursor = Cursor(Cursor.HAND_CURSOR)
            }
            
            val buttonPanel = JPanel(FlowLayout(FlowLayout.RIGHT)).apply {
                background = JBColor(Color(40, 44, 52), Color(40, 44, 52))
                add(copyButton)
            }
            container.add(buttonPanel, BorderLayout.NORTH)
            
            return container
        }
        
        /**
         * Determine syntax style based on language identifier
         * @param language The programming language identifier
         * @return The appropriate syntax style constant
         */
        /**
         * Pre-process code to improve line wrapping for comments and long strings
         * @param code The original code content
         * @return Processed code with improved line breaks
         */
        private fun preprocessCode(code: String): String {
            val maxLineLength = 80
            val lines = code.lines().toMutableList()
            
            for (i in lines.indices) {
                val line = lines[i]
                
                // Only process lines longer than the max length
                if (line.length <= maxLineLength) continue
                
                // More precise comment detection using regex patterns
                val trimmedLine = line.trim()
                val isComment = when {
                    // JavaScript/Java/C++/Kotlin style comments
                    Regex("^\\s*//").matches(trimmedLine) -> true
                    // Python/Shell style comments
                    Regex("^\\s*#").matches(trimmedLine) -> true
                    // SQL style comments
                    Regex("^\\s*--").matches(trimmedLine) -> true
                    // Multi-line comment starts
                    Regex("^\\s*/\\*").matches(trimmedLine) -> true
                    // Multi-line comment continuations
                    Regex("^\\s*\\*").matches(trimmedLine) -> true
                    // Not a comment
                    else -> false
                }
                
                if (isComment) {
                    // Find the comment prefix more precisely
                    val prefixMatch = Regex("^(\\s*)(//|#|--|/\\*|\\*)").find(line)
                    if (prefixMatch != null) {
                        val prefix = prefixMatch.groupValues[1] // Whitespace
                        val commentPrefix = prefixMatch.groupValues[2] // Comment marker
                        
                        // Calculate where the actual comment content starts
                        val contentStartIndex = prefix.length + commentPrefix.length
                        if (contentStartIndex < line.length) {
                            // Get the comment content
                            val commentContent = line.substring(contentStartIndex)
                            
                            // Calculate effective max length for chunks
                            val effectiveMaxLength = maxLineLength - prefix.length - commentPrefix.length - 1
                            
                            // Split the comment into chunks
                            val chunks = commentContent.chunked(effectiveMaxLength)
                            
                            // Replace the original line with the first chunk
                            lines[i] = "$prefix$commentPrefix ${chunks[0]}"
                            
                            // Add the remaining chunks as new lines
                            for (j in 1 until chunks.size) {
                                lines.add(i + j, "$prefix$commentPrefix ${chunks[j]}")
                            }
                        }
                    }
                }
            }
            
            return lines.joinToString("\n")
        }
        
        /**
         * Determine syntax style based on language identifier
         * @param language The programming language identifier
         * @return The appropriate syntax style constant
         */
        private fun getSyntaxStyle(language: String): String {
            return when (language.lowercase()) {
                "java" -> SyntaxConstants.SYNTAX_STYLE_JAVA
                "kotlin" -> SyntaxConstants.SYNTAX_STYLE_KOTLIN
                "python" -> SyntaxConstants.SYNTAX_STYLE_PYTHON
                "javascript", "js" -> SyntaxConstants.SYNTAX_STYLE_JAVASCRIPT
                "typescript", "ts" -> SyntaxConstants.SYNTAX_STYLE_TYPESCRIPT
                "html" -> SyntaxConstants.SYNTAX_STYLE_HTML
                "xml" -> SyntaxConstants.SYNTAX_STYLE_XML
                "css" -> SyntaxConstants.SYNTAX_STYLE_CSS
                "json" -> SyntaxConstants.SYNTAX_STYLE_JSON
                "sql" -> SyntaxConstants.SYNTAX_STYLE_SQL
                "bash", "sh" -> SyntaxConstants.SYNTAX_STYLE_UNIX_SHELL
                "c" -> SyntaxConstants.SYNTAX_STYLE_C
                "cpp", "c++" -> SyntaxConstants.SYNTAX_STYLE_CPLUSPLUS
                "csharp", "c#" -> SyntaxConstants.SYNTAX_STYLE_CSHARP
                "go" -> SyntaxConstants.SYNTAX_STYLE_GO
                "php" -> SyntaxConstants.SYNTAX_STYLE_PHP
                "ruby" -> SyntaxConstants.SYNTAX_STYLE_RUBY
                "scala" -> SyntaxConstants.SYNTAX_STYLE_SCALA
                "yaml" -> SyntaxConstants.SYNTAX_STYLE_YAML
                else -> SyntaxConstants.SYNTAX_STYLE_NONE
            }
        }
    }
}
