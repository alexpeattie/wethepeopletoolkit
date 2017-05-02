# encoding: utf-8
import click
import os
import logging
import sys

class DataImporter:
  def __init__(self, data_directory, spark_home, force):
    self.data_directory = data_directory
    self.spark_home = spark_home
    self.force = force

  def create_tables(self):
    import findspark
    try:
      findspark.init(self.spark_home)
    except IndexError:
      if self.spark_home:
        click.echo(click.style('Fatal: looks like there was an error finding Spark. Check that --spark-home is pointing to the correct directory (see also https://github.com/minrk/findspark).', fg='red'))
      else:
        click.echo(click.style('Fatal: looks like there was an error finding Spark. You might have to manually specify your Spark directory with the --spark-home option.', fg='red'))
      return

    import pyspark
    from pyspark.sql.session import SparkSession
    sc = pyspark.SparkContext(appName="weThePeople")

    from pyspark.sql import HiveContext
    from pyspark.sql.functions import col
    sqlContext = HiveContext(sc)

    # Check Hive is accessible
    try:
      sqlContext.sql("CREATE TABLE IF NOT EXISTS wtp_tmp_test (id int)")
      sqlContext.sql("DROP TABLE IF EXISTS wtp_tmp_test")
    except pyspark.sql.utils.AnalysisException:
      click.echo(click.style("Fatal: couldn't connect to Hive. Ensure Hadoop is running and the Hive server (i.e. hiveserver2) is started.", fg='red'))

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
    states.write.mode("overwrite").saveAsTable("wtp_data_states")
    click.echo(click.style(u'✔ Success', fg='green'))

    click.echo("\nImporting petitions data...")
    petitions = sqlContext.read.csv(files['wtp_data_petitions.csv']).select(col('_c1').alias('id'), col('_c2').alias('title'), col('_c4').alias('body'))
    petitions.write.mode("overwrite").saveAsTable("wtp_data_petitions")
    click.echo(click.style(u'✔ Success', fg='green'))