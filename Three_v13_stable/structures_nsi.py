from __future__ import annotations

from collections import deque


class Pile:
    def __init__(self):
        self._donnees = []

    def empiler(self, valeur):
        self._donnees.append(valeur)

    def depiler(self):
        if self.est_vide():
            return None
        return self._donnees.pop()

    def est_vide(self):
        return len(self._donnees) == 0


class File:
    def __init__(self):
        self._donnees = deque()

    def enfiler(self, valeur):
        self._donnees.append(valeur)

    def defiler(self):
        if self.est_vide():
            return None
        return self._donnees.popleft()

    def est_vide(self):
        return len(self._donnees) == 0
