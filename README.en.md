<h1 align="center">Universal Translate for RimWorld</h1>

<p align="center">
<a href="README.br.md"><img src="https://img.shields.io/badge/LANGUAGE-PORTUGU%C3%8AS-555555?style=for-the-badge" alt="Português"></a>
<a href="README.en.md"><img src="https://img.shields.io/badge/LANGUAGE-ENGLISH-2ea44f?style=for-the-badge" alt="English"></a>
<br>
<a href="https://steamcommunity.com/workshop/filedetails/?id=2009463077"><img src="https://img.shields.io/badge/REQUIRES-HARMONY-1b2838?style=for-the-badge&logo=steam&logoColor=white" alt="Harmony (Steam Workshop)"></a>
<a href="https://github.com/argosopentech/argos-translate"><img src="https://img.shields.io/badge/TRANSLATION_ENGINE-ARGOS_TRANSLATE-0366d6?style=for-the-badge&logo=github&logoColor=white" alt="Argos Translate (GitHub)"></a>
</p>

<div align="justify">

**Current version: 0.026** · [Download from the Releases tab](../../releases/latest)

Translates the other mods in your game into your language **automatically**, **without needing a translation mod for each mod**.
The translation runs **on your computer and for free**. After the model for your language is downloaded once, **no internet is needed**. Every translation is saved, so it is only done once.

> **Under development.** This project was made with the help of **Claude** (Anthropic's AI) and is still at an early stage (current version 0.026). See "Current status" below.

<h2 align="left">Compatibility</h2>

<table>
<tr><td width="22%"><b>Game</b></td><td align="justify">RimWorld <b>1.6</b> and <b>1.7</b> (1.7 is still in beta)</td></tr>
<tr><td width="22%"><b>System</b></td><td align="justify"><b>Windows</b> 10/11</td></tr>
<tr><td width="22%"><b>Original language of the mods</b></td><td align="justify"><b>Any</b>: the mod detects it by itself (English, Chinese, Russian, Portuguese, ...)</td></tr>
<tr><td width="22%"><b>Target language</b></td><td align="justify"><b>Only the 30 languages RimWorld itself offers</b>: Catalan, Chinese (Simplified), Chinese (Traditional), Czech, Danish, Dutch, English, Estonian, Finnish, French, German, Greek, Hungarian, Italian, Japanese, Korean, Korean (Fast Channel), Norwegian (Bokmål), Polish, Portuguese (Brazil), Portuguese (Portugal), Romanian, Russian, Slovak, Spanish (Castilian), Spanish (Latin America), Swedish, Turkish, Ukrainian and Vietnamese. Any other language is not offered. Each one has its own translation model, checked against the Argos Translate model list (the Spanish and Korean variants share one model), downloaded on demand.</td></tr>
</table>


<h2 align="left">How it works</h2>

1. The mod looks at the texts of your other mods (names, descriptions and interface texts) and **detects the language of each one** (for example, a mod written in Chinese or Portuguese).<br><sub>────────────</sub>
2. If the mod **already has a translation** (its own, or from another translation mod), it **does not translate**. The existing translation is the one that counts.<br><sub>────────────</sub>
3. What **has no translation** is translated, from the detected language to yours, by a program that runs on your PC (the **executable**). If the text is already in your language, it is left alone. Pairs without a direct model (e.g. Chinese → Portuguese) go through English, which is a bit slower and may lower the quality.<br><sub>────────────</sub>
4. If a mod causes a problem, **only that mod** is switched off. The others carry on as normal.

<h2 align="left">Why do I need the executable?</h2>

A RimWorld mod is just a set of files that runs **inside** the game and cannot load a translation engine (AI models are large and heavy). That is why the translation is done by a separate program, **UniversalTranslate-Helper.exe**, which runs on your computer, uses your CPU, works **offline** (it only downloads the model for your language once) and talks to the mod **only inside your own computer** (it does not go through the internet or your home network) and only answers requests that carry a password. **It only needs to be open while there is something new to translate.** What has already been translated is saved and the game shows it without the program; what has not been translated yet appears in the original language until you open the program.

<h2 align="left">Installation (step by step)</h2>

Download the two files from the **Releases** tab (right side of this page, newest version):
`UniversalTranslate-Helper.exe` (the program that translates) and `UniversalTranslate-Mod.zip` (the ready-made mod).

1. Install the **Harmony** mod from the [Steam Workshop](https://steamcommunity.com/workshop/filedetails/?id=2009463077).<br><sub>────────────</sub>
2. Extract the `AutoTranslate` folder from `UniversalTranslate-Mod.zip` into `RimWorld\Mods`.<br><sub>────────────</sub>
3. **Double-click** `UniversalTranslate-Helper.exe`. **A window** opens.<br><sub>────────────</sub>
4. The first time: pick the **target language** by name (it is chosen **here, in the executable**, and the game uses the same one) and wait for the model to download. **Keep the window open while you play RimWorld.** It is only needed while something is being translated during the game: **if everything is already translated, you no longer need it and can play with the program closed**. Note: texts that only exist inside the game (such as the action buttons of the Orders tab that some mods create in code) **cannot be translated beforehand**; for those, open the program **before** starting RimWorld and play with it open, so it translates and saves them in the cache. The next times they are already done. **If you translate or update mods while the game is open and do not see the translation applied, restart the game** so it is applied. Open it again when you install new mods or update one.<br><sub>────────────</sub>
5. Open RimWorld, enable [**Harmony**](https://steamcommunity.com/workshop/filedetails/?id=2009463077) and then **Auto Translate** (in that order) and start the game.<br><sub>────────────</sub>
6. The first time the translation takes a few minutes; afterwards it is instant. To speed it up, use the **Translate mods** tab of the executable (see below). The mod's settings are in **Options → Mods → Auto Translate**.

<h3 align="left">Windows warning when opening the <code>.exe</code></h3>

The executable **does not have a digital signature yet** (publisher certificate), and Windows is wary of programs from an "unknown publisher". **This is not a virus detection.** All the code is in this repository and the `.exe` is built automatically by GitHub (folder `.github/workflows`), so you can check how it is made.
- **"Windows protected your PC" (SmartScreen):** click **More info → Run anyway**.<br><sub>────────────</sub>
- **"Smart App Control blocked an app" (Windows 11):** this block **has no "run anyway" button**. Today the ways out are: turn off Smart App Control (Windows Security → App & browser control → Smart App Control settings), or wait for the signed version. **According to Microsoft's documentation, once it is turned off it cannot be turned on again without resetting Windows**, so only do this if you understand and accept that cost. Signing the executable is the definitive solution and **has not been done yet**.

**Steam Workshop:** the mod will be published there (planned). The executable will keep being downloaded here, from the Releases tab.

<h2 align="left">Updating</h2>

Open `UniversalTranslate-Helper.exe` and click **Check for updates**. If there is a new version, click **Update now**: it downloads from GitHub, checks the file, updates the executable **and the mod** (if it finds the RimWorld folder; **close the game first**) and restarts by itself. It also checks for updates when it opens.
- Only files from GitHub are accepted, and the downloaded file must match the hash (SHA-256) published in the Release. This protects against a corrupted download, but you are still trusting the repository.

<h2 align="left">Translate all mods at once ("Translate mods" tab, without opening the game)</h2>

In the **Translate mods** tab of the executable:
- It looks for the installed mods, **even those that are not enabled in the game**. Right above the buttons you see the **numbered list of the folders searched**: the default folders (RimWorld's `Mods` and the Steam Workshop, marked "default") and the ones you added with **Add folder** (marked "added by you"; they are saved and searched every time you open the program, together with the others). You can have several folders at once.<br><sub>────────────</sub>
- **Translate pending:** translates what has not been translated yet, with a **progress bar**, "X of N mods (%)", the **estimated time left** and a **table per mod** (source language, texts, words and state). At the end it shows the **summary** with the number of texts and words translated.<br><sub>────────────</sub>
- **Search mods:** if you installed new mods (or updated one) later, it recognizes which ones are **new** or **changed** and translates only those. **Redo everything** checks all of them again (what is already saved is not translated a second time).<br><sub>────────────</sub>
- **Stop:** interrupts; what has already been translated stays saved.<br><sub>────────────</sub>
- **Delete translations:** deletes all saved translations of the chosen language (it asks before deleting). The mods appear as new again. Your manual corrections (`overrides`) are kept.<br><sub>────────────</sub>
- **"Folder" column:** click "Open folder" on a mod's row to open its folder in the file explorer.<br><sub>────────────</sub>
- **Double-clicking a mod** (outside the "Folder" column) opens a window with three tabs: **Translated texts** (original and translation; the full text appears when you select it), **Translated words** (the same texts with the number of words of each) and **Not translated by the mod** (original, **existing translation** and the reason: "already has a translation", "already in your language", "no support", "failed"). If you change the window language while this screen is open, it changes language immediately.<br><sub>────────────</sub>
- The translations go in the same cache the game uses, so when you play they are already done. **If the game is already open**, it applies the translations **in real time, mod by mod**: as soon as the program finishes translating a mod, the game applies only what changed in that mod, without restarting and without reloading the others. **Without weighing the game down:** while the program is not translating, the game only looks at a tiny signal file every 5 seconds (almost zero cost); only while the signal exists does it check the files, every second and a half; when the program finishes, the game does a final check and goes quiet again. For example, when translating a pallet mod, the name and description of the pallets change on screen within moments. This is a head start: it reads the mods' XML files; texts that only exist during the game (or that depend on other mods) are translated by the mod on the spot, as always. **For those, open the program before starting RimWorld and play with it open**: the game asks for the translation, the program translates and saves it in the cache, and the next times it is already done. If the translation does not show up in the game, restart the game.

<h2 align="left">Log tab (what the program is doing)</h2>

- **Everything the game asks for:** each translation request from the game appears with the mod's name and the number of texts. Click the line and the details show **each original text with its translation** (for example, the "Search and rescue" button and the translation it got).<br><sub>────────────</sub>
- **Batch translation:** the start, each mod (how many texts, how many translated now, from the cache, already translated, already in your language, failures, words and whether there is no support) and the new translations saved.<br><sub>────────────</sub>
- **Models, updates, warnings and errors:** model downloads, update search and installation, and the program's warnings and errors, with the technical details.<br><sub>────────────</sub>
- **Filter, "Copy log", "Clear" and "Open logs folder".** The text of each line changes language together with the window.<br><sub>────────────</sub>
- **Limits:** the tab's list keeps the last 3000 lines and disappears when the program closes (the technical history stays in the `helper.log` file, in the logs folder). The game only shows up here while the program is open.

<h2 align="left">Mod options</h2>

In **Options → Mods → Auto Translate** (the screen follows your game's language):
- **Turn translations off:** a button that shows the original texts **instantly, without restarting**, so you can compare. Click again to go back to the translations.<br><sub>────────────</sub>
- **Keyboard shortcut:** click "Set shortcut" and press the key you want, alone or with Shift, Ctrl or Alt (for example, Shift + Tab). At any moment in the game, this shortcut switches the translations on and off **in real time**, with an on-screen notice. Choose a combination the game does not already use. It does not fire while you type in a text box.<br><sub>────────────</sub>
- **Target language:** it is chosen **in the executable**; here it only shows which one is in use. If you change it in the executable while the game is open, the mod notices and reloads by itself.<br><sub>────────────</sub>
- **Mod list:** for each mod you see what is going on and whether there is **support** for the chosen language ("supported", "NO SUPPORT" or "unknown" if the translator program is closed). Each mod has an **Enabled** switch and the choice of which translation to use: automatic (recommended), prefer the mod's own, prefer another translation mod's, or always automatic. With the "prefer" options, whatever the chosen source does not provide is translated automatically: no text stays in English because of the mode.<br><sub>────────────</sub>
- **Search mod:** a box above the list filters the mods by name or identifier (the counter shows, for example, 3/64).<br><sub>────────────</sub>
- **Apply to all shown:** a button with a menu to choose at once the translation for all the mods that appear in the list (use the search to pick only a group): automatic (recommended), prefer the mod's own, prefer another translation mod's, or always automatic. Mods you turned off, or that were turned off because of problems, are not touched. It takes effect when you close the options window.<br><sub>────────────</sub>
- **Diagnostics:** a button on each mod that copies a short report (the mod's state, how many texts are translated and applied, which ones are waiting, whether the translation file has that text and whether there is a nearly identical text). Paste it in a message to find out why a mod is not showing the translation. There is also a button that gathers the diagnostics of all mods in a text file.<br><sub>────────────</sub>
- **Advanced** (collapsed): what to translate (items, interface, descriptions), hiding the texts with odd accents from developer mode (see below), detailed log, logs folder, problem report and clearing the cache.

<h2 align="left">What it translates (and what not)</h2>

- **Translates:** names, descriptions and interface texts of mods (including the Orders-tab buttons that some mods create in code), and the **description of each mod on the Mods screen** (of the active mods).<br><sub>────────────</sub>
- **Does not translate:** texts written directly in the code of some mods, texts that are already in your language, and the game's official content.<br><sub>────────────</sub>
- **"Translation" files that only repeat the original text** (common: RimWorld's own tool creates files like this) **do not count as a translation**: those texts are translated. A real translation, made by the mod's author or by another mod, is respected.<br><sub>────────────</sub>
- **Language detection:** works well with long texts and with languages that have their own script (Chinese, Japanese, Korean, Russian...). In mods with few short Latin-script texts it assumes English and may be wrong (if that happens, send a problem report).<br><sub>────────────</sub>
- It is **automatic** translation: it may have mistakes. You can correct any text in the `overrides` file (see below) and your correction always wins.

<h2 align="left">Texts with odd accents in developer mode</h2>

With RimWorld's **developer mode** on, the game itself marks the texts that have no translation in the game's language by putting accents on the letters ("Séàrçh ànd rèsçùè"). It is a feature for translators, but it gets in the way of people who just want to play. The mod hides this and shows the original text (or the automatic translation, when there is one). You can turn it off in Options → Mods → Auto Translate → Advanced. If some mod stores the text at game start, restart the game after changing the option or developer mode.

<h2 align="left">Security of the connection between the game and the program</h2>

- The program only "listens" inside the computer itself (the technical address `127.0.0.1` means "this computer"; it is **not your IP** and is not reachable from the internet or from other devices on your network).<br><sub>────────────</sub>
- Every request needs a **random password** kept in your data folder; requests from web pages open in the browser are refused.<br><sub>────────────</sub>
- The program only knows how to translate text and download translation models: it **does not read, delete or run files** at anyone's request.<br><sub>────────────</sub>
- Honest limit: a malicious program already running in your Windows account could read the password, but that program would already have access to everything, with or without this mod. This code has not been through an independent audit.

<h2 align="left">Privacy and files</h2>

- **Nothing is sent over the internet.** The only thing downloaded is the translation model, once (and updates, if you click for them).<br><sub>────────────</sub>
- **Where the model comes from:** the open-source [**Argos Translate**](https://github.com/argosopentech/argos-translate) project. The model list is on its GitHub and the files are downloaded from `argos-net.com`. It is an anonymous download: **no account, no login, no key and no subscription to any service** (the program uses no online AI; the model does the translating, running on your computer). Honest limit: Argos's list carries no fingerprint (hash) of the models, so they are not verified after downloading, only protected by the secure connection (https).<br><sub>────────────</sub>
- Everything lives in `%LOCALAPPDATA%\RimWorldAutoTranslate`: models, saved translations (`cache`), your corrections (`overrides`) and logs (`logs`).<br><sub>────────────</sub>
- **License:** the code is free software under the [MIT license](LICENSE): you may use, copy, modify and redistribute it, including in other projects, as long as you keep the copyright notice; the program is provided "as is", with no warranty. **If you use or adapt this code (including in add-ons), please credit the author, peraquetocosta, and link to this repository.**<br><sub>────────────</sub>
- **Credits and third-party licenses** (Harmony, CTranslate2, SentencePiece, Argos Translate and others): see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

<h2 align="left">Current status (transparency)</h2>

This is an **early version** (current version 0.026), made with the help of Claude. The mod compiles against the RimWorld 1.6 API and the code passed the automated tests (including the executable's window test on GitHub's Windows), but it **has not yet been tested in depth inside RimWorld** nor with many real mods. Errors may appear, mainly with mods that touch the same texts. **Automatic translation is not 100% perfect**, but it is much better than playing with a mod that is not in your language. **If you find any mistake, please report it** (see "Problem or conflict with a mod?" below): it helps improve the project for everyone.

<h2 align="left">Problem or conflict with a mod?</h2>

1. In the game: **Options → Mods → Auto Translate → Advanced → Create problem report** (or the executable's **Problem report** button).<br><sub>────────────</sub>
2. A GitHub page and the report folder will open. **Drag the file** onto the page and send it.

The report shows which mod caused the problem and what happened. Your user name and personal folders are removed. Nothing is sent unless you attach it.

---
Change history: [CHANGELOG.md](CHANGELOG.md)

</div>
