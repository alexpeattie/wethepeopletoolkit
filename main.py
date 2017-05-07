import click
import os
from downloader import Downloader
from sql_extractor import SqlExtractor
from file_cleaner import FileCleaner
from data_importer import DataImporter
from state_processor import StateProcessor
from clusterer import Clusterer
from cluster_evaluator import ClusterEvaluator
from top_petitions import TopPetitions
from topic_extractor import TopicExtractor
from choropleth import ChoroplethMap

class SortedCommandGroup(click.Group):
  def list_commands(self, ctx):
    """Override"""
    # original value --> return sorted(self.commands)
    return ['fetch-data', 'projection', 'cluster', 'cluster-evaluation', 'top-petitions', 'topic-extraction']

class Config(object):
  def __init__(self):
    pass

def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options

pass_config = click.make_pass_decorator(Config, ensure=True)

@click.group(cls=SortedCommandGroup)
@pass_config
@click.option('--data-directory', '-d', default="data/", type=click.Path(), help="Path to data (./data/ by default).")
@click.option('--spark-home', '-S', required=False, type=click.Path(), help="Path to Spark installation (automatically discovered by default).")
def cli(config, data_directory, spark_home):
  config.data_directory = data_directory
  config.spark_home = spark_home
  pass

@click.command(name = 'fetch-data')
@pass_config
@click.option('--keep-files', is_flag=True, help="Don't delete files after they've been extracted, converted and processes.")
@click.option('--force', is_flag=True, help="Recreate Hive tables, even if they already exist")
def fetch_data(config, keep_files, force):
  """ Download and preprocess the neccessary data.
  By default, files will be downloaded to the directory ./data/
  """
  if not os.path.exists(config.data_directory):
    os.makedirs(config.data_directory)

  downloader = Downloader(config.data_directory)
  downloader.download_all_missing()
  if not downloader.wtp_prepared:
    SqlExtractor(config.data_directory).unzip('petitions.zip', 'petitions.sql') 

  cleaner = FileCleaner(config.data_directory, keep_files)
  cleaner.initial_clean()
  click.echo(click.style("Data downloaded, extracted and converted succesfully. Loading into Spark/Hive...", fg='green'))

  DataImporter(config.data_directory, config.spark_home, force).create_tables()
  cleaner.final_clean()

@click.command()
@pass_config
@click.option('--show-party-affiliation', '-p', is_flag=True, help="Color states based on their affiliation to Republicans/Democrats. Based on the 2014 Cook Partisan Voting Index.")
@click.option('--show-points', is_flag=True, help="Show points next to state labels.")
@click.option('--z-score-exclude', '-z', type=float, default=0.0, help="Don't show points with a z-score higher than this value. For example, -z 3.0 would exclude points more than 3 standard deviations from the mean. If the value is 0, no points are excluded.")
def projection(config, show_party_affiliation, show_points, z_score_exclude):
  """ Create a 2-D projection of states w/ PCA.
  States which react more similarly to petitions will be closer together.
  """
  StateProcessor(config.spark_home, config.data_directory).create_projection(show_party_affiliation, show_points, z_score_exclude)

cluster_options = [
  click.option('--model-type', '-m', type=click.Choice(['kmeans', 'spectral']), default='kmeans', prompt="Model type (choose from kmeans, spectral). Default", help="The type of clustering model to use. Valid values:\nkmeans: K-means clustering, spectral: spectral clustering"),
  click.option('--pca', is_flag=True, help="Performs PCA (dimensionality reduction) to reduce the data to two dimensions before clustering."),
  click.option('--z-score-exclude', '-z', type=float, default=0.0, help="Don't show points with a z-score higher than this value. For example, -z 3.0 would exclude points more than 3 standard deviations from the mean. If the value is 0, no points are excluded. This can only be used in conjunction with K-means clustering."),
  click.option('--seed', type=int, default=None, help="Sets the random seed for clustering.")
]

@click.command()
@click.option('--number-of-clusters', '-n', type=click.IntRange(2, 50), default=2, prompt="Number of clusters (from 2 - 50). Default", help="The number of clusters to generate. Must be between 2 and 50.")
@add_options(cluster_options)
@pass_config
def cluster(config, number_of_clusters, model_type, pca, z_score_exclude, seed):
  """ Performs clustering on states based on their similar reactions to petitions.
  """
  state_processor = StateProcessor(config.spark_home, config.data_directory)
  clusterer = Clusterer()
  states_map = ChoroplethMap()
  clusterer.cluster(number_of_clusters, state_processor, pca, model_type, z_score_exclude, seed)

  click.echo(click.style("\nClustering successful! Your cluster IDs are:", fg='green'))
  click.echo("\n".join(map(lambda (n, id): "Cluster #%d (%s): %s" % (n + 1, states_map.COLOR_NAMES[min(n, len(states_map.COLOR_NAMES) - 1)], id), clusterer.cluster_ids())))

  states_map.show_clustered_map(clusterer.results_dict())

@click.command(name = 'cluster-evaluation')
@click.option('--range', '-r', nargs=2, type=click.IntRange(2, 50), default=(2, 10), help="The beginning and end of the range of cluster numbers to test. For example, -r 2 5 would evaluate four models with 2, 3, 4 and 5 clusters. Both numbers must be between 2 and 50.")
@click.option('--evaluation-metric', '-e', type=click.Choice(['silhouette', 'calinski_harabaz', 'inertia']), prompt="Evaluation metric (choose from silhouette, calinski_harabaz, inertia). Default", default='silhouette')
@click.option('--distance', type=click.Choice(['cityblock', 'cosine', 'euclidean', 'l1', 'l2', 'manhattan', 'braycurtis', 'canberra', 'chebyshev', 'correlation', 'dice', 'hamming', 'jaccard', 'kulsinski', 'mahalanobis', 'matching', 'minkowski', 'rogerstanimoto', 'russellrao', 'seuclidean', 'sokalmichener', 'sokalsneath', 'sqeuclidean', 'yule']), default='euclidean', help="The type of distance measure to used to calculate the silhouette score.")
@add_options(cluster_options)
@pass_config
def cluster_evaluation(config, range, evaluation_metric, distance, model_type, pca, z_score_exclude, seed):
  """ Shows comparisons of performance as number of clusters is varied.
  """
  state_processor = StateProcessor(config.spark_home, config.data_directory)
  evaluator = ClusterEvaluator([state_processor, pca, model_type, z_score_exclude, seed])
  click.echo("Evaluating models from %d to %d clusters..." % tuple(sorted(range)))
  evaluator.evaluate_range(evaluation_metric, distance, *sorted(range))

@click.command(name = 'top-petitions')
@click.argument('cluster-id')
@click.option('--top-n', '-n', type=click.IntRange(1, 3891), default=10, help="Dictates what number of the top petitions (by number of signatures) are displayed.")
@click.option('--no-truncation', is_flag=True, help="Always show the entire petition titles.")
@click.option('--show-body', '-b', is_flag=True, help="Additionally show the body of the petitions.")
@pass_config
def top_petitions(config, cluster_id, top_n, no_truncation, show_body):
  """ Displays the top N most signed petitions for a given cluster. Defaults to the top 10.
  CLUSTER_ID is the Base58 encoded cluster ID (as provided by the 'cluster' command).
  """
  truncate = False if no_truncation else 50
  columns = ['Title', 'Signatures']
  if show_body:
    columns.append('Body')

  petitions = TopPetitions(config.spark_home).top_n_for_cluster(cluster_id, top_n).select(*columns).show(top_n, truncate = truncate)

@click.command(name = 'topic-extraction')
@click.argument('cluster-ids', nargs=-1)
@click.option('--extraction-method', '-m', type=click.Choice(['lda', 'nmf']), default='lda', help="The type of topic extraction model to use. Valid values:\nlda: latent Dirichlet allocation, nmf: non-negative matrix factorization")
@click.option('--petition-sample-size', '-P', type=click.IntRange(1, 3891), default=500, help="Dictates what number of the top petitions (by number of signatures) are used as the data for topic extraction (default 500).")
@click.option('--number-of-topics', '-n', type=click.IntRange(1, 100), default=10, help="How many topics to extract (1 - 100, default 10).")
@click.option('--words-per-topic', '-w', type=click.IntRange(1, 100), default=10, help="How many words should be in each topic (1 - 100, default 10).")
@pass_config
def topic_extraction(config, cluster_ids, extraction_method, number_of_topics, words_per_topic, petition_sample_size):
  """ Performs topic extraction on the top N most signed petitions for given cluster(s). Uses the top 500 petitions by default, and constructs 10 topics of 10 words.
  Extraction can be performed with latent Dirichlet allocation (LDA) or non-negative matrix factorization (NMF).
  CLUSTER_IDS are the Base58 encoded cluster IDs (as provided by the 'cluster' command) that you want to display/compare.
  """
  TopicExtractor(config.spark_home).topic_extraction(cluster_ids, extraction_method, number_of_topics, words_per_topic, petition_sample_size)

cli.add_command(fetch_data)
cli.add_command(projection)
cli.add_command(cluster)
cli.add_command(cluster_evaluation)
cli.add_command(top_petitions)
cli.add_command(topic_extraction)

if __name__ == '__main__':
  cli()