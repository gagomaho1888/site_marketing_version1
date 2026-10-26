import unicodedata


def normalize(text):
    text = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def levenshtein(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(
                min(
                    prev[j] + 1,
                    cur[j - 1] + 1,
                    prev[j - 1] + (ca != cb),
                )
            )
        prev = cur
    return prev[-1]


def word_similarity(query, name):
    """Renvoie une distance max parmi les mots du nom et du query."""
    q_words = normalize(query).split()
    n_words = normalize(name).split()
    best = float("inf")
    matched = False
    for qw in q_words:
        for nw in n_words:
            if qw == nw:
                return 0
            if len(qw) >= 3 and len(nw) >= 3:
                d = levenshtein(qw, nw)
                if d <= 1:
                    best = min(best, 0.5)
    return best
