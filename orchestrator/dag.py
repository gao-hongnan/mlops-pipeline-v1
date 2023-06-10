from concurrent.futures import ThreadPoolExecutor

import matplotlib.pyplot as plt
import networkx as nx


class Task:
    def __init__(self, f, pipeline):
        self.f = f
        self.pipeline = pipeline
        self.name = f.__name__

    def __call__(self, *args, **kwargs):
        return self.f(*args, **kwargs)

    def __rshift__(self, other):
        self.pipeline.add_dependency(self, other)
        return other


class Pipeline:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.tasks = {}

    def task(self):
        def decorator(f):
            task = Task(f, self)
            self.tasks[task.name] = task
            self.graph.add_node(task.name)
            return task

        return decorator

    def add_dependency(self, upstream, downstream):
        self.graph.add_edge(upstream.name, downstream.name)

    def run(self):
        with ThreadPoolExecutor(max_workers=3) as executor:
            for task_name in nx.topological_sort(self.graph):
                task_func = self.tasks[task_name]
                future = executor.submit(task_func)
                future.result()

    def visualize(self):
        pos = nx.spring_layout(self.graph)
        for node in self.graph.nodes:
            plt.text(
                pos[node][0],
                pos[node][1],
                node,
                fontsize=12,
                bbox=dict(
                    facecolor="blue", edgecolor="black", boxstyle="round,pad=0.2"
                ),
            )
        nx.draw(self.graph, pos, with_labels=False, node_color="w", edgecolors="k")
        plt.show()


pipeline = Pipeline()


@pipeline.task()
def feature_pipeline():
    from mlops_pipeline_feature_v1 import pipeline

    print("Running feature pipeline")
    pipeline.run()


@pipeline.task()
def training_pipeline():
    print("Running training pipeline")


@pipeline.task()
def prediction_pipeline():
    print("Running prediction pipeline")


feature_pipeline >> training_pipeline >> prediction_pipeline

# pipeline.visualize()
pipeline.run()
