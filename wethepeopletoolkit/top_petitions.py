from wethepeopletoolkit.spark_starter import SparkStarter
from wethepeopletoolkit.hive_checker import HiveChecker
from wethepeopletoolkit.clusterer import Clusterer

class TopPetitions:
  def __init__(self, spark_home):
    self.spark_home = spark_home
    self.sc = None

  def top_n_for_cluster(self, cluster_id, n = 10):
    if not self.sc:
      self.sc, self.sqlContext = SparkStarter(self.spark_home).start()
      HiveChecker(self.sqlContext).check_healthy_setup()

    from pyspark.sql.functions import count, col, first
    cluster_states = Clusterer().cluster_id_to_states(cluster_id)
    signatures = self.sqlContext.sql("select * from wtp_data_signatures").filter(col("state").isin(list(cluster_states)))
    petitions = self.sqlContext.sql("select * from wtp_data_petitions")

    all_top = petitions.join(signatures, signatures.petition_id == petitions.id).groupBy(col("title").alias("Title")).agg(count('*').alias('Signatures'), first(col('body')).alias('Body')).orderBy('Signatures', ascending = False)
    return all_top.limit(n)