import click
import urllib
import os
import hashlib

class Downloader:
  def __init__(self, data_directory):
    self.data_directory = data_directory
    self.wtp_prepared = False

  @staticmethod
  def __reporthook(count, block_size, total_size):
    ''' Callback function to urllib.urlretrieve to add progress bar '''
    if count is 0:
      Downloader.bar = click.progressbar(length=int(total_size / 1024.0), show_pos=True, show_percent=True)
      Downloader.bar.update(0)
      Downloader.total_completed = 0

    completed = (count * block_size)

    if completed > 0 and Downloader.bar is not None:
      Downloader.bar.update(int(block_size / 1024.0))

    # Move to next line if the file download is complete
    if Downloader.bar.finished:
      click.echo()

  def check_free_space(self):
    statvfs = os.statvfs(os.path.join(os.getcwd(), self.data_directory))

    if (statvfs.f_frsize * statvfs.f_bavail) < (5 * 1024 ** 3):
      click.echo(click.style('Warning < 5GB of disk space available - you might not have enough space to download and extract the necessary data.', fg='yellow'))

  def download_file(self, url, outname):
    urllib.urlretrieve(url, outname, Downloader.__reporthook)
    Downloader.total_completed = 0

  def is_wtp_prepared(self):
    paths = [os.path.join(os.getcwd(), self.data_directory, f + '.csv') for f in ['wtp_data_petitions', 'wtp_data_signatures']]
    md5s = { 'wtp_data_petitions.csv': '53145a886f092d7664b1a7b88eb7d22f', 'wtp_data_signatures.csv': '0e7a3f4168778e710ab4390678f244c7' }
    
    for path in paths:
      if not (os.path.exists(path)):
        return False
    click.echo(click.style('CSV files already present, checking integrity...', fg='yellow'))
    
    for path in paths:
      if not hashlib.md5(open(path, 'rb').read()).hexdigest() == md5s.get(path.split('/')[-1]):
        return False

    return True

  def download_all_missing(self):
    self.check_free_space()

    rename = { 'data.sql.zip': 'petitions.zip', 'murders.csv': 'population.csv' }
    md5s = { 'petitions.zip': '3c433968d8e90a70d17ab16b67633aef', 'us_postal_codes.csv': 'b7ba2f9a3da74fc6737fa28eab047dc1', 'population.csv': 'ab7666bed5955c96e353cd8d14aa14ce', 'pvi_scores.csv': 'b6156f49bd73d97417ac87dadb8e0401' }
    files = [
      'https://s3-us-west-1.amazonaws.com/wethepeopledata/data.sql.zip',
      'http://scrapmaker.com/data/wordlists/places/us_postal_codes.csv',
      'https://raw.githubusercontent.com/cran/dslabs/master/inst/extdata/murders.csv',
      'https://gist.githubusercontent.com/alexpeattie/b534d3dd31735c4359ca378424fb4169/raw/626ac26e64635a23aac5f519dc8a9fe14a030035/pvi_scores.csv'
    ]
    self.wtp_prepared = self.is_wtp_prepared()

    if self.wtp_prepared:
      click.echo(click.style('CSV already prepared. Skipping petitions.zip', fg='yellow'))
      files.remove('https://s3-us-west-1.amazonaws.com/wethepeopledata/data.sql.zip')

    for i, url in enumerate(files):
      remote_filename = url.split('/')[-1]
      filename = rename.get(remote_filename) or remote_filename

      file_path = os.path.join(os.getcwd(), '%s/%s' % (self.data_directory, filename))
      if os.path.exists(file_path):
        if hashlib.md5(open(file_path, 'rb').read()).hexdigest() == md5s.get(filename):
          click.echo(click.style('[%d/%d] File %s already exits. Skipping' % (i + 1, len(files), filename), fg='yellow'))
        else:
          click.echo(click.style('[%d/%d] File %s is damaged or incomplete, redownloading...' % (i + 1, len(files), filename), fg='red'))
          self.download_file(url, file_path)
      else:
        click.echo('[%d/%d] Downloading %s...' % (i + 1, len(files), filename))
        self.download_file(url, file_path)