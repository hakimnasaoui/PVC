
''' Module permettant de tester systématiquement une série de solveurs
pour le problème du voyageur de commerce.

Permet de lancer automatiquement une série de solveurs sur une série de problèmes
et génère une grille de résultats au format CSV.

'''

# PARAMETRES
# =========
# modifier cette partie pour l'adapter à vos besoins

# Le nom des modules à tester
# Ces modules doivent être dans le PYTHONPATH; p.ex. dans le répertoire courant

modules = (
	"Solution",
	# Éventuellement d'autres modules pour comparer plusieurs versions...
)

# Liste des tests à effectuer
# sous forme de couples (<datafile>, <maxtime>) où
# <datafile> est le fichier contenant les données du problème et
# <maxtime> le temps (en secondes) imparti pour la résolution
tests = (
    ('data/5 villes.txt',1),
    ('data/10 villes.txt',5),
    ('data/10 villes.txt',10),
    ('data/50 villes.txt',30),
    ('data/50 villes.txt',60),
    ('data/100 villes.txt',20),
    ('data/100 villes.txt',90),
)

# On tolère un dépassement de 5% du temps imparti:
tolerance = 0.05

# Fichier dans lequel écrire les résultats
import sys
outfile = sys.stdout
# ou :
#outfile = open('results.csv', 'w')

# affichage à la console d'informations d'avancement?
verbose = False

# est-ce qu'on veut un affichage graphique?
gui = False

# PROGRAMME
# =========
# Cette partie n'a théoriquement pas à être modifiée

import os
from time import time
from math import hypot

def dist(city1,city2):
    x1,y1 = city1
    x2,y2 = city2
    return hypot(x2 -x1,y2-y1)

def validate(filename, length, path, duration, maxtime):

    error = ""

    if duration>maxtime * (1+tolerance):
        error += "Timeout (%.2f) " % (duration-maxtime)
    try:
        cities = dict([(name, (int(x),int(y))) for name,x,y in [l.split() for l in open(filename)]])
    except:
        print(sys.exc_info()[0])
        return "(Validation echoue...)"
    tovisit = list(cities.keys())

    try:
        totaldist = 0
        for (ci, cj) in zip(path, path[1:] +path[0:1]):

            totaldist += dist(cities[ci],  cities[cj])
            tovisit.remove(ci)

        if int(totaldist) != int(length):
            error += "Erreur : Mauvaise distance! (%d au lieu de %d)" % (length, totaldist)
    except KeyError:
        error += "Erreur : Ville %s n'existe pas! " % ci
    except ValueError:
        error += "Erreur : Ville %s apparait deux fois en  %r! " % (ci, path)
    except Exception as e:
        error += "Erreur pendant la validation: %r" % e

    if tovisit:
        error += "Erreur : tous les villes n'a pas visité ! %r" % tovisit

    return error



if __name__ == '__main__':

    solvers = {}

    outfile.write('Tests de tous les villes dans le dossier "data" :')

    for m in modules:
        exec ("from %s import ga_solve" % m)
        solvers[m] = ga_solve
        #outfile.write("%s;" % m)

    outfile.write('\n')

    # Cette partie effectue les tests proprement dits
    # et rapporte les résultats dans outfile

    for (filename, maxtime) in tests:
        if verbose:
            print ("--> %s, %d" % (filename, maxtime))
        # normalisation du nom de fichier (pour l'aspect multi-plateforme)
        filename = os.path.normcase(os.path.normpath(filename))
        # Écriture de l'en-tête de ligne
        outfile.write("%s (%ds);" % (filename, maxtime))
        # Appel des solveurs proprement dits, vérification et écriture des résultats
        for m in modules:
            if verbose:
                print ("## %s" % m)
            try:
                start = time()
                length, path = solvers[m](filename, gui, maxtime)
                duration = time()-start
            except Exception as e:
                    outfile.write("%r;" % e)
            except SystemExit:
                outfile.write("Essayé d'arrete !;")
            else:
                error = validate(filename, length, path, duration, maxtime)
                if not error:
                    outfile.write("Longueur de chemin : %d" % length)
                else:
                    outfile.write("%s" % error)
            outfile.flush()
        outfile.write('\n\n')