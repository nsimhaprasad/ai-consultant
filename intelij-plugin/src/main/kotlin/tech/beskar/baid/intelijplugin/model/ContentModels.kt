package tech.beskar.baid.intelijplugin.model

import org.json.JSONArray
import org.json.JSONObject

data class ContentResponse(
    val blocks: List<Block>
)

sealed class Block {
    data class Paragraph(
        val content: String,
    ) : Block() {

        override fun toJson() = JSONObject().apply {
            put("type", "paragraph")
            put("content", content)
        }
    }

    data class Code(
        val language: String,
        val content: String,
        val executable: Boolean,
        val filename: String? // New field
    ) : Block() {

        override fun toJson() = JSONObject().apply {
            put("type", "code")
            put("language", language)
            put("content", content)
            put("executable", executable)
            filename?.let { put("filename", it) } // Add filename if not null
        }
    }

    data class Command(
        val commandType: CommandType,
        val target: Target,
        val parameters: Parameters
    ) : Block() {
        override fun toJson() = JSONObject().apply {
            put("type", "command")
            put("commandType", commandType.name.lowercase())
            put("target", target.name.lowercase())
            put("parameters", parameters.toJson())
        }
    }

    data class ListBlock(
        val ordered: Boolean,
        val items: List<Paragraph>
    ) : Block() {
        override fun toJson() = JSONObject().apply {
            put("type", "list")
            put("ordered", ordered)
            put("items", JSONArray().apply {
                items.forEach { put(it.toJson()) }
            })
        }
    }


    data class Heading(
        val level: Int,
        val content: String
    ) : Block(){
        override fun toJson() = JSONObject().apply {
            put("type", "heading")
            put("level", level)
            put("content", content)
        }
    }
    data class Callout(
        val style: String,
        val title: String,
        val content: String
    ) : Block() {
        override fun toJson() = JSONObject().apply {
            put("type", "callout")
            put("style", style)
            put("title", title)
            put("content", content)
        }
    }

    open fun toJson(): JSONObject = when (this) {
        is Paragraph -> toJson()
        is Code -> toJson()
        is Command -> toJson()
        is ListBlock -> toJson()
        is Heading -> toJson()
        is Callout -> toJson()
    }
    
    companion object {
        fun toJsonArray(blocks: List<Block>): JSONArray = JSONArray().apply {
            blocks.forEach { put(it.toJson()) }
        }
    }
}

enum class CommandType {
    CREATE,
    EXECUTE
}

enum class Target {
    FILE,
    GRADLE
}

sealed class Parameters {
    data class CreateFileParams(
        val path: String,
        val content: String
    ) : Parameters() {
        override fun toJson() = JSONObject().apply {
            put("type", "create_file")
            put("path", path)
            put("content", content)
        }
    }

    data class ExecuteGradleParams(
        val command: String,
        val args: List<String>
    ) : Parameters() {
        override fun toJson() = JSONObject().apply {
            put("type", "execute_gradle")
            put("command", command)
            put("args", JSONArray().apply { args.forEach { put(it) } })
        }
    }

    open fun toJson(): JSONObject = when (this) {
        is CreateFileParams -> toJson()
        is ExecuteGradleParams -> toJson()
    }
}
