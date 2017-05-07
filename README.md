We the People analysis toolkit
==============================

[![PyPI version](https://img.shields.io/pypi/v/wethepeopletoolkit.svg)]()
[![PyPI license](https://img.shields.io/pypi/l/wethepeopletoolkit.svg)]()

During the Obama administration the [“We the People”](https://petitions.obamawhitehouse.archives.gov) petitioning system was established, to let US residents engage with issues they care about; the project gathered over 20 million signatures on almost 4000 signatures over five years (2011 – 2016). This provides a very exciting way to group states not based on party affiliation, but on their levels of engagement on actual issues (petitions).

This toolkit provides tools to visualize states by their level of similarity/difference, to create novel clusterings of the electoral map, and generate insights about those clusters. It is built with Python 2.7 and uses [Spark](http://spark.apache.org/), [Hive](https://hive.apache.org/), [SciPy](https://www.scipy.org/), [scikit-learn](http://scikit-learn.org/stable/) and [Matplotlib](https://matplotlib.org/).

## Installation

The toolkit is available as a Python package:

```
pip install wethepeopletoolkit
```

#### Prerequisites

The following **won't** be installed with the toolkit, but need to be installed for everything to work smoothly:

- Apache Spark 2+
- Hive
- PyQT4

## Examples

2-D projection of states, colored by party affiliation:

```
$ wethepeopletoolkit projection --show-party-affiliation --z-score-exclude 1
```

![2-D projection of states](https://cloud.githubusercontent.com/assets/636814/25782254/03cc9076-333f-11e7-9d93-722a66242173.png)
<br><br>

K-means clustering of states with 6 clusters, z-score > 1 exclusion during initial centroid clustering, and PCA applied as a pre-processing step:

```
$ wethepeopletoolkit cluster -n 6 -model-type kmeans --pca --z-score-exclude 1
```

<img src='https://cloud.githubusercontent.com/assets/636814/25782508/4e6cb48a-3344-11e7-9192-b24cb0731387.png' width='600'>
<br><br>

Evaluating the effectiveness of models with 2-8 clusters, using the Silhouette score and Euclidian distance:

```
$ wethepeopletoolkit cluster-evaluation -m spectral --range 2 8 --evaluation-metric silhouette
````

![Cluster evaluation plot](https://cloud.githubusercontent.com/assets/636814/25782535/c424d928-3344-11e7-939d-847ed56f585c.png)
<br><br>

The top 10 most signed petitions for Utah:

```
$ wethepeopletoolkit top-petitions 27 -n 10
```
<img src='https://cloud.githubusercontent.com/assets/636814/25782548/1ac2d19a-3345-11e7-8e6e-c9d1d081368f.png' width='600'>
<br>

Topic extraction for the 500 most signed petitions for Washington, Oregon and Colorado:

```
$ wethepeopletoolkit topic-extraction 8y7nF3D1
```

<img src='https://cloud.githubusercontent.com/assets/636814/25782566/73e8deae-3345-11e7-9af7-293415b7a365.png' width='600'>

## Usage

```
$ wethepeopletoolkit
Usage: wethepeopletoolkit [OPTIONS] COMMAND [ARGS]...

Options:
  -d, --data-directory PATH  Path to data (./data/ by default).
  -S, --spark-home PATH      Path to Spark installation (automatically
                             discovered by default).
  --help                     Show this message and exit.

Commands:
  fetch-data          Download and preprocess the neccessary data.
  projection          Create a 2-D projection of states w/ PCA.
  cluster             Performs clustering on states based on their...
  cluster-evaluation  Shows comparisons of performance as number of...
  top-petitions       Displays the top N most signed petitions for...
  topic-extraction    Performs topic extraction on the top N most...
```

#### Fetching data

The toolkit can automatically fetch and process the data necessary for clustering, topic extraction etc.

```
$ wethepeopletoolkit fetch-data --help
Usage: wethepeopletoolkit fetch-data [OPTIONS]

  Download and preprocess the neccessary data. By default, files will be
  downloaded to the directory ./data/

Options:
  --keep-files  Don't delete files after they've been extracted, converted and
                processes.
  --force       Recreate Hive tables, even if they already exist
  --help        Show this message and exit.
````

#### 2-D projection visualization

Generates a 2-D projection of the states, based on Principal Component Analysis of a 50 x 3892 matrix, describing the number of signatures per 1,000 residents for every combination of petition and state. States which have similar patterns of engagement towards petitions will be closer together, those with dissimilar patterns will be further apart.

```
$ wethepeopletoolkit projection --help
Usage: wethepeopletoolkit projection [OPTIONS]

  Create a 2-D projection of states w/ PCA. States which react more
  similarly to petitions will be closer together.

Options:
  -p, --show-party-affiliation  Color states based on their affiliation to
                                Republicans/Democrats. Based on the 2014 Cook
                                Partisan Voting Index.
  --show-points                 Show points next to state labels.
  -z, --z-score-exclude FLOAT   Don't show points with a z-score higher than
                                this value. For example, -z 3.0 would exclude
                                points more than 3 standard deviations from
                                the mean. If the value is 0, no points are
                                excluded.
  --help                        Show this message and exit.
```

#### Clustering

Clusters the states, based on the similarity of signature engagement, uses scikit-learn under the hood.

```
$ wethepeopletoolkit cluster --help
Usage: wethepeopletoolkit cluster [OPTIONS]

  Performs clustering on states based on their similar reactions to
  petitions.

Options:
  -n, --number-of-clusters INTEGER RANGE
                                  The number of clusters to generate. Must be
                                  between 2 and 50.
  -m, --model-type [kmeans|spectral]
                                  The type of clustering model to use. Valid
                                  values:
                                  kmeans: K-means clustering,
                                  spectral: spectral clustering
  --pca                           Performs PCA (dimensionality reduction) to
                                  reduce the data to two dimensions before
                                  clustering.
  -z, --z-score-exclude FLOAT     Don't show points with a z-score higher than
                                  this value. For example, -z 3.0 would
                                  exclude points more than 3 standard
                                  deviations from the mean. If the value is 0,
                                  no points are excluded. This can only be
                                  used in conjunction with K-means clustering.
  --seed INTEGER                  Sets the random seed for clustering.
  --help                          Show this message and exit.
```

#### Cluster evaluation

Evaluates the effectiveness different cluster numbers, and plots the results. Can use Silhouette score, Calinski and Harabaz score or inertia (K-means clustering only). Silhouette score can be used in conjunction with any distance measure supported by [`sklearn.metrics.pairwise.pairwise_distances`](http://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.pairwise_distances.html#sklearn.metrics.pairwise.pairwise_distances) (specified with the `--distance` option).

```
$ wethepeopletoolkit cluster-evaluation --help
Usage: wethepeopletoolkit cluster-evaluation [OPTIONS]

  Shows comparisons of performance as number of clusters is varied.

Options:
  -r, --range INTEGER RANGE...    The beginning and end of the range of
                                  cluster numbers to test. For example, -r 2 5
                                  would evaluate four models with 2, 3, 4 and
                                  5 clusters. Both numbers must be between 2
                                  and 50.
  -e, --evaluation-metric [silhouette|calinski_harabaz|inertia]
  --distance [cityblock|cosine|euclidean|l1|l2|manhattan|braycurtis|canberra|chebyshev|correlation|dice|hamming|jaccard|kulsinski|mahalanobis|matching|minkowski|rogerstanimoto|russellrao|seuclidean|sokalmichener|sokalsneath|sqeuclidean|yule]
                                  The type of distance measure to used to
                                  calculate the silhouette score.
  -m, --model-type [kmeans|spectral]
                                  The type of clustering model to use. Valid
                                  values:
                                  kmeans: K-means clustering,
                                  spectral: spectral clustering
  --pca                           Performs PCA (dimensionality reduction) to
                                  reduce the data to two dimensions before
                                  clustering.
  -z, --z-score-exclude FLOAT     Don't show points with a z-score higher than
                                  this value. For example, -z 3.0 would
                                  exclude points more than 3 standard
                                  deviations from the mean. If the value is 0,
                                  no points are excluded. This can only be
                                  used in conjunction with K-means clustering.
  --seed INTEGER                  Sets the random seed for clustering.
  --help                          Show this message and exit.
```

#### Top petitions

Displays the top petitions for a given cluster ID (provided by the `cluster` command). Useful for understanding the most important issues for a given cluster.

```
$ wethepeopletoolkit top-petitions --help
Usage: wethepeopletoolkit top-petitions [OPTIONS] CLUSTER_ID

  Displays the top N most signed petitions for a given cluster. Defaults to
  the top 10. CLUSTER_ID is the Base58 encoded cluster ID (as provided by
  the 'cluster' command).

Options:
  -n, --top-n INTEGER RANGE  Dictates what number of the top petitions (by
                             number of signatures) are displayed.
  --no-truncation            Always show the entire petition titles.
  -b, --show-body            Additionally show the body of the petitions.
  --help                     Show this message and exit.
```

#### Topic extraction

The topic extractor takes one or more cluster IDs, then takes the top N most signed petitions for each cluster (500 by default) and extracts the most important topics present in that corpus, using either latent Dirichlet Allocation (LDA) or non-negative Matrix Factorization (NMF). Useful for comparing and contrasting the different key themes present in the most key petitions for each cluster.

```
$ wethepeopletoolkit topic-extraction --help
Usage: wethepeopletoolkit topic-extraction [OPTIONS] [CLUSTER_IDS]...

  Performs topic extraction on the top N most signed petitions for given
  cluster(s). Uses the top 500 petitions by default, and constructs 10
  topics of 10 words. Extraction can be performed with latent Dirichlet
  allocation (LDA) or non-negative matrix factorization (NMF). CLUSTER_IDS
  are the Base58 encoded cluster IDs (as provided by the 'cluster' command)
  that you want to display/compare.

Options:
  -m, --extraction-method [lda|nmf]
                                  The type of topic extraction model to use.
                                  Valid values:
                                  lda: latent Dirichlet
                                  allocation, nmf: non-negative matrix
                                  factorization
  -P, --petition-sample-size INTEGER RANGE
                                  Dictates what number of the top petitions
                                  (by number of signatures) are used as the
                                  data for topic extraction (default 500).
  -n, --number-of-topics INTEGER RANGE
                                  How many topics to extract (1 - 100, default
                                  10).
  -w, --words-per-topic INTEGER RANGE
                                  How many words should be in each topic (1 -
                                  100, default 10).
  --help                          Show this message and exit.
```

## Development

To develop the toolkit, first clone this repository:

```
git clone git@github.com:alexpeattie/wethepeopletoolkit.git
cd wethepeopletoolkit
```

If you don't have virtualenv installed, install it:

```
pip install virtualenv
```

Next create a new virtual environment:

```
virtualenv venv --system-site-packages
. venv/bin/activate
```

Then install the package in editable mode:

```
pip install --editable .
```

## Contributing

Pull requests are very welcome! Please try to follow these simple rules if applicable:

* Fork it (https://github.com/alexpeattie/wethepeopletoolkit/fork)
* Create your feature branch (`git checkout -b my-new-feature`)
* Commit your changes (`git commit -am 'Add some feature'`)
* Push to the branch (`git push origin my-new-feature`)
* Create a new Pull Request

## License

All code is released under the MIT license. (See [License.md](./License.md))

## Author

Alex Peattie / [alexpeattie.com](https://alexpeattie.com/) / [@alexpeattie](https://twitter.com/alexpeattie) 