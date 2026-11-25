# CI transport memory

Purpose: public encryption key for encrypted CI evidence transport, not APK signing.
`transport-public.pem` has no private material. The private counterpart is protected
with Windows DPAPI CurrentUser in the ignored task-private directory; never upload it.
Public CI publishes only an authenticated encrypted evidence bundle, no exposed APK.
Temporary emulator signing is disposable and unrelated to the local upgrade key.
