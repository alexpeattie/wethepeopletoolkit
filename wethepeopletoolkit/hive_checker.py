# encoding: utf-8
import click
import os
import logging
import sys

class HiveChecker:
  def __init__(self, sqlContext):
    self.sqlContext = sqlContext

  def check_connectivity(self):
    from pyspark.sql.utils import AnalysisException

    try:
      self.sqlContext.sql("CREATE TABLE IF NOT EXISTS wtp_tmp_test (id int)")
      self.sqlContext.sql("DROP TABLE IF EXISTS wtp_tmp_test")
      return True
    except AnalysisException:
      click.echo(click.style("Fatal: couldn't connect to Hive. Ensure Hadoop is running and the Hive server (i.e. hiveserver2) is started.", fg='red'))

  def check_healthy_setup(self):
    from pyspark.sql.utils import AnalysisException

    tables = ['wtp_data_signatures', 'wtp_data_petitions', 'wtp_data_states']

    if not set(tables) < set(self.sqlContext.tables().rdd.map(lambda t: t.tableName).collect()):
      click.echo(click.style("Tables already exist, skipping data import (you can force import with the --force option)", fg='yellow'))
      return False

    try:
      self.sqlContext.sql("select * from wtp_data_states limit 1").collect()
      return True
    except AnalysisException:
      click.echo(click.style("Fatal: couldn't connect to Hive. Ensure Hadoop is running and the Hive server (i.e. hiveserver2) is started.", fg='red'))