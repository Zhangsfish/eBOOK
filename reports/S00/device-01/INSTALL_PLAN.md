# Concrete internal installation proposal

This records the owner-authorized internal installation follow-up. Execution
states are recorded separately in DELIVERY.md; this document is not upload evidence.

## Proposed eBOOK identity

| Field | Value |
|---|---|
| Platform | iOS, minimum iOS 17 |
| Bundle ID | `com.zhangsfish.ebook` |
| Version | `0.1.0` |
| App Store Connect working name | `eBOOK Reader Lab` (subject to name availability) |
| Primary language | Simplified Chinese (`zh-Hans`) |
| Internal SKU | `ebook-reader-lab-20261124` |
| App Store Connect app record | `6838578846`, created in Apple's official UI on 2026-11-24 |
| Distribution | TestFlight Internal Only, owner as internal tester |
| Public availability / App Review | Not requested; do not submit |

The name is for a separate app record. Never reuse the Lecture Asset bundle ID,
app record or build/version identity for the ebook reader.

The owner completed the Apple login directly in the in-app browser. The explicit
Bundle ID and the Simplified Chinese/iOS app record above were created and read
back successfully. The new TestFlight page initially showed no uploaded builds.
No App Review, storefront availability or legal declaration was submitted.

## Credential-preserving route

GitHub metadata confirms three App Store Connect secrets and the team variable
already exist in the owner's public `Zhangsfish/lecture-asset` repository; none
exist in `Zhangsfish/eBOOK`. Secret values were neither read nor copied.

Use a separate worktree/branch and explicitly triggered
eBOOK-only workflow in the existing signing repository. That workflow checks out
the exact tested eBOOK commit and reuses the proven unsigned-archive → automatic
distribution export path. The existing key stays in the existing repository's
encrypted Actions Secrets; expose it only to the signing step and delete the
ephemeral key file and raw logs afterward. Do not alter Lecture Asset source,
bundle ID, release branch, pending release workflow, or unrelated local files.

The helper branch is `Zhangsfish/lecture-asset:codex/ebook-device-installation`,
current code `68ec0136774cb147004887ee79e0c1d099c41c01`; reader checkout is pinned to
`1e556ae1622b4d56fa3c0c9e05ca0a14877073ac`. The existing manual workflow ID is
reused on that branch only, without merging/changing the default release workflow.
Prepare-only run https://github.com/Zhangsfish/lecture-asset/actions/runs/45324168773
passed real Xcode/Swift preflight and the unsigned device archive with no Apple
credentials. This is not signing/upload evidence.

The separate upload run
https://github.com/Zhangsfish/lecture-asset/actions/runs/45325301937
then exported/uploaded `0.1.0 (35.1)` and read Apple processing status VALID.
The UI showed the Internal badge and Ready to Test, and the manually managed
Owner iPhone group has one build/one existing owner tester. The owner reported
successful iPhone installation and launch. No Lecture Asset build was uploaded.

Create/verify eBOOK's own Bundle ID and App Store Connect app record in Apple's
official UI, then upload with `testFlightInternalTestingOnly = true`. Never
request the owner to post passwords, a P8/P12 key or UDID to chat/GitHub. Owner
handles any Apple login, verification code or legal prompt directly in Apple's UI.

Upload acceptance, Apple VALID processing, internal-group availability and owner
installation must each be observed. A green unsigned build is insufficient.

## Scope of the later installation instruction

`tasks/S00_READER_FOUNDATION.md`, Out of scope, says:
“Do not submit to App Store or TestFlight in this task.”

That exclusion applied to the original S00 development task. The owner then
explicitly requested parallel phone installation/testing after S00 merged. This
separate instruction authorizes the internal-TestFlight route needed on the
owner's Windows/iPhone setup, including eBOOK-specific app records and reuse of
the existing signing pipeline. No new paid plan, App Review, public release or
new credential request is authorized. Do not turn the old task's scope into a
redundant approval requirement for this later owner-requested installation.

## Current official references (checked 2026-11-24)

- Apple distinguishes Internal Only builds from App Store/external distribution:
  https://developer.apple.com/help/app-store-connect/test-a-beta-version/add-internal-testers/
- Current upload toolchain requirements:
  https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/
- New app records are created in the website, not the Apps REST API:
  https://developer.apple.com/documentation/appstoreconnectapi/apps
- Bundle identifiers remain bound to the app after first upload:
  https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleidentifier
