import click
import os
import csv
import hashlib
from zipfile import ZipFile

class SqlExtractor:
  def __init__(self, data_directory):
    self.data_directory = data_directory

  @staticmethod
  def __reporthook(count, block_size, total_size):
    ''' Callback function to urllib.urlretrieve to add progress bar '''
    if count is 0:
      SqlExtractor.bar = click.progressbar(length=int(total_size / 1024.0), show_pos=True, show_percent=True)
      SqlExtractor.bar.update(0)
      SqlExtractor.total_completed = 0

    completed = (count * block_size)

    if completed > 0 and SqlExtractor.bar is not None:
      SqlExtractor.bar.update(int(block_size / 1024.0))

    # Move to next line if the file download is complete
    if SqlExtractor.bar.finished:
      click.echo()

  def unzip_in_chunks(self, zf, name, unzipped_path):
    bar = click.progressbar(length=int(zf.infolist()[0].file_size / 1024.0), show_pos=True, show_percent=True)
    
    chunk_size = 4096
    f = zf.open(name)
    read_data = ''

    try:
      os.remove(unzipped_path)
    except OSError:
      pass

    with open(unzipped_path, "w") as unzipped:
      while 1:
        data = f.read(chunk_size)
        if not data:
          unzipped.write(read_data)
          read_data = ''
          click.echo()
          break

        bar.update(int(len(data) / 1024.0))
        read_data += data

        # Write every 100MB
        if len(read_data) > (5 * 1024 ** 2):
          unzipped.write(read_data)
          read_data = ''

  def target_table(self, line, tables):
    """
    Returns true if the line begins a SQL insert statement for a target table.
    """
    target_table = next((t for t in tables if line.startswith('INSERT INTO `' + t + '`')), False)
    return target_table

  def values_sanity_check(self, values):
    """
    Ensures that values from the INSERT statement meet basic checks.
    """
    assert values
    assert values[0] == '('
    # Assertions have not been raised
    return True

  def get_values(self, line):
    """
    Returns the portion of an INSERT statement containing values
    """
    return line.partition('` VALUES ')[2]

  def parse_values(self, values, outfile):
    """
    Given a file handle and the raw values from a MySQL INSERT
    statement, write the equivalent CSV to the file
    """
    latest_row = []

    reader = csv.reader([values], delimiter=',',
      doublequote=False,
      escapechar='\\',
      quotechar="'",
      strict=True
    )

    writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
    for reader_row in reader:
      for column in reader_row:
        # If our current string is empty...
        if len(column) == 0 or column == 'NULL':
          latest_row.append(chr(0))
          continue

        # If our string starts with an open paren
        if column[0] == "(":
          # Assume that this column does not begin
          # a new row.
          new_row = False
          # If we've been filling out a row
          if len(latest_row) > 0:
            # Check if the previous entry ended in
            # a close paren. If so, the row we've
            # been filling out has been COMPLETED
            # as:
            #    1) the previous entry ended in a )
            #    2) the current entry starts with a (
            if latest_row[-1][-1] == ")":
              # Remove the close paren.
              latest_row[-1] = latest_row[-1][:-1]
              new_row = True
            # If we've found a new row, write it out
            # and begin our new one
            if new_row:
              writer.writerow(latest_row)
              latest_row = []
            # If we're beginning a new row, eliminate the
            # opening parentheses.
            if len(latest_row) == 0:
              column = column[1:]

        # Add our column to the row we're working on.
        latest_row.append(column)
        # At the end of an INSERT statement, we'll
        # have the semicolon.
        # Make sure to remove the semicolon and
        # the close paren.
        if latest_row[-1][-2:] == ");":
          latest_row[-1] = latest_row[-1][:-2]
          writer.writerow(latest_row)

  def unzip(self, filename, unzipped_name):
    file_path = os.path.join(os.getcwd(), self.data_directory, filename)
    unzipped_path = os.path.join(os.getcwd(), self.data_directory, unzipped_name)
    zf = ZipFile(file_path, "r")

    if os.path.exists(unzipped_path) and hashlib.md5(open(unzipped_path, 'rb').read()).hexdigest() == '309dfe5898639e1c598ddf5e5205ce6b':
        click.echo(click.style('[1/1] File %s already exits. Skipping' % unzipped_name, fg='yellow'))
    else:
      if os.path.exists(unzipped_path):
        click.echo(click.style('[1/1] File %s is damaged or incomplete, reextracting...' % unzipped_name, fg='red'))
        os.remove(unzipped_path)

      for name in zf.namelist():
        click.echo("Extracting %s..." % name)
        data = self.unzip_in_chunks(zf, name, unzipped_path)

    with open(unzipped_path, 'rU') as f:
      click.echo("Converting %s to CSV..." % unzipped_name)
      bar = click.progressbar(length=2316, show_pos=True, show_percent=True)
      tables = ['wtp_data_petitions', 'wtp_data_signatures']

      for t in tables:
        existing_csv_path = os.path.join(os.getcwd(), self.data_directory, t + '.csv')
        os.remove(existing_csv_path) if os.path.exists(existing_csv_path) else None

      for line in f:
        target_table = self.target_table(line, ['wtp_data_petitions', 'wtp_data_signatures'])
        if target_table:
          cleaned_line = line.replace('\\r', '').replace('\\n', '').replace('"', '')

          values = self.get_values(cleaned_line)
          if self.values_sanity_check(values):
            csv_path = os.path.join(os.getcwd(), self.data_directory, target_table + '.csv')
            self.parse_values(values, open(csv_path, 'a+'))
            bar.update(1)

      click.echo()