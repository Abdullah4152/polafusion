# Language Coverage

## Overview

PolaFusion supports 22 languages across 3 subtasks. Coverage tiers are based on macro-F1 scores from competition evaluation runs.

## Tier Definitions

| Tier | F1 Range | UI Badge |
|------|----------|----------|
| 🟢 High | ≥ 0.60 | ✓ High Accuracy |
| 🟡 Medium | 0.35 – 0.59 | ~ Medium Accuracy |
| 🔴 Low | < 0.35 | ⚠ Limited Accuracy |

## Language Table

| Code | Language | Script | Family | ST1 | ST2 | ST3 | Tier |
|------|----------|--------|--------|-----|-----|-----|------|
| `hin` | Hindi | Devanagari | Indo-Aryan | ✅ | ✅ | ✅ | 🟢 High |
| `zho` | Chinese | Hanzi | Sino-Tibetan | ✅ | ✅ | ✅ | 🟢 High |
| `urd` | Urdu | Nastaliq | Indo-Aryan | ✅ | ✅ | ✅ | 🟢 High |
| `arb` | Arabic | Arabic | Semitic | ✅ | ✅ | ✅ | 🟢 High |
| `khm` | Khmer | Khmer | Austroasiatic | ✅ | ✅ | ✅ | 🟢 High |
| `nep` | Nepali | Devanagari | Indo-Aryan | ✅ | ✅ | ✅ | 🟢 High |
| `eng` | English | Latin | Germanic | ✅ | ✅ | ✅ | 🟡 Medium |
| `deu` | German | Latin | Germanic | ✅ | ✅ | ✅ | 🟡 Medium |
| `spa` | Spanish | Latin | Romance | ✅ | ✅ | ✅ | 🟡 Medium |
| `ben` | Bengali | Bengali | Indo-Aryan | ✅ | ✅ | ✅ | 🟡 Medium |
| `pan` | Punjabi | Gurmukhi | Indo-Aryan | ✅ | ✅ | ✅ | 🟡 Medium |
| `tel` | Telugu | Telugu | Dravidian | ✅ | ✅ | ✅ | 🟡 Medium |
| `tur` | Turkish | Latin | Turkic | ✅ | ✅ | ✅ | 🟡 Medium |
| `swa` | Swahili | Latin | Bantu | ✅ | ✅ | ✅ | 🟡 Medium |
| `amh` | Amharic | Ge'ez | Semitic | ✅ | ✅ | ✅ | 🟡 Medium |
| `mya` | Burmese | Burmese | Sino-Tibetan | ✅ | ✅ | ❌ | 🟡 Medium |
| `ita` | Italian | Latin | Romance | ✅ | ✅ | ❌ | 🟡 Medium |
| `pol` | Polish | Latin | Slavic | ✅ | ✅ | ❌ | 🟡 Medium |
| `rus` | Russian | Cyrillic | Slavic | ✅ | ✅ | ❌ | 🟡 Medium |
| `fas` | Persian | Perso-Arabic | Iranian | ✅ | ✅ | ⚠️ | 🔴 Low |
| `hau` | Hausa | Latin | Afro-Asiatic | ✅ | ✅ | ⚠️ | 🔴 Low |
| `ori` | Odia | Odia | Indo-Aryan | ✅ | ✅ | ⚠️ | 🔴 Low |

## ST3 Exclusions

Four languages were excluded from Subtask 3 in the competition data:
- **Burmese** (`mya`) — no ST3 annotations provided
- **Italian** (`ita`) — no ST3 annotations provided
- **Polish** (`pol`) — no ST3 annotations provided
- **Russian** (`rus`) — no ST3 annotations provided

## ST3 Suppressions

Three languages have ST3 data but results are unreliable and suppressed in the UI:
- **Persian** (`fas`) — ST3 macro-F1 = 0.0 across all experiments
- **Hausa** (`hau`) — ST3 macro-F1 ≈ 0.14 average
- **Odia** (`ori`) — ST3 macro-F1 ≈ 0.03 average

These languages still run ST3 inference internally but the scores are not shown to avoid misleading users.

## Language Detection

Language detection uses [lingua-language-detector](https://github.com/pemistahl/lingua-rs). Languages not included in lingua's model set (Nepali, Amharic, Burmese, Odia, Khmer, Hausa in some builds) default to English detection. A `lang` override parameter can be added to the `/predict` API call to force a specific language.
