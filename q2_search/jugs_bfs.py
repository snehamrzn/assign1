"""
Question 2: the three-jug problem, solved with breadth-first search.

Jugs hold 12, 8 and 3 gallons. There is a faucet. Goal: any jug holds
exactly 1 gallon.

Problem is the jug problem: initial state, actions, results, goal test
and action cost. Node is one node in the search tree.
breadth_first_search follows AIMA Figure 3.9.
"""

from collections import deque
from typing import List, Optional, Tuple

State = Tuple[int, ...]   # gallons in each jug, e.g. (12, 0, 0)
Action = Tuple            # ("Fill", i) | ("Empty", i) | ("Pour", i, j)


class Problem:
    """The 12/8/3 gallon jug problem.

    State:      a tuple (a, b, c). a, b, c are the gallons in each jug.
                0 <= a <= 12, 0 <= b <= 8, 0 <= c <= 3.
    Initial:    (0, 0, 0). All jugs are empty.
    Goal test:  any jug holds exactly `target` gallons (target = 1).
    Actions:    ("Fill", i)    fill jug i from the faucet.
                ("Empty", i)   empty jug i onto the ground.
                ("Pour", i, j) pour jug i into jug j until i is empty
                               or j is full.
    Cost:       1 per action.
    """

    def __init__(self, capacities=(12, 8, 3), initial=None, target=1):
        self.capacities = tuple(capacities)
        if initial is None:
            initial = tuple(0 for _ in self.capacities)
        self.initial = tuple(initial)
        self.target = target

    def path_cost(self, cost_so_far):
        """Every action costs 1, so the path cost is the number of actions."""
        return cost_so_far + 1

    def actions(self, state: State) -> List[Action]:
        """Only actions that change the state are listed.
        (Filling a full jug or emptying an empty jug does nothing.)"""
        acts = []
        n = len(state)
        for i in range(n):
            if state[i] < self.capacities[i]:
                acts.append(("Fill", i))
            if state[i] > 0:
                acts.append(("Empty", i))
        for i in range(n):
            for j in range(n):
                if i != j and state[i] > 0 and state[j] < self.capacities[j]:
                    acts.append(("Pour", i, j))
        return acts

    def result(self, state: State, action: Action) -> State:
        """Transition model RESULT(s, a)."""
        s = list(state)
        kind = action[0]
        if kind == "Fill":
            i = action[1]
            s[i] = self.capacities[i]
        elif kind == "Empty":
            i = action[1]
            s[i] = 0
        elif kind == "Pour":
            i, j = action[1], action[2]
            amount = min(s[i], self.capacities[j] - s[j])  # until i empty or j full
            s[i] -= amount
            s[j] += amount
        else:
            raise ValueError(f"Unknown action: {action}")
        return tuple(s)

    def goal_test(self, state: State) -> bool:
        """Any jug holds exactly target gallons."""
        return self.target in state


class Node:

    def __init__(self, state, parent=None, action=None, path_cost=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.path_cost = path_cost

    def __repr__(self):
        return f"<Node {self.state}>"

    def child_node(self, problem: Problem, action) -> "Node":
        """CHILD-NODE(problem, parent, action)."""
        next_state = problem.result(self.state, action)
        return Node(next_state, self, action, problem.path_cost(self.path_cost))

    def expand(self, problem: Problem) -> List["Node"]:
        """EXPAND(problem, node): all child nodes of this node."""
        return [self.child_node(problem, a) for a in problem.actions(self.state)]

    def solution(self) -> List[Action]:
        """SOLUTION(node): the actions from the root to this node."""
        return [node.action for node in self.path()[1:]]

    def path(self) -> List["Node"]:
        """The nodes from the root to this node (follow parent links back)."""
        nodes = []
        node = self
        while node is not None:      # stop when we pass the start node
            nodes.append(node)       # save this node
            node = node.parent       # move one step toward the start
        nodes.reverse()              # start node first, this node last
        return nodes


def breadth_first_search(problem: Problem) -> Optional[Node]:
    """ Returns the goal node, or None if no solution exists.

    The goal is tested when a child is generated, before it is expanded.
    reached holds states on the frontier and states already expanded, which
    is the same check as "not in explored or frontier" in the 3rd edition.
    """
    node = Node(problem.initial)
    if problem.goal_test(node.state):
        return node
    frontier = deque([node])
    reached = {problem.initial}
    while frontier:
        node = frontier.popleft()
        for child in node.expand(problem):
            s = child.state
            if problem.goal_test(s):
                return child
            if s not in reached:
                reached.add(s)
                frontier.append(child)
    return None


def describe(action: Action, capacities=(12, 8, 3)) -> str:
    """Readable text for one action."""
    names = [f"{c}-gal" for c in capacities]
    if action[0] == "Fill":
        return f"Fill the {names[action[1]]} jug from the faucet"
    if action[0] == "Empty":
        return f"Empty the {names[action[1]]} jug onto the ground"
    return f"Pour the {names[action[1]]} jug into the {names[action[2]]} jug"


def reachable_states(problem: Problem) -> set:
    """All states reachable from the initial state (used for the analysis)."""
    seen = {problem.initial}
    frontier = deque([problem.initial])
    while frontier:
        s = frontier.popleft()
        for a in problem.actions(s):
            t = problem.result(s, a)
            if t not in seen:
                seen.add(t)
                frontier.append(t)
    return seen
