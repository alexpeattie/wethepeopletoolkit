import pandas
import numpy as np
import click
from bitstring import BitArray
from base58 import b58encode_int, b58decode_int

class Clusterer:
  def __init__(self):
    pass

  def cluster(self, n, state_processor, pca = False, model_type = 'kmeans', z_score_exclude = 0.0, seed = None, quiet = False):
    from sklearn.cluster import FeatureAgglomeration, KMeans, SpectralClustering
    from scipy import stats

    model_types = {
      'feature-agglomeration': FeatureAgglomeration,
      'kmeans': KMeans,
      'spectral': SpectralClustering,
    }
    states = state_processor.states(two_d = pca)
    excluded_states, labels = [], []

    if z_score_exclude > 0:
      if not model_type == 'kmeans':
        raise click.UsageError("--z-score-exclude can only be used when --model-type is 'kmeans'")

      states_2d = state_processor.states(two_d = True)
      excluded_states = states[-(np.abs(stats.zscore(states_2d)) < z_score_exclude).all(axis=1)]
      states = states[(np.abs(stats.zscore(states_2d)) < z_score_exclude).all(axis=1)]

    seed = seed or np.random.randint(0, 10 ** 6)
    np.random.seed(seed)
    if not quiet:
      click.echo("Clustering with seed %d..." % seed)

    self.model = model_types[model_type](n_clusters = n)
    self.data = states.as_matrix()
    self.model.fit(self.data)
    labels = self.model.labels_
    self.results = pandas.DataFrame([states.index, self.model.labels_]).T.sort_values(by=0)

    if any(excluded_states):
      excluded_results = pandas.DataFrame([excluded_states.index, self.model.predict(excluded_states)]).T
      self.results = pandas.DataFrame(np.concatenate([self.results, excluded_results]))

  def cluster_ids(self):
    labels = self.results[1]
    sorted_labels = sorted(labels.unique())
    ids = map(lambda l: b58encode_int(BitArray((labels == l).astype(int).tolist()).uint), sorted_labels)

    return zip(sorted_labels, ids)

  def cluster_id_to_states(self, cluster_id):
    states = np.array(['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'])
    return states[list(BitArray(uint = b58decode_int(cluster_id), length = 50))]

  def evaluate(self, metric, distance = None):
    from sklearn.metrics import silhouette_score, calinski_harabaz_score
    if metric == 'silhouette':
      return silhouette_score(self.data, self.model.labels_, metric = distance)
    if metric == 'calinski_harabaz':
      return calinski_harabaz_score(self.data, self.model.labels_)
    if metric == 'inertia':
      return self.model.inertia_

  def results_dict(self):
    return self.results.set_index(0)[1].to_dict()