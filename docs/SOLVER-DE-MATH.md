# Solver Mechanics: The Math of Differential Evolution

This document explains the variables ($U, V, X, F$) and equations used by the solver to move from one iteration to the next.

## 1. The Variables (The Actors)

| Symbol              | Name                       | Description                                                        | Role                                                               |
| :------------------ | :------------------------- | :----------------------------------------------------------------- | :----------------------------------------------------------------- |
| $\mathbf{x}_{i, G}$ | **Target Vector** (Parent) | The definition of a specific layout at Generation $G$ (index $i$). | The "current state" we are trying to improve.                      |
| $\mathbf{v}_{i, G}$ | **Mutant Vector**          | A noisy vector created by mixing other population members.         | An intermediate mathematical construct (not a valid solution yet). |
| $\mathbf{u}_{i, G}$ | **Trial Vector** (Child)   | The final proposed candidate for the next generation.              | The "challenger" that tries to replace the Target Vector.          |
| $\mathbf{x}_{best}$ | **Best Vector**            | The vector with the lowest cost in the **current** population.     | The anchor point for mutation (in `best1bin` strategy).            |
| $F$                 | **Mutation Factor**        | A constant (usually $0.5 - 1.0$).                                  | Controls the "step size" or "aggression" of the mutation.          |
| $CR$                | **Crossover Rate**         | A probability (usually $0.7 - 0.9$).                               | Controls how much of the Mutant is inherited vs. the Parent.       |

---

## 2. The Flow: How we move from G to G+1

For **every** individual $\mathbf{x}_i$ in the population, we execute these 3 steps to decide if it evolves or stays the same.

### Step 1: Mutation (Creating $V$)

We create a **Mutant Vector** $\mathbf{v}_i$ by adding a "difference" to the best known solution. This is how the solver "explores" directions that have worked for others.

**Equation (`best1bin` strategy):**
$$ \mathbf{v}_i = \mathbf{x}_{best} + F \cdot (\mathbf{x}_{r1} - \mathbf{x}_{r2}) $$

- $\mathbf{x}_{best}$: The best layout found so far (the "attractor").
- $F$: Scaling factor (e.g., 0.5).
- $(\mathbf{x}_{r1} - \mathbf{x}_{r2})$: The **Difference Vector** between two random layouts. This represents a random "direction" and "magnitude" found within the population.

> **Analogy**: "Take the best spot we know, and assume the solution lies in a direction similar to the distance between two random friends."

### Step 2: Crossover (Creating $U$)

We create the **Trial Vector** $\mathbf{u}_i$ by mixing parameters (genes) from the Mutant $\mathbf{v}_i$ and the old Target $\mathbf{x}_i$. This ensures we don't lose all existing information.

For each parameter $j$ (e.g., $R, x_1, y_1...$):

$$
u_{j,i} =
\begin{cases}
v_{j,i} & \text{if } \text{rand}(0,1) \le CR \text{ or } j = j_{rand} \\
x_{j,i} & \text{otherwise}
\end{cases}
$$

- **$CR$ (Crossover Rate)**: High $CR$ means we take mostly from the Mutant (aggressive). Low $CR$ means we keep mostly the Parent (conservative).
- **Result**: $\mathbf{u}_i$ is a hybrid of the old self and the new mutation.

### Step 3: Selection (Survival of the Fittest)

We compare the "Cost" (Objective Function Value) of the **Trial Child ($\mathbf{u}$)** against the **Target Parent ($\mathbf{x}$)**.

$$
\mathbf{x}_{i, G+1} =
\begin{cases}
\mathbf{u}_{i, G} & \text{if } f(\mathbf{u}_{i, G}) \le f(\mathbf{x}_{i, G}) \\
\mathbf{x}_{i, G} & \text{otherwise}
\end{cases}
$$

- **If Child is Better (Lower Cost)**: The Child replaces the Parent in the next generation.
- **If Child is Worse**: The Parent survives. The Child is discarded.

---

## 3. Summary Diagram

$$
\text{Population} \xrightarrow{\text{Pick } r1, r2} (\mathbf{x}_{r1}, \mathbf{x}_{r2})
$$

$$
\downarrow
$$

$$
\mathbf{v} = \mathbf{x}_{best} + F(\mathbf{x}_{r1} - \mathbf{x}_{r2}) \quad \text{(Mutation)}
$$

$$
\downarrow
$$

$$
\mathbf{u} = \text{Mix}(\mathbf{x}_{target}, \mathbf{v}) \quad \text{(Crossover)}
$$

$$
\downarrow
$$

$$
\text{Is } Cost(\mathbf{u}) \le Cost(\mathbf{x})? \quad \text{(Selection)}
$$

$$
\swarrow \qquad \searrow
$$

$$
\text{Yes: Keep } \mathbf{u} \qquad \text{No: Keep } \mathbf{x}
$$
