from collections import defaultdict


class Graph:
    def __init__(self):
        self.graph = defaultdict(list)

    def add_edge(self, u, v):
        self.graph[u].append(v)
        if v not in self.graph:
            self.graph[v] = []

    def cycler(self, v, visited, stack):

        visited[v] = True
        stack[v] = True

        for neighbour in self.graph[v]:
            if not visited[neighbour]:
                cycle = self.cycler(neighbour, visited, stack)
                if cycle:
                    return cycle
            elif stack[neighbour]:
                return v, neighbour

        stack[v] = False
        return None

    def get_cycles(self):
        cycles = []
        cycle = True
        while cycle:
            visited = {k: False for k in self.graph}
            stack = {k: False for k in self.graph}
            for node in self.graph.keys():
                if not visited[node]:
                    cycle = self.cycler(node, visited, stack)
                    if cycle:
                        cycles.append(cycle)
                        self.graph[cycle[0]].remove(cycle[1])
                        break

        return cycles

    def topological_sort(self):

        in_degree = {k: 0 for k in self.graph}

        for i in self.graph:
            for j in self.graph[i]:
                in_degree[j] += 1

        queue = []
        for i in self.graph.keys():
            if in_degree[i] == 0:
                queue.append(i)

        ordered = []
        while queue:
            u = queue.pop(0)
            ordered.append(u)

            for i in self.graph[u]:
                in_degree[i] -= 1

                if in_degree[i] == 0:
                    queue.append(i)

        return ordered


class HasCircularReferencesError(Exception):
    def __init__(self, found_refs):
        self.message = f'Circular references found: {found_refs}.\n Please fix them before ' \
            f'attempting to get deletion order.'

    def __str__(self):
        return self.message


class FkProfiler:

    def __init__(self, db):
        self.tables = db.metadata.tables
        self.graph = self.make_fk_graph()
        self.circular_references = self.find_circular_references()

    def make_fk_graph(self):
        graph = Graph()
        for name, table in self.tables.items():
            for constraint in table.constraints:
                if constraint.__visit_name__ == 'foreign_key_constraint':
                    for fk in constraint.elements:
                        if constraint.ondelete is None or constraint.ondelete == 'RESTRICT':
                            graph.add_edge(name, fk.constraint.referred_table.fullname)
        return graph

    def find_circular_references(self):
        return self.graph.get_cycles()

    def get_deletion_order(self):
        if len(self.circular_references) > 0:
            raise HasCircularReferencesError(self.circular_references)
        else:
            return self.graph.topological_sort()
