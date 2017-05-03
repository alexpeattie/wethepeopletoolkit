import click
import pandas
import os
from spark_starter import SparkStarter
from hive_checker import HiveChecker

class PCAProjector:
  def __init__(self, spark_home, data_directory):
    self.spark_home = spark_home
    self.data_directory = data_directory

  def load_or_create_matrix(self):
    csv_path = os.path.join(os.getcwd(), self.data_directory, 'population_adjusted_engagement_matrix.csv')

    sc, self.sqlContext = SparkStarter(self.spark_home).start()
    HiveChecker(self.sqlContext).check_healthy_setup()

    if os.path.exists(csv_path):
      return pandas.read_csv(csv_path, index_col = 0)
    else:
      from pyspark.sql.functions import col, count, first, expr

      signatures = self.sqlContext.sql("select * from wtp_data_signatures").alias("signatures")
      states = self.sqlContext.sql("select * from wtp_data_states").alias("states")
      signatures_by_state = signatures.join(states, signatures.state == states.abb).select("signatures.*", "states.population").groupBy("state", "petition_id")

      population_adjusted_engagement_matrix = signatures_by_state.agg(((count("*") * 1000) / first(col("population"))).alias('adjusted_count')).groupBy("state").pivot("petition_id").agg(expr("first(adjusted_count)")).fillna(0).toPandas()
      population_adjusted_engagement_matrix.to_csv(csv_path, header = True)

      return population_adjusted_engagement_matrix

  def create_projection(self, show_party_affiliation, show_points):
    from sklearn.decomposition import PCA
    import matplotlib.pyplot as plt

    population_adjusted_engagement_matrix = self.load_or_create_matrix()
    population_adjusted_engagement_matrix.set_index('state', inplace = True)

    pca = PCA(n_components = 2)
    pca.fit(population_adjusted_engagement_matrix)
    population_2d = pandas.DataFrame(pca.transform(population_adjusted_engagement_matrix))

    population_2d.index = population_adjusted_engagement_matrix.index
    population_2d.columns = ['PC1', 'PC2']

    party_colors = { None: 'black', 'R': 'red', 'D': 'blue' }

    if show_party_affiliation:
      state_parties = self.sqlContext.sql("select abb, party from wtp_data_states").rdd.map(lambda r: (r.abb, r.party)).collectAsMap()
    else:
      state_parties = {}

    ax = population_2d.plot(kind = 'scatter', x = 'PC2', y = 'PC1', alpha = { False: 0, True: 1 }[show_points])
    for i, state in enumerate(population_2d.index):
      ax.annotate(state, (population_2d.iloc[i].PC2, population_2d.iloc[i].PC1), color = party_colors[state_parties.get(state, None)])

    plt.show()