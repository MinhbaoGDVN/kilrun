# Kilrun Terms of Use

**Status:** Draft template. Replace every bracketed placeholder and obtain legal review before presenting these terms as binding.

**Last updated:** September 26, 2026

**Maintainer / contact:** MinhbaoGDVN · minhbaom45@gmail.com

## 1. About Kilrun

Kilrun is an open-source terminal application. Its source code is distributed under the MIT License in the `LICENSE` file. That license governs rights to use, copy, modify, merge, publish, distribute, sublicense, and sell copies of the software, subject to its stated conditions and disclaimer.

These terms describe use of the Kilrun project and any services the maintainer operates. They do not replace or alter the MIT License for the source code. If a provision here conflicts with the MIT License as applied to the software, the MIT License controls for those software rights.

## 2. Third-party services

Kilrun is a client and may connect to third-party APIs. The default API endpoint is `https://apidocs.kilgoreai.xyz`, and it can be changed with `KILGORE_BASE_URL`. AI inference, file processing, web search, image generation, speech generation, authentication, availability, pricing, and retention may be controlled by the service operator and its upstream providers, not by the Kilrun source-code maintainer.

Your use of an API or other third-party service is also subject to that provider's terms, privacy policy, limits, and acceptable-use rules. You are responsible for reviewing those terms and for any account, API key, or charges associated with your use.

## 3. Your responsibilities

You agree to use Kilrun and connected services lawfully. You are responsible for:

- Prompts, files, code, and other material you submit, and confirming you have the rights and permissions needed to use and share them with the selected providers.
- Reviewing AI-generated output before relying on, publishing, or executing it.
- Reviewing proposed file changes and commands before approving them.
- Protecting API keys and other credentials, including secrets stored in `.env`.
- Maintaining backups and checking the effect of commands on your own machine.

Do not use Kilrun to facilitate unlawful activity, violate others' rights, compromise systems without authorization, or bypass applicable provider policies. Nothing in these terms is intended to restrict lawful security research or other lawful uses.

## 4. Agent actions and local environment

Agent mode can create or modify files in `workspace/` and can run shell commands or Python code on your computer after you approve those actions. These commands execute with the permissions of your operating-system account. The workspace path check is not a general-purpose sandbox for arbitrary shell commands. You are responsible for evaluating commands and their effects before approval.

## 5. No warranties

Kilrun is provided on an “AS IS” basis to the maximum extent permitted by applicable law. The MIT License contains the software warranty disclaimer and limitation language. The maintainer does not warrant that Kilrun, any AI output, or any third-party API will be accurate, secure, uninterrupted, or fit for a particular purpose.

Third-party services are provided under their own terms. The Kilrun maintainer does not control and is not responsible for their availability, processing, model behavior, or policies.

## 6. Limitation of liability

To the maximum extent permitted by applicable law, the Kilrun software authors and maintainers are not liable for indirect, incidental, special, consequential, or punitive damages, loss of data, loss of profits, or damages resulting from use of the software, AI output, or third-party services. Nothing in these terms excludes liability that cannot lawfully be excluded. The MIT License also applies to the software and includes its own disclaimer and limitation language.

**Review required:** Have local counsel adapt this section and confirm whether any consumer-protection laws require different language.

## 7. Suspension and third-party access

The maintainer may change or discontinue services they operate, subject to applicable law. Third-party providers may independently suspend access, change APIs, enforce limits, or discontinue service under their own terms.

## 8. Updates and legal note

These terms should be reviewed whenever the project, its operators, or its service integrations materially change. This draft is informational and is not legal advice. Obtain legal review for the jurisdictions where the software or any related service is offered.
