import org.jetbrains.intellij.platform.gradle.TestFrameworkType
import org.jetbrains.intellij.platform.gradle.tasks.VerifyPluginTask

plugins {
    id("java")
    id("org.jetbrains.kotlin.jvm") version "2.0.21"  // Updated to Kotlin 2.0.21 for IntelliJ 2025.1+ compatibility
    id("org.jetbrains.intellij.platform") version "2.6.0"
}

group = "tech.beskar.baid"
version = "1.1.6"

repositories {
    mavenCentral()
    intellijPlatform {
        defaultRepositories()
    }
}

dependencies {
    implementation("org.json:json:20240303")
    implementation("com.vladsch.flexmark:flexmark-all:0.64.8")
    implementation("com.fifesoft:rsyntaxtextarea:3.3.3")

    intellijPlatform {
        intellijIdeaUltimate("2025.1.1")

        // Simplified bundled plugins
        bundledPlugins("com.intellij.java")

        // Test framework with correct import
        testFramework(TestFrameworkType.Platform)

        // Plugin verifier and signing tools
        pluginVerifier()
        zipSigner()

        // Note: instrumentationTools() is deprecated and no longer needed
    }
}

intellijPlatform {
    projectName = "Baid"

    pluginConfiguration {
        version = "1.1.5"

        // Plugin compatibility - updated for 2025.1+ with no upper limit
        ideaVersion {
            sinceBuild = "251"
            // Removed untilBuild to support all future versions
        }
    }

    publishing {
        token = providers.environmentVariable("INTELLIJ_PUBLISH_TOKEN")
    }

    signing {
        certificateChain = providers.environmentVariable("CERTIFICATE_CHAIN")
        privateKey = providers.environmentVariable("PRIVATE_KEY")
        password = providers.environmentVariable("PRIVATE_KEY_PASSWORD")
    }

    pluginVerification {
        ides {
            // Test against multiple IntelliJ IDEA versions for comprehensive compatibility
//            ide("IC", "2024.1.7")      // IntelliJ IDEA Community 2024.1.7
//            ide("IC", "2024.2.5")      // IntelliJ IDEA Community 2024.2.5
//            ide("IC", "2024.3.1.1")    // IntelliJ IDEA Community 2024.3.1.1
//            ide("IC", "2025.1.1")      // IntelliJ IDEA Community 2025.1.1 (latest)
//
//            ide("IU", "2024.1.7")      // IntelliJ IDEA Ultimate 2024.1.7
//            ide("IU", "2024.2.5")      // IntelliJ IDEA Ultimate 2024.2.5
//            ide("IU", "2024.3.1.1")    // IntelliJ IDEA Ultimate 2024.3.1.1
            ide("IU", "2025.1.1")      // IntelliJ IDEA Ultimate 2025.1.1 (latest)
        }

        // Configure failure levels for strict verification
        failureLevel.set(listOf(
            VerifyPluginTask.FailureLevel.COMPATIBILITY_PROBLEMS,
            VerifyPluginTask.FailureLevel.INVALID_PLUGIN,
            VerifyPluginTask.FailureLevel.NOT_DYNAMIC
        ))

        // Optionally verify against recommended IDEs automatically
        // recommended()  // Uncomment to use JetBrains recommended IDE versions
    }
}

tasks {
    withType<JavaCompile> {
        sourceCompatibility = "21"
        targetCompatibility = "21"
    }

    withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile> {
        // Updated to use compilerOptions instead of deprecated kotlinOptions
        compilerOptions {
            jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_21)
        }
    }
}