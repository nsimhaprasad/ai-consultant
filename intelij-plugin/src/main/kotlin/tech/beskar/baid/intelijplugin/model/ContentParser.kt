package tech.beskar.baid.intelijplugin.model

import org.json.JSONObject
import java.util.Base64

/**
 * Utility class for parsing content from JSON responses.
 */
object ContentParser {
    fun decodeBase64ToBytes(base64String: String): ByteArray {
        return Base64.getDecoder().decode(base64String)
    }

    fun decodeBase64ToString(base64String: String): String {
        val decodedBytes = decodeBase64ToBytes(base64String)
        return String(decodedBytes, Charsets.UTF_8)
    }

    fun decodeSafeJsonContent(encodedContent: String): String {
        return try {
            // Decode from base64 to bytes, then convert bytes to UTF-8 string
            String(Base64.getDecoder().decode(encodedContent), Charsets.UTF_8)
        } catch (e: Exception) {
            // If base64 decoding fails, assume it's using the fallback method (escaped newlines)
            encodedContent.replace("\\n", "\n").replace("\\r", "\r")
        }
    }

    fun parseResponse(json: String): ContentResponse {
        val root = JSONObject(json)
        val blocksJson = root.getJSONArray("blocks")
        val blocks = mutableListOf<Block>()
        for (i in 0 until blocksJson.length()) {
            val blockObj = blocksJson.getJSONObject(i)
            blocks.add(parseBlock(blockObj))
        }
        return ContentResponse(
            blocks = blocks
        )
    }

    fun parseJetbrainsResponse(json: String): ContentResponse {
        val root = JSONObject(json)

        // Check if this is the new format
        if (root.has("schema") && root.getString("schema") == "jetbrains-llm-response") {
            val responseObj = root.getJSONObject("response")

            // Ensure it's a content type response
            if (responseObj.has("type") && responseObj.getString("type") == "content") {
                val contentObj = responseObj.getJSONObject("content")

                if (contentObj.has("blocks")) {
                    val blocksJson = contentObj.getJSONArray("blocks")
                    val blocks = mutableListOf<Block>()

                    for (i in 0 until blocksJson.length()) {
                        val blockObj = blocksJson.getJSONObject(i)
                        blocks.add(parseBlock(blockObj))
                    }

                    return ContentResponse(blocks = blocks)
                }
            }
        }

        // Fallback to original parser if not in the expected format
        return parseResponse(json)
    }

    fun parseBlock(blockObj: JSONObject): Block = when (blockObj.getString("type")) {
        "paragraph" -> {
            val content = blockObj.getString("content")
            val formatting = mutableListOf<String>()
            blockObj.optJSONArray("formatting")?.let { arr ->
                for (j in 0 until arr.length()) formatting.add(arr.getString(j))
            }
            Block.Paragraph(content)
        }
        "code" -> {
            val language = blockObj.getString("language")
            val content = decodeSafeJsonContent(blockObj.getString("content"))
            val executable = blockObj.optBoolean("executable", false)
            Block.Code(language, content, executable)
        }
        "command" -> {
            val cmdType = CommandType.valueOf(blockObj.getString("commandType").uppercase())
            val target = Target.valueOf(blockObj.getString("target").uppercase())
            val paramsJson = blockObj.getJSONObject("parameters")
            val parameters = when (cmdType) {
                CommandType.CREATE -> Parameters.CreateFileParams(
                    path = paramsJson.getString("path"),
                    content = paramsJson.getString("content")
                )
                CommandType.EXECUTE -> Parameters.ExecuteGradleParams(
                    command = paramsJson.getString("command"),
                    args = paramsJson.optJSONArray("args")?.let { arr ->
                        List(arr.length()) { idx -> arr.getString(idx) }
                    } ?: emptyList()
                )
            }
            Block.Command(cmdType, target, parameters)
        }
        "list" -> {
            val ordered = blockObj.optBoolean("ordered", false)
            val itemsJson = blockObj.getJSONArray("items")
            val items = mutableListOf<Block.Paragraph>()
            for (i in 0 until itemsJson.length()) {
                val itemObj = itemsJson.getJSONObject(i)
                val content = itemObj.getString("content")
                val formatting = mutableListOf<String>()
                itemObj.optJSONArray("formatting")?.let { arr ->
                    for (j in 0 until arr.length()) formatting.add(arr.getString(j))
                }
                items.add(Block.Paragraph(content))
            }
            Block.ListBlock(ordered, items)
        }
        "heading" -> Block.Heading(
            blockObj.optInt("level", 1),
            blockObj.getString("content")
        )
        "callout" -> Block.Callout(
            blockObj.getString("style"),
            blockObj.getString("title"),
            blockObj.getString("content")
        )
        else -> throw IllegalArgumentException("Unknown block type: ${blockObj.getString("type")}")
    }
}
