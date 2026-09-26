# Kilrun Privacy Policy

**Status:** Draft template. Replace every bracketed placeholder and verify the statements against the services and release you actually operate before publishing.

**Last updated:** September 26, 2026

**Maintainer / contact:** MinhbaoGDVN · minhbaom45@gmail.com

## 1. Scope

Kilrun is open-source client software distributed under the MIT License. This policy describes data handling by the Kilrun application as currently implemented. It does not replace the privacy policies of third-party API providers, model providers, hosting providers, or other services you choose to use.

The MIT License governs use, copying, modification, and distribution of the source code. It is not a privacy policy and does not grant control over third-party services or their data practices.

## 2. Information Kilrun handles

Depending on how you use the software, Kilrun may handle:

- Prompts, conversation history, model responses, and optional system prompts in the running process.
- Files you explicitly attach, including their contents and filenames.
- An API key supplied in the project `.env` file, if you choose to configure one.
- Local files created, read, or modified in the `workspace/` directory, and output from commands you approve.
- Chat history you explicitly save with `/save`, written as JSON files in the local `logs/` directory.

Kilrun does not intentionally collect account profiles, analytics, or telemetry in the client code described by this policy. Third-party services may collect technical or account information as part of their own operations.

## 3. Information sent to third parties

When you send a prompt, Kilrun sends the conversation context required for that request to the API endpoint configured by `KILGORE_BASE_URL` (default: `https://apidocs.kilgoreai.xyz`). The API provider may route requests to one or more model or feature providers to produce a response.

When you attach a file, Kilrun uploads it to that API service and includes its returned file reference in the chat request. The service may retain the upload or conversation according to its own policies and implementation. Do not attach information unless you are permitted to share it with those providers.

Image generation, text-to-speech, web search, model listing, and other API features send the relevant prompt or request data to the configured service and potentially its upstream providers.

Review the policies and terms of each service you use:

- KilgoreAI API: https://apidocs.kilgoreai.xyz/
- [Add links to any other API/model providers enabled in your deployment]

## 4. Local storage and security

Conversation history is held in memory while the application runs. It is written to `logs/` only when you use `/save`; that file remains on your device until you delete it. The API client may keep session cookies in memory for the lifetime of the process. An API key placed in `.env` is stored as ordinary local text; protect that file and do not commit or share it.

Agent file tools are intended to operate within `workspace/`. Shell and Python actions run on your machine and may access resources available to the local operating-system account; review each command and proposed file change before approving it. Workspace containment is not an operating-system sandbox.

Use appropriate device security, backups, access controls, and secret management. No software or transmission method can be guaranteed completely secure.

## 5. Retention and deletion

Kilrun does not automatically save local conversation logs unless `/save` is used. You can delete saved JSON logs and workspace files yourself. Files and conversations uploaded to a third-party service are subject to that service's retention and deletion controls; consult the service directly to request access to or deletion of those records.

**Provider-specific retention/deletion instructions:** [Add verified instructions and links for the API provider you distribute or recommend.]

## 6. Children and sensitive information

Kilrun is a developer tool and is not designed to collect information directly from children. Do not send sensitive personal, confidential, regulated, or third-party information to an API unless you have the necessary rights and the relevant providers are suitable for that data.

## 7. Your choices and rights

You control whether to configure an API key, send prompts, attach files, save local logs, or use optional API features. Depending on your location and the providers involved, you may have privacy rights concerning data processed by a provider. Contact the relevant provider to exercise rights over data it controls.

For questions about this policy or the Kilrun client, contact: [Privacy contact email].

## 8. Changes

This draft should be reviewed and updated when Kilrun's data flows, default API endpoint, or third-party providers change. The maintainer will update the date above when publishing a revised policy.

## 9. Legal note

This document is an informational template, not legal advice. The maintainer must verify it against actual operations and obtain legal review appropriate to the jurisdictions in which Kilrun is distributed or used.
