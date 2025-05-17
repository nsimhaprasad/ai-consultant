package tech.beskar.baid.intelijplugin.service

import com.intellij.openapi.diagnostic.Logger
import org.json.JSONObject
import tech.beskar.baid.intelijplugin.model.Block
import tech.beskar.baid.intelijplugin.model.ContentParser.parseBlock
import tech.beskar.baid.intelijplugin.model.ContentParser.parseJetbrainsResponse
import tech.beskar.baid.intelijplugin.model.ContentParser.parseResponse
import java.util.function.Consumer
import javax.swing.SwingUtilities


object StreamingResponseHandler {
    private val LOG = Logger.getInstance(StreamingResponseHandler::class.java)

    fun processJsonBlock(
        jsonObj: JSONObject,
        onBlock: Consumer<Block?>,
        onSessionId: Consumer<String?>
    ) {
        // Check if this is a session ID update
        if (jsonObj.has("session_id")) {
            val sessionId = jsonObj.optString("session_id", "")
            SwingUtilities.invokeLater { onSessionId.accept(sessionId) }
            return
        }


        // Process content blocks
        try {
            if (jsonObj.has("blocks")) {
                // Multiple blocks format
                val response =
                    parseResponse(jsonObj.toString())
                for (block in response.blocks) {
                    SwingUtilities.invokeLater { onBlock.accept(block) }
                }
            } else if (jsonObj.has("schema") && jsonObj.getString("schema") == "jetbrains-llm-response") {
                // JetBrains LLM response format
                val response =
                    parseJetbrainsResponse(jsonObj.toString())
                for (block in response.blocks) {
                    SwingUtilities.invokeLater { onBlock.accept(block) }
                }
            } else {
                // Single block format
                val block = parseBlock(jsonObj)
                SwingUtilities.invokeLater { onBlock.accept(block) }
            }
        } catch (e: Exception) {
            LOG.error("Error processing JSON block: $jsonObj", e)
            // Create an error block
            val errorBlock: Block = Block.Paragraph("Error processing response: " + e.message)
            SwingUtilities.invokeLater { onBlock.accept(errorBlock) }
        }
    }

    fun createErrorBlock(error: Throwable): Block {
        var message = "Sorry, I encountered an error: Please try again!"


        // Check for common error types
        if (error.message != null) {
            if (error.message!!.contains("401") || error.message!!.contains("403")) {
                message = "Your session has expired. Please sign in again."
            } else if (error.message!!.contains("timeout") || error.message!!.contains("timed out")) {
                message = "The request timed out. Please try again later."
            } else if (error.message!!.contains("connect")) {
                message = "Could not connect to the server. Please check your internet connection."
            }
        }

        return Block.Paragraph(message)
    }
}