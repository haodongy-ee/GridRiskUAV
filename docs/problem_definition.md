# Mathematical problem definition

## Data

Let the depot be node 0 and candidate inspection tasks be
\(V=\{1,\ldots,n\}\). Task \(i\) has inspection value \(v_i\ge 0\), risk
score \(r_i\ge 0\), and service time \(s_i\ge 0\). Travel time between nodes
is \(t_{ij}=d_{ij}/q\), where \(d_{ij}\) is Euclidean distance and \(q>0\) is
UAV speed. The sortie time budget is \(B\), and \(\lambda\ge 0\) controls the
importance of capturing grid risk.

Here, risk is a priority benefit: inspecting a high-risk asset captures more
risk. If later work introduces flight-path hazard, it should be represented by
a separate edge exposure term rather than overloading \(r_i\).

## Decision variables

- \(x_i\in\{0,1\}\): task \(i\) is inspected.
- \(y_{ij}\in\{0,1\}\): the route directly travels from node \(i\) to node \(j\).
- \(u_i\): visit-order variable used to eliminate subtours.

## Objective

The primary objective is

\[
\max \sum_{i\in V}(v_i+\lambda r_i)x_i.
\]

Reported metrics keep raw inspection value and captured risk separate so that
results remain interpretable for different values of \(\lambda\).

## Constraints

For every task \(i\in V\):

\[
\sum_{j\in V\cup\{0\},j\ne i}y_{ij}=x_i,\qquad
\sum_{j\in V\cup\{0\},j\ne i}y_{ji}=x_i.
\]

The depot has one departure and one return when at least one task is selected.
Standard MTZ order constraints eliminate disconnected subtours. The resource
constraint is

\[
\sum_{i\ne j}t_{ij}y_{ij}+\sum_{i\in V}s_ix_i\le B.
\]

Each task is visited at most once. A feasible route starts and ends at the
depot. The empty route is allowed and has zero cost.

## Evaluation metrics

- **task coverage**: \(\sum_i x_i/n\).
- **captured risk**: \(\sum_i r_i x_i\).
- **risk coverage**: captured risk divided by total scenario risk.
- **route cost**: travel time plus service time, including the final return.
- **runtime**: wall-clock planning time measured with a monotonic high-resolution clock.
- **objective**: captured inspection value plus \(\lambda\) times captured risk.

