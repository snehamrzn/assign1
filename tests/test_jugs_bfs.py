"""Tests for Question 2: the three-jug problem and breadth-first search.

assert means "this must be true". If it is false, pytest stops that test and marks it failed.
"""

from jugs_bfs import Node, Problem, breadth_first_search, reachable_states


def replay(problem, actions):
    """Start from the initial jugs and do each action in order.

    An action is legal when problem.actions(state) lists it for the current filling.
    """
    state = problem.initial
    for action in actions:
        legal_actions = problem.actions(state)
        assert action in legal_actions, f"{action} is not allowed when the jugs are {state}"
        state = problem.result(state, action)
    return state


def test_bfs_finds_a_goal():
    # Step 1. Search the normal 12, 8, and 3 gallon problem.
    problem = Problem()
    goal = breadth_first_search(problem)

    # Step 2. The search must return a solution.
    assert goal is not None

    # Step 3. The final filling must pass the goal test.
    assert problem.goal_test(goal.state)

    # Step 4. One of the three jugs must hold exactly 1 gallon.
    assert 1 in goal.state


def test_solution_path_is_valid():
    # Step 1. Search, then read the path from the empty jugs to the goal.
    problem = Problem()
    goal = breadth_first_search(problem)
    path = goal.path()

    # Step 2. The first filling must be all jugs empty.
    assert path[0].state == (0, 0, 0)

    # Step 3. Each later filling must come from a legal action on the one before it.
    for i in range(len(path) - 1):
        parent = path[i]
        child = path[i + 1]
        assert child.action in problem.actions(parent.state)
        assert problem.result(parent.state, child.action) == child.state

    # Step 4. Doing those actions again from the start must reach the same goal.
    final = replay(problem, goal.solution())
    assert final == goal.state

    # Step 5. That final filling must contain 1 gallon.
    assert 1 in final


def test_bfs_solution_is_shortest():
    # Step 1. Search. Every action costs 1, so the first goal found is a shortest plan.
    goal = breadth_first_search(Problem())

    # Step 2. The shortest plan is 3 actions: fill 12, pour into 8, pour into 3.
    assert len(goal.solution()) == 3

    # Step 3. The path cost must equal that number of actions.
    assert goal.path_cost == 3


def test_transition_model():
    problem = Problem()

    # Fill the 12-gallon jug from empty. It becomes 12. The others stay 0.
    assert problem.result((0, 0, 0), ("Fill", 0)) == (12, 0, 0)

    # Pour the 12 into the 8. The 8 fills up, so 4 gallons stay in the 12.
    assert problem.result((12, 0, 0), ("Pour", 0, 1)) == (4, 8, 0)

    # Pour 5 gallons from the 8 into the empty 12. The 8 runs dry.
    assert problem.result((0, 5, 0), ("Pour", 1, 0)) == (5, 0, 0)

    # Empty the 8-gallon jug. It becomes 0. The others stay as they were.
    assert problem.result((4, 8, 3), ("Empty", 1)) == (4, 0, 3)


def test_actions_never_exceed_capacity():
    problem = Problem()

    # For every reachable filling, try every legal action.
    for state in reachable_states(problem):
        for action in problem.actions(state):
            next_state = problem.result(state, action)

            # Each jug must stay between 0 and its size.
            for i in range(len(next_state)):
                gallons = next_state[i]
                capacity = problem.capacities[i]
                assert 0 <= gallons <= capacity

            # The total water can rise only when the action fills from the faucet.
            water_increased = sum(next_state) > sum(state)
            if water_increased:
                assert action[0] == "Fill"


def test_state_space_is_finite():
    # There are at most 13 x 9 x 4 = 468 fillings that fit in the three jugs.
    reachable = len(reachable_states(Problem()))
    assert reachable <= 13 * 9 * 4


def test_goal_at_start_returns_root():
    # Step 1. Start with the 12-gallon jug already holding 1 gallon.
    problem = Problem(initial=(1, 0, 0))
    goal = breadth_first_search(problem)

    # Step 2. The search is already done, so it returns that filling and no actions.
    assert goal.state == (1, 0, 0)
    assert goal.solution() == []


def test_failure_when_goal_unreachable():
    # Jugs of 4 and 2 gallons can only hold even amounts, so 1 gallon is impossible.
    goal = breadth_first_search(Problem(capacities=(4, 2)))

    # The search must stop and report that there is no solution.
    assert goal is None


def test_node_path_and_solution():
    # Step 1. Start at empty jugs and fill the 3-gallon jug.
    root = Node((0, 0, 0))
    problem = Problem()
    child = root.child_node(problem, ("Fill", 2))

    # Step 2. The new filling is (0, 0, 3), and it points back to the start.
    assert child.state == (0, 0, 3)
    assert child.parent is root

    # Step 3. The action list is that one fill.
    assert child.solution() == [("Fill", 2)]

    # Step 4. The path from the start is empty, then the filled 3-gallon jug.
    assert [node.state for node in child.path()] == [(0, 0, 0), (0, 0, 3)]
