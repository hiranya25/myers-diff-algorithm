""" Assignment 1 - Myers diff 

run: python main.py lines A B   or   python main.py highlight A B
"""
import sys

def readLines(path):
    # read as raw bytes, text mode would eat the \r
    with open(path, "rb") as f:
        data =f.read()
    lines = data.split(b"\n")
    # last piece is empty if file ends with \n (or file is empty) -> drop it
    if lines[-1] == b"":
        lines.pop()
    return lines

# Myers' algorithm: the middle snake

def middleSnake(a, b, a0, a1, b0, b1):
    """
    Myers from both ends at once (paper section 4b).
    v1[off + k] = how far right (x) we got going forward on diagonal k = x - y
    v2[off + k] = same thing going backward, x counted from the end
    once the two meet on a diagonal, the forward end point is on a shortest path
    returns the split point (x, y), relative to a0, b0

    """
    n =a1 - a0
    m =b1 - b0
    sa =a[a0:a1]            # local copies: the hot loops avoid offset maths
    sb =b[b0:b1]
    ra =sa[::-1]           # reversed copies so the backward loop looks just like the forward one
    rb =sb[::-1]
    max_d = (n+m+1)//2
    off = max_d
    vlen = 2*max_d+2
    v1 = [-1] *vlen            # -1 = this diagonal not reached yet
    v1[off + 1]=0          # so that d = 0, k = 0 starts at x = 0
    v2 =v1[:]
    delta = n-m
    front =delta & 1      # odd -> paths meet during forward step, even -> backward step
    # these trim k once a path runs off the grid edge
    k1start =k1end =k2start =k2end = 0

    for d in range(max_d+1):
      
        for k1 in range(-d +k1start, d+1-k1end, 2):
            ko = off + k1
            # Move down (insert) from diagonal k+1, or right (delete) from k-1,
            # whichever reaches further.
            if k1 == -d or (k1 != d and v1[ko-1] <v1[ko+1]):
                x1 = v1[ko+1]
            else:
                x1 = v1[ko-1]+1
            y1 = x1-k1
            # Follow the snake: diagonal moves over equal elements are free.
            while x1 < n and y1 < m and sa[x1] == sb[y1]:
                x1 +=1
                y1 +=1
            v1[ko]=x1
            if x1 > n:
                k1end+=2       # ran off the right edge
            elif y1 >m:
                k1start +=2     # ran off the bottom edge
            elif front:
                k2o = off+delta-k1   # same diagonal, seen from the end
                if 0 <= k2o <vlen and v2[k2o] != -1:
                    if x1 >=n-v2[k2o]:
                        return x1, y1

        # ---- backward search, step d ----
        for k2 in range(-d +k2start, d+1-k2end, 2):
            ko = off + k2
            if k2 == -d or (k2 != d and v2[ko - 1] < v2[ko + 1]):
                x2 =v2[ko+1]
            else:
                x2 =v2[ko-1]+1
            y2 = x2-k2
            while x2 < n and y2 < m and ra[x2] == rb[y2]:
                x2+=1
                y2+=1
            v2[ko] = x2
            if x2 > n:
                k2end +=2
            elif y2 > m:
                k2start +=2
            elif not front:
                k1o = off+delta-k2
                if 0 <= k1o < vlen and v1[k1o] != -1:
                    x1 =v1[k1o]
                    y1 =x1-(k1o-off)
                    if x1 >= n-x2:
                        return x1, y1

    raise RuntimeError("middle snake not found")  # cannot happen


# Full diff on any sequence (lines as ints, or characters)

def diff_matches(a, b):
    """Return `match` where match[i] = j if a[i] is kept as b[j], else -1.

    The kept pairs form a longest common subsequence, so the number of
    deletions + insertions is minimal.
    """
    n = len(a)
    match = [-1] * n

    # Elements that never appear in the other sequence can never be kept,
    # so remove them before running Myers. This does not change the LCS.
    in_a = set(a)
    in_b = set(b)
    ai = [i for i in range(n) if a[i] in in_b]
    bj = [j for j in range(len(b)) if b[j] in in_a]
    fa = [a[i] for i in ai]
    fb = [b[j] for j in bj]

    # Divide and conquer with an explicit stack (no recursion limit issues).
    stack = [(0, len(fa), 0, len(fb))]
    while stack:
        a0, a1, b0, b1 = stack.pop()
        # Common prefix: keep.
        while a0 < a1 and b0 < b1 and fa[a0] == fb[b0]:
            match[ai[a0]] = bj[b0]
            a0 += 1
            b0 += 1
        # Common suffix: keep.
        while a0 < a1 and b0 < b1 and fa[a1 - 1] == fb[b1 - 1]:
            a1 -= 1
            b1 -= 1
            match[ai[a1]] = bj[b1]
        # One side empty: everything left is a pure delete or pure insert.
        if a0 == a1 or b0 == b1:
            continue
        x, y = middleSnake(fa, fb, a0, a1, b0, b1)
        stack.append((a0 + x, a1, b0 + y, b1))
        stack.append((a0, a0 + x, b0, b0 + y))
    return match


# Part B: character ranges

def format_ranges(changed):
    """[False, True, True, False, True] -> '1-3,4-5'; nothing changed -> '.'"""
    parts = []
    i, n = 0, len(changed)
    while i < n:
        if changed[i]:
            start = i
            while i < n and changed[i]:
                i += 1
            parts.append(f"{start}-{i}")
        else:
            i += 1
    return ",".join(parts) if parts else "."


def highlight_line(old, new):
    """Build the '? old | new' line for one paired - / + line."""
    s = old.decode("utf-8", "surrogateescape")   # str indexes are code points
    t = new.decode("utf-8", "surrogateescape")
    match = diff_matches(s, t)
    old_changed = [j == -1 for j in match]
    new_changed = [True] * len(t)
    for j in match:
        if j != -1:
            new_changed[j] = False
    return f"? {format_ranges(old_changed)} | {format_ranges(new_changed)}\n".encode()


# Output

def output(A, B, match, highlight):
    """Walk the kept pairs in order. Between two kept lines is a change block:
    print all '-' lines, then all '+' lines (delete-first rule)."""
    out = []
    n, m = len(A), len(B)
    i = j = 0
    kept = [(x, match[x]) for x in range(n) if match[x] != -1]
    kept.append((n, m))  # sentinel: flushes the final change block
    for ci, cj in kept:
        dels = A[i:ci]
        ins = B[j:cj]
        for line in dels:
            out.append(b"-" + line + b"\n")
        for k, line in enumerate(ins):
            out.append(b"+" + line + b"\n")
            if highlight and k < len(dels):
                out.append(highlight_line(dels[k], line))
        if ci < n:
            out.append(b" " + A[ci] + b"\n")
        i, j = ci + 1, cj + 1
    return b"".join(out)


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A B", file=sys.stderr)
        sys.exit(2)
    mode, path_a, path_b = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        A = readLines(path_a)
        B = readLines(path_b)
    except OSError as e:
        print(f"error: cannot read file: {e}", file=sys.stderr)
        sys.exit(2)

    # Turn each distinct line into a small int so comparisons are cheap.
    ids = {}
    a_ids = [ids.setdefault(line, len(ids)) for line in A]
    b_ids = [ids.get(line, -1 - j) for j, line in enumerate(B)]  # unseen -> unique negative

    match = diff_matches(a_ids, b_ids)
    sys.stdout.buffer.write(output(A, B, match, mode == "highlight"))


if __name__ == "__main__":
    main()
