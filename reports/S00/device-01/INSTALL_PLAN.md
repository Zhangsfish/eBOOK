# Concrete internal installation proposal

This is a proposal, not an executed Apple operation.

## Proposed eBOOK identity

| Field | Value |
|---|---|
| Platform | iOS, minimum iOS 17 |
| Bundle ID | `com.zhangsfish.ebook` |
| Version | `0.1.0` |
| App Store Connect working name | `eBOOK Reader Lab` (subject to name availability) |
| Primary language | Simplified Chinese (`zh-Hans`) |
| Internal SKU | `ebook-reader-lab-20261124` |
| Distribution | TestFlight Internal Only, owner as internal tester |
| Public availability / App Review | Not requested; do not submit |

The name is for a separate app record. Never reuse the Lecture Asset bundle ID,
app record or build/version identity for the ebook reader.

## Credential-preserving route

GitHub metadata confirms three App Store Connect secrets and the team variable
already exist in the owner's public `Zhangsfish/lecture-asset` repository; none
exist in `Zhangsfish/eBOOK`. Secret values were neither read nor copied.

After owner authorization, use a separate worktree/branch and explicitly triggered
eBOOK-only workflow in the existing signing repository. That workflow checks out
the exact tested eBOOK commit and reuses the proven unsigned-archive → automatic
distribution export path. The existing key stays in the existing repository's
encrypted Actions Secrets; expose it only to the signing step and delete the
ephemeral key file and raw logs afterward. Do not alter Lecture Asset source,
bundle ID, release branch, pending release workflow, or unrelated local files.

Create/verify eBOOK's own Bundle ID and App Store Connect app record in Apple's
official UI, then upload with `testFlightInternalTestingOnly = true`. Never
request the owner to post passwords, a P8/P12 key or UDID to chat/GitHub. Owner
handles any Apple login, verification code or legal prompt directly in Apple's UI.

Upload acceptance, Apple VALID processing, internal-group availability and owner
installation must each be observed. A green unsigned build is insufficient.

## Why a follow-up authorization is needed

`tasks/S00_READER_FOUNDATION.md`, Out of scope, says:
“Do not submit to App Store or TestFlight in this task.”

The new request authorizes phone-installation preparation. Explicitly confirm the
separate internal-TestFlight step and reuse of the existing signing pipeline
before changing Apple records or uploading. This requires no new paid plan and
does not authorize App Review or an App Store release.

## Current official references (checked 2026-11-24)

- Apple distinguishes Internal Only builds from App Store/external distribution:
  https://developer.apple.com/help/app-store-connect/test-a-beta-version/add-internal-testers/
- Current upload toolchain requirements:
  https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/
- New app records are created in the website, not the Apps REST API:
  https://developer.apple.com/documentation/appstoreconnectapi/apps
- Bundle identifiers remain bound to the app after first upload:
  https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleidentifier
