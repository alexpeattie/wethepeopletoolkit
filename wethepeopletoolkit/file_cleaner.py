import click
import os

class FileCleaner:
  def __init__(self, data_directory, keep_files):
    self.data_directory = data_directory
    self.keep_files = keep_files

  def clean(self, files):
    for file in files:
      path = os.path.join(os.getcwd(), self.data_directory, file)
      if os.path.exists(path):
        click.echo("Cleaning up %s" % file)
        os.remove(path)

  def initial_clean(self):
    if self.keep_files:
      pass
    else:
      self.clean(['petitions.sql', 'petitions.zip'])

  def final_clean(self):
    self.clean(['population.csv', 'us_postal_codes.csv', 'wtp_data_signatures.csv', 'pvi_scores.csv', 'wtp_data_petitions.csv'])