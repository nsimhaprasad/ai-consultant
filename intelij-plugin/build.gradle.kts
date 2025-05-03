plugins {
    id("java")
    id("org.jetbrains.kotlin.jvm") version "1.9.25"
    id("org.jetbrains.intellij") version "1.17.4"
}

group = "com.aiconsultant"
version = "1.1-SNAPSHOT"

repositories {
    mavenCentral()
}

// Configure Gradle IntelliJ Plugin
// Read more: https://plugins.jetbrains.com/docs/intellij/tools-gradle-intellij-plugin.html
intellij {
    // There are two approaches to configuring the plugin:

    // Approach 1: Use version and type (default)
    // This will download and use the specified version of IntelliJ
    // When running/debugging, it will launch a new instance of the specified type
    version.set("2024.1.7")
    // Uncomment one of these lines based on which IDE you want to target:
    // type.set("IC") // IntelliJ IDEA Community Edition
    // type.set("IU") // IntelliJ IDEA Ultimate Edition
    // type.set("CL") // CLion
    // type.set("PY") // PyCharm
    // type.set("PS") // PhpStorm
    // type.set("RD") // Rider
    // type.set("GO") // GoLand

    // Approach 2: Use localPath to target a specific IntelliJ installation
    // This will use the IDE at the specified path and won't launch a new instance
    // Uncomment and set the path to your IntelliJ installation:
    // localPath.set(System.getProperty("intellijPath", "/Applications/IntelliJ IDEA.app"))

    // You can pass the path as a system property when running Gradle:
    // ./gradlew runIde -DintellijPath=/path/to/your/intellij

    plugins.set(listOf(/* Plugin Dependencies */))
}

dependencies {
    implementation("org.json:json:20240303")
}

tasks {
    // Set the JVM compatibility versions
    withType<JavaCompile> {
        sourceCompatibility = "17"
        targetCompatibility = "17"
    }
    withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile> {
        kotlinOptions.jvmTarget = "17"
    }

    patchPluginXml {
        sinceBuild.set("241")
        untilBuild.set("243.*")
    }

    signPlugin {
        certificateChain.set(System.getenv("CERTIFICATE_CHAIN"))
        privateKey.set(System.getenv("PRIVATE_KEY"))
        password.set(System.getenv("PRIVATE_KEY_PASSWORD"))
    }

    publishPlugin {
        token.set(System.getenv("INTELLIJ_PUBLISH_TOKEN"))
    }
}
