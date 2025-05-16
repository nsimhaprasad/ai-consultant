package tech.beskar.baid.intelijplugin.model

data class ContentResponse(
    val blocks: List<Block>
)

sealed class Block {
    data class Paragraph(
        val content: String,
    ) : Block()

    data class Code(
        val language: String,
        val content: String,
        val executable: Boolean
    ) : Block()

    data class Command(
        val commandType: CommandType,
        val target: Target,
        val parameters: Parameters
    ) : Block()
    data class ListBlock(
        val ordered: Boolean,
        val items: List<Paragraph>
    ) : Block()
    data class Heading(
        val level: Int,
        val content: String
    ) : Block()
    data class Callout(
        val style: String,
        val title: String,
        val content: String
    ) : Block()
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
    ) : Parameters()

    data class ExecuteGradleParams(
        val command: String,
        val args: List<String>
    ) : Parameters()
}
