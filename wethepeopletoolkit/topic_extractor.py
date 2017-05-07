import click
from wethepeopletoolkit.top_petitions import TopPetitions

class TopicExtractor:
  def __init__(self, spark_home):
    self.spark_home = spark_home
    self.top_petitions = TopPetitions(self.spark_home)
    self.colors = ['green', 'blue', 'red', 'yellow', 'magenta', 'cyan']

  def print_top_words(self, model, feature_names, n_top_words, cluster_idx):
    for topic_idx, topic in enumerate(model.components_):
      click.echo(click.style("Topic #%d:" % (topic_idx + 1), fg=self.colors[cluster_idx % 6]))
      click.echo(" ".join([feature_names[i] for i in topic.argsort()[:-n_top_words - 1:-1]]))

  def petition_content(self, cluster_id, petition_sample_size):
    petitions = self.top_petitions.top_n_for_cluster(cluster_id, petition_sample_size)
    return petitions.rdd.map(lambda p: p.Title + ' ' + p.Body).collect()

  def topic_extraction(self, cluster_ids, extraction_method, number_of_topics, words_per_topic, petition_sample_size):
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
    from sklearn.decomposition import NMF, LatentDirichletAllocation

    click.echo()
    clusters_data = map(lambda cid: self.petition_content(cid, petition_sample_size), cluster_ids)

    for i, data_samples in enumerate(clusters_data):
      vectorizer_class = { 'lda': CountVectorizer, 'nmf': TfidfVectorizer }[extraction_method]

      vectorizer = vectorizer_class(max_df=0.95, min_df=2, max_features=1000, stop_words='english')
      features = vectorizer.fit_transform(data_samples)

      if extraction_method == 'lda':
        results = LatentDirichletAllocation(n_topics = number_of_topics, max_iter = 5, learning_method = 'online', learning_offset = 50.0, random_state = 0).fit(features)
      elif extraction_method == 'nmf':
        results = NMF(n_components = number_of_topics, random_state = 1, alpha = .1, l1_ratio = .5).fit(features)
      else:
        raise
      
      click.echo(click.style("\nTopics for cluster %s" % cluster_ids[i], fg=self.colors[i % 6]))
      click.echo('=' * 30 + '\n')

      self.print_top_words(results, vectorizer.get_feature_names(), words_per_topic, i)