import re

class NFA:
    def __init__(self, states, start, final, transition):
        self.states = states
        self.start = start
        self.final = final
        self.transition = transition # {state : {char : {states}}}

    def getregex(self):
        return self.regex

    def __str__(self):
        lst = [*map(repr, [self.states, self.start, self.final, self.transition])]
        return "states:\n" + lst[0] + "\n\nstart:\n" + lst[1] + "\n\nfinal:\n" + lst[2] + "\n\ntransition:\n" + lst[3]

    def run(self, word, prefix=True, index=0, stride=1):
        index += 1
        word = "\n" + word + "\n"
        current = self.start.copy()
        intersection = self.final & current
        matched = index if intersection else None

        while index >= 0 and index < len(word) and current and not (prefix and matched is not None and not self.greedy):
            newcurrent = set()
            for state in current:
                dct = self.transition.get(state, {})
                for key in dct:
                    if re.match(key, word[index]):
                        newcurrent |= dct[key]

            current = newcurrent
            intersection = self.final & current
            index += stride
            matched = index if intersection else matched

        if intersection:
            return index - 1

        if prefix and matched is not None:
            return matched - 1

        return None

    def filerun(self, fl, prefix=True, stride=1):
        x, y = fl.getposition()
        current = self.start.copy()
        intersection = self.final & current
        matched = fl.getposition() if intersection else None

        while current and not (prefix and matched is not None and not self.greedy):
            char = fl.getchar()
            newcurrent = set()
            for state in current:
                dct = self.transition.get(state, {})
                for key in dct:
                    if re.match(key, char):
                        newcurrent |= dct[key]

            current = newcurrent
            intersection = self.final & current
            fl.move(stride, False)
            matched = fl.getposition() if intersection else matched

        if intersection:
            return True

        if prefix and matched is not None:
            fl.setposition(*matched)
            return True

        fl.setposition(x, y)
        return False

    # Mabe check if there is a copy error with NFA.fromregex("ab") (unreachable states)
    def union(nfa1, nfa2, state):
        transition = {**nfa1.transition, **nfa2.transition}
        return NFA(nfa1.states |nfa2.states, nfa1.start | nfa2.start, nfa1.final | nfa2.final, transition), state

    def combinedct(dct1, dct2):
        dct = {}
        for key in dct1.keys():
            dct[key] = dct1[key]
        for key in dct2.keys():
            dct[key] = dct.get(key, set()) | dct2[key]
        return dct

    def concat(nfa1, nfa2, state):
        transition = {**nfa1.transition, **nfa2.transition}
        dct = {}
        for start in nfa2.start:
            dct = NFA.combinedct(dct, nfa2.transition.get(start, {}))
        for final in nfa1.final:
            transition[final] = NFA.combinedct(nfa1.transition.get(final, {}), dct)
        final = nfa2.final | (nfa1.final if nfa2.start & nfa2.final else set())
        return NFA(nfa1.states | nfa2.states, nfa1.start, final, transition), state

    def plus(nfa, state):
        transition = {**nfa.transition}
        dct = {}
        for start in nfa.start:
            dct = NFA.combinedct(dct, nfa.transition.get(start, {}))
        for final in nfa.final:
            transition[final] = NFA.combinedct(nfa.transition.get(final, {}), dct)
        return NFA(nfa.states, nfa.start, nfa.final, transition), state

    def questionmark(nfa, state):
        nfa, state = NFA.concat(NFA({state}, {state}, {state}, {}), nfa, state + 1)
        nfa.final |= nfa.start
        return nfa, state + 1

    def star(nfa, state):
        return NFA.questionmark(*NFA.plus(nfa, state))

    def notescaped(string, index):
        switch = True
        index -= 1
        while index >= 0:
            char = string[index]
            if char != "\\":
                break
            index -= 1
            switch = not switch
        return switch

    def getsections(regex, index, openchar, midchar, closechar):
        index += 1
        old = index
        counter = 1
        sections = []
        while counter > 0 and index < len(regex):
            notesc = NFA.notescaped(regex, index)
            if notesc:
                if regex[index] == midchar and counter == 1:
                    sections.append(regex[old : index])
                    old = index + 1
                elif regex[index] == openchar:
                    counter += 1
                elif regex[index] == closechar:
                    counter -= 1
                    if counter == 0:
                        sections.append(regex[old : index])
            index += 1
        return sections, index

    def __fromregex(regex, index=0, state=0):
        if index >= len(regex):
            return NFA({state}, {state}, {state}, {}), state + 1

        nfa = None
        notesc = NFA.notescaped(regex, index)
        if notesc and regex[index] in "\\":
            return NFA.__fromregex(regex, index + 1, state)
        elif notesc and regex[index] == "(":
            sections, index2 = NFA.getsections(regex, index, "(", "|", ")")
            nfa = NFA(set(), set(), set(), {})
            for section in sections:
                nfa, state = NFA.union(nfa, *NFA.__fromregex(section, 0, state))
            index = index2
        elif notesc and regex[index] == "[":
            _, index2 = NFA.getsections(regex, index, "[", "", "]")
            nfa = NFA({state, state + 1}, {state}, {state + 1}, {state : {regex[index : index2] : {state + 1}}})
            state, index = state + 2, index2
        else:
            prefix = "" if notesc else "\\"
            nfa = NFA({state, state + 1}, {state}, {state + 1}, {state : {prefix + regex[index] : {state + 1}}})
            state, index = state + 2, index + 1

        while index < len(regex) and NFA.notescaped(regex, index):
            if regex[index] == "?":
                nfa, state = NFA.questionmark(nfa, state)
            elif regex[index] == "*":
                nfa, state = NFA.star(nfa, state)
            elif regex[index] == "+":
                nfa, state = NFA.plus(nfa, state)
            else:
                break
            index += 1

        if index >= len(regex):
            return nfa, state
        return NFA.concat(nfa, *NFA.__fromregex(regex, index, state))

    def fromregex(regex):
        greedy = False
        newregex = regex

        if regex and "+" == regex[0]:
            greedy = True
            newregex = regex[1 : ]

        nfa = NFA.__fromregex(newregex)[0]
        nfa.greedy = greedy
        nfa.regex = regex
        return nfa
