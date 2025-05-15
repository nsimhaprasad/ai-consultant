package tech.beskar.baid.intelijplugin.api

import com.intellij.ui.components.JBPanel
import org.json.JSONObject
import tech.beskar.baid.intelijplugin.model.Block
import tech.beskar.baid.intelijplugin.model.ContentParser
import tech.beskar.baid.intelijplugin.ui.ContentRenderer
import java.awt.BorderLayout
import java.awt.Dimension
import java.awt.LayoutManager
import java.io.InputStream
import javax.swing.JComponent
import javax.swing.JPanel
import javax.swing.JTextPane
import javax.swing.SwingUtilities
import tech.beskar.baid.intelijplugin.util.getMessageWidth

class StreamingResponseHandler(
    private val onSessionIdReceived: (String?) -> Unit,
    private val onErrorReceived: (Exception, Boolean) -> Unit
) : ResponseHandler {

    override fun handleStreamingResponse(responseStream: InputStream, messagePanel: JPanel): String? {
        var updatedSessionId: String? = null
        var lineCount = 0

        try {
            // Get the bubble container from the message panel
            val bubbleContainer = findBubbleContainer(messagePanel)
                ?: throw IllegalStateException("Could not find bubble container in message panel")

            // Process the stream line by line
            responseStream.bufferedReader().use { reader ->
                while (true) {
                    val rawLine = reader.readLine() ?: break
                    lineCount++
                    
                    if (!rawLine.startsWith("data: ")) continue
                    val data = rawLine.substringAfter("data: ").trim()
                    
                    if (data == "[DONE]") break

                    // Accumulate JSON block, handling multi-line objects
                    val sb = StringBuilder().append(data)
                    var braceCount = data.count { it == '{' } - data.count { it == '}' }
                    
                    while (braceCount > 0) {
                        val nextLine = reader.readLine() ?: break
                        sb.append(nextLine)
                        braceCount += nextLine.count { it == '{' } - nextLine.count { it == '}' }
                    }
                    
                    val jsonStr = sb.toString()

                    // Parse and render the block
                    try {
                        val jsonObj = JSONObject(jsonStr)
                        
                        // Check if this is a session ID response
                        if (jsonObj.has("session_id")) {
                            updatedSessionId = jsonObj.optString("session_id", "")
                            break
                        }
                        
                        // Process content blocks
                        processContentBlock(jsonObj, bubbleContainer)
                    } catch (e: Exception) {
                        // Log error but continue processing
                        println("Error parsing block: $e")
                    }
                }
            }

            // Return the updated session ID
            return updatedSessionId
        } catch (e: Exception) {
            // Handle any errors during stream processing
            onErrorReceived(e, false)
            return null
        } finally {
            // If we got a session ID, notify the callback
            if (updatedSessionId != null) {
                onSessionIdReceived(updatedSessionId)
            }
        }
    }

    override fun handleError(error: Exception, isAuthError: Boolean) {
        onErrorReceived(error, isAuthError)
    }

    override fun onSessionIdReceived(sessionId: String?) {
        onSessionIdReceived.invoke(sessionId)
    }

    private fun processContentBlock(jsonObj: JSONObject, bubbleContainer: JPanel) {
        SwingUtilities.invokeLater {
            try {
                // First, check if this is a "Thinking..." message and remove it
                if (bubbleContainer.componentCount > 0) {
                    val firstComponent = bubbleContainer.getComponent(0)
                    if (firstComponent is JTextPane && firstComponent.text.contains("Thinking...")) {
                        bubbleContainer.remove(firstComponent)
                    }
                }
                
                if (jsonObj.has("response") && jsonObj.getJSONObject("response").has("content")) {
                    // Handle the structured response format
                    val content = jsonObj.getJSONObject("response").getJSONObject("content")
                    if (content.has("blocks")) {
                        // Process blocks from the content object
                        val blocks = content.getJSONArray("blocks")
                        for (i in 0 until blocks.length()) {
                            val blockJson = blocks.getJSONObject(i)
                            val block = ContentParser.parseBlock(blockJson)
                            val component = renderBlock(block)
                            component?.let {
                                bubbleContainer.add(it)
                                bubbleContainer.revalidate()
                                bubbleContainer.repaint()
                            }
                        }
                    }
                } else if (jsonObj.has("blocks")) {
                    // Process multiple blocks directly
                    val response = ContentParser.parseResponse(jsonObj.toString())
                    response.blocks.forEach { block ->
                        val component = renderBlock(block)
                        component?.let {
                            bubbleContainer.add(it)
                            bubbleContainer.revalidate()
                            bubbleContainer.repaint()
                        }
                    }
                } else {
                    // Process a single block
                    val block = ContentParser.parseBlock(jsonObj)
                    
                    // Special handling for code blocks to ensure proper syntax highlighting
                    val component = if (block is Block.Code) {
                        // Apply special preprocessing for code blocks as mentioned in memories
                        val codeComponent = ContentRenderer.renderCode(block)
                        // Ensure the code component has proper width constraints
                        codeComponent.maximumSize = Dimension(getMessageWidth(), Int.MAX_VALUE)
                        codeComponent
                    } else {
                        renderBlock(block)
                    }
                    
                    component?.let {
                        bubbleContainer.add(it)
                        bubbleContainer.revalidate()
                        bubbleContainer.repaint()
                    }
                }
            } catch (e: Exception) {
                // If parsing fails, add a simple error message
                val errorComponent = ContentRenderer.renderParagraph(
                    Block.Paragraph("Error processing response: ${e.message}")
                )
                bubbleContainer.add(errorComponent)
                bubbleContainer.revalidate()
                bubbleContainer.repaint()
            }
        }
    }

    private fun renderBlock(block: Block): JComponent? {
        return when (block) {
            is Block.Paragraph -> ContentRenderer.renderParagraph(block)
            is Block.Code -> ContentRenderer.renderCode(block)
            is Block.Command -> ContentRenderer.renderCommand(block)
            is Block.ListBlock -> ContentRenderer.renderList(block)
            is Block.Heading -> ContentRenderer.renderHeading(block)
            is Block.Callout -> ContentRenderer.renderCallout(block)
            else -> null
        }
    }

    private fun findBubbleContainer(messagePanel: JPanel): JPanel? {

        try {
            // For AI messages with BorderLayout
            val contentPanel = messagePanel.getComponent(0) as? JPanel
            if (contentPanel?.layout is BorderLayout) {
                // AI message structure
                return contentPanel.getComponent(1) as? JBPanel<*>
            } else if (contentPanel?.layout is LayoutManager) {
                // User message structure with FlowLayout
                for (i in 0 until (contentPanel?.componentCount ?: 0)) {
                    val component = contentPanel?.getComponent(i)
                    if (component is JBPanel<*>) {
                        return component
                    }
                }
            }
        } catch (e: Exception) {
            println("Error finding bubble container: ${e.message}")
        }
        
        return null
    }
}
