# encoding: utf-8
import click
import os
import logging
import sys
from wethepeopletoolkit.spark_starter import SparkStarter
from wethepeopletoolkit.hive_checker import HiveChecker

class DataImporter:
  def __init__(self, data_directory, spark_home, force):
    self.data_directory = data_directory
    self.spark_home = spark_home
    self.force = force

  def create_tables(self):
    sc, sqlContext = SparkStarter(self.spark_home).start()
    from pyspark.sql.functions import col, expr
    
    # Check Hive is accessible
    if not HiveChecker(sqlContext).check_connectivity():
      return

    tables = ['wtp_data_signatures', 'wtp_data_petitions', 'wtp_data_states']
    if set(tables) < set(sqlContext.tables().rdd.map(lambda t: t.tableName).collect()) and not self.force:
      click.echo(click.style("Tables already exist, skipping data import (you can force import with the --force option)", fg='yellow'))
      return

    filenames = ['population.csv', 'us_postal_codes.csv', 'wtp_data_signatures.csv', 'pvi_scores.csv', 'wtp_data_petitions.csv']
    files = dict((f, os.path.join(os.getcwd(), self.data_directory, f)) for f in filenames)

    click.echo("\nImporting signatures data...")
    raw_signatures = sqlContext.read.csv(files['wtp_data_signatures.csv']).toDF('id', 'petition_id', 'type', 'initials', 'zip', 'timestamp').select('petition_id', 'zip')
    zips = sqlContext.read.csv(files['us_postal_codes.csv'], header = True)

    signatures = raw_signatures.join(zips, raw_signatures.zip == col('Postal Code')).select('petition_id', col('State Abbreviation').alias('state'))
    signatures.write.mode("overwrite").saveAsTable("wtp_data_signatures")
    click.echo(click.style(u'✔ Success', fg='green'))

    click.echo("\nImporting states data...")
    states_w_dc = sqlContext.read.csv(files['population.csv'], header = True).select("abb", "population")
    states = states_w_dc.filter("abb != 'DC'")

    party_affiliation = sqlContext.read.csv(files['pvi_scores.csv']).select(col('_c0').alias('abb'), expr('SUBSTRING(_c4, 1, 1)').alias('party'))
    states = states.alias("states").join(party_affiliation.alias("pa"), states.abb == party_affiliation.abb).select("states.*", "pa.party")

    states.write.mode("overwrite").saveAsTable("wtp_data_states")
    click.echo(click.style(u'✔ Success', fg='green'))

    click.echo("\nImporting petitions data...")
    petitions = sqlContext.read.csv(files['wtp_data_petitions.csv']).select(col('_c1').alias('id'), col('_c3').alias('title'), col('_c4').alias('body'))
    petitions.write.mode("overwrite").saveAsTable("wtp_data_petitions")
    click.echo(click.style(u'✔ Success', fg='green'))