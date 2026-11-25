# Build and delivery memory

Purpose: compile with existing official Android SDK/JDK, test, verify and package.
Do not install dependencies here without owner authorization. Prefer preinstalled
free standard CI tools. Owner2026-11-26 chose cloud signing with NO additional
local tool. Generate the upgrade key in a temporary mode0700 cloud folder,
transfer it only over SSH into local Windows DPAPI CurrentUser storage, verify
the encrypted round trip, then remove the cloud private key/password before
shutdown. No key/password in CI, source, reports or delivery. No local signer JAR.
CI output must not expose an installable APK: encrypt binary artifacts to a local
transport public key; never include signing/transport private keys in Git or CI output.
