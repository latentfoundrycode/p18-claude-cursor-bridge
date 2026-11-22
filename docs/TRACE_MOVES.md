# Trace moves

This file records the instruction passages a pull request retires, rewords or moves out of `bridge/`. `trace-check.py --moves` reads it (R-077; docs/DESIGN.md, Change: the program release, T-MOVE).

## What the mode compares

The mode compares two sets of files: every `.md` file under `bridge/` except `bridge/cursor-bridge/CHANGELOG.md`, once at the base and once at HEAD. The base is the merge-base of HEAD with `origin/main`, or with the revision `--base` names.

A passage fails when it stands in a file that changed and appears in none of these files at HEAD. A passage reworded at HEAD counts as dropped. An entry this pull request adds can excuse a passage.

## The form of an entry

An entry is one line. Paste it from the failure the mode prints; never compose it by hand:

    - <the passage's hash: 64 lowercase hex digits> <its first eight words>

- **Normal form.** The mode uses the pinned mode's normal form:
  - a paragraph, list item or table has its whitespace collapsed to single spaces;
  - a fenced block keeps its lines, each with its trailing whitespace removed.
- **Hash.** The SHA-256 of the normal form's UTF-8 bytes.
- **First words.** The normal form's first eight whitespace-separated words, joined by single spaces. They are written with the pinned mode's escaping: every character outside printable ASCII becomes `\xhh`, `\uhhhh` or `\Uhhhhhhhh`, so every entry is ASCII.
- **What it excuses.** An entry excuses the one passage whose hash and first words both match it.

## Which entries are read

- **Only the range's.** The mode reads only the entries the range adds: the lines of this file added between the base and HEAD.
- **Earlier entries are never re-read.** An entry an earlier pull request added is not read again. It cannot excuse a later drop, and it causes no later failure.
- **An entry that excuses nothing is a finding.** An added entry that excuses no passage dropped in the range is reported.
- **Other lines are ignored.** A line not of the entry's form is not read.

The file stays after the merge. A change to it takes the full gate (`review-guard.py premerge-records`).

## Entries

- c5f8ee39b31e06981b027ed0b4f1b1725551827cece72ea6c45cc4cbf7747bbf **Before a push, every commit it publishes.** When
- 03ab2e5b8cb8f1a9129a84aa4591d6e7e2b30fef436ce627161b1bc5b2b29ee6 The brief opens with its header (the core's
- 0c072589e1a539c5921f30cf255cedf1ae19bb30e916fbf96c3ede774b9e133b **The loop (Phase 6, one increment).** 1 Checkpoint:
- 83b37fecef2529da9b7d4ebaeb4eb51ec72f9175d9bef6237a3aea418f89bc3e **CI green means the run of the pushed
- dc82b5d3a57038ec4a68adc4fe06879a106a8b37466ab19236911cbade916d2c The gate decides *whether* a branch may merge;
- 6fba56023fb431ab0d59ce9fdb5f3736af132335ee1a0fc0b4adffb5cfb330e2 2. **Only if both APPROVE and no gate-integrity
- adc6a2d4462fd8ed62281d84c0a5d973352d9fdd16f8a93c9f566a88074a0b25 **Completing the merge \u2014 do not depend on
- 3fba79ea0f77c8a56291b4666c03d7ab1969c35a2f64c9116436c03517fd81a6 So the model reviews gate the *authorisation*; the
- f732d7c5992f49e4bf0043d3801cb52e2e9ee3e9b9d3dd63010a810aa729ca94 **Do not use the CI status bar's blanket
- 34551f9ad92df915406021d171c4b0a05002d7e3e73a813dfbb4d64797ff123c After a run of what a builder wrote
- 45b102dc55443ef6ba8bc07d0a2cc7cac52690a4ce911d05678d99db05e15600 **Before every push.** Every commit the push publishes
- ba5e38e006deee02c4a76f22875902edeb5d647bf925d5a5e3bcd8dbb000334c When all four hold the merge is authorised.
- 10e1e62b1f912da34f11bfcbb4abab2bffbfca49c8702c66a2444b8f8b2abf01 **Then the stage's demonstration runs live:** the build
- 07b60bf4b1f57016e0aa39c1830915f640593ed7ad0c536e97b5716f9ab50c26 - The **weekly dependency scan**, `.github/workflows/dependency-scan.yml`, a workflow
- dded23983a6efee41e1dd787cebcf2d258e506c8a924e5cfb722fd0033b931b8 **Before a push, every commit it publishes.** When
- b9651360e736570bd6ecc11b14281586456adc87383bb8dd82d4425e61303b87 The re-reading below pushes working detail out of
- deac707043e1890ad15157af68fc9aa0d448e61baa790bff5dcc46a70a569477 It hashes every governance file against the release
- 10b6b8d2aa58d267ffc16cc1ec70e086bffcb85b4fbaf3b28b0b232218ad4951 - **The records' headers** (release B2) are a
- f2cc8fa3651a7c54b1c6a239417608a1ebdd8c981c8e034847e33149776fb66d It writes `Reports/Evaluations/<date>/unprocessed.md`: every entry absent from the
- 16b23d0e959e04dd593291e992678fbf7f45fdada8fbc563ed4d206bb51ea978 1b. **Read the weekly dependency scan and the
- 551ad3b34e72ffddeba1b6734711b5de943bf410bd95b936a41eb6e40383d7b5 ```bash gh workflow list --all --repo <owner>/<repo> ```
- 7ecf353c2f14d8b8f20fed70fd746c22867dd834c6c3b9b45decdd870e3f2ffb Any disabled state of the workflow (`disabled_inactivity`, `disabled_manually`)
- 1a85ea8b855118fb8c8f2971a3beda1882a479ee8d450020d28804e0f087fc89 ```bash gh run list --repo <owner>/<repo> --workflow dependency-scan.yml
- e62fb4168ad1da42b52fc9b235bd728aa2fa0628ea5c21409bd8d620b6066e48 The date is a day and the schedule
- 46d6d6efe2084c6023b686ff9f9541c827c8fe2a9667ef28e4586a72170d75ae ```bash gh run view <run id> --repo <owner>/<repo>
- c7f3fb4fed3ef1effdf12fb85a3d5487bd8c60ddc8e30b0f48330ae38959c496 Each project falls in one of three kinds,
- 67e31b4f615dca6384038bda5e3dfb60f2f22225e9efb23927cd65f932a0d761 - **A finding**: a completed run of the
- 5c4fdfeeffa77c4b6d932136a6f7a2e42365fa2580e4aa49e3fa70b9e1c360e1 - **A scanner failure**: the window's last completed
- 1a3a0ff7f396cbfb70088109ba9082e66d0b47dfea35520629de0ee8ea2ab4b8 - **No completed run since the previous evaluation**:
- ced258888c3e7451922913e9a8db3cd62bbb6d88f5d3308c1c942194db338a1c A window whose last completed run ended `success`,
- 4141f52ee499fe0c4c500f723229c66a4aa0a8b77b2bb741b1f7e6c68889e7f5 ```bash gh api repos/<owner>/<repo>/vulnerability-alerts ```
- 4edf43e6a39208d070f2573c8c2c9968d58ec8206e39070908488ac1189fa7ae answers 204 where the alerts are enabled and
- b5483b45345f0907b329a194405827e2b215bd13926dfb470948670d8ed7411f ```bash gh api --paginate "repos/<owner>/<repo>/dependabot/alerts?state=open" ```
- f92ea57514633b92af9aa4431b38a0c5b5ebb217bb00a32cdf4baa01bd3328ff lists the open alerts, every page of them,
- 06c6354e7e2b3cf5e57fa4cc2aa967517b78dff915c36d56c1168a153933ff49 54. **A pause writes the position down first.**
- e3faf1924a026a894f177ba5d84e88f9270a212d80e5ae0ded6dce455542786f - **CI / Pro (Semgrep).** Run the Semgrep
- e70de1ae7c5424841ada51607f4ccec78f22cc19f555e03ffcf4edfbb9c53518 8. **The weekly dependency scan, every project's.** The
- 9ce830264981344044dc75a8173b47e34b6703e6220fe337227448ac6f8969b6 - **Surfaced:** reAngle, 2026-10-10: rule 43 said to
- 9615a8b046933cd90a730fa73974b4e67d49c612c50879459bc3b11416b9a40e - **Correction (2026.10.10b):** the live position goes to
- 9b965e1f7aee4c2cc1bf60665e7820f8fb62365c0e3623db1193e88bb754863c - **Correction:** the merge policy's procedure (release A5):
- 70a074c9c6664a1b281532759102e416bd2704be071ec903bb78b558761aa128 - **Correction:** when a watch ends, the green
- b8ad6f7aa389f12204cea9bee6c021781738ad05713d1dda3b704a667503e5c9 **A vulnerability newly published in a pinned library
- 466957bf926585db51df1db23ec7a0412f8f8ec79685b0072f34c6b7685f7413 - *Default \u2014 via Cursor's CLI (no new
- ed43d42e216b6cfa43e1d24b4b42b2fae496d58610c0580ae718288bd42cb09a 1. **Prepare each branch in your own checkout**,
- 8b9cc2f8a3725bfe3fbeab6b3ed01f7fcd66ba92b142bc947c2513b01956ef4c 4. **When a builder finishes**, make step 4's
- a02266358924d79bc83373ab1bbf803806ff4779d611a7d5e8b4b51bfd0fe09b Never use Cursor's own `--worktree` option: it places
- 202f9c30b676c883cecb399c87b557cd97a1ecbec9a4cab683357ea293b4c3a0 **The mutants are yours; the engine is the
- 85aacbda3f645c7b30e0ca6853a99df4e8794b87f59a0f6c16878f0662c63873 - **Iterate** \u2014 something is wrong and you
- 56fb7ad692a8804d0b733030416c59a969e08a4eaecee9dcf2e1680c8bd7ea41 **Before every push.** Every commit the push publishes
- 88ede79b92feb26176fa3d58399ae6f91f7da810d2979459c8fce58b540702f0 When all four hold the merge is authorised.
- 6c26c5362ab69f55c5d4e64be1d4c32c959bd5f21123f224b969e370a0ec1b9a - `supervisor` *(default)* \u2014 you arm and complete
