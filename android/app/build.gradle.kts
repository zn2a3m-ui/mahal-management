plugins { id("com.android.application") }

val signingStorePath = System.getenv("ANDROID_KEYSTORE_PATH")

android {
    namespace = "com.mahal.app"
    compileSdk = 35
    defaultConfig {
        applicationId = "com.mahal.app"
        minSdk = 23
        targetSdk = 35
        versionCode = 4
        versionName = "2.1.0"
    }
    signingConfigs {
        create("release") {
            if (!signingStorePath.isNullOrBlank()) {
                storeFile = file(signingStorePath)
                storePassword = System.getenv("ANDROID_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("ANDROID_KEY_ALIAS")
                keyPassword = System.getenv("ANDROID_KEY_PASSWORD")
            }
        }
    }
    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
        }
    }
}
