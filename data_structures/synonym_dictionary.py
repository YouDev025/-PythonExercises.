"""
Synonym Dictionary
──────────────────────────────────────────────
A program that lets you look up synonyms for words,
add your own custom word-synonym entries, and manage
a personal synonym dictionary — all without internet.

Features:
  • Look up synonyms from a built-in dictionary
  • Add new words and their synonyms
  • View all words in the dictionary
  • Remove a word from the dictionary
  • Case-insensitive input handling
──────────────────────────────────────────────
"""

# ─────────────────────────────────────────────
#  Built-in Synonym Dictionary
# ─────────────────────────────────────────────

SYNONYMS = {
    "happy": ["joyful", "cheerful", "content", "pleased", "glad", "delighted", "elated", "blissful", "ecstatic", "jovial"],
    "sad": ["unhappy", "sorrowful", "dejected", "melancholy", "gloomy", "miserable", "downcast", "heartbroken", "woeful", "despondent"],
    "angry": ["furious", "enraged", "irate", "livid", "incensed", "wrathful", "irritated", "annoyed", "outraged", "infuriated"],
    "beautiful": ["gorgeous", "stunning", "attractive", "lovely", "elegant", "exquisite", "radiant", "dazzling", "charming", "graceful"],
    "ugly": ["unattractive", "hideous", "unsightly", "repulsive", "ghastly", "grotesque", "unpleasant", "homely", "revolting"],
    "big": ["large", "huge", "enormous", "vast", "gigantic", "massive", "colossal", "immense", "grand", "substantial"],
    "small": ["tiny", "little", "miniature", "petite", "minute", "compact", "diminutive", "slight", "microscopic", "minuscule"],
    "fast": ["quick", "swift", "rapid", "speedy", "brisk", "hasty", "nimble", "fleet", "prompt", "instantaneous"],
    "slow": ["sluggish", "leisurely", "gradual", "unhurried", "languid", "plodding", "delayed", "lagging", "tardy", "dawdling"],
    "good": ["excellent", "great", "superb", "fine", "wonderful", "outstanding", "splendid", "admirable", "exceptional", "quality"],
    "bad": ["awful", "terrible", "dreadful", "poor", "inferior", "atrocious", "horrible", "abysmal", "wretched", "lousy"],
    "smart": ["intelligent", "clever", "brilliant", "sharp", "wise", "astute", "knowledgeable", "gifted", "ingenious", "perceptive"],
    "stupid": ["foolish", "idiotic", "dull", "dense", "dim-witted", "ignorant", "brainless", "moronic", "absurd", "senseless"],
    "strong": ["powerful", "mighty", "sturdy", "robust", "muscular", "tough", "resilient", "formidable", "vigorous", "stalwart"],
    "weak": ["feeble", "frail", "fragile", "delicate", "puny", "powerless", "vulnerable", "infirm", "flimsy", "helpless"],
    "rich": ["wealthy", "affluent", "prosperous", "opulent", "well-off", "moneyed", "lavish", "flourishing", "comfortable", "well-to-do"],
    "poor": ["impoverished", "destitute", "needy", "penniless", "broke", "underprivileged", "indigent", "bankrupt", "hard-up", "disadvantaged"],
    "old": ["ancient", "aged", "elderly", "antique", "archaic", "vintage", "mature", "venerable", "decrepit", "time-worn"],
    "new": ["fresh", "modern", "recent", "novel", "current", "latest", "contemporary", "brand-new", "up-to-date", "innovative"],
    "bright": ["luminous", "radiant", "vivid", "brilliant", "gleaming", "shining", "dazzling", "glowing", "vibrant", "lustrous"],
    "dark": ["dim", "shadowy", "gloomy", "murky", "dusky", "obscure", "dreary", "somber", "overcast", "sunless"],
    "cold": ["chilly", "frigid", "icy", "frosty", "freezing", "cool", "arctic", "bitter", "wintry", "crisp"],
    "hot": ["warm", "scorching", "boiling", "blazing", "sweltering", "sizzling", "torrid", "fiery", "tropical", "sultry"],
    "clean": ["spotless", "neat", "tidy", "pristine", "immaculate", "sanitary", "sterile", "hygienic", "pure", "polished"],
    "dirty": ["filthy", "grimy", "muddy", "messy", "soiled", "stained", "tainted", "unclean", "squalid", "contaminated"],
    "easy": ["simple", "effortless", "straightforward", "uncomplicated", "manageable", "basic", "painless", "smooth", "elementary", "light"],
    "hard": ["difficult", "tough", "challenging", "demanding", "strenuous", "arduous", "complex", "grueling", "laborious", "taxing"],
    "brave": ["courageous", "bold", "fearless", "daring", "heroic", "gallant", "valiant", "intrepid", "audacious", "gutsy"],
    "scared": ["frightened", "terrified", "fearful", "anxious", "alarmed", "horrified", "petrified", "timid", "startled", "panicked"],
    "funny": ["humorous", "amusing", "comical", "hilarious", "witty", "entertaining", "laughable", "playful", "silly", "whimsical"],
    "serious": ["solemn", "grave", "earnest", "stern", "sober", "intense", "sincere", "resolute", "thoughtful", "weighty"],
    "kind": ["gentle", "generous", "caring", "compassionate", "warm", "tender", "benevolent", "thoughtful", "considerate", "gracious"],
    "cruel": ["harsh", "brutal", "heartless", "vicious", "merciless", "ruthless", "savage", "callous", "inhumane", "cold-blooded"],
    "calm": ["peaceful", "serene", "tranquil", "composed", "relaxed", "still", "placid", "unruffled", "poised", "collected"],
    "noisy": ["loud", "boisterous", "rowdy", "clamorous", "raucous", "tumultuous", "blaring", "deafening", "thunderous", "uproarious"],
    "tired": ["exhausted", "weary", "fatigued", "drowsy", "sleepy", "drained", "worn-out", "lethargic", "spent", "listless"],
    "energetic": ["lively", "vigorous", "dynamic", "spirited", "active", "enthusiastic", "animated", "peppy", "vibrant", "zippy"],
    "important": ["significant", "crucial", "vital", "essential", "critical", "major", "key", "fundamental", "notable", "paramount"],
    "useless": ["worthless", "pointless", "futile", "ineffective", "redundant", "vain", "idle", "trivial", "fruitless", "meaningless"],
    "strange": ["odd", "weird", "peculiar", "unusual", "bizarre", "eccentric", "abnormal", "curious", "uncanny", "mysterious"],
    "normal": ["ordinary", "typical", "standard", "common", "regular", "conventional", "average", "usual", "routine", "familiar"],
    "start": ["begin", "commence", "initiate", "launch", "embark", "open", "trigger", "activate", "set off", "introduce"],
    "stop": ["cease", "halt", "end", "discontinue", "terminate", "conclude", "quit", "pause", "suspend", "abort"],
    "walk": ["stroll", "march", "stride", "saunter", "trek", "amble", "wander", "roam", "hike", "pace"],
    "run": ["sprint", "dash", "jog", "race", "gallop", "bolt", "rush", "charge", "hurry", "scurry"],
    "say": ["speak", "utter", "state", "declare", "express", "announce", "mention", "tell", "articulate", "voice"],
    "think": ["ponder", "consider", "reflect", "contemplate", "reason", "deliberate", "meditate", "imagine", "speculate", "muse"],
    "look": ["gaze", "stare", "glance", "observe", "watch", "examine", "peer", "scrutinize", "behold", "survey"],
    "make": ["create", "build", "construct", "produce", "form", "craft", "develop", "fabricate", "generate", "assemble"],
    "break": ["shatter", "crack", "smash", "fracture", "rupture", "split", "destroy", "demolish", "collapse", "dismantle"],
    "help": ["assist", "aid", "support", "guide", "contribute", "facilitate", "enable", "serve", "back", "cooperate"],
    "love": ["adore", "cherish", "treasure", "admire", "worship", "idolize", "fancy", "care for", "devote", "hold dear"],
    "hate": ["despise", "detest", "loathe", "abhor", "dislike", "resent", "scorn", "disdain", "execrate", "abominate"],
    "talk": ["chat", "converse", "discuss", "communicate", "speak", "dialogue", "gossip", "lecture", "debate", "address"],
    "show": ["display", "exhibit", "present", "demonstrate", "reveal", "expose", "illustrate", "depict", "showcase", "manifest"],
    "change": ["alter", "modify", "transform", "adjust", "revise", "shift", "amend", "convert", "adapt", "reshape"],
    "buy": ["purchase", "acquire", "obtain", "procure", "invest in", "pay for", "get", "secure", "pick up", "order"],
    "sell": ["trade", "market", "vend", "auction", "deal", "exchange", "offer", "retail", "advertise", "promote"],
    "keep": ["retain", "maintain", "preserve", "store", "hold", "save", "protect", "conserve", "guard", "sustain"],
    "give": ["donate", "offer", "provide", "present", "grant", "bestow", "contribute", "supply", "hand over", "deliver"],
    "take": ["grab", "seize", "collect", "receive", "obtain", "acquire", "snatch", "retrieve", "capture", "fetch"],
    "go": ["travel", "move", "proceed", "depart", "advance", "journey", "head", "migrate", "venture", "set out"],
    "come": ["arrive", "approach", "appear", "return", "reach", "emerge", "near", "advance", "enter", "show up"],
    "work": ["labor", "toil", "operate", "function", "perform", "endeavor", "strive", "hustle", "grind", "execute"],
    "play": ["enjoy", "participate", "compete", "engage", "perform", "frolic", "amuse", "entertain", "recreate", "sport"],
    "idea": ["concept", "notion", "thought", "theory", "plan", "vision", "suggestion", "proposal", "insight", "inspiration"],
    "problem": ["issue", "challenge", "difficulty", "obstacle", "dilemma", "complication", "setback", "trouble", "predicament", "hurdle"],
    "answer": ["solution", "response", "reply", "result", "outcome", "explanation", "resolution", "reaction", "feedback", "rebuttal"],
    "question": ["inquiry", "query", "doubt", "problem", "matter", "issue", "challenge", "puzzle", "concern", "riddle"],
    "friend": ["companion", "buddy", "ally", "associate", "comrade", "pal", "confidant", "colleague", "partner", "mate"],
    "enemy": ["foe", "rival", "opponent", "adversary", "antagonist", "nemesis", "competitor", "detractor", "challenger", "opposition"],
    "home": ["house", "residence", "dwelling", "abode", "domicile", "haven", "shelter", "habitat", "lodging", "quarters"],
    "money": ["cash", "currency", "funds", "wealth", "capital", "income", "finances", "assets", "earnings", "revenue"],
    "time": ["period", "moment", "duration", "era", "epoch", "interval", "phase", "span", "occasion", "instance"],
    "place": ["location", "spot", "site", "position", "area", "region", "venue", "locale", "zone", "territory"],
}

# User-defined words added during the session
custom_synonyms = {}

DIVIDER = "─" * 48


# ─────────────────────────────────────────────
#  Core Functions
# ─────────────────────────────────────────────

def find_synonyms(word):
    """Look up synonyms for a word (case-insensitive)."""
    key = word.strip().lower()
    if key in custom_synonyms:
        return custom_synonyms[key]
    if key in SYNONYMS:
        return SYNONYMS[key]
    return None


def display_synonyms(word):
    """Find and display synonyms for the given word."""
    print(f"\n  {'SYNONYM LOOKUP':^44}")
    print(DIVIDER)
    key = word.strip().lower()
    synonyms = find_synonyms(key)

    if synonyms is None:
        print(f"  ✘ '{word}' was not found in the dictionary.")
        print("  💡 Tip: You can add it via option 3 in the menu.")
    elif not synonyms:
        print(f"  ⚠  '{word}' exists but has no synonyms listed.")
    else:
        source = "custom" if key in custom_synonyms else "built-in"
        print(f"  🔍 Synonyms for  \"{key}\"  [{source} dictionary]:\n")
        for i, syn in enumerate(synonyms, 1):
            print(f"    {i:>2}. {syn}")
        print(f"\n  Total: {len(synonyms)} synonym(s) found.")
    print(DIVIDER)


def add_word():
    """Add a new word and its synonyms to the custom dictionary."""
    print(f"\n  {'ADD CUSTOM WORD':^44}")
    print(DIVIDER)
    word = input("  Enter the new word: ").strip().lower()

    if not word:
        print("  ✘ Word cannot be empty.")
        return

    existing = find_synonyms(word)
    if existing is not None:
        print(f"  ⚠  '{word}' already exists with {len(existing)} synonym(s).")
        overwrite = input("  Do you want to overwrite it? (yes/no): ").strip().lower()
        if overwrite not in ("yes", "y"):
            print("  ✔ No changes made.")
            return

    syn_input = input(f"  Enter synonyms for '{word}' (comma-separated): ").strip()
    if not syn_input:
        print("  ✘ No synonyms entered. Word not added.")
        return

    synonyms = [s.strip().lower() for s in syn_input.split(",") if s.strip()]
    if not synonyms:
        print("  ✘ No valid synonyms found. Word not added.")
        return

    custom_synonyms[word] = synonyms
    print(f"  ✔ '{word}' added with {len(synonyms)} synonym(s): {', '.join(synonyms)}")


def view_all_words():
    """Display all words available in the dictionary."""
    print(f"\n  {'ALL DICTIONARY WORDS':^44}")
    print(DIVIDER)

    all_words = sorted(set(list(SYNONYMS.keys()) + list(custom_synonyms.keys())))
    total = len(all_words)

    print(f"  Total words available: {total}\n")
    cols = 3
    for i in range(0, len(all_words), cols):
        row = all_words[i:i + cols]
        line = "".join(f"  {'[C] ' if w in custom_synonyms else '    '}{w:<18}" for w in row)
        print(line)
    print(f"\n  [C] = Custom word added by you")
    print(DIVIDER)


def remove_word():
    """Remove a custom word from the dictionary."""
    print(f"\n  {'REMOVE CUSTOM WORD':^44}")
    print(DIVIDER)
    if not custom_synonyms:
        print("  ✘ You have no custom words to remove.")
        return

    word = input("  Enter the custom word to remove: ").strip().lower()
    if not word:
        print("  ✘ No input provided.")
        return

    if word in custom_synonyms:
        del custom_synonyms[word]
        print(f"  ✔ '{word}' has been removed from your custom dictionary.")
    elif word in SYNONYMS:
        print(f"  ⚠  '{word}' is a built-in word and cannot be removed.")
    else:
        print(f"  ✘ '{word}' was not found in your custom dictionary.")


def lookup_menu():
    """Prompt the user for a word and display its synonyms."""
    print(f"\n  {'LOOK UP A WORD':^44}")
    print(DIVIDER)
    word = input("  Enter a word to look up: ").strip()
    if not word:
        print("  ✘ No word entered.")
        return
    display_synonyms(word)


# ─────────────────────────────────────────────
#  Menu
# ─────────────────────────────────────────────

def print_intro():
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║          SYNONYM DICTIONARY  📖               ║")
    print("  ╠══════════════════════════════════════════════╣")
    print("  ║  Instantly find synonyms for any word.        ║")
    print("  ║  • Built-in dictionary with 80+ common words  ║")
    print("  ║  • Add your own custom word-synonym entries   ║")
    print("  ║  • Case-insensitive — type freely             ║")
    print("  ║  • Handles unknown words gracefully           ║")
    print("  ╚══════════════════════════════════════════════╝")


def print_menu():
    print(f"\n{'═' * 48}")
    print("             SYNONYM DICTIONARY MENU")
    print(f"{'═' * 48}")
    print("  1. Look up synonyms for a word")
    print("  2. View all words in the dictionary")
    print("  3. Add a custom word and synonyms")
    print("  4. Remove a custom word")
    print("  5. Exit")
    print(DIVIDER)


def main():
    print_intro()

    while True:
        print_menu()
        choice = input("  Enter your choice (1–5): ").strip()
        print()

        if choice == "1":
            lookup_menu()
        elif choice == "2":
            view_all_words()
        elif choice == "3":
            add_word()
        elif choice == "4":
            remove_word()
        elif choice == "5":
            print("  Goodbye! Keep expanding your vocabulary. 📚\n")
            break
        else:
            print("  ✘ Invalid choice. Please enter a number between 1 and 5.")


if __name__ == "__main__":
    main()