# CSC111_Project2
\documentclass[fontsize=11pt]{article}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{amsthm}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.75in]{geometry}
\usepackage{algorithm}
\usepackage{algpseudocode}
\usepackage{url}
\allowdisplaybreaks

\title{CSC111 Project 2 Proposal: Origin to Destination Route Planning in a Road Network}
\author{Mingxiao Wei, Zheyuan Zhang}
\date{\today}

\begin{document}
\maketitle

\section*{Problem Description and Research Question}
\subsection*{Introduction}
Road transportation plays a prominent role in the present-day transportation system. Freight transported by trucks accounts for 62\% of the total tonnage of freight movement in the US in 2020 [1], and motor vehicles traveled 3.17 trillion vehicle miles on US roads in 2022 [2]. Due to the dominant role of road transportation, it arises as a significant objective for motor vehicle users to determine an optimal route to travel from a given origin to a given destination via a system of roads that minimizes travel costs, such as distance or time. A variety of algorithms for planning routes in a network of roads have been proposed and applied.

\subsection*{Road Networks as Weighted Graphs}
A weighted graph is a graph in which a number, namely weight, is associated with each edge to represent a quantity such as distance or cost [3]. Formally, a weighted graph can be defined as a tuple $G = (V, E, w)$, where $V$ is the set of all vertices, $E$ is the set of all edges, and $w: E \rightarrow \mathbb{R}$ is a function such that $\forall e \in E, w(e)$ is the weight of the edge $e$. Networks of roads in the real world can be naturally abstracted as weighted graphs, in which each vertex represents a junction between segments of roads, each edge represents a segment of road between 2 junctions, and the weight associated with an edge represents the length or cost of the road segment represented by the edge. Consequently, finding the optimal origin-to-destination route in a road network amounts to minimizing the total weight of a path in a weighted graph between two given vertices.

\subsection*{Related Work}
A classical algorithm for finding the shortest paths from a given vertex to every other vertex in a weighted graph was proposed by Dijkstra [4]. The pseudocode Algorithm 1 illustrates the general design of Dijkstra algorithm.
\begin{algorithm}
    \caption{Dijkstra algorithm}
    \begin{algorithmic}
    \Require $G = (V, E, w) \text{ is a weighted graph defined the same as previously described and } v \in V.$
        \Procedure {Dijkstra}{$G$, $v$}
            \State $V \gets G[0]$
            \State $E \gets G[1]$
            \State $w \gets G[2]$
            \State $dist \gets \{\}$
            \State $prev \gets \{\}$
            \State $dist[v] \gets 0$
            \State $prev[v] \gets \textbf{undefined}$
            \ForAll {$u \in V \backslash \{v\}$}
                \State $dist[u] \gets \infty$
                \State $prev[u] \gets \textbf{undefined}$
            \EndFor
            \State $S \gets \{u: u \in V\}$ \Comment{A set of unvisited vertices.}
            \While {$S \neq \emptyset$}
                \State $cur\_vertex \gets \arg\min_{\substack u \in S} dist[u]$
                \State $S \gets S \backslash \{cur\_vertex\}$
                \ForAll {$neighbour \in \{u \in S: \{u, cur\_vertex \in E\}\}$}
                    \If {$dist[cur\_vertex] + w(\{cur\_vertex, neighbour\}) < dist[neighbour]$}
                        \State $dist[neighbour] \gets dist[cur\_vertex] + w(\{cur\_vertex, neighbour\})$
                        \State $prev[neighbour] \gets cur\_vertex$
                    \EndIf
                \EndFor
            \EndWhile
            \State \Return {$dist, prev$}
        \EndProcedure
    \end{algorithmic}
\end{algorithm}
 The mapping $\texttt{dist}$ returned by the algorithm maps each vertex in the graph to the total weight of the edges in the optimal path from the origin vertex. The mapping $\texttt{prev}$ returned by the algorithm maps each vertex $u$ to the previous vertex on the optimal path from the origin vertex to $u$. By tracing from the destination back to the origin using the mapping $prev$, one can determine the optimal route to travel from the origin to the destination. In order to efficiently determine the unvisited vertex with the minimum distance from the origin, data structures such as priority queues, heaps, and self-balancing binary search trees are often used to store the set of unvisited vertices [5]. When binary heaps or self-balancing binary search trees are used to store the set of unvisited vertices, the worst-case running time of the Dijkstra algorithm is $\Theta((|V| + |E|)\log(|V|))$ where $V$ and $E$ are the vertices and edges of a graph [5].

\subsection*{Project Goal}
The goal of this project is to develop a route planning program that can determine a route in a road network from a given origin to a given destination that minimizes the expected travel time. The expected travel time of each road segment in a road network can be calculated based on the length of the road segment and historical data on average traffic speed. Dijkstra algorithm will play a central role in the route planning algorithm in this project.

\section*{Computational Plan}
\subsection*{Dataset}
Ideally, a real-world dataset that reflects the information on both the lengths and historical average traffic speeds of roads will be used for the project. But such a dataset hasn't been found yet. We tentatively plan to use a csv file containing information about roads in North America obtained from the US Bureau of Transportation of Statistics as the dataset [6]. In this csv file, each road is subdivided into road segments and each road segment has a unique id. The length and speed limit of each road segment is also present. Using the API of the US Bureau of Transportation of Statistics [7], the latitudes and longitudes of the start and end points of each road segment can be obtained, which makes it possible to determine the connectivity of the roads. We tentatively use the speed limits as the estimated travel speeds of the road segments to calculate the expected travel time the road segments.

\subsection*{Storing Road Network}
A class \texttt{WeightedGraph} will be used to represent the road network obtained from the dataset, in which each vertex represents a junction between road segments and each edge represents a road segment between 2 junctions. A class \texttt{Vertex} will be used to represent a vertex. The \texttt{Vertex} class will have an instance attribute \texttt{id} of type \texttt{int} as a unique identifier of the junction. It will also contain an instance attribute \texttt{weights} of type \texttt{dict[Vertex, float]}. For an instance \texttt{v} of \texttt{Vertex} class, for any \texttt{u in v.weights}, \texttt{u} is a neighbor of \texttt{v} and \texttt{v.weights[u]} denotes the weight of the edge \texttt{\{v, u\}}. The edges will be weighted by the expected time needed for a vehicle to travel from \texttt{v} to \texttt{w} via the road segment between \texttt{v} and \texttt{w} represented by the edge. The \texttt{WeightedGraph} class will have an instance attribute \texttt{vertices} of type \texttt{dict[int, Vertex]}. For an instance \texttt{g} of the \texttt{WeightedGraph} class, for every \texttt{i in g.vertices}, \texttt{i} is the unique identifier of the vertex \texttt{g.vertices[i]} (i.e. \texttt{g.vertices[i].id = i}). In this way, the vertices of a \texttt{WeightedGraph} are explicitly kept track of and it is possible to get a vertex of a \texttt{WeightedGraph} by id in $\Theta(1)$ running time, while the edges and weights in a \texttt{WeightedGraph} are implicitly kept track of as instance attributes of the \texttt{Vertex} class. 

\subsection*{Implementation of Dijkstra Algorithm}

Algorithm 2 illustrates the pseudocode of the function that will be used to compute the optimal route from the origin vertex with the \texttt{start\_id} to the destination vertex with the id \texttt{end\_id}. A class \texttt{MinHeap} that implements a binary min heap ADT will be used as a helper to efficiently keep track of the unvisited vertices with the smallest distances to the origin vertex. A binary min heap is a balanced binary tree in which each value is smaller than or equal to its left child and right child. The \texttt{MinHeap} class can be initialized by taking an argument \text{vertices} of type \texttt{list[Vertex]} and an argument \texttt{vertices\_to\_float} of type \texttt{dict[Vertex, float]} that maps each vertex in \texttt{vertices} to a \texttt{float} value. Each vertex in the list \texttt{vertices} will be stored as a value in the \texttt{MinHeap} in a way such that if \texttt{u1} and \texttt{u2} are the left and right child of the \texttt{u}, then \texttt{vertices\_to\_float[u1] $\geq$ vertices\_to\_float[u]} and \texttt{vertices\_to\_float[u2]$\geq$ vertices\_to\_float[u]}. The \texttt{MinHeap} class will have a \texttt{extract\_min(self, vertices\_to\_float: dict[Vertex, float])} method that removes and returns the root of the \texttt{MinHeap} and restores the heap property with respect to the \texttt{vertices\_to\_float} dictionary. The \texttt{MinHeap} class also has a method \texttt{sift\_up(self, v: Vertex, vertices\_to\_float: dict[Vertex, float])} that restores the heap property after \texttt{dist[v]} is lowered.

\begin{algorithm}
    \caption{The route planning algorithm for this project}
    \begin{algorithmic}
        \Require $self \text{ is an instance of } \texttt{WeightedGraph} \text{ class and } start\_id, end\_id \in self.vertices$
        \Ensure 
            \State $\text{If } self.vertices[start\_id] \text{ is connected to } self.vertices[end\_id] \text{, then}$ 
            \State $\texttt{self.find\_optimal\_path(start\_id, end\_id) = (weight, path)}$
            \State $\text{where } weight \text{ is the total weight of the edges in the optimal path and } $
            \State $path \text{ is a } \texttt{list} \text{ of the unique identifiers of the vertices in the path in the order from \texttt{start\_id} to \texttt{end\_id}.}$ 
            \State $\text{Else, } \texttt{None} \text{ is returned.}$
        \Procedure {find\_optimal\_path}{$self$, $start\_id$, $end\_id$}
        \If {$\texttt{start\_id} == \texttt{end\_id}$}
            \State \Return{\texttt{0, [start\_id]}}
        \Else
            \State $\texttt{v1} \gets \texttt{self.vertices[start\_id]}$
            \State $\texttt{v2} \gets \texttt{self.vertices[end\_id]}$
            \State $\texttt{dist} \gets \{\}$
            \State $\texttt{prev} \gets \{\}$
            \State $\texttt{dist[v1]} \gets 0$
            \State $\texttt{dist[v1]} \gets \texttt{None}$
            \ForAll{$\texttt{i in self.vertices}$}
                \State $\texttt{v} \gets \texttt{self.vertices[i]}$
                \State $\texttt{dist[v]} \gets \infty$
                \State $\texttt{prev[v]} \gets \texttt{None}$
            \EndFor
            \State $\texttt{hp} \gets \texttt{MinHeap(self.vertices.values(), dist)}$
            \While{$\texttt{not hp.is\_empty()}$}
                \State $\texttt{cur\_vertex} \gets \texttt{hp.extract\_min(dist)}$
                \ForAll{$\texttt{neighbour in cur\_vertex.weights}$}
                    \State $\texttt{alt\_dist} \gets \texttt{dist[cur\_vertex]} + \texttt{cur\_vertex.weights[neighbour]}$
                    \If{$\texttt{alt\_dist} < \texttt{dist[neighbour]}$}
                        \State $\texttt{dist[neighbour]} \gets \texttt{alt\_dist}$
                        \State $\texttt{prev[neighbour]} \gets \texttt{cur\_vertex}$
                        \State $\texttt{hp.sift\_up(cur\_vertex, dist)}$
                    \EndIf
                \EndFor
            \EndWhile
            \If{$\texttt{dist[v2]} == \infty$}
                \State \Return{\texttt{None}}
            \Else
                \State $\texttt{path} \gets \texttt{[v2.id]}$
                \State $\texttt{u} \gets \texttt{v2}$
                \While{$\texttt{u != v1}$}
                    \State $\texttt{u} \gets \texttt{prev[u]}$
                    \State $\texttt{path.append(u.id)}$
                \EndWhile
                \State $\texttt{path.reverse()}$
                \State \Return{$\texttt{dist[v2], path}$}
            \EndIf
        \EndIf
        \EndProcedure
    \end{algorithmic}
\end{algorithm}

\section*{References}
\begin{itemize}
    \item Placek, M. (2023, December 8). U.S. freight movement mode share by tonnage 2020. Statista. \url{https://www.statista.com/statistics/184595/us-freight-movement-mode-share-by-tonnage/} 
    \item Carlier, M. (2023, May 4). Road traffic in the United States: Vehicle-miles. Statista. \url{https://www.statista.com/statistics/185537/us-vehicle-miles-on-highways-from-since-1990/}
    \item GfG. (2023, June 7). What is weighted graph with applications, advantages and disadvantages. GeeksforGeeks. \url{https://www.geeksforgeeks.org/applications-advantages-and-disadvantages-of-weighted-graph/}
    \item Dijkstra, E.W. A note on two problems in connexion with graphs. Numer. Math. 1, 269–271 (1959). \url{https://doi.org/10.1007/BF01386390}
    \item Wikimedia Foundation. (2024, February 23). Dijkstra’s algorithm. Wikipedia. \url{https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm}
    \item North American roads. Geospatial at the Bureau of Transportation Statistics. (n.d.). \url{https://geodata.bts.gov/datasets/usdot::north-american-roads/about} 
    \item North American roads. Geospatial at the Bureau of Transportation Statistics. (n.d.-a). \url{https://geodata.bts.gov/datasets/usdot::north-american-roads/api} 
\end{itemize}

% NOTE: LaTeX does have a built-in way of generating references automatically,
% but it's a bit tricky to use so you are allowed to write your references manually
% using a standard academic format like MLA or IEEE.
% See project proposal handout for details.

\end{document}
