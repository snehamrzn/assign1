"""
Command line entry point for Question 2.

    python q2_search/main.py                 # 12/8/3 jugs, target 1 gallon
    python q2_search/main.py --target 4      # try another target
"""

import argparse

from jugs_bfs import Problem, breadth_first_search, describe, reachable_states


def main():
    # Dealing with arguments and initial problem definition
    p = argparse.ArgumentParser(description="Three-jug problem solved with BFS.")
    p.add_argument("--capacities", type=int, nargs="+", default=[12, 8, 3])
    p.add_argument("--target", type=int, default=1)
    args = p.parse_args()

    # Defining the problem and solving it
    problem = Problem(capacities=args.capacities, target=args.target)
    goal = breadth_first_search(problem)

    print(f"Jugs: {problem.capacities}  start: {problem.initial}  goal: a jug holds {args.target}")
    print(f"Reachable states: {len(reachable_states(problem))}")
    if goal is None:
        print("failure: no solution")
        return
    print(f"Solution found with {len(goal.solution())} actions:\n")
    for step, node in enumerate(goal.path()):
        if node.parent is None:
            print(f"  {step}. {'Start':44}-> {node.state}")
        else:
            print(f"  {step}. {describe(node.action, problem.capacities):44}-> {node.state}")
    print(f"\nSolution (actions): {goal.solution()}")


if __name__ == "__main__":
    main()
