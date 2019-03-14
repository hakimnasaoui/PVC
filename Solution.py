import os, sys
import pygame
from pygame.locals import *
import time
import math
import random
from collections import OrderedDict

ville_coleur = [255,255,0]
ville_diametre = 4

def ga_solve(filename=None, gui=True, maxtime=0):

    if filename == None:
        pygame.init()
        window = pygame.display.set_mode((700, 700))

        pygame.display.set_caption('Solution de Problème de Voyageur de Commerce')
        ecran = pygame.display.get_surface()

        ecran.fill(0)

        collecting = True

        font = pygame.font.Font(None,30)
        villes = []

        while collecting:
            for event in pygame.event.get():
                if event.type == QUIT:
                    sys.exit(0)
                elif event.type == KEYDOWN and event.key == K_RETURN:
                    collecting = False
                elif event.type == MOUSEBUTTONDOWN:
                    villes.append(pygame.mouse.get_pos())
                    ecran.fill(0)
                    drawPoint(villes, ecran)
                    pygame.display.flip()


        nodes_distances_dict, nodes_pos = data_ecran_parser(villes)

    else:
        nodes_distances_dict, nodes_pos = data_parser(filename)

        ecran = None
        if gui:
            pygame.init()
            window = pygame.display.set_mode((700, 700))
            pygame.display.set_caption('Solution : ')
            ecran = pygame.display.get_surface()

            ecran.fill(0)
            drawPoint(nodes_pos.values(), ecran)
            pygame.display.flip()

            event = pygame.event.wait()




    global verbose
    verbose = False

    global global_nodes_dict
    global_nodes_dict = nodes_distances_dict

    global global_MeilleurChemin
    global_MeilleurChemin = MeilleurChemin(maxtime)

    return darwinism(create_population(), nodes_pos, ecran)


def drawPoint(positions, ecran):
    font = pygame.font.Font(None,24)

    for pos in positions:
        pygame.draw.circle(ecran,ville_coleur,pos,ville_diametre)
    text = font.render("Nombre de villes: %i" % len(positions), True, [255,255,255])
    textRect = text.get_rect()
    ecran.blit(text, textRect)



def drawChromosome(ecran, chemin, nodes_pos, cheminLongueur):
    ecran.fill(0)

    ville_id_ancien = chemin[0]

    i=1
    while i < len(chemin):
        villeId = chemin[i]

        ville1 = nodes_pos[villeId]
        ville2 = nodes_pos[ville_id_ancien]

        pygame.draw.line(ecran, [240,240,240], ville1, ville2, 2)

        ville_id_ancien = villeId
        i+=1

    pygame.draw.line(ecran, [255,255,255], nodes_pos[chemin[0]], nodes_pos[chemin[-1]], 2)

    font = pygame.font.Font(None,24)
    text = font.render("Longueur de meilleur chemin: %i" % cheminLongueur, True, [255,255,255])
    textRect = text.get_rect()
    ecran.blit(text, (0, 20))

    drawPoint(nodes_pos.values(), ecran)
    pygame.display.flip()



def ga_solver_brute(filename, gui, maxtime, populationsize, tournaments, elitismrate, mutationrate):
    nodes_distances_dict, node_pos = data_parser(filename)

    global verbose
    verbose = False

    global global_nodes_dict
    global_nodes_dict = nodes_distances_dict

    global global_MeilleurChemin
    global_MeilleurChemin = MeilleurChemin(maxtime, _populationsize=populationsize, _tournaments=tournaments,
                                               _elitismrate=elitismrate, _mutationrate=mutationrate)

    return darwinism(create_population())


def dist(ville1, ville2):
    x1, y1 = ville1
    x2, y2 = ville2
    return math.hypot(x2 - x1, y2 - y1)


class MeilleurChemin:
    def __init__(self, _maxtime, _populationsize=7, _tournaments=3, _elitismrate=0.8,
                 _maxgenerations=2000, _mutationrate=0.2, _clonelimit=50):
        self.population_size = _populationsize
        self.tournaments = _tournaments
        self.elitism_rate = _elitismrate
        self.max_generations = _maxgenerations
        self.use_max_generation = False
        self.mutation_rate = _mutationrate
        self.clone_limit = _clonelimit
        self.use_clone_limit = (_maxtime <= 0)
        self.maxtime = _maxtime


        self.elite_amount = int(self.population_size * self.elitism_rate)

    def fitness(self, _chromosome):

        looped_chromosome = list(_chromosome)
        looped_chromosome.append(_chromosome[0])
        _chromosome = tuple(looped_chromosome)

        return sum(
            (global_nodes_dict[_chromosome[gene]][_chromosome[gene + 1]] for gene in range(0, len(_chromosome) - 1)))

    def mutation(self, _chromosome):

        probability = random.randint(1, 100) / 100
        if probability >= self.mutation_rate:
            parts = sorted(random.sample(list(range(1, len(_chromosome))), 2))
            _chromosome[parts[0]], _chromosome[parts[1]] = _chromosome[parts[1]], _chromosome[parts[0]]

        return tuple(_chromosome)

    def selection_tournament(self, _population):

        gagnants = random.sample(list(_population.items()), self.tournaments)
        sorted_gagnants = sorted(gagnants, key=lambda t: t[1])
        return sorted_gagnants[0][0]

    def selection_rank(self, _population):

        population_size = len(_population)
        threshold = random.randint(1, (population_size * (population_size - 1)) / 2)
        total_rank = 0

        for index, chromosome in enumerate(sorted(_population, key=lambda t: t[1])):
            current_rank = population_size - index
            total_rank += current_rank
            if threshold <= total_rank:
                return chromosome

    def selection_roulette(self, _population):

        roulette = random.random()
        threshold = list(_population.items())[0][1]
        bottom_chance = 0.0

        for index, chromosome in enumerate(sorted(_population, key=lambda t: t[1])):
            current_chance = global_MeilleurChemin.fitness(chromosome) / threshold
            top_chance = bottom_chance + current_chance
            if bottom_chance <= roulette <= top_chance:
                return chromosome
            else:
                bottom_chance = top_chance

    def crossover(self, _couple):

        couple = list(_couple)
        random.shuffle(couple)
        parts = sorted(random.sample(list(range(0, len(couple[0]))), 2))
        half = couple[0][parts[0]:parts[1]]

        chemin = [None] * len(couple[0])
        chemin[parts[0]:parts[1]] = half

        pointer = 0
        for index, item in enumerate(chemin):
            if not item:
                gene = couple[1][pointer]
                while gene in half:
                    pointer += 1
                    gene = couple[1][pointer]

                chemin[index] = couple[1][pointer]
                pointer += 1

        return chemin


def bird_distance(node1, node2):
    x1, y1 = node1
    x2, y2 = node2
    return math.hypot(x2 - x1, y2 - y1)

def dist_calcul(nodes_dict):

    data_dict = {}
    for node in list(nodes_dict.keys()):
        distances_dict = {}
        for next_node in nodes_dict:
            if next_node != node:
                distances_dict[next_node] = bird_distance(nodes_dict[node], nodes_dict[next_node])
            else:
                distances_dict[next_node] = 0

        data_dict[node] = distances_dict
    return data_dict

def data_parser(file=None):
    if file is None:
        return -1

    nodes_dict = {}
    data_file = open(file, 'r')

    for line in data_file:
        values = line.split()
        nodes_dict[int(values[0][1:]) + 1] = (int(values[1]), int(values[2]))

    data_dict = dist_calcul(nodes_dict)

    return data_dict, nodes_dict


def data_ecran_parser(villesPos):

    nodes_dict = {}

    i=1
    for ville in villesPos:
        nodes_dict[i] = (int(ville[0]), int(ville[1]))
        i+=1

    data_dict = dist_calcul(nodes_dict)

    return data_dict, nodes_dict

def create_population():
    population_list = []
    fitness_list = []
    position_possibilities_list = tuple(range(2, len(global_nodes_dict) + 1))

    for individualChromosome in range(0, global_MeilleurChemin.population_size):

        chromosome = []
        possible = list(position_possibilities_list)

        while len(possible) != 0:
            selected = random.choice(possible)
            del possible[possible.index(selected)]
            chromosome.append(selected)

        chromosome.insert(0, 1)
        distance = global_MeilleurChemin.fitness(chromosome)

        fitness_list.append(distance)
        population_list.append(tuple(chromosome))

    population = dict(zip(population_list, fitness_list))
    population = OrderedDict(sorted(population.items(), key=lambda t: t[1]))

    return population


def darwinism(population, nodes_pos, ecran=None):

    meilleur_chemin = list(population.items())[0]
    clone_counter = 0

    start = time.time()
    generation = 0

    while (generation < global_MeilleurChemin.max_generations or not global_MeilleurChemin.use_max_generation) or global_MeilleurChemin.use_clone_limit:


        noble_population_list = []

        elite = list(population.keys())[:global_MeilleurChemin.elite_amount]
        actuel_ville = list(population.items())[0]

        if actuel_ville[1] == meilleur_chemin[1]:
            clone_counter += 1
        elif actuel_ville[1] < meilleur_chemin[1]:
            clone_counter = 0
            meilleur_chemin = actuel_ville
            del elite[elite.index(actuel_ville[0])]


        if global_MeilleurChemin.clone_limit == clone_counter and global_MeilleurChemin.use_clone_limit:
            if verbose:
                print("clone counter  : ", clone_counter)
                print("clone limit : ", global_MeilleurChemin.clone_limit)
                print("Clone limit achieved :)")
            break

        noble_population_list.append(meilleur_chemin[0])
        noble_population_list.extend(elite)

        while len(noble_population_list) != global_MeilleurChemin.population_size:
            answer = False
            if answer:
                selections = [
                    global_MeilleurChemin.selection_tournament(population),
                    global_MeilleurChemin.selection_rank(population),
                    global_MeilleurChemin.selection_roulette(population)
                ]
                couple = selections[random.randrange(0, len(selections), 1)], selections[random.randrange(0, len(selections), 1)]
            else:
                couple = global_MeilleurChemin.selection_rank(population), global_MeilleurChemin.selection_rank(population)

            chemin = global_MeilleurChemin.crossover(couple)
            muted_chemin = global_MeilleurChemin.mutation(chemin)
            noble_population_list.append(muted_chemin)

        fitness_list = [global_MeilleurChemin.fitness(chromosome) for chromosome in noble_population_list]
        population = dict(zip(noble_population_list, fitness_list))
        population = OrderedDict(sorted(population.items(), key=lambda t: t[1]))

        if verbose:
            fitness_average = int(sum(list(population.values())) / len(population))
            fittest = list(population.keys())[0]
            fittest_value = population[fittest]

            print()
            print("-----------------------------")
            print("Generation: #" + str(generation))
            print("Distance moyenne: " + str(fitness_average))
            print('Distance: ' + str(meilleur_chemin[1]))
            print("Chromosome avec meilleur distance: " + str(fittest))
            print("Distance: " + str(fittest_value))
            print("-----------------------------")


        if ecran is not None:
            drawChromosome(ecran, meilleur_chemin[0], nodes_pos, meilleur_chemin[1])

        if (time.time() - start) >= global_MeilleurChemin.maxtime and (global_MeilleurChemin.maxtime > 0):
            if verbose:
                print("Temps fini !")
            break

        generation += 1

    ville_meilleur_chemin = []
    for villeNb in meilleur_chemin[0]:
        ville_meilleur_chemin.append('v' + str(villeNb - 1))

    ville_name = str(ville_meilleur_chemin).replace("v", "ville ")
    print('\nMeilleur chemin: ' + ville_name)
    print('Meilleur Distance: ' + str(round(meilleur_chemin[1],2)))
    print('Nbr generation: ' + str(generation))

    if ecran is not None :
        font = pygame.font.Font(None,30)
        temps = round(time.time() - start, 2);
        text = font.render(("Solution optimale aprés "+str(temps) + " sec"), True, [255,255,255])
        ecran.blit(text, (160, 40))

        pygame.display.flip()

        while True:
            event = pygame.event.wait()
            if event.type == KEYDOWN: break

    return meilleur_chemin[1], ville_meilleur_chemin



if __name__ == "__main__":

    gui = True
    fileName = None
    maxtime = 0

    for iArg in range(1,len(sys.argv)):

        if sys.argv[iArg] == "--nogui":
            gui = False
        elif sys.argv[iArg] == "--maxtime":
            maxtime = int(sys.argv[iArg + 1])
        else:
            if sys.argv[iArg -1] != "--maxtime":
                fileName = str(sys.argv[iArg])


    print("GUI : ", gui)
    print("file : ", fileName)
    print("maxtime : ", maxtime)

    ga_solve(fileName, gui, maxtime)
