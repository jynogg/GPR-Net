# Model pseudocode

This directory provides the high-level pseudocode of GPR-Net reported in the manuscript. The full model implementation will be released after paper acceptance.

## Algorithm 1: Forward propagation of GPR-Net for steady-state temperature prediction

**Input:** Thermal-conduction graph $\mathcal{G}=(\mathcal{V},\mathcal{E})$, node powers $\{p_i\}$, edge thermal conductances $\{g_{ij}\}$, and grid-index mapping.

**Output:** Refined chiplet-layer temperature field $\hat{Y}$.

### 1. Calculate the total chip power

```math
P_{\mathrm{tot}} = \sum_{i \in \mathcal{V}} p_i
```

### 2. Construct the node features

```math
x_i =
\begin{bmatrix}
p_i \\
P_{\mathrm{tot}}
\end{bmatrix},
\qquad i \in \mathcal{V}
```

### 3. Map the node and edge features into the hidden space

```math
h_i = W_n x_i,
\qquad
e_{ij} = W_e g_{ij}
```

### 4. Calculate the edge-aware attention score

```math
s_{uv}
=
\mathrm{LeakyReLU}
\left(
a_u^{\mathrm{T}} h_u
+
a_e^{\mathrm{T}} e_{uv}
+
a_v^{\mathrm{T}} h_v
\right)
```

### 5. Normalize the attention coefficients

```math
\alpha_{uv}
=
\frac{\exp(s_{uv})}
{\sum_{k \in \mathcal{N}(u)} \exp(s_{uk})},
\qquad
v \in \mathcal{N}(u)
```

### 6. Aggregate the neighboring features

```math
\tilde{h}_u
=
\sum_{v \in \mathcal{N}(u)}
\alpha_{uv} h_v
```

### 7. Apply the residual connection and normalization

```math
h_u^{\mathrm{attn}}
=
\mathrm{ReLU}
\left(
\mathrm{LayerNorm}
\left(
\tilde{h}_u + W_{\mathrm{res}} x_u
\right)
\right)
```

### 8. Construct the normalized binary adjacency matrix

```math
\tilde{A} = A + I,
\qquad
\hat{A}
=
\tilde{D}^{-\frac{1}{2}}
\tilde{A}
\tilde{D}^{-\frac{1}{2}},
\qquad
\tilde{D}_{uu}
=
\sum_v \tilde{A}_{uv}
```

### 9. Form the multi-head attention output

```math
H^{(0)}
=
\mathrm{Concat}
\left(
H^{\mathrm{attn},1},
H^{\mathrm{attn},2},
H^{\mathrm{attn},3},
H^{\mathrm{attn},4}
\right),
\qquad
L = 3
```

### 10. For $l=0,1,2$ do

### 11. Propagate the graph features

```math
H^{(l+1)}
=
\mathrm{ReLU}
\left(
\hat{A} H^{(l)} W^{(l)}
\right)
```

### 12. End for

### 13. Apply the linear output layer to obtain node-level temperatures

```math
\hat{T}^{\mathrm{graph}}_i
=
W_{\mathrm{out}}^{\mathrm{T}} h_i^{(L)}
+
b_{\mathrm{out}},
\qquad
i \in \mathcal{V}
```

### 14. Arrange graph predictions according to the grid indices

Arrange $\hat{T}^{\mathrm{graph}}$ according to the grid indices to obtain $\hat{T}^{\mathrm{grid}}$.

### 15. Construct the spatial power inputs

Construct $P^{\mathrm{grid}}$ and expand $P_{\mathrm{tot}}$ to obtain $P_{\mathrm{tot}}^{\mathrm{grid}}$.

### 16. Construct the spatial-layer input

```math
X
=
\mathrm{concat}
\left(
\hat{T}^{\mathrm{grid}},
P^{\mathrm{grid}},
P_{\mathrm{tot}}^{\mathrm{grid}}
\right)
\in
\mathbb{R}^{3 \times 64 \times 64}
```

### 17. Refine the temperature field using U-Net

```math
\hat{Y}
=
\mathrm{U\!-!Net}(X)
```

### 18. Return the refined temperature field

**Return** $\hat{Y}$.

---

The pseudocode mirrors the forward-propagation procedure described in the manuscript: edge-aware GAT aggregation, three GCN propagation layers, graph-to-grid reconstruction, and U-Net spatial refinement.
