# Third-party notices / Avisos de terceiros

**English.** Auto Translate Mods uses the open-source projects below. Each keeps its own copyright and license; the license text of each
project is the authoritative one, and this list is a courtesy summary. Nothing here is legal advice.

**Português.** O Auto Translate Mods usa os projetos de código aberto abaixo. Cada um mantém os seus direitos autorais e a sua licença; vale
o texto da licença de cada projeto, e esta lista é só um resumo de cortesia. Nada aqui é aconselhamento jurídico.

## In the mod (the game DLL) / No mod (a DLL do jogo)

| Project | Use | License |
|---|---|---|
| [Harmony](https://github.com/pardeike/Harmony) by Andreas Pardeike (the "Harmony" RimWorld mod, [Steam Workshop](https://steamcommunity.com/workshop/filedetails/?id=2009463077)) | patches the game at run time; it is a **required mod**, not included in this mod | MIT |

## In the helper program (UniversalTranslate-Helper.exe) / No programa auxiliar

| Project | Use | License |
|---|---|---|
| [CTranslate2](https://github.com/OpenNMT/CTranslate2) (OpenNMT) | runs the translation models on the CPU | MIT |
| [SentencePiece](https://github.com/google/sentencepiece) (Google) | splits text into the pieces the models use | Apache-2.0 |
| [NumPy](https://numpy.org/) | numeric arrays used by CTranslate2 | BSD-3-Clause |
| [PyYAML](https://pyyaml.org/) | configuration files read by CTranslate2 | MIT |
| [Python](https://www.python.org/) (with Tcl/Tk for the window) | the language and window toolkit packed in the .exe | PSF License; Tcl/Tk license |
| [PyInstaller](https://pyinstaller.org/) | builds the single-file .exe | GPL-2.0-or-later **with an exception** that allows bundling it with programs under any license |

## Translation models / Modelos de tradução

The program downloads translation models from the [Argos Translate](https://github.com/argosopentech/argos-translate) project
(Argos Translate itself is MIT-licensed; the model list is on [argospm-index](https://github.com/argosopentech/argospm-index)).
**The models are not part of this repository, the mod or the .exe**: each person downloads them from the original source, once. The license of
each model is set by its authors and can differ between models; please check the model you use.

O programa baixa os modelos de tradução do projeto [Argos Translate](https://github.com/argosopentech/argos-translate) (o Argos Translate em
si é MIT; a lista de modelos fica no [argospm-index](https://github.com/argosopentech/argospm-index)). **Os modelos não fazem parte deste
repositório, do mod nem do .exe**: cada pessoa os baixa da fonte original, uma vez. A licença de cada modelo é definida pelos autores dele e pode
variar de um modelo para outro; confira a do modelo que você usa.

## Not included / Não incluídos

RimWorld, its art and its name belong to Ludeon Studios. The game's libraries are used only to build the mod (through the public reference
package) and are not redistributed here.

O RimWorld, a arte e o nome pertencem à Ludeon Studios. As bibliotecas do jogo são usadas só para compilar o mod (pelo pacote público de
referência) e não são redistribuídas aqui.
