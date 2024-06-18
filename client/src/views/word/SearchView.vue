<template>
  <div v-if="error">{{ error }}</div>
  Word search: {{ wordStr }}
  <ol>
    <li v-for="word in wordsList" :key="word.id" class="word-element">
      {{ word.lem }}, {{ word.pos }}, {{ word.synset }}, {{ word.declination }} - {{ word.definition }}
    </li>
  </ol>
</template>

<script>
import { useRouter } from 'vue-router'

export default {
  name: 'WordsList',
  data() {
    return {
      error: '',
      wordStr: '',
      wordsList: []
    }
  },
  mounted() {
    this.searchWords()
  },
  methods: {
    searchWords() {
      const router = useRouter()
      const query = router.currentRoute.value.query
      if (query.q) {
        this.wordStr = query.q
        fetch(`${process.env.VUE_APP_API_URL}/words/find/${this.wordStr}`)
        .then(response => response.json())
        .then(data => (this.wordsList = data))
        .catch(err => this.error = err)
      }
    }
  }
}
</script>

<style>
.word-element {
  text-align: left;
}
</style>