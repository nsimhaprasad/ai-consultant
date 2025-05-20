package tech.beskar.baid.intelijplugin.service

import com.intellij.diff.comparison.ComparisonManager
import com.intellij.diff.comparison.ComparisonPolicy
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.progress.DumbProgressIndicator
import com.intellij.openapi.progress.ProgressIndicator

enum class DiffHunkType {
    ADD,    // Lines added in the new version
    DELETE, // Lines removed from the old version
    CHANGE, // Lines changed between old and new
    EQUAL   // Lines that are the same (might be useful for context, but often omitted from active hunks)
}

data class DiffHunk(
    val type: DiffHunkType,
    val oldStartLine: Int, // 0-indexed, inclusive start line in the old text
    val oldEndLine: Int,   // 0-indexed, exclusive end line in the old text (or count of lines for DELETE)
    val newStartLine: Int, // 0-indexed, inclusive start line in the new text
    val newEndLine: Int,   // 0-indexed, exclusive end line in the new text (or count of lines for ADD/CHANGE)
    val newContentLines: List<String> = emptyList() // Added
)

class InlineDiffService {

    private val logger = Logger.getInstance(InlineDiffService::class.java)

    fun calculateLineDiffs(oldText: String, newText: String): List<DiffHunk> {
        val hunks = mutableListOf<DiffHunk>()
        val indicator: ProgressIndicator = DumbProgressIndicator.INSTANCE // Or a proper one if available contextually
        
        // Split newText into lines to easily access them by index
        val newTextLines = newText.lines()

        try {
            val comparisonManager = ComparisonManager.getInstance()
            val lineFragments = comparisonManager.compareLinesInner(
                oldText,
                newText,
                ComparisonPolicy.DEFAULT, // Or .IGNORE_WHITESPACE
                indicator
            )

            for (fragment in lineFragments) {
                val oldStart = fragment.startLine1
                val oldEnd = fragment.endLine1
                val newStart = fragment.startLine2
                val newEnd = fragment.endLine2
                
                // Based on LineFragment documentation:
                // - If startLine1 == endLine1, it's an ADD block in text2 from startLine2 to endLine2.
                // - If startLine2 == endLine2, it's a DELETE block in text1 from startLine1 to endLine1.
                // - Otherwise, it's a CHANGE block.
                // - Equal parts are usually not included in `compareLinesInner` directly unless it's a specific policy.
                //   The fragments represent differences.
                
                var currentNewContentLines: List<String> = emptyList()

                when {
                    oldStart == oldEnd && newStart < newEnd -> { // ADD
                        if (newStart < newEnd) { // Ensure there are lines to add
                            currentNewContentLines = newTextLines.subList(newStart, newEnd)
                        }
                        hunks.add(DiffHunk(DiffHunkType.ADD, oldStart, oldEnd, newStart, newEnd, currentNewContentLines))
                    }
                    newStart == newEnd && oldStart < oldEnd -> { // DELETE
                        // newContentLines remains emptyList()
                        hunks.add(DiffHunk(DiffHunkType.DELETE, oldStart, oldEnd, newStart, newEnd))
                    }
                    oldStart < oldEnd && newStart < newEnd -> { // CHANGE
                        if (newStart < newEnd) { // Ensure there are new lines for the change
                            currentNewContentLines = newTextLines.subList(newStart, newEnd)
                        }
                        hunks.add(DiffHunk(DiffHunkType.CHANGE, oldStart, oldEnd, newStart, newEnd, currentNewContentLines))
                    }
                    else -> {
                        logger.warn("Unexpected LineFragment: $fragment")
                    }
                }
            }
        } catch (e: Exception) {
            logger.error("Error calculating line diffs: ${e.message}", e)
            // Fallback or rethrow as appropriate
        }
        return hunks
    }
}
