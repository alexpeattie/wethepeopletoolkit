import pandas
import numpy as np
import os
from wethepeopletoolkit.spark_starter import SparkStarter
from wethepeopletoolkit.hive_checker import HiveChecker

class StateProcessor:
  def __init__(self, spark_home, data_directory):
    self.spark_home = spark_home
    self.data_directory = data_directory
    self.sqlContext = None

  def load_or_create_matrix(self):
    csv_path = os.path.join(os.getcwd(), self.data_directory, 'population_adjusted_engagement_matrix.csv')

    if os.path.exists(csv_path):
      return pandas.read_csv(csv_path, index_col = 0)
    else:
      sc, self.sqlContext = SparkStarter(self.spark_home).start()
      HiveChecker(self.sqlContext).check_healthy_setup()
      from pyspark.sql.functions import col, count, first, expr

      signatures = self.sqlContext.sql("select * from wtp_data_signatures").alias("signatures")
      states = self.sqlContext.sql("select * from wtp_data_states").alias("states")
      signatures_by_state = signatures.join(states, signatures.state == states.abb).select("signatures.*", "states.population").groupBy("state", "petition_id")

      population_adjusted_engagement_matrix = signatures_by_state.agg(((count("*") * 1000) / first(col("population"))).alias('adjusted_count')).groupBy("state").pivot("petition_id").agg(expr("first(adjusted_count)")).fillna(0).toPandas()
      if not os.path.exists(config.data_directory):
        os.makedirs(config.data_directory)

      population_adjusted_engagement_matrix.sort('state').to_csv(csv_path, header = True)

      return population_adjusted_engagement_matrix

  def get_state_parties(self):
    if not self.sqlContext:
      sc, self.sqlContext = SparkStarter(self.spark_home).start()

    return self.sqlContext.sql("select abb, party from wtp_data_states").rdd.map(lambda r: (r.abb, r.party)).collectAsMap()

  def states(self, two_d = True):
    from sklearn.decomposition import PCA

    population_adjusted_engagement_matrix = self.load_or_create_matrix()
    population_adjusted_engagement_matrix.set_index('state', inplace = True)
    if not two_d:
      return population_adjusted_engagement_matrix

    pca = PCA(n_components = 2)
    pca.fit(population_adjusted_engagement_matrix)
    states_2d = pandas.DataFrame(pca.transform(population_adjusted_engagement_matrix))

    states_2d.index = population_adjusted_engagement_matrix.index
    states_2d.columns = ['PC1', 'PC2']
    return states_2d

  def create_projection(self, show_party_affiliation, show_points, z_score_exclude):
    import matplotlib.pyplot as plt
    from scipy import stats

    states_2d = self.states(two_d = True)
    party_colors = { None: 'black', 'R': 'red', 'D': 'blue' }

    if show_party_affiliation:
      state_parties = self.get_state_parties()
    else:
      state_parties = {}

    if z_score_exclude > 0:
      states_2d = states_2d[(np.abs(stats.zscore(states_2d)) < z_score_exclude).all(axis=1)]

    ax = states_2d.plot(kind = 'scatter', x = 'PC2', y = 'PC1', alpha = { False: 0, True: 1 }[show_points])
    for i, state in enumerate(states_2d.index):
      ax.annotate(state, (states_2d.iloc[i].PC2, states_2d.iloc[i].PC1), color = party_colors[state_parties.get(state, None)])

    plt.show()