import click

class SparkStarter:
  def __init__(self, spark_home):
    self.spark_home = spark_home

  def start(self):
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
    sc = pyspark.SparkContext(appName="weThePeople")
    if not sc.version[0] == '2':
      click.echo(click.style("Warning: Spark 1.x is not supported by the toolkit, which may lead to errors or crashes. Please upgrade to Spark 2.0+"))

    from pyspark.sql import HiveContext
    sqlContext = HiveContext(sc)
    return (sc, sqlContext)