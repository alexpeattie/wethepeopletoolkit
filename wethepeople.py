import click
import os
from downloader import Downloader
from sql_extractor import SqlExtractor
from file_cleaner import FileCleaner
from data_importer import DataImporter
from pca_projector import PCAProjector

class SortedCommandGroup(click.Group):
  def list_commands(self, ctx):
    """Override"""
    # original value --> return sorted(self.commands)
    return ['fetch-data', 'projection', 'cluster']

class Config(object):
  def __init__(self):
    pass

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
  """ Download and preprocess the neccessary data. By default, files will be downloaded to the directory ./data/
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
def projection(config, show_party_affiliation, show_points):
  """ Create a 2-D projection of states w/ PCA.
  States which react more similarly to petitions will be closer together.
  """
  PCAProjector(config.spark_home, config.data_directory).create_projection(show_party_affiliation, show_points)

@click.command()
@pass_config
def cluster(config):
  """ Performs k-means clustering on states based on petitions behaviour.
  """
  click.echo()

cli.add_command(fetch_data)
cli.add_command(cluster)
cli.add_command(projection)

if __name__ == '__main__':
  cli()