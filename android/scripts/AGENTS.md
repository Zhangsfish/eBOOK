# Build and delivery memory

Purpose: compile with existing official Android SDK/JDK, test, verify and package.
Do not install dependencies here without owner authorization. Prefer preinstalled
free standard CI tools. Internal upgrade key stays in ignored LOCAL storage only.
CI output must not expose an installable APK: encrypt binary artifacts to a local
transport public key; never include signing/transport private keys in Git or CI output.
