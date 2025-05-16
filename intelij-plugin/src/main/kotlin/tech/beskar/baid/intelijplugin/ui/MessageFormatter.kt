package tech.beskar.baid.intelijplugin.ui

import com.vladsch.flexmark.html.HtmlRenderer
import com.vladsch.flexmark.parser.Parser
import com.vladsch.flexmark.util.ast.Node
import com.vladsch.flexmark.util.data.MutableDataSet


class MessageFormatter {
    companion object {
        // HTML styling for message content - base style without width (added dynamically)
        private const val HTML_WRAPPER_STYLE =
            "word-wrap: break-word; margin: 0; padding: 0; overflow-wrap: break-word;"

        // Markdown parser and renderer
        private val options = MutableDataSet()
        private val parser = Parser.builder(options).build()

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
                "<!-- $placeholder -->"
            }

            // Step 2: Pre-process numbered lists and bullet points before Markdown processing
            processedMessage = preProcessLists(processedMessage)

            // Step 3: Parse and render the processed text with Markdown
            val htmlrenderer = HtmlRenderer.builder(options).build()
            val document: Node = parser.parse(processedMessage)
            val html: String = htmlrenderer.render(document)

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
                            .code-placeholder-wrapper { display: block; margin: 0.8em 0; background-color: #1e1e1e; border-radius: 4px; } /* Wrapper for code placeholders with dark background */
                            .code-placeholder { display: none; } /* Hide code placeholders */
                            pre { background-color: #1e1e1e; color: #dcdcdc; padding: 10px; border-radius: 4px; } /* Style for pre elements to match code blocks */
                            code { background-color: #2d2d2d; color: #dcdcdc; padding: 2px 4px; border-radius: 3px; } /* Style for inline code */
                        </style>
                    </head>
                    <body>$cleanedHtml</body>
                </html>
            """.trimIndent()

            return Pair(wrappedHtml, codeBlocks)
        }

        private fun preProcessLists(text: String): String {
            var result = text

            // Process ordered lists (1., 2., etc.)
            val orderedListPattern = Regex("(^|\\n)(\\d+\\.)\\s(.+)")
            result = orderedListPattern.replace(result) { matchResult ->
                val prefix = matchResult.groupValues[1] // newline or start of text
                val number = matchResult.groupValues[2] // number with dot
                val content = matchResult.groupValues[3] // The actual list item content
                "${prefix}ORDERED_LIST_ITEM_${number}_START $content ORDERED_LIST_ITEM_END"
            }

            // Process unordered lists (* or -)
            val unorderedListPattern = Regex("(^|\\n)([*\\-])\\s(.+)")
            result = unorderedListPattern.replace(result) { matchResult ->
                val prefix = matchResult.groupValues[1] // newline or start of text
                val marker = matchResult.groupValues[2] // * or -
                val content = matchResult.groupValues[3] // The actual list item content
                "${prefix}UNORDERED_LIST_ITEM_${marker}_START $content UNORDERED_LIST_ITEM_END"
            }

            // Replace standalone asterisks with newline markers
            // This handles cases like "* This is a point" where the asterisk is not at the start of a line
            result = result.replace(" * ", " STANDALONE_ASTERISK ") // Mark standalone asterisks
                .replace("\\n * ", "\\n STANDALONE_ASTERISK ") // Mark asterisks after newline with space

            return result
        }

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
            val unorderedListPattern = Regex("UNORDERED_LIST_ITEM_([*-])_START\\s(.+?)\\sUNORDERED_LIST_ITEM_END")
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
                result = result.replace(
                    "<!-- $placeholder -->",
                    "<div class='code-placeholder-wrapper' id='${placeholder}'>${placeholder}</div>"
                )
                // Also handle any direct placeholders that might have escaped the HTML comments
                result = result.replace(
                    "<p>${placeholder}</p>",
                    "<div class='code-placeholder-wrapper' id='${placeholder}'>${placeholder}</div>"
                )
            }

            return result
        }
    }
}
