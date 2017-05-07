import click
from wethepeopletoolkit.clusterer import Clusterer

class ClusterEvaluator:
  def __init__(self, clusterer_args):
    self.clusterer_args = clusterer_args
    self.clusterer = Clusterer()

  def evaluate_for_n(self, n, evaluation_metric, distance):
    self.clusterer.cluster(*[n] + self.clusterer_args + [True])
    return self.clusterer.evaluate(evaluation_metric, distance = distance)

  def evaluate_range(self, evaluation_metric, distance, min_clusters, max_clusters):
    import matplotlib.pyplot as plt
    if evaluation_metric == 'inertia' and (not self.clusterer_args[2] == 'kmeans'):
      raise click.UsageError("'inertia' can only be used for --evaluation-metric when --model-type is 'kmeans'")

    target_range = range(min_clusters, max_clusters + 1)
    evaluation = map(lambda n: self.evaluate_for_n(n, evaluation_metric, distance), target_range)
    metric_name = { 'silhouette': 'Silhouette score', 'calinski_harabaz': 'Calinski and Harabaz score', 'inertia': 'Inertia' }[evaluation_metric]

    if evaluation_metric == 'silhouette':
      metric_name += ' (%s distance)' % distance

    plt.plot(target_range, evaluation)
    plt.xticks(target_range)

    plt.ylabel(metric_name)
    plt.xlabel('Number of clusters')

    plt.show()