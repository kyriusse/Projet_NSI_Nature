from __future__ import annotations

from collections import deque #importe deque une structure de données pour les files 


class Pile: #définition de la classe Pile 
    def __init__(self):
        self._donnees = []  #créer une liste vide pour stocker les éléments de la pile

    def empiler(self, valeur):
        self._donnees.append(valeur) #ajoute une valeur au somment de la pile 

    def depiler(self):
        if self.est_vide():  #vérifie si la pile est vide 
            return None #si elle est vide on retourne None 
        return self._donnees.pop() #enlève et retourne le dernier élément ajouté 

    def est_vide(self):
        return len(self._donnees) == 0  #retourne True si la pile est vide sinon False 


class File: #définition de la classe File 
    def __init__(self):
        self._donnees = deque()  #Initialise une deque pour stocker les éléments de la file 

    def enfiler(self, valeur):
        self._donnees.append(valeur) #ajoute une valeur à la fin de la file 

    def defiler(self):
        if self.est_vide():   #vérifie si la file est vide 
            return None  #si elle l'est on retourne None 
        return self._donnees.popleft()  #on retire et retourne le le premier élément ajouté 

    def est_vide(self):
        return len(self._donnees) == 0  #Retourne True si la file est vide sinon cela retourne False 
