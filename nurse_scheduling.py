import tkinter as tk
import matplotlib.pyplot as plt
from ortools.sat.python import cp_model
import random


def generate_shift_requests(
    num_nurses, num_days, num_shifts, requests_per_nurse_per_week
):
    shift_requests = []

    for _ in range(num_nurses):
        nurse_requests = [
            [0 for _ in range(num_shifts)] for _ in range(num_days)
        ]

        weeks = num_days // 7

        for week in range(weeks):
            request_count = 0

            while request_count < requests_per_nurse_per_week:
                day = random.randint(
                    week * 7,
                    min((week + 1) * 7 - 1, num_days - 1)
                )
                shift = random.randint(0, num_shifts - 1)

                if nurse_requests[day][shift] == 0:
                    if (
                        (shift == 0 or nurse_requests[day][shift - 1] == 0)
                        and
                        (
                            shift == num_shifts - 1
                            or nurse_requests[day][shift + 1] == 0
                        )
                    ):
                        nurse_requests[day][shift] = 1
                        request_count += 1

        shift_requests.append(nurse_requests)

    return shift_requests


def print_shift_requests(shift_requests):
    print("Shift Requests by Nurses:")

    for i, nurse_requests in enumerate(shift_requests):
        print(f"Nurse {i} shift requests:")

        for day_requests in nurse_requests:
            print(day_requests)

        print()


def solve_nurse_scheduling(
    num_nurses,
    num_shifts,
    num_days,
    requests_per_nurse_per_week,
    min_nurses_per_shift,
    max_nurses_per_shift,
):
    shift_requests = generate_shift_requests(
        num_nurses,
        num_days,
        num_shifts,
        requests_per_nurse_per_week,
    )

    model = cp_model.CpModel()

    # Create shift variables
    shifts = {}

    for n in range(num_nurses):
        for d in range(num_days):
            for s in range(num_shifts):
                shifts[(n, d, s)] = model.NewBoolVar(
                    f"shift_n{n}d{d}s{s}"
                )

    # Minimum and maximum nurses per shift
    for d in range(num_days):
        for s in range(num_shifts):
            nurses_working = [
                shifts[(n, d, s)] for n in range(num_nurses)
            ]

            model.Add(
                sum(nurses_working) >= min_nurses_per_shift
            )
            model.Add(
                sum(nurses_working) <= max_nurses_per_shift
            )

    # Prevent consecutive shifts
    for n in range(num_nurses):
        for d in range(num_days):
            for s in range(num_shifts - 1):
                model.Add(
                    shifts[(n, d, s)] + shifts[(n, d, s + 1)] <= 1
                )

    # Maximum one shift per day per nurse
    for n in range(num_nurses):
        for d in range(num_days):
            model.Add(
                sum(
                    shifts[(n, d, s)]
                    for s in range(num_shifts)
                ) <= 1
            )

    # Maximize the number of granted shift requests
    model.Maximize(
        sum(
            shift_requests[n][d][s] * shifts[(n, d, s)]
            for n in range(num_nurses)
            for d in range(num_days)
            for s in range(num_shifts)
        )
    )

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule = [
            [
                [0 for _ in range(num_nurses)]
                for _ in range(num_shifts)
            ]
            for _ in range(num_days)
        ]

        for d in range(num_days):
            for s in range(num_shifts):
                for n in range(num_nurses):
                    if solver.Value(shifts[(n, d, s)]) == 1:
                        schedule[d][s][n] = 1

        return schedule, shift_requests, solver

    return None, shift_requests, solver


def print_solution(
    schedule,
    shift_requests,
    num_nurses,
    num_shifts,
    num_days,
):
    print("\nDetailed Schedule:")

    for d in range(num_days):
        print(f"\nDay {d + 1}")

        for s in range(num_shifts):
            nurses_working = []

            for n in range(num_nurses):
                if schedule[d][s][n] == 1:
                    request_status = (
                        "(requested)"
                        if shift_requests[n][d][s] == 1
                        else "(not requested)"
                    )

                    nurses_working.append(
                        f"Nurse {n} {request_status}"
                    )

            if nurses_working:
                print(
                    f"  Shift {s + 1}: "
                    f"{', '.join(nurses_working)}"
                )
            else:
                print(
                    f"  Shift {s + 1}: No nurses scheduled"
                )


def plot_schedule(
    schedule,
    num_nurses,
    num_shifts,
    num_days,
):
    fig, axs = plt.subplots(
        1,
        num_days,
        figsize=(15, 6),
        sharey=True,
    )

    if num_days == 1:
        axs = [axs]

    nurse_colors = plt.cm.rainbow(
        [i / num_nurses for i in range(num_nurses)]
    )

    for d, ax in enumerate(axs):
        ax.set_title(f"Day {d + 1}")

        for s in range(num_shifts):
            nurses_in_shift = [
                n
                for n in range(num_nurses)
                if schedule[d][s][n] == 1
            ]

            for i, nurse in enumerate(nurses_in_shift):
                rect = plt.Rectangle(
                    (0, s + 0.1 * i),
                    1,
                    0.1,
                    color=nurse_colors[nurse],
                    edgecolor="black",
                )

                ax.add_patch(rect)

                ax.text(
                    0.5,
                    s + 0.1 * i + 0.05,
                    f"N{nurse}",
                    va="center",
                    ha="center",
                    fontsize=8,
                )

        ax.set_xticks([0.5])
        ax.set_xticklabels([""])

        ax.set_yticks(
            [i + 0.5 for i in range(num_shifts)]
        )

        ax.set_yticklabels(
            [f"Shift {i + 1}" for i in range(num_shifts)]
        )

        ax.set_xlim(0, 1)
        ax.set_ylim(0, num_shifts)

    plt.tight_layout()
    plt.show()


def plot_requests_summary(
    shift_requests,
    schedule,
    num_nurses,
    num_days,
    num_shifts,
):
    met_requests = [0] * num_nurses
    unmet_requests = [0] * num_nurses

    for n in range(num_nurses):
        for d in range(num_days):
            for s in range(num_shifts):
                if shift_requests[n][d][s] == 1:
                    if schedule[d][s][n] == 1:
                        met_requests[n] += 1
                    else:
                        unmet_requests[n] += 1

    fig, ax = plt.subplots(figsize=(12, 6))

    bar_width = 0.35
    index = range(num_nurses)

    ax.bar(
        index,
        met_requests,
        bar_width,
        label="Met Requests",
        color="green",
        alpha=0.7,
    )

    ax.bar(
        index,
        unmet_requests,
        bar_width,
        bottom=met_requests,
        label="Unmet Requests",
        color="red",
        alpha=0.7,
    )

    ax.set_xlabel("Nurse ID", fontsize=12, labelpad=10)
    ax.set_ylabel(
        "Number of Requests",
        fontsize=12,
        labelpad=10,
    )

    ax.set_title(
        "Summary of Met vs Unmet Shift Requests by Nurse",
        fontsize=14,
        pad=20,
    )

    ax.set_xticks(index)
    ax.set_xticklabels(
        [str(i) for i in range(num_nurses)]
    )

    plt.xticks(rotation=0)

    ax.grid(
        True,
        axis="y",
        linestyle="--",
        alpha=0.7,
    )

    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1, 1),
    )

    plt.tight_layout()
    plt.show()


def analyze_nurse_availability(
    schedule,
    num_shifts,
    num_days,
    max_nurses_per_shift,
    num_nurses,
    requests_per_nurse,
):
    print("\nNurse Availability Analysis:")

    # Analyze shift coverage
    for d in range(num_days):
        for s in range(num_shifts):
            nurses_scheduled = sum(schedule[d][s])

            print(
                f"Day {d + 1}, Shift {s + 1}: "
                f"{nurses_scheduled} nurses scheduled"
            )

    # Analyze individual nurse workload
    nurse_shifts = [
        sum(
            schedule[d][s][n]
            for d in range(num_days)
            for s in range(num_shifts)
        )
        for n in range(num_nurses)
    ]

    print("\nNurse Workload Summary:")

    for n in range(num_nurses):
        print(
            f"Nurse {n}: {nurse_shifts[n]} shifts assigned"
        )

    print(
        f"\nAverage shifts per nurse: "
        f"{sum(nurse_shifts) / num_nurses:.2f}"
    )

    print(
        f"Maximum shifts assigned to a nurse: "
        f"{max(nurse_shifts)}"
    )

    print(
        f"Minimum shifts assigned to a nurse: "
        f"{min(nurse_shifts)}"
    )


def get_user_input():
    def on_submit():
        try:
            inputs["num_nurses"] = int(
                num_nurses_entry.get()
            )

            inputs["num_shifts"] = int(
                num_shifts_entry.get()
            )

            inputs["num_days"] = int(
                num_days_entry.get()
            )

            inputs["requests_per_nurse"] = int(
                requests_per_nurse_entry.get()
            )

            inputs["min_nurses_per_shift"] = int(
                min_nurses_per_shift_entry.get()
            )

            inputs["max_nurses_per_shift"] = int(
                max_nurses_per_shift_entry.get()
            )

            if (
                inputs["min_nurses_per_shift"]
                > inputs["max_nurses_per_shift"]
            ):
                raise ValueError(
                    "Minimum nurses cannot be greater "
                    "than maximum nurses"
                )

            root.quit()

        except ValueError as e:
            error_label.config(text=str(e))

    root = tk.Tk()
    root.title("Nurse Scheduling Input")

    padx = 5
    pady = 5

    tk.Label(
        root,
        text="Total number of nurses:",
    ).grid(row=0, padx=padx, pady=pady)

    num_nurses_entry = tk.Entry(root)
    num_nurses_entry.grid(
        row=0,
        column=1,
        padx=padx,
        pady=pady,
    )

    tk.Label(
        root,
        text="Number of shifts per day:",
    ).grid(row=1, padx=padx, pady=pady)

    num_shifts_entry = tk.Entry(root)
    num_shifts_entry.grid(
        row=1,
        column=1,
        padx=padx,
        pady=pady,
    )

    tk.Label(
        root,
        text="Number of days for the roster:",
    ).grid(row=2, padx=padx, pady=pady)

    num_days_entry = tk.Entry(root)
    num_days_entry.grid(
        row=2,
        column=1,
        padx=padx,
        pady=pady,
    )

    tk.Label(
        root,
        text="Number of shift requests per nurse each week:",
    ).grid(row=3, padx=padx, pady=pady)

    requests_per_nurse_entry = tk.Entry(root)
    requests_per_nurse_entry.grid(
        row=3,
        column=1,
        padx=padx,
        pady=pady,
    )

    tk.Label(
        root,
        text="Minimum nurses needed per shift:",
    ).grid(row=4, padx=padx, pady=pady)

    min_nurses_per_shift_entry = tk.Entry(root)
    min_nurses_per_shift_entry.grid(
        row=4,
        column=1,
        padx=padx,
        pady=pady,
    )

    tk.Label(
        root,
        text="Maximum nurses allowed per shift:",
    ).grid(row=5, padx=padx, pady=pady)

    max_nurses_per_shift_entry = tk.Entry(root)
    max_nurses_per_shift_entry.grid(
        row=5,
        column=1,
        padx=padx,
        pady=pady,
    )

    error_label = tk.Label(
        root,
        text="",
        fg="red",
    )

    error_label.grid(
        row=6,
        columnspan=2,
        padx=padx,
        pady=pady,
    )

    submit_button = tk.Button(
        root,
        text="Submit",
        command=on_submit,
    )

    submit_button.grid(
        row=7,
        columnspan=2,
        padx=padx,
        pady=pady,
    )

    # Center the window
    root.update_idletasks()

    width = root.winfo_width()
    height = root.winfo_height()

    x = (
        root.winfo_screenwidth() // 2
        - width // 2
    )

    y = (
        root.winfo_screenheight() // 2
        - height // 2
    )

    root.geometry(
        f"{width}x{height}+{x}+{y}"
    )

    inputs = {}

    root.mainloop()
    root.destroy()

    if inputs:
        return (
            inputs["num_nurses"],
            inputs["num_shifts"],
            inputs["num_days"],
            inputs["requests_per_nurse"],
            inputs["min_nurses_per_shift"],
            inputs["max_nurses_per_shift"],
        )

    return None


def main():
    user_input = get_user_input()

    if user_input:
        (
            num_nurses,
            num_shifts,
            num_days,
            requests_per_nurse,
            min_nurses_per_shift,
            max_nurses_per_shift,
        ) = user_input

        shift_requests = generate_shift_requests(
            num_nurses,
            num_days,
            num_shifts,
            requests_per_nurse,
        )

        print_shift_requests(shift_requests)

        schedule, shift_requests, solver = solve_nurse_scheduling(
            num_nurses,
            num_shifts,
            num_days,
            requests_per_nurse,
            min_nurses_per_shift,
            max_nurses_per_shift,
        )

        if schedule is not None:
            print_solution(
                schedule,
                shift_requests,
                num_nurses,
                num_shifts,
                num_days,
            )

            plot_schedule(
                schedule,
                num_nurses,
                num_shifts,
                num_days,
            )

            plot_requests_summary(
                shift_requests,
                schedule,
                num_nurses,
                num_days,
                num_shifts,
            )

            analyze_nurse_availability(
                schedule,
                num_shifts,
                num_days,
                max_nurses_per_shift,
                num_nurses,
                requests_per_nurse,
            )

            print("\nSolution Statistics:")
            print(
                f"  - Shift requests met: "
                f"{solver.ObjectiveValue()}"
            )

            print(
                f"  - Conflicts: {solver.NumConflicts()}"
            )

            print(
                f"  - Branches: {solver.NumBranches()}"
            )

            print(
                f"  - Wall time: "
                f"{solver.WallTime()} seconds"
            )

        else:
            print(
                "\nNo feasible solution found. "
                "Try adjusting the constraints:"
            )

            print("- Increase the number of nurses")
            print("- Decrease the minimum nurses per shift")
            print("- Increase the maximum nurses per shift")
            print("- Reduce the number of shifts or days")
            print("- Reduce the number of requests per nurse")

    else:
        print("User input was cancelled or invalid.")


if __name__ == "__main__":
    main()
