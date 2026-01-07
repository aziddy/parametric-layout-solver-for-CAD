# SOLVER STEP BY STEP QUESTION: Trace 3 Iterations (with Differential Evolution Steps)

**Problem Statement:**
You are given a Parametric Layout Solver that uses **Differential Evolution (DE)** to pack rectangles into a circle.
The objective is to minimizing the Radius $R$.

**Input:**

- **Shape A**: $10 \times 10$ Square.
- **Shape B**: $10 \times 10$ Square.
- **Constraints**: No Rotation (`FIXED_0`). Padding = 0.
- **Strategy**: `best1bin` (Best + 1 Difference Vector).
- **Parameters**: Mutation Factor $F = 0.5$, Crossover $CR = 0.9$.

**The State Vector $\mathbf{x}$**:
$$ \mathbf{x} = [R, x_A, y_A, x_B, y_B] $$

---

## 1. Initialization (Generation G=0)

The solver initializes a population of 4 vectors randomly within bounds $[-20, 20]$.

**Population Table (G=0):**

| ID    | Vector $\mathbf{x} = [R, x_A, y_A, x_B, y_B]$ | Status      | Penalty              | Cost     |
| :---- | :-------------------------------------------- | :---------- | :------------------- | :------- |
| **0** | $[10.0, 0, 0, 0, 0]$                          | **Overlap** | Identical positions. | **Huge** |
| **1** | $[20.0, -15, 0, 15, 0]$                       | **Valid**   | OK.                  | **20.0** |
| **2** | $[15.0, -5, 5, 5, -5]$                        | **Valid**   | OK. Best So Far.     | **15.0** |
| **3** | $[5.0, 10, 10, -10, -10]$                     | **Out**     | Out of bounds.       | **Huge** |

_Current Best ($\mathbf{x}_{best}$): ID #2 ($Cost=15.0$).\_

---

## 2. Iteration 1: Target ID #0 (The Bad Candidate)

We attempt to improve **Vector #0** (which is currently terrible).
Since we use `best1bin`, we mutate around the **Best Vector ($\mathbf{x}_2$)**.

**Step A: Mutation**
We select two random distinct vectors from the remainder of the population: $r1=1, r2=3$.
Formula: $\mathbf{v} = \mathbf{x}_{best} + F \cdot (\mathbf{x}_{r1} - \mathbf{x}_{r2})$

$$
\begin{aligned}
\mathbf{x}_{best} (\text{ID } 2) &= [15.0, -5, 5, 5, -5] \\
\mathbf{x}_{r1} (\text{ID } 1) &= [20.0, -15, 0, 15, 0] \\
\mathbf{x}_{r2} (\text{ID } 3) &= [5.0, 10, 10, -10, -10] \\
\text{Diff} &= [15.0, -25, -10, 25, 10] \\
F \cdot \text{Diff} (F=0.5) &= [7.5, -12.5, -5, 12.5, 5]
\end{aligned}
$$

**Mutant Vector $\mathbf{v}$**:
$$ \mathbf{v} = [15, -5, 5, 5, -5] + [7.5, -12.5, -5, 12.5, 5] = [22.5, -17.5, 0, 17.5, 0] $$

**Step B: Crossover**
We mix $\mathbf{v}$ with the target $\mathbf{x}_0$ based on $CR=0.9$. Most parameters are taken from $\mathbf{v}$.
Let's assume the **Trial Vector $\mathbf{u}$** takes all values from $\mathbf{v}$ for simplicity.
$$ \mathbf{u} = [22.5, -17.5, 0, 17.5, 0] $$

**Step C: Selection**

1.  **Evaluate $\mathbf{u}$**:
    - Shapes at $(-17.5, 0)$ and $(17.5, 0)$. Distance = $17.5 + 5 (\text{half-width}) = 22.5$.
    - Radius $R=22.5$. Fits exactly.
    - **Status**: Valid. **Cost**: $22.5$.
2.  **Compare**:
    - $\text{Cost}(\mathbf{u}) = 22.5$.
    - $\text{Cost}(\mathbf{x}_0) = \text{Huge}$.
3.  **Decision**: **ACCEPT**.
    - Vector #0 is replaced by $\mathbf{u}$.

_Result_: We replaced a broken solution with a valid (but large) solution.

---

## 3. Iteration 2: Target ID #2 (The Leader)

We attempt to improve the leader **Vector #2** itself.
We select random vectors $r1=0$ (newly updated), $r2=1$.

**Step A: Mutation**
$$ \mathbf{v} = \mathbf{x}_{best} + F \cdot (\mathbf{x}_{0} - \mathbf{x}\_{1}) $$

$$
\begin{aligned}
\mathbf{x}_{best} (\text{ID } 2) &= [15.0, -5, 5, 5, -5] \\
\mathbf{x}_{0} (\text{New}) &= [22.5, -17.5, 0, 17.5, 0] \\
\mathbf{x}_{1} &= [20.0, -15, 0, 15, 0] \\
\text{Diff} &= [2.5, -2.5, 0, 2.5, 0] \\
F \cdot \text{Diff} &= [1.25, -1.25, 0, 1.25, 0]
\end{aligned}
$$

**Mutant Vector $\mathbf{v}$**:
$$ \mathbf{v} = [16.25, -6.25, 5, 6.25, -5] $$
*Notice how $R$ increased to 16.25. This move seems slightly "safer".\*

**Step B: Evaluate**

- **Cost**: $16.25$.

**Step C: Selection**

- $\text{Cost}(\mathbf{v}) = 16.25$.
- $\text{Cost}(\mathbf{x}_2) = 15.0$.
- **Decision**: **REJECT**.
- We keep the tighter radius of $15.0$. The mutation tried to expand the circle, which is worse for minimization.

---

## 4. Iteration 3: Target ID #1

Target $\mathbf{x}_1 = [20.0, ...]$. We want to beat $20.0$.
Assume mutation produces an aggressive vector:
**Trial Vector $\mathbf{u} = [14.0, -4, 4, 4, -4]$**.

**Step A: Evaluate**

1.  **Overlap**:
    - Shape A: $[-9, 1] \times [-1, 9]$ (approx).
    - Shape B: $[-1, 9] \times [-9, 1]$ (approx).
    - It looks tight. Let's say checks pass.
2.  **Containment**:
    - Corner of A at approx $(-4-5, 4+5) = (-9, 9)$. Dist $\approx \sqrt{81+81} \approx 12.7$.
    - $R=14.0$. $12.7 \le 14.0$. Valid.
3.  **Cost**: $14.0$.

**Step B: Selection**

- $\text{Cost}(\mathbf{u}) = 14.0$.
- $\text{Cost}(\mathbf{x}_1) = 20.0$.
- **Decision**: **ACCEPT**.

**New Global Best**: $\mathbf{x}_1$ with Cost $14.0$ (beats old best of 15.0).

---

## 5. Summary

| Iteration | Target     | Action | Result                       | Note                       |
| :-------- | :--------- | :----- | :--------------------------- | :------------------------- |
| **1**     | #0 (Trash) | Accept | replaced with valid $R=22.5$ | Fixed broken solution.     |
| **2**     | #2 (Best)  | Reject | kept $R=15.0$                | Trial $R=16.25$ was worse. |
| **3**     | #1 (Avg)   | Accept | replaced with valid $R=14.0$ | **New Record!**            |
