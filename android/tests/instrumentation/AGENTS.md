# Native test APK memory

Purpose: actual Android system file-picker, viewport, process restart and TTS service
validation. Uses only original fixtures; assets copied from tracked Tests/Fixtures
and reproducibly generated long TXT during build, not committed or shipped.

ReaderInstrumentation runs two phases separated by a real target process stop.
Original files are pushed only to the emulator Downloads folder and selected
through the real system document picker. The earlier custom FixtureProvider was
removed after it did not appear in the Android11 picker; do not count that attempt
as import validation. Test evidence lives in app-private files and is collected
from a rooted TEST VM (no Huawei phone root required). The PCM engine
deliberately returns one installed Chinese offline voice plus unsafe candidates to
exercise filtering. Its tone is NOT a Huawei voice or a user-listening assessment.
EngineModeReceiver is test-only, absent from production manifest and APK.

Screenshots/results go to emulator app external files and are encrypted before
CI publication. Actual Huawei device, voice inventory, thermal/battery and hardware
fold hinge checks remain NOT_RUN unless that specific device is connected.
