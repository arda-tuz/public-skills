---
name: "study-buddy"
description: "Personal study partner for any course and exam (quiz, midterm, final): sets up a self-updating study folder, explains topics top-down, maps past questions, tracks progress, builds practice exams and annotated slides. Use whenever the user studies a course (ders çalışma, vize, final, quiz, çıkmış sorular)."
metadata:
  version: "1.0.0"
---

# Study Buddy · system v3

Turns a course folder into a study system that maintains itself. Markdown files in `kb/` are the buddy's memory: course settings, a map of every file, learned preferences, exam analysis, progress. Read them at the start of every session, keep them current, and improve them from every piece of feedback. The skill installs and runs the system; the folder carries its own `AGENTS.md`, so any agent can continue it later.

## 1. Defaults (every new course starts with these)

They come from the user's first course (BIL420). `kb/course.md` and `kb/preferences.md` override them per course; the user's current message overrides everything.

**Explanation style = the default detail level.** The level of the slide-side notes the user liked:
- Big picture first: one or two sentences on what this is, what problem it solves, where it sits in the course. Then the parts in logical order, each with what it is in plain words and why it matters. Then exact details, numbers and the source's own terms. Then the exam angle: how it was or may be asked, and the trap.
- Plain, simple language in full sentences. Detailed but not padded: every sentence adds information. No telegraphic shorthand. The user should understand it without opening the slide.
- Define each term at first use and keep the source's (exam-language) term: "kimlik doğrulama (authentication)".
- Shape of one slide's notes: "Bu slayt ne anlatıyor: ...", numbered points ① ② explaining each marked item and why it matters, a "BİREBİR EZBERLE" line, the past question in full with the answer and why, then "TUZAK (ÇELDİRİCİ)".

**Language and format.** Turkish (the user's language), English technical term in parentheses at first use. Never the em dash; use "-". Visual first: comparison = table, process = numbered steps or diagram; inline visuals in chat when the environment has them. Practice questions in the exam's language and format.

**Asking the user.** Questions and answers between the user and the AI are a bulk conversation held by speech-to-text: the user dictates one long, free-form reply that answers many questions at once. So never use option cards (AskUserQuestion). Ask in plain chat, in bulk: every open question at once as one numbered list, each with your recommended default, so the user can answer everything in one go. Read the dictated answer carefully (it may cover the questions out of order or add new information), apply it, then ask again in bulk only about what is still missing; repeat until nothing is missing.

**Sources.** Original files are read-only: never edit, move, rename or delete them; derived content goes to `kb/` or output folders. Every claim carries its location (`Day 3 s.15`, `Kitap 4.2 s.112`). Fidelity is `strict` until the user chooses (section 5). Anything from outside the sources is labeled ("slayt dışı" / "kaynak dışı").

**Priorities.** Current-term material outweighs past terms. Focus on what is likely to be asked; mark low-yield parts. Ask what the user already knows and don't spend their time there.

**Outputs.** Notes in full sentences. Past questions shown verbatim: stem, all options, correct answer, why it is right and why the tempting distractors are wrong. When content doesn't fit, add pages; with annotated slides also give a standalone reading PDF with the same content. Every past question must land somewhere (coverage 100%).

**Self-contained by default.** Unless the user says otherwise, every explanation, page and document must be fully understandable on its own: reading it is enough, the user never has to open a slide, case file or other source to follow it. References (`Day 3 s.15`, `L1 s.11-15`) stay, but only as a trailing parenthetical for optional extra lookup; delete them in your head and every sentence must still be complete and true. Never write sentences that hand the meaning to the source ("as in the slide's example", "see the slide", "the slide says", "bkz."): state the content itself, and when you mention an example, case or code, explain it in the text (what the system is, which parts exist, what happens step by step). Even when citing, quote or paraphrase the needed part so the user does not have to look it up.

**Dynamic artifact = also tablet PDFs.** Whenever you build a dynamic artifact (an interactive web page) for studying, also build its PDF version for annotating on a tablet (e.g. GoodNotes on iPad), in two layouts: portrait (A4) and landscape (A4 landscape), from the same content source so they never drift apart. Keep the interactivity as PDF links (index/map -> section, question -> answer -> back to question, "back to map" on every section) plus a bookmark outline; hidden answers become an answer-key section with links. Let the artifact offer both PDFs (e.g. a "Tablet PDF: Dikey / Yatay" choice) and also send both files to the user. Before delivering, render pages of both layouts and check that nothing breaks: no figure or diagram split across pages or cut at the edge, no orphan heading at a page bottom, no near-empty pages, all internal links land on the right page, fonts embedded.

**Devices.** The user opens dynamic artifacts only on a desktop computer and the PDFs only on a tablet; never on a phone. Do not spend effort on phone or mobile layouts and do not run mobile checks: verify artifacts at desktop widths and PDFs as rendered pages.

## 2. Which mode

Find the course folder (the one the user names, or the current/connected one) and work directly in it.
- No `AGENTS.md` mentioning study-buddy: **Setup** (section 3).
- `AGENTS.md` says `study-buddy system vN`: **Session** (section 4). If N is older than this skill's version, offer the upgrade (end of section 9) first.
- A hand-made older system (e.g. `kb/feedback.md`, `kb/slides/`): offer migration (end of section 9).

## 3. Setup

1. **Inventory (read-only).** Write `tools/buddy.py` (Appendix B) and run `python3 tools/buddy.py scan`. Open each file enough to classify it: slides, lecture notes, book, syllabus, announcement, quiz/exam with or without answers, answer key, homework, transcript, LLM-written notes, other. Note the term (current/past), units covered, question count and problems (scanned pages, garbled text, missing answers). If the user already described the folder, treat that as ground truth and check it against the files.
2. **Interview.** Show a short table of how you read the folder, then ask only what is missing and changes the setup. Ask in plain chat as one numbered list with every open question (section 1, Asking the user; never option cards), put your recommended default next to each, and repeat with only the remaining gaps until nothing is missing. Typical first round:
   - Which assessment, when, what format (count, type, duration, language), what scope?
   - Fidelity: only the sources / a little beyond / beyond when useful / freely beyond (section 5)? Weights if there are several kinds of sources (e.g. slides 70, book 30).
   - Is my reading of the folder right (roles, terms, what each file is)?
   - What does the instructor tend to ask, what should practice questions focus on or avoid, what do you already know?
   Second round only if needed: outputs wanted (explanations, annotated slides, practice exams, flashcards, plan) and time available. Skip anything the user already said. If the user is away: take the recommended defaults, mark them `(varsayım, onayla)` in `kb/course.md`, and list the open questions at the top of your reply.
3. **Write the system files** from Appendix A: `AGENTS.md`, `CLAUDE.md`, `kb/course.md`, `kb/index.md`, `kb/preferences.md`, `kb/progress.md`, `kb/decisions.md`; plus `kb/questions.md` and `kb/exam-analysis.md` when questions exist (without questions, exam-analysis holds the topic map).
4. **Text index.** `python3 tools/buddy.py extract <pdf/pptx/docx ...>` writes `kb/text/<name>.md` with one `## <name> · s.N` section per page. Look at pages the tool flags (scanned) and at slides whose text looks garbled (e.g. a dash extracted as "4").
5. **Analysis.** Section 6 with past questions, section 7 without.
6. **Hand over.** Short message: what was set up, the plan (by priority and time left), the first step, open questions. Then `python3 tools/buddy.py scan --update`.

## 4. Every session

1. Read `AGENTS.md`, `kb/course.md`, `kb/preferences.md`, `kb/progress.md`; open `kb/index.md` when you need a file.
2. `python3 tools/buddy.py scan`. For NEW / CHANGED / REMOVED files run the source-change flow (4a) before the request; if the request is urgent, right after it, and say so.
3. Serve the request (section 8), anchored on `kb/text` (grep) and on page images when layout matters.
4. Before finishing: update `kb/progress.md`, add new outputs to `kb/index.md`, then `scan --update`.

**4a. Source change.** Classify the file; if its role is unclear, ask in one line with your best guess. Add it to `kb/index.md`. Extract text if it is pdf/pptx/docx. Questions or answer keys go to `kb/questions.md` and `kb/exam-analysis.md` (re-weigh priorities, re-check coverage). New units go to the topic map; mark affected outputs stale (the "Türetilen" column of `kb/index.md`) and offer to rebuild. A removed file is marked in the index; derived files stay. Structural change goes to `kb/decisions.md`. Tell the user in one line.

## 5. Source policy (`kb/course.md`, Kaynak politikası)

| fidelity | user's words | what you may add |
|---|---|---|
| strict | "slayttan çıkma", "sadece kitap" | nothing outside the primary sources; if asked, answer labeled "kaynak dışı" |
| light | "çok az dışına çık" | short context, analogies, prerequisite definitions that help understanding; no new testable facts; labeled |
| moderate | "gerektiğinde dışına çık" | related standard concepts and examples that support the sources; labeled |
| open | "bayağı dışına çık" | teach beyond the sources at textbook level, anchored on their topics; labeled |

- **Weights**: percentages per source class (e.g. slides 60 / book 30 / outside 10) decide how much explanation and how many practice questions come from each.
- **Terms**: current term x2, previous x1, older x0.5 unless the user says otherwise. Instructor or user sample questions weigh like the current term.
- **Conflicts**: current over past; instructor's key over derived answers; primary over secondary. Flag every conflict to the user instead of choosing silently.
- **Scope**: out-of-scope pages are marked, never deleted; they matter for the next exam. Versioned standards (e.g. OWASP 2021 vs 2025): follow the version the current slides use and note the mapping when past exams used another.
- **Low-trust text**: LLM-generated or third-party notes are never the source of truth unless the user says so. Clean such text out of a source file only when the user asks, after copying the original to `kb/originals/`.

## 6. With past questions

1. Normalize every question into `kb/questions.md` (format in Appendix A): code, exam label, `where` (source location), answer, key type (official / derived / user), why. Raw files stay untouched. Flag questions whose topic is not in the sources: they show the instructor goes beyond the slides.
2. Analyze in `kb/exam-analysis.md`: question format; stem patterns (scenario-based, log/header reading, "which is NOT"); which source elements get asked (tables, comparisons, lists, numbers, definitions); distractor patterns (neighbouring concept on the same slide, swapped pair, true statement in the wrong context); answer-letter distribution; hits per unit and page; topics repeated across terms; in-scope pages never asked yet.
3. Priority per unit/page = weighted hits (term weights) + bonus for in-scope-but-never-asked + instructor emphasis + user focus - user avoid. It drives the plan, the page verdicts and the practice-exam distribution.
4. No answer key: derive the answer from the sources, set `key: derived`, and say it needs confirming.

## 7. Without past questions

Build a topic map from the sources and predict what will be asked from: learning objectives and summary slides, emphasized or repeated items, comparisons and tables (A vs B), enumerations ("three types of"), definitions, processes and steps, numbers, worked examples, homework, the syllabus' exam description, and anything the user says the instructor stressed. Ask the user about the instructor's style. As soon as a real quiz or key arrives, switch to section 6.

## 8. Serving requests

- **Explain a topic/page/chapter**: grep `kb/text`, read the pages, explain in the default style, cite locations, add related past questions (code + one-line gist) and the trap.
- **A question from the user**: answer, reasoning, location, similar past question, trap. If it is outside the sources, say so and follow the fidelity setting.
- **What to study now**: from progress, priorities and time left; a time-boxed list, already-known units last.
- **Practice questions in chat**: exam format and language, instructor style, focus/avoid lists respected; a quiz widget if the environment has one. Record weak spots in `kb/progress.md`.
- **Practice exam**: same count, option count, duration and language as the real exam; distribution by priority. Exam 1 rebuilds repeated/past topics, exam 2 covers in-scope pages never asked. Each question has a source location, why it was chosen (`mirrors`), one correct answer and distractors in the instructor's style; answer letters spread like the instructor's key. Write `kb/mock/<name>.md` in the block format and render with `python3 tools/render.py exam kb/mock/<name>.md` (exam PDF + separate key PDF). Before delivering, have an independent agent (or a fresh pass of your own using only the sources) take it; fix any question that is ambiguous or needs knowledge beyond the fidelity setting.
- **Annotated slides + reading guide**: one spec per unit in `kb/annotations/<unit>.py` (Appendix A), built with `python3 tools/render.py annotate <spec>` (Appendix C). Verdict per page: MEM (ezberle), KNOW (sadece şunu bil), SKIM (göz at), SKIP (atla), OUT (kapsam dışı). Highlight phrases copied exactly from `kb/text`; numbered notes in the default style; past questions by code; predictions; trap. Then run `python3 tools/render.py coverage` (target: nothing NOT PLACED or NOT VISIBLE, or `place: none` with a reason) and look at rendered pages before delivering. `merge` builds one combined guide.
- **Cheat sheet, memorize list, flashcards, study page**: same style and citations; record the file in `kb/index.md`.
- **After an exam**: ask what was asked and how it went; add recalled questions (`key: user`) or the official key; update weights, scope and the active assessment in `kb/course.md`; carry weak spots forward.

## 9. Self-improvement protocol

This is what makes the system learn. Whenever the user states a preference, corrects you, complains or praises, gives information about the exam, the instructor or the files, or study results show a pattern:
1. **Apply** it immediately (redo the last output if it was about that output).
2. **Write** it where it belongs (routing table in `AGENTS.md`): behavior to `kb/preferences.md`; exam, scope, fidelity, weights to `kb/course.md`; file roles to `kb/index.md`; instructor style, focus/avoid to `kb/exam-analysis.md`; questions to `kb/questions.md`; studied/known/weak to `kb/progress.md`; structure/method to `kb/decisions.md`.
3. **Format**: one dated line per rule (`- 2026-10-26: ... (bağlam: ...)`). Replace a conflicting older rule instead of keeping both (newest wins). Merge duplicates; keep files short.
4. **Only what the user said.** Save explicit statements right away. A pattern you inferred becomes a rule only after the user confirms it (ask in one line).
5. **Confirm** in one short line: "Kaydettim: ... (kb/preferences.md)".
6. **Promote**: if a rule sounds course-independent ("her derste", "hep") or shows up in two courses, ask whether it should become a default for all courses. If yes, update section 1 of this skill with the environment's skill-update mechanism (propose the complete updated SKILL.md, or edit the installed file when the skill lives in a writable local folder), bump the version line, and also write it into the current course.
7. **Upkeep** at each new assessment: review preferences for stale or conflicting rules, update the active assessment and scope, re-check `kb/index.md` against `scan`.

**Upgrade / migration.** If a folder shows an older system version, or a hand-made system exists: say what will change, then add the missing files and sections without dropping any user rule or history (e.g. `kb/feedback.md` to `kb/preferences.md`, `kb/slides/` to `kb/text/`, quiz files to `kb/questions.md`), note it in `kb/decisions.md`, and set the version line.

## 10. Before delivering

- Every factual claim traces to a source location (grep it); anything else is labeled.
- Practice and mock answers are checked against the sources by a fresh pass; arithmetic and code are run, not eyeballed.
- PDFs are rendered to images and looked at (missing text, overflow, overlaps); `coverage` is clean for annotated outputs.
- Self-contained check: no sentence leans on a reference ("slayttaki", "bkz.", "as in the example"); for a dynamic artifact, both tablet PDFs (portrait and landscape) exist, were rendered and looked at, and their links work.
- `kb/index.md` lists every new or changed file.
- Tools need Python 3.8+ and PyMuPDF >= 1.25 (`pip install -U pymupdf`; `python-pptx` / `python-docx` for those formats). Run them where the folder lives; if a dependency can't be installed there, process copies elsewhere and write the results back.

## Appendix A · File templates

Write content in the user's language; keep the file names and the `kb/questions.md` keys exactly as here (the tools read them).

**AGENTS.md**
```markdown
# <KOD> <Ders adı> · study-buddy

study-buddy system v3 · kurulum <tarih>. Kullanıcının bu ders için çalışma klasörü; ajan çalışma partneridir. Ayrıntılı prosedürler `study-buddy` skill'inde (varsa yükle).

## Oturum başında
1. `python3 tools/buddy.py scan`: yeni, değişen veya silinen dosya varsa önce "Kaynak değişti".
2. Oku: `kb/course.md` (ders, sınavlar, kaynak politikası), `kb/preferences.md` (kurallar), `kb/progress.md` (nerede kaldık).
3. Gerekince: `kb/index.md` (her dosya ne), `kb/exam-analysis.md` (soru haritası, hoca stili), `kb/questions.md` (soru bankası), `kb/text/` (sayfa etiketli metin, grep).

## Kurallar
- Kaynak dosyalar salt okunur; türetilen her şey `kb/` veya çıktı klasörlerine.
- Her bilgiye yer: `<kaynak> s.N`. Kaynak dışına çıkma seviyesi `kb/course.md`de; dışarıdan gelen her şey etiketli.
- Türkçe, terimin İngilizcesi parantezde; büyük resimden detaya; sade, tam cümleli, detaylı ama şişirmeden; slayta bakmadan anlaşılır. Uzun tire yok.
- Kendi kendine yeterli (self-contained) yaz: okumak yeterli olmalı; referanslar sadece sonda parantez içinde, ek bakış için. Dinamik bir artifact üretilirse tablet için dikey ve yatay PDF'i de üretilir; telefon kontrolü yapılmaz (artifact masaüstünde, PDF tablette açılır).
- Güncel dönem ağır basar; çıkmış ve çıkabilecek yerlere odaklan; kullanıcının bildiğini tekrar etme.

## Kullanıcı bir şey söyleyince: uygula, buraya yaz, tek satırla bildir
| Ne | Nereye |
|---|---|
| Anlatım, format, iletişim tercihi | kb/preferences.md |
| Sınav tarihi, formatı, kapsamı; kaynak ağırlığı; dışına çıkma seviyesi | kb/course.md |
| Bir dosyanın ne olduğu, rolü | kb/index.md |
| Hocanın soru stili, odaklan / kaçın | kb/exam-analysis.md |
| Yeni çıkmış soru, örnek soru, cevap anahtarı | kb/questions.md + kb/exam-analysis.md |
| Çalışılan / bilinen konu, zayıf nokta | kb/progress.md |
| Yapı veya yöntem değişikliği | kb/decisions.md |
| "Bütün derslerimde" geçerli tercih | burada uygula + skill varsayılanı yapmayı öner |
Çelişen eski kuralı güncelle (en yeni geçerli). Tahmini kural olarak yazma, önce sor.

## Kaynak değişti
`kb/index.md`ye işle (rolü belirsizse sor); pdf/pptx/docx ise `python3 tools/buddy.py extract <dosya>`; soru içeriyorsa `kb/questions.md` + `kb/exam-analysis.md`; etkilenen çıktıları index'teki "Türetilen" sütunundan bul, yeniden üretmeyi öner.

## Oturum sonunda
`kb/progress.md` güncelle, yeni dosyaları `kb/index.md`ye ekle, `python3 tools/buddy.py scan --update`.
```

**CLAUDE.md**: tek satır `@AGENTS.md`.

**kb/course.md**
```markdown
# Ders ayarları
Ders, sınavlar ve kaynak politikası. Kullanıcı bunlardan birini değiştirince burası güncellenir.

## Ders
- Kod / ad / dönem / hoca:
- Materyal dili: · Sınav dili: · Anlatım dili: Türkçe (terimin İngilizcesi parantezde)
- Atıf biçimi: `Day N s.X` (slayt) · `Kitap <bölüm> s.X`

## Sınavlar
| id | tür | tarih, saat | süre | format | kapsam | durum |
|---|---|---|---|---|---|---|
Aktif sınav:

## Kaynak politikası
- Birincil kaynak (doğruluk kaynağı):
- Dışına çıkma seviyesi: strict | light | moderate | open (kullanıcının sözü: "...")
- Kaynak ağırlıkları: örn. slayt 100
- Dönem ağırlığı: bu dönem x2 · geçen dönem x1 · daha eski x0.5
- Kaynak dışı etiketi: "slayt dışı"

## Önceden bilinen
-

## Çıktılar
- Klasörler: Annotated Notes/, Study Guide/, Practice Exams/

## Açık sorular
-
```

**kb/index.md**
```markdown
# Dosya haritası
Klasördeki her dosya: ne olduğu, ne işe yaradığı, nereden türediği. Dosya eklenince, değişince veya silinince güncellenir.
Son kontrol: <tarih> (`python3 tools/buddy.py scan`)

## Kullanıcının kaynakları (salt okunur)
| Dosya | Tür | Dönem | Rol / ağırlık | İçerik | Türetilen |
|---|---|---|---|---|---|
| Lecture Notes/Day_3.pdf | slayt, 16 s. | 2026 Güz | birincil | Ağ temelleri: OSI, IP, portlar, pcap vs flow | kb/text/Day_3.md, kb/annotations/day03.py |

## Sistem dosyaları
| Dosya | Ne işe yarar |
|---|---|
| AGENTS.md | giriş noktası: okuma sırası, kurallar, güncelleme yönlendirmesi |
| CLAUDE.md | AGENTS.md'yi yükler |
| kb/course.md | ders, sınavlar, kaynak politikası |
| kb/preferences.md | kullanıcının kuralları (en yeni geçerli) |
| kb/progress.md | çalışma durumu, zayıf noktalar, sonraki adım |
| kb/decisions.md | yapı ve yöntem kararları |
| kb/exam-analysis.md | soru haritası, hoca stili, öncelikler |
| kb/questions.md | soru bankası (tek biçim) |
| kb/text/ | kaynakların sayfa etiketli metni |
| tools/buddy.py | tarama, metin çıkarma, soru bankası kontrolü |
| kb/.snapshot.tsv | tarama durumu (elle düzenlenmez) |

## Üretilen çıktılar
| Dosya | Ne | Kaynağı | Yeniden üret |
|---|---|---|---|
```

**kb/preferences.md**
```markdown
# Tercihler ve öğrenilen kurallar
Her oturumda okunur. Varsayılanlar study-buddy skill'inden gelir; burada bu derse özel ve sonradan öğrenilen kurallar var. En yeni kural geçerli; çelişen eskisi güncellenir.
Biçim: `- YYYY-AA-GG: <kural> (bağlam: ...)`

## Kurallar
-
```

**kb/progress.md**
```markdown
# İlerleme
Aktif sınav: <id> · <tarih> (<kalan gün>)

## Ünite durumu
| Ünite | Durum (başlanmadı / okundu / pratik yapıldı / hazır) | Not |
|---|---|---|

## Zayıf noktalar
- YYYY-AA-GG: <konu> (<nasıl ortaya çıktı>)

## Oturum günlüğü
- YYYY-AA-GG: <ne yapıldı>

## Sonraki adım
-
```

**kb/decisions.md**
```markdown
# Kararlar
Yapı veya yöntem değişince en üste yeni kayıt. Eskiler silinmez; geçersizse "İPTAL: <tarih>, yerine #N".

## #1 - YYYY-AA-GG - study-buddy kurulumu
Karar: ... Neden: ...
```

**kb/exam-analysis.md**
```markdown
# Sınav analizi
Neyin, nasıl, ne sıklıkla sorulduğu. Yeni soru veya cevap anahtarı gelince önce burası güncellenir.

## Soru kaynakları
| Kod öneki | Sınav | Dönem | Soru | Ağırlık | Ham dosya |
|---|---|---|---|---|---|

## Hocanın stili
- Format: · Soru kökü kalıpları: · Çeldirici kalıpları: · Şık dağılımı: · Hangi kaynak öğeleri soruluyor:

## Odaklan / kaçın
- Odaklan: · Kaçın:

## Ünite bazında isabet ve öncelik
| Ünite | Konu | Kodlar | Ağırlıklı isabet | Öncelik |
|---|---|---|---|---|

## Tekrar eden konular
## Kapsamda ama hiç sorulmamış
## Tahminler
```

**kb/questions.md** (practice exams in `kb/mock/` use the same blocks)
```markdown
# Soru bankası
Bütün çıkmış, örnek ve hatırlanan sorular tek biçimde. Ham dosyalar değişmez; bu dosya onlardan türetilir.
Kodlar: PQk-n = bu dönem Quiz k soru n · HQk-n = geçen dönem quiz · HV-n = geçen dönem vize (derse göre seç, burada açıkla)

### PQ1-15
- exam: Bu dönem Quiz 1 · Soru 15
- where: Day 3 s.14-15
- answer: D
- key: official
- why: Flows are compact summaries for long-term, large-scale detection; full pcap would not fit.

You need to spot command-and-control beaconing across 20,000 hosts over the last 90 days, with limited storage. Which data source fits best?

    (log or code lines: indent 4 spaces)

A) Full packet capture on every network segment
B) ARP tables collected from each switch
C) DHCP lease logs
D) NetFlow/IPFIX flow records
E) HTTP cookies from proxy logs
```
Rules: `- key: value` lines directly under the `###` code; a blank line; the stem; options as `A) ...`. Optional keys: `topic`, `place: none (neden)`. No question text (answer key only): leave the stem out. A practice exam file starts with `# <başlık>` plus `- course:`, `- info:`, `- footer:` lines, and each question can add `- section:` (unit heading) and `- mirrors:` (which past question or slide it imitates).

**kb/annotations/<unit>.py**
```python
SPEC = {
 'source': 'Lecture Notes/Day_3.pdf', 'unit': 'Day 3', 'title': 'Networking Fundamentals',
 'hits': '9 soru (bu dönem Quiz 1: 5, geçen dönem: 4)', 'essence': '<günün tek cümlelik özü>',
 'why': '<neden önemli, neler çıktı>', 'last_page': None,  # kapsam bir sayfada bitiyorsa o sayı; sonrası OUT
 'pages': {
  15: {'v': 'MEM', 'min': 2, 'topic': 'Packets vs flows', 'what': '<slayt ne anlatıyor>',
       'hl': [('Best for: Detailed incident investigation', 1), ('Best for: Continuous threat hunting', 2)],
       'notes': ['<1 numaralı işaretin detaylı açıklaması>', '<2 numaralı>'],
       'memo': '<birebir ezberlenecek satır>',
       'exam': [('PQ1-15', '<neden bu cevap, çeldiriciler neden yanlış>')],
       'predict': ['<tahmini soru>'], 'trap': '<çeldirici>',
       'dim': [('<atlanacak bölgenin ilk ifadesi>', '<son ifadesi>')], 'diagram': None},  # diagram: mermaid metni
 }}
```
Notes may contain `<b>`, `<code>`. Pages left out of `pages` count as SKIP.

## Appendix B · tools/buddy.py (write at setup)

````python
#!/usr/bin/env python3
"""study-buddy helper. Course root = parent of this tools/ folder; run from anywhere.
  python3 tools/buddy.py scan [--update]  files NEW / CHANGED / REMOVED since kb/.snapshot.tsv (--update saves current state)
  python3 tools/buddy.py extract FILE...  page-tagged text of pdf/pptx/docx -> kb/text/<name>.md (grep + citations)
  python3 tools/buddy.py questions        check kb/questions.md: count per exam, missing fields, duplicate codes
Needs: pymupdf (pdf), python-pptx (pptx), python-docx (docx).
"""
import os, re, sys, time, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = os.path.join(ROOT, 'kb')
SNAP, TEXT, QFILE = os.path.join(KB, '.snapshot.tsv'), os.path.join(KB, 'text'), os.path.join(KB, 'questions.md')
PAGE = 's.'  # page tag used in kb/text and citations (s. = sayfa)


def rel(p):
    return os.path.relpath(p, ROOT)


def walk():
    for d, dirs, fs in os.walk(ROOT):
        dirs[:] = sorted(x for x in dirs if not x.startswith('.') and x not in ('__pycache__', 'node_modules', 'venv'))
        for f in sorted(fs):
            if not (f.startswith('.') or f.startswith('~$') or f.endswith('.pyc')):
                st = os.stat(os.path.join(d, f))
                yield rel(os.path.join(d, f)), st.st_size, int(st.st_mtime)


def scan(update):
    now = {p: (s, m) for p, s, m in walk()}
    old = {}
    if os.path.exists(SNAP):
        for line in open(SNAP, encoding='utf-8'):
            p, s, m = line.rstrip('\n').split('\t')
            old[p] = (int(s), int(m))
    if not old:
        print(f'No snapshot yet ({len(now)} files). Once kb/index.md covers them, run: scan --update')
    else:
        rows = [('NEW', p) for p in sorted(set(now) - set(old))]
        rows += [('CHANGED', p) for p in sorted(set(now) & set(old)) if now[p] != old[p]]
        rows += [('REMOVED', p) for p in sorted(set(old) - set(now))]
        print('\n'.join(f'{t}\t{p}' for t, p in rows) or 'No changes since the last snapshot.')
    if update:
        os.makedirs(KB, exist_ok=True)
        with open(SNAP, 'w', encoding='utf-8') as o:
            o.writelines(f'{p}\t{s}\t{m}\n' for p, (s, m) in sorted(now.items()))
        print(f'Snapshot saved ({len(now)} files).')


def pages_of(path):
    ext = path.lower().rsplit('.', 1)[-1]
    if ext == 'pdf':
        import pymupdf
        with pymupdf.open(path) as d:
            return [(f'{PAGE}{i + 1}', p.get_text('text', sort=True)) for i, p in enumerate(d)]
    if ext == 'pptx':
        from pptx import Presentation
        out = []
        for i, s in enumerate(Presentation(path).slides, 1):
            t = []
            for sh in s.shapes:
                if sh.has_text_frame:
                    t.append(sh.text_frame.text)
                if getattr(sh, 'has_table', False) and sh.has_table:
                    t += [' | '.join(c.text for c in r.cells) for r in sh.table.rows]
            if s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip():
                t.append('[speaker notes] ' + s.notes_slide.notes_text_frame.text)
            out.append((f'{PAGE}{i}', '\n'.join(t)))
        return out
    if ext == 'docx':  # no pages in docx: split at headings (and every 40 paragraphs)
        import docx
        out, buf, title = [], [], 'start'
        for para in docx.Document(path).paragraphs:
            head = para.style.name.lower().startswith('heading')
            if (head and buf) or len(buf) >= 40:
                out.append((f'§{len(out) + 1} {title}', '\n'.join(buf)))
                buf = []
            if head:
                title = para.text.strip()
            if para.text.strip():
                buf.append(para.text)
        if buf:
            out.append((f'§{len(out) + 1} {title}', '\n'.join(buf)))
        return out
    return None


def extract(paths):
    os.makedirs(TEXT, exist_ok=True)
    for f in map(os.path.abspath, paths):
        if not os.path.isfile(f):
            print(f'{f}: not found')
            continue
        try:
            pages = pages_of(f)
        except ImportError as e:
            print(f'{rel(f)}: missing library {e.name}; install it (pip install pymupdf / python-pptx / python-docx)')
            continue
        if pages is None:
            print(f'{rel(f)}: not pdf/pptx/docx; read it directly')
            continue
        name = os.path.splitext(os.path.basename(f))[0]
        out = os.path.join(TEXT, name + '.md')
        with open(out, 'w', encoding='utf-8') as o:
            o.write(f'# {name}\nSource: {rel(f)} · extracted {time.strftime("%Y-%m-%d")} · {len(pages)} parts\n\n')
            o.writelines(f'## {name} · {tag}\n{t.strip()}\n\n' for tag, t in pages)
        empty = [tag for tag, t in pages if len(t.strip()) < 15]
        print(f'{rel(f)} -> {rel(out)} ({len(pages)} parts)'
              + (f'; little or no text on {", ".join(empty)}: scanned/image pages, look at them' if empty else ''))


# ---- question blocks: kb/questions.md and practice exams share this format ----
META, OPT = re.compile(r'^- ([a-z][a-z-]*):\s*(.*)$'), re.compile(r'^([A-H])\)\s+(.*)$')


def parse_blocks(path):
    """-> (title, preamble_meta, blocks); block = {code, meta, parts: [('p'|'pre', text)], opts: [(letter, text)]}"""
    title, pre_meta, blocks, cur, fence, in_meta = '', {}, [], None, False, False
    for line in (l.rstrip() for l in open(path, encoding='utf-8').read().splitlines()):
        if not fence and line.startswith('### '):
            cur, in_meta = {'code': line[4:].split()[0], 'meta': {}, 'parts': [], 'opts': []}, True
            blocks.append(cur)
        elif not fence and re.match(r'^#{1,2} ', line):
            title = title or (line[2:].strip() if line.startswith('# ') else '')
            cur, in_meta = None, False
        elif cur is None:
            m = META.match(line)
            if m and not blocks:
                pre_meta[m.group(1)] = m.group(2).strip()
        elif line.strip().startswith('```'):
            fence = not fence
        elif fence or line.startswith(('    ', '\t')):
            cur['parts'].append(('pre', line[4:] if line.startswith('    ') else line.lstrip('\t')))
        elif in_meta and META.match(line):
            m = META.match(line)
            cur['meta'][m.group(1)] = m.group(2).strip()
        elif not line.strip():
            in_meta = False
            cur['parts'].append(('p', ''))
        else:
            in_meta = False
            m = OPT.match(line)
            if m:
                cur['opts'].append((m.group(1), m.group(2)))
            elif cur['parts'] and cur['parts'][-1][0] == 'p' and cur['parts'][-1][1]:
                cur['parts'][-1] = ('p', cur['parts'][-1][1] + ' ' + line.strip())
            else:
                cur['parts'].append(('p', line.strip()))
    for b in blocks:  # drop paragraph breaks; merge consecutive preformatted lines
        merged = []
        for k, t in b['parts']:
            if k == 'pre' and merged and merged[-1][0] == 'pre':
                merged[-1] = ('pre', merged[-1][1] + '\n' + t)
            elif t or k == 'pre':
                merged.append((k, t))
        b['parts'] = merged
    return title, pre_meta, blocks


def load_questions(path=QFILE):
    return {b['code']: b for b in parse_blocks(path)[2]} if os.path.exists(path) else {}


def letter_of(answer):
    m = re.match(r'^([A-H])\b', answer or '')
    return m.group(1) if m else None


def md_inline(t):
    t = H.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    return re.sub(r'`(.+?)`', r'<code>\1</code>', t).replace('—', '-')


def check_questions():
    if not os.path.exists(QFILE):
        return print('kb/questions.md not found')
    blocks, seen, groups, problems = parse_blocks(QFILE)[2], set(), {}, []
    for b in blocks:
        m, c = b['meta'], b['code']
        if c in seen:
            problems.append(f'{c}: duplicate code')
        seen.add(c)
        g = re.sub(r'\s*·\s*(Soru|Q|Question)\s*\d+\s*$', '', m.get('exam', '?'))
        groups[g] = groups.get(g, 0) + 1
        problems += [f"{c}: no '{k}'" for k in ('exam', 'where', 'answer') if not m.get(k)]
        if not b['parts']:
            problems.append(f'{c}: no question text (fine if only the answer key exists)')
        a = letter_of(m.get('answer'))
        if b['opts'] and a and a not in dict(b['opts']):
            problems.append(f'{c}: answer {a} is not among the options')
    print(f'{len(blocks)} questions\n' + '\n'.join(f'  {v:3d}  {k}' for k, v in groups.items()))
    print('\n'.join(problems) or 'No problems found.')


if __name__ == '__main__':
    a = sys.argv[1:] or ['-h']
    if a[0] == 'scan':
        scan('--update' in a)
    elif a[0] == 'extract':
        extract(a[1:])
    elif a[0] == 'questions':
        check_questions()
    else:
        print(__doc__)
````

## Appendix C · tools/render.py (write on the first PDF output)

````python
#!/usr/bin/env python3
"""study-buddy PDF outputs. Course root = parent of this tools/ folder.
  python3 tools/render.py annotate SPEC.py [...] | all   annotated slides + A4 reading guide per unit (kb/annotations/*.py)
  python3 tools/render.py coverage                       every question in kb/questions.md placed in a spec and visible in the PDFs?
  python3 tools/render.py merge "<Course> Guide.pdf"     all guides -> one compressed PDF with bookmarks
  python3 tools/render.py exam kb/mock/<name>.md         practice exam PDF + separate answer-key PDF
Specs name question codes only; the text comes from kb/questions.md. "WARN s.N: not found" = a highlight phrase is not
on that page: copy it exactly from kb/text, avoiding characters the text layer garbles.
Needs PyMuPDF >= 1.25 (its default fonts cover Turkish and symbols). Mermaid diagrams need `mmdc` (optional).
"""
import sys, os, re, glob, shutil, importlib.util, subprocess, tempfile, html as H
import pymupdf as fitz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from buddy import ROOT, rel, parse_blocks, load_questions, letter_of, md_inline

if tuple(int(x) for x in fitz.VersionBind.split('.')[:2]) < (1, 25):
    sys.exit(f'PyMuPDF {fitz.VersionBind} is too old: its font subsetting drops letters such as ş, ğ, İ. Run: pip install -U pymupdf')

OUT_ANN, OUT_GUIDE, OUT_EXAM = 'Annotated Notes', 'Study Guide', 'Practice Exams'  # rename per course; record in kb/index.md
LANG = 'tr'  # panel/key language: 'tr' or 'en' (a spec can set 'lang')
T = {
 'tr': dict(what='Bu slayt ne anlatıyor:', marked='İŞARETLİ YERLER: NE DEMEK, NEDEN ÖNEMLİ', notes='NOTLAR', memo='BİREBİR EZBERLE',
            exam='SINAVDA BÖYLE SORULDU', predict='BÖYLE SORULABİLİR (TAHMİN)', trap='TUZAK (ÇELDİRİCİ)', correct='Doğru cevap',
            official='Cevap anahtarındaki açıklama', derived='Açıklama (cevap anahtarı yok, kaynaktan çıkarıldı)', note='Açıklama',
            notext='(soru metni yok, sadece cevap var)', nextp='Devamı bir sonraki sayfada →', cont=' (devam)', done='[ ] bitti',
            mins='dk', page='Sayfa', verdict='Karar', time='Süre', topic='Konu', check='Bitti', oneline='Tek cümlede:',
            total='Toplam ~{m} dk · Çıkmış soru: {h}', howto='NASIL OKUNUR', skipped='Atla.', dim='atla', guide='rehber',
            howto_text='Slaytta <b>çerçeve + numara</b> = notlardaki aynı numaralı madde. Gölgeli kısım = atla.',
            outside='Bu sınavın kapsamı dışında; notları annotated slaytlarda sonraki sınav için duruyor.',
            key='Cevap Anahtarı', keyline='Cevap anahtarı', letters='Şık dağılımı', unit='Ünite', count='Soru', where='Kaynak',
            mirrors='Neden bu soru', howkey='Önce sadece üstteki satırla kendini puanla, sonra yanlışlarının açıklamasını oku.'),
 'en': dict(what='What this slide is about:', marked='MARKED ITEMS: WHAT THEY MEAN, WHY THEY MATTER', notes='NOTES', memo='MEMORIZE VERBATIM',
            exam='HOW IT WAS ASKED', predict='HOW IT MAY BE ASKED (PREDICTION)', trap='TRAP (DISTRACTOR)', correct='Correct answer',
            official='Answer key explanation', derived='Explanation (no answer key; derived from the source)', note='Note',
            notext='(no question text, answer only)', nextp='Continued on the next page →', cont=' (cont.)', done='[ ] done',
            mins='min', page='Page', verdict='Verdict', time='Time', topic='Topic', check='Done', oneline='In one sentence:',
            total='Total ~{m} min · Past questions: {h}', howto='HOW TO READ', skipped='Skip.', dim='skip', guide='guide',
            howto_text='On the slide, <b>box + number</b> = the note with the same number. Shaded area = skip.',
            outside="Outside this exam's scope; its notes stay in the annotated slides for the next exam.",
            key='Answer Key', keyline='Answer key', letters='Letter distribution', unit='Unit', count='Questions', where='Source',
            mirrors='Why this question', howkey='Score yourself with the line above first, then read the explanations of your mistakes.'),
}
VERDICT = {  # code: (tr label, en label, color, tr meaning, en meaning)
 'MEM': ('EZBERLE', 'MEMORIZE', (0.79, 0.16, 0.16), 'İşaretli her şeyi birebir bil.', 'Know every marked item exactly.'),
 'KNOW': ('SADECE ŞUNU BİL', 'KNOW THIS', (0.85, 0.42, 0.0), 'Sadece işaretli satırları bil; gerisini okuyup geç.', 'Know the marked lines; read the rest once.'),
 'SKIM': ('GÖZ AT', 'SKIM', (0.11, 0.42, 0.75), 'Hızlıca oku, ezberleme; doğrudan çıkma ihtimali düşük.', 'Read quickly; unlikely to be asked directly.'),
 'SKIP': ('ATLA', 'SKIP', (0.45, 0.47, 0.5), 'Sınavlık içerik yok.', 'Nothing exam-relevant.'),
 'OUT': ('KAPSAM DIŞI', 'OUT OF SCOPE', (0.42, 0.33, 0.6), 'Bu sınavda yok; notlar sonraki sınav için duruyor.', 'Not in this exam; notes kept for the next one.'),
}
ALIAS = {'EZ': 'MEM', 'BIL': 'KNOW', 'GOZ': 'SKIM', 'ATLA': 'SKIP', 'DISI': 'OUT'}  # older Turkish codes
PANEL_BG, YEL, CIRC = (0.965, 0.957, 0.93), (1, 0.83, 0.23), '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮'
CSS = """*{font-family:sans-serif;font-size:10.6px;line-height:1.36;color:#1b1f24} p{margin:0 0 5px 0}
.what{background-color:#e6eef3;padding:4px} .n{font-weight:bold;color:#9a6a00} .h{font-weight:bold;font-size:9.6px;color:#4a5562;margin:8px 0 3px 0}
.memo{background-color:#fbe9e7;padding:4px} .q{background-color:#eef5ee;padding:4px;margin-bottom:6px} .qs{font-weight:bold}
.opt{margin:0 0 1px 10px} .ok{font-weight:bold;color:#1f6b2e} .why{color:#24414e} .tr{color:#a61e1e}
code,pre{font-family:monospace;font-size:9.6px} pre{background-color:#e9e5da;padding:3px;margin:2px 0 4px 0}
td{font-size:10px;padding:2px 6px;border-bottom:1px solid #d9d3c4}"""
EXAM_CSS = """*{font-family:sans-serif;font-size:10.5px;line-height:1.38;color:#15191e} p{margin:0 0 3px 0}
.hdr{border:1px solid #333;padding:6px;margin-bottom:8px} .sec{font-weight:bold;font-size:11.5px;margin:12px 0 5px 0;border-bottom:1px solid #888}
.opt{margin:0 0 1px 14px} .q{margin-bottom:9px} code,pre{font-family:monospace;font-size:9.4px}
pre{background-color:#eeeeee;padding:3px;margin:2px 0 3px 14px} .ex{color:#23404c} .src{color:#666;font-size:9.5px}
td{font-size:10px;padding:2px 6px;border-bottom:1px solid #ccc}"""
QB, WARN, ARCH = {}, [], [None]


def hexc(c):
    return '#%02x%02x%02x' % tuple(int(x * 255) for x in c)


def natural(s):
    return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', s)]


def render_pdf(html, dst, footer, css, archive=None, margins=(46, 42, 46, 46)):
    """HTML -> A4 pages with footers. Every <img> must sit inside a <p>: MuPDF Story can drop the text after a bare <img> that moves to a new page."""
    story, mb = fitz.Story(html, user_css=css, archive=archive), fitz.paper_rect('a4')
    tmp, more = dst + '.part', 1
    w = fitz.DocumentWriter(tmp)
    while more:
        dev = w.begin_page(mb)
        more, _ = story.place(mb + (margins[0], margins[1], -margins[2], -margins[3]))
        story.draw(dev)
        w.end_page()
    w.close()
    d = fitz.open(tmp)
    for k, p in enumerate(d):
        p.insert_text((margins[0], mb.height - 24), f'{footer} - {k + 1}/{d.page_count}', fontsize=8, color=(0.45, 0.45, 0.45))
    d.subset_fonts()
    d.save(dst, garbage=4, deflate=True)
    d.close()
    os.remove(tmp)
    print('written:', rel(dst))


def parts_html(parts):
    return ''.join(f'<p>{md_inline(t)}</p>' if k == 'p' else f'<pre>{H.escape(t) or " "}</pre>' for k, t in parts)


# ---------------- practice exam ----------------
def exam(path, lang=LANG):
    t = T[lang]
    title, pm, qs = parse_blocks(path)
    name = os.path.splitext(os.path.basename(path))[0]
    title, footer, out = title or name, pm.get('footer', title or name), os.path.join(ROOT, pm.get('out', OUT_EXAM))
    os.makedirs(out, exist_ok=True)
    h = f"<div class='hdr'><p style='font-size:15px;font-weight:bold'>{md_inline(title)}</p>"
    h += ''.join(f'<p>{md_inline(pm[k])}</p>' for k in ('course', 'info') if pm.get(k))
    h += f"<p>{md_inline(pm.get('name-line', 'Name: ______________________   Student ID: ______________   Start: ____   End: ____'))}</p></div>"
    cur = None
    for i, b in enumerate(qs, 1):
        if b['meta'].get('section') and b['meta']['section'] != cur:
            cur = b['meta']['section']
            h += f"<p class='sec'>{md_inline(cur)}</p>"
        first = [('p', f'**{i}.** ' + b['parts'][0][1])] + b['parts'][1:] if b['parts'] and b['parts'][0][0] == 'p' else [('p', f'**{i}.**')] + b['parts']
        h += f"<div class='q'>{parts_html(first)}" + ''.join(f"<p class='opt'>{k}) {md_inline(v)}</p>" for k, v in b['opts']) + '</div>'
    rows = ''.join('<tr>' + ''.join(f'<td>{r * 6 + c + 1}. ____</td>' for c in range(6) if r * 6 + c < len(qs)) + '</tr>' for r in range((len(qs) + 5) // 6))
    h += f"<p class='sec'>{md_inline(pm.get('sheet', 'Answer sheet'))}</p><table style='width:100%;border-collapse:collapse'>{rows}</table>"
    render_pdf(h, os.path.join(out, f'{name}.pdf'), footer, EXAM_CSS)
    letters = [letter_of(b['meta'].get('answer')) or '-' for b in qs]
    line = ' '.join(f'{i}{a}' + (' ·' if i % 5 == 0 and i < len(qs) else '') for i, a in enumerate(letters, 1))
    dist, cnt = {}, {}
    for b, a in zip(qs, letters):
        dist[b['meta'].get('section', '-')] = dist.get(b['meta'].get('section', '-'), 0) + 1
        cnt[a] = cnt.get(a, 0) + 1
    k = (f"<p style='font-size:15px;font-weight:bold'>{md_inline(title)} - {t['key']}</p><p><b>{t['keyline']}:</b> <code>{line}</code></p>"
         f"<p>{t['howkey']}</p><p><b>{t['letters']}:</b> " + ', '.join(f'{x}: {cnt[x]}' for x in sorted(cnt)) + '</p>'
         f"<table style='width:100%;border-collapse:collapse;margin:6px 0'><tr style='background-color:#e6e6e6'><td><b>{t['unit']}</b></td><td><b>{t['count']}</b></td></tr>"
         + ''.join(f'<tr><td>{md_inline(u)}</td><td>{c}</td></tr>' for u, c in dist.items()) + '</table>')
    for i, (b, a) in enumerate(zip(qs, letters), 1):
        m = b['meta']
        k += (f"<div class='q'><p><b>{i}. {a})</b> {md_inline(dict(b['opts']).get(a, m.get('answer', '')))}</p>"
              + (f"<p class='ex'>{md_inline(m['why'])}</p>" if m.get('why') else '')
              + f"<p class='src'>{t['where']}: {md_inline(m.get('where', '-'))}" + (f" · {t['mirrors']}: {md_inline(m['mirrors'])}" if m.get('mirrors') else '') + '</p></div>')
    render_pdf(k, os.path.join(out, f"{name} - {t['key']}.pdf"), f"{footer} - {t['key']}", EXAM_CSS)
    print('key:', ''.join(letters), '| letters:', dict(sorted(cnt.items())))


# ---------------- annotated slides + guide ----------------
def lab(v, lang):
    e = VERDICT[v]
    return (e[0], e[3]) if lang == 'tr' else (e[1], e[4])


def spec_paths(args):
    if args in ([], ['all']):
        return sorted(glob.glob(os.path.join(ROOT, 'kb', 'annotations', '*.py')), key=natural)
    return [os.path.abspath(a) for a in args]


def load_spec(path):
    s = importlib.util.spec_from_file_location('spec', path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    spec = m.SPEC
    spec.setdefault('lang', LANG)
    spec.setdefault('unit', os.path.splitext(os.path.basename(path))[0])
    last = spec.get('last_page', spec.get('midterm_last_page'))  # pages after it: out of this exam's scope
    for n, ps in list(spec['pages'].items()):
        ps['v'] = ALIAS.get(ps.get('v', 'SKIP'), ps.get('v', 'SKIP'))
        ps.setdefault('min', 0)
        ps.setdefault('topic', '-')
        if last and n > last and ps['v'] != 'SKIP':
            spec['pages'][n] = dict(ps, v='OUT', min=0)
    return spec


def slug(unit):
    return re.sub(r'[^\w.-]+', '_', unit).strip('_')


def exam_html(code, note, t):
    q = QB.get(code)
    if not q:
        WARN.append(f'question {code} is not in kb/questions.md')
        return f"<div class='q'><p class='qs'>[{code}]</p><p class='why'>{note}</p></div>"
    m = q['meta']
    ans, letter = m.get('answer', ''), letter_of(m.get('answer'))
    body = parts_html(q['parts']) or "<p class='why'>" + t['notext'] + '</p>'
    out = f"<div class='q'><p class='qs'>[{code}] {md_inline(m.get('exam', ''))}</p>{body}"
    out += ''.join(f"<p class='opt{' ok' if k == letter else ''}'>{k}) {md_inline(v)}{'  ✔' if k == letter else ''}</p>" for k, v in q['opts'])
    out += f"<p class='ok'>{t['correct']}: {md_inline(ans)}</p>" if ans else ''
    out += f"<p class='why'>{t['official'] if m.get('key', 'official') == 'official' else t['derived']}: {md_inline(m['why'])}</p>" if m.get('why') else ''
    return out + (f"<p class='why'><b>{t['note']}:</b> {note}</p>" if note else '') + '</div>'


def blocks(ps, t, diagram=None):
    b = [f"<p class='what'><b>{t['what']}</b> {ps['what']}</p>"] if ps.get('what') else []
    if ps.get('notes'):
        b.append(f"<p class='h'>{t['marked'] if ps.get('hl') else t['notes']}</p>")
        b += [f"<p><span class='n'>{CIRC[i] if ps.get('hl') else '•'}</span> {n}</p>" for i, n in enumerate(ps['notes'])]
    b += [diagram] if diagram else []
    b += [f"<p class='h'>{t['memo']}</p><p class='memo'>{ps['memo']}</p>"] if ps.get('memo') else []
    b += [(f"<p class='h'>{t['exam']}</p>" if k == 0 else '') + exam_html(c, n, t) for k, (c, n) in enumerate(ps.get('exam', []))]
    b += [(f"<p class='h'>{t['predict']}</p>" if k == 0 else '') + f"<div class='q'><p class='why'>{x}</p></div>" for k, x in enumerate(ps.get('predict', []))]
    return b + ([f"<p class='h'>{t['trap']}</p><p class='tr'>{ps['trap']}</p>"] if ps.get('trap') else [])


def fits(w, h, html):
    p = fitz.open().new_page(width=w + 20, height=h + 20)
    return p.insert_htmlbox(fitz.Rect(0, 0, w, h), html, css=CSS, archive=ARCH[0], scale_low=1)[0] >= 0


def pack(bl, w, h):
    taken = []
    for i, x in enumerate(bl):
        if not fits(w, h, ''.join(taken + [x])):
            return (taken, bl[i:]) if taken else ([x], bl[i + 1:])
        taken.append(x)
    return taken, []


def mermaid(src, tmp, name, width):
    if not shutil.which('mmdc'):
        WARN.append(f'{name}: mmdc not installed, diagram skipped')
        return None
    mmd, png, cfg = (os.path.join(tmp, name + x) for x in ('.mmd', '.png', '.json'))
    open(mmd, 'w', encoding='utf-8').write(src)
    open(cfg, 'w').write('{"themeVariables":{"fontFamily":"Helvetica, Arial, sans-serif","fontSize":"15px"}}')
    r = subprocess.run(['mmdc', '-i', mmd, '-o', png, '-b', 'white', '-t', 'neutral', '-w', '900', '-s', '2', '-c', cfg], capture_output=True)
    if r.returncode:
        WARN.append(f'{name}: mermaid failed: {r.stderr.decode()[:200]}')
        return None
    return f"<p style='margin:0'><img src='{os.path.basename(png)}' style='width:{width}'/></p>"


def find(page, phrase, pno):
    hits, words = page.search_for(phrase), phrase.split()
    if words:  # search_for ignores case: keep hits whose first or last word matches exactly
        hits = [r for r in hits if any(w in page.get_textbox(r + (-1, -1, 1, 1)) for w in (words[0], words[-1]))]
    if not hits:
        WARN.append(f's.{pno}: not found -> {phrase!r}')
    return hits


def draw_marks(page, w, h, ps, pno, t):
    pix = page.get_pixmap(clip=fitz.Rect(0, 0, w, h), dpi=12)
    light = sum(sum(pix.samples[i:i + 3]) / 3 for i in range(0, len(pix.samples), pix.n)) / (pix.width * pix.height) > 140
    mark, num_col = ((0.88, 0.33, 0.0), (1, 1, 1)) if light else (YEL, (0.1, 0.1, 0.1))
    shade, op = ((1, 1, 1), 0.72) if light else ((0, 0, 0), 0.62)
    for a, b in ps.get('dim', []):
        ra, rb = find(page, a, pno), find(page, b, pno)
        if ra and rb:
            r = fitz.Rect(ra[0]) | rb[-1]
            for blk in page.get_text('blocks'):
                if fitz.Rect(blk[:4]).intersects(r) and fitz.Rect(blk[:4]).width < w * 0.6:
                    r |= fitz.Rect(blk[:4])
            r = fitz.Rect(r.x0 - 8, r.y0 - 6, r.x1 + 8, r.y1 + 6)
            page.draw_rect(r, color=None, fill=shade, fill_opacity=op)
            page.insert_text((r.x1 - 30, r.y0 + 11), t['dim'], fontsize=9, color=(0.55, 0.55, 0.55))
    seen = set()
    for phrase, num in ps.get('hl', []):
        for q in find(page, phrase, pno):
            r = fitz.Rect(q.x0 - 2.5, q.y0 - 1.5, q.x1 + 2.5, q.y1 + 1.5)
            page.draw_rect(r, color=mark, width=1.3, radius=0.15)
            if num not in seen:
                seen.add(num)
                cx = r.x0 - 8 if r.x0 > 14 else r.x0 + 6
                page.draw_circle((cx, r.y0 + 1), 6.8, color=None, fill=mark)
                page.insert_text((cx - (2.6 if num < 10 else 5), r.y0 + 4.1), str(num), fontsize=8.6, fontname='hebo', color=num_col)
    if ps['v'] in ('SKIP', 'OUT') and ps.get('dimall', True):
        page.draw_rect(fitz.Rect(0, 0, w, h), color=None, fill=shade, fill_opacity=0.55)


def header(page, x0, y, spec, pno, ps, cont=False):
    t, (label, _) = T[spec['lang']], lab(ps['v'], spec['lang'])
    tw = fitz.get_text_length(label.translate(str.maketrans('ŞİÖÜÇĞ', 'SIOUCG')), 'hebo', 10.5) + 16
    tag = fitz.Rect(x0, y, x0 + tw, y + 18)
    page.draw_rect(tag, color=None, fill=VERDICT[ps['v']][2], radius=0.18)
    page.insert_htmlbox(tag + (0, 3, 0, 0), f"<p style='text-align:center;color:#fff;font-weight:bold;font-size:10.5px'>{label}</p>", css=CSS)
    page.insert_htmlbox(fitz.Rect(x0 + tw + 10, y + 3, x0 + 700, y + 20), f"<p style='color:#5b6470;font-size:10.5px'>~{ps['min']:g} {t['mins']} · "
                        f"{H.escape(spec['unit'])} s.{pno}{t['cont'] if cont else ''} · {H.escape(ps['topic'])} · {t['done']}</p>", css=CSS)


def plan_rows(spec):
    t = T[spec['lang']]
    rows = ''.join(f"<tr><td>s.{n}</td><td style='color:{hexc(VERDICT[p['v']][2])};font-weight:bold'>{lab(p['v'], spec['lang'])[0]}</td>"
                   f"<td>{p['min']:g} {t['mins']}</td><td>{H.escape(p['topic'])}</td><td>[  ]</td></tr>" for n, p in sorted(spec['pages'].items()))
    return (f"<table style='width:100%;border-collapse:collapse'><tr style='background-color:#e4dfd2'><td><b>{t['page']}</b></td><td><b>{t['verdict']}</b></td>"
            f"<td><b>{t['time']}</b></td><td><b>{t['topic']}</b></td><td><b>{t['check']}</b></td></tr>{rows}</table>")


def intro_html(spec):
    t, total = T[spec['lang']], sum(p['min'] for p in spec['pages'].values())
    leg = ''.join(f"<p><b style='color:{hexc(v[2])}'>{lab(k, spec['lang'])[0]}</b>: {lab(k, spec['lang'])[1]}</p>" for k, v in VERDICT.items())
    return (f"<p style='font-size:19px;font-weight:bold'>{H.escape(spec['unit'])} · {H.escape(spec.get('title', ''))}</p>"
            + (f"<p class='what'><b>{t['oneline']}</b> {spec['essence']}</p>" if spec.get('essence') else '') + (f"<p>{spec['why']}</p>" if spec.get('why') else '')
            + f"<p style='color:#4a5562'>{t['total'].format(m=f'{total:g}', h=spec.get('hits', '-'))}</p><p class='h'>{t['howto']}</p><p>{t['howto_text']}</p>{leg}")


def annotated(spec, src, tmp):
    t, out, index = T[spec['lang']], fitz.open(), {}
    w0, h0 = src[0].rect.width, src[0].rect.height
    pw = round(max(380, min(520, 0.52 * w0)))
    cover = out.new_page(width=w0 + pw, height=h0)
    cover.draw_rect(cover.rect, color=None, fill=PANEL_BG)
    cover.insert_htmlbox(fitz.Rect(30, 24, (w0 + pw) * 0.45, h0 - 14), intro_html(spec), css=CSS, scale_low=0)
    cover.insert_htmlbox(fitz.Rect((w0 + pw) * 0.47, 24, w0 + pw - 30, h0 - 14), plan_rows(spec), css=CSS, scale_low=0)
    WARN.extend(f'spec page {n} > {src.page_count} pages in the source' for n in spec['pages'] if n > src.page_count)
    for i in range(src.page_count):
        pno, (w, h) = i + 1, (src[i].rect.width, src[i].rect.height)
        ps = spec['pages'].get(pno, {'v': 'SKIP', 'min': 0, 'topic': '-'})
        pg = out.new_page(width=w + pw, height=h)
        index[pno] = pg.number
        pg.show_pdf_page(fitz.Rect(0, 0, w, h), src, i)
        draw_marks(pg, w, h, ps, pno, t)
        pg.draw_rect(fitz.Rect(w, 0, w + pw, h), color=None, fill=PANEL_BG)
        header(pg, w + 14, 12, spec, pno, ps)
        img = mermaid(ps['diagram'], tmp, f'a{pno}', '100%') if ps.get('diagram') else None
        taken, rest = pack(blocks(ps, t, img), pw - 28, h - 50)
        if rest:
            taken.append(f"<p style='color:#a61e1e;font-weight:bold'>{t['nextp']}</p>")
        pg.insert_htmlbox(fitz.Rect(w + 14, 40, w + pw - 14, h - 8), ''.join(taken), css=CSS, archive=ARCH[0], scale_low=0)
        while rest:  # overflow: extra two-column page right after the slide
            cp = out.new_page(width=w + pw, height=h)
            cp.draw_rect(cp.rect, color=None, fill=PANEL_BG)
            header(cp, 24, 14, spec, pno, ps, cont=True)
            colw = (w + pw - 72) / 2
            for c in range(2):
                if rest:
                    taken, rest = pack(rest, colw, h - 56)
                    cp.insert_htmlbox(fitz.Rect(24 + c * (colw + 24), 44, 24 + c * (colw + 24) + colw, h - 10), ''.join(taken), css=CSS, archive=ARCH[0], scale_low=0)
    os.makedirs(os.path.join(ROOT, OUT_ANN), exist_ok=True)
    dst = os.path.join(ROOT, OUT_ANN, f"{slug(spec['unit'])}_annotated.pdf")
    out.subset_fonts()
    out.save(dst, garbage=4, deflate=True, deflate_fonts=True, use_objstms=1)
    print('written:', rel(dst))
    return out, index


def guide(spec, ann, index, src, tmp):
    t, body = T[spec['lang']], intro_html(spec) + plan_rows(spec)
    for i in range(src.page_count):
        pno = i + 1
        ps = spec['pages'].get(pno, {'v': 'SKIP', 'min': 0, 'topic': '-'})
        body += (f"<p style='font-size:13.5px;font-weight:bold;margin-top:16px;border-bottom:1px solid #888'>s.{pno} · {H.escape(ps['topic'])} · "
                 f"<span style='color:{hexc(VERDICT[ps['v']][2])}'>{lab(ps['v'], spec['lang'])[0]}</span> · ~{ps['min']:g} {t['mins']}</p>")
        if ps['v'] in ('SKIP', 'OUT'):
            body += f"<p style='color:#666'>{(' '.join(ps.get('notes', [])) or t['skipped']) if ps['v'] == 'SKIP' else t['outside']}</p>"
            continue
        ann[index[pno]].get_pixmap(clip=fitz.Rect(0, 0, src[i].rect.width, src[i].rect.height), dpi=110).save(os.path.join(tmp, f'g{pno}.png'))
        body += f"<p style='margin:0'><img src='g{pno}.png' style='width:100%'/></p>"
        body += ''.join(blocks(ps, t, mermaid(ps['diagram'], tmp, f'g{pno}d', '75%') if ps.get('diagram') else None))
    os.makedirs(os.path.join(ROOT, OUT_GUIDE), exist_ok=True)
    render_pdf(body, os.path.join(ROOT, OUT_GUIDE, f"{slug(spec['unit'])}_{t['guide']}.pdf"), f"{spec['unit']} {t['guide']}",
               CSS + '*{font-size:10.8px}', archive=ARCH[0], margins=(42, 40, 42, 46))


def build(path):
    spec = load_spec(path)
    src = fitz.open(os.path.join(ROOT, spec['source']))
    with tempfile.TemporaryDirectory() as tmp:
        ARCH[0] = fitz.Archive(tmp)
        ann, index = annotated(spec, src, tmp)
        guide(spec, ann, index, src, tmp)


def coverage():
    placed, in_scope = {}, set()
    for p in spec_paths(['all']):
        spec = load_spec(p)
        for n, ps in spec['pages'].items():
            for code, _ in ps.get('exam', []):
                placed.setdefault(code, []).append(f"{spec['unit']} s.{n}")
                in_scope |= {code} if ps['v'] != 'OUT' else set()
    waived = {c for c, q in QB.items() if q['meta'].get('place', '').startswith('none')}
    print(f'{len(QB)} questions in kb/questions.md · placed: {len(set(QB) & set(placed))} · waived (place: none): {len(waived)}')
    print('NOT PLACED:', ', '.join(sorted(set(QB) - set(placed) - waived, key=natural)) or '-')
    print('UNKNOWN CODES in specs:', ', '.join(sorted(set(placed) - set(QB), key=natural)) or '-')
    for folder, need in ((OUT_ANN, set(placed)), (OUT_GUIDE, in_scope)):
        text = ''
        for f in glob.glob(os.path.join(ROOT, folder, '*.pdf')):
            with fitz.open(f) as d:
                text += ' '.join(pg.get_text() for pg in d)
        text = re.sub(r'\s+', ' ', text)
        print(f'NOT VISIBLE in {folder}/:', ', '.join(sorted((c for c in need if f'[{c}]' not in text), key=natural)) or '-')


def merge(name):
    out, toc = fitz.open(), []
    for p in spec_paths(['all']):
        spec = load_spec(p)
        f = os.path.join(ROOT, OUT_GUIDE, f"{slug(spec['unit'])}_{T[spec['lang']]['guide']}.pdf")
        if os.path.exists(f) and os.path.basename(f) != name:
            toc.append([1, f"{spec['unit']} · {spec.get('title', '')}", out.page_count + 1])
            with fitz.open(f) as d:
                out.insert_pdf(d)
    out.set_toc(toc)
    try:
        out.rewrite_images(quality=78, lossy=True, lossless=True)
    except Exception as e:  # older PyMuPDF
        WARN.append(f'image compression skipped: {e}')
    out.subset_fonts()
    out.save(os.path.join(ROOT, OUT_GUIDE, name), garbage=4, deflate=True, deflate_fonts=True, use_objstms=1)
    print('written:', rel(os.path.join(ROOT, OUT_GUIDE, name)), f'({out.page_count} pages)')


if __name__ == '__main__':
    a = sys.argv[1:] or ['-h']
    QB.update(load_questions())
    if a[0] == 'annotate':
        for p in spec_paths(a[1:]):
            build(p)
    elif a[0] == 'coverage':
        coverage()
    elif a[0] == 'merge':
        merge(a[1] if len(a) > 1 else 'Guide.pdf')
    elif a[0] == 'exam':
        exam(a[1])
    else:
        print(__doc__)
    for w in dict.fromkeys(WARN):
        print('  WARN', w)
````